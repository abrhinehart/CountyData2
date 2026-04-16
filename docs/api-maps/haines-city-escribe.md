# Haines City FL — eScribe API Map (CR)

Last updated: 2026-04-16
Session of record: Session G (commit `76a7d7c`)
Recon method: anonymous HTTPS probes + WSDL dump + live JSON endpoint exercise

## 1. Platform Overview

| Property | Value |
|----------|-------|
| Platform family | eScribe (Diligent / OnBoard-family meeting management) |
| Tenant host | `pub-hainescity.escribemeetings.com` |
| Tenant URL pattern | `pub-<slug>.escribemeetings.com` — the scraper keys off `tenant_host` YAML field |
| Server stack | ASP.NET WebForms + ASP.NET AJAX PageMethods + ASMX web service + Syncfusion EJ2 chrome |
| CDN / WAF | Cloudflare (CF-RAY header, `__cf_bm` session cookie) |
| Auth | Anonymous read. No login surface exposed on the public subdomain. |
| Rate limiting | None observed at 180-day scrape volumes. Cloudflare challenges the default Python `User-Agent` on `FileStream.ashx`; an explicit UA (`CommissionRadar/1.0`) is accepted. |
| Transport security | TLS chain terminates at the Comodo **AAA Certificate Services** root — not shipped by current `certifi`. Production hosts with an up-to-date OS trust store or the `truststore` package handle this transparently; `requests`-only environments need a combined CA bundle via `REQUESTS_CA_BUNDLE`. |
| CountyData2 adapter | `modules/commission/scrapers/escribe.py` (Session G, commit `76a7d7c`) |
| Jurisdiction configs | `modules/commission/config/jurisdictions/FL/haines-city-cc.yaml`, `haines-city-pc.yaml` |
| Registry status | `live` — 12 CC + 3 PC agenda PDFs validated over the trailing 180 days |

### Probe quick-check (2026-04-16)

```
GET  https://pub-hainescity.escribemeetings.com/
  -> HTTP 200, text/html, ~200 KB
GET  https://pub-hainescity.escribemeetings.com/robots.txt
  -> HTTP 200, 33 bytes, blocks PetalBot only
POST https://pub-hainescity.escribemeetings.com/MeetingsCalendarView.aspx/GetCalendarMeetings
     Content-Type: application/json; charset=utf-8
     Body: {"calendarStartDate":"2025-10-18","calendarEndDate":"2026-04-16"}
  -> HTTP 200, {"d": [<47 meetings>]}
GET  https://pub-hainescity.escribemeetings.com/FileStream.ashx?DocumentId=27357
     User-Agent: CommissionRadar/1.0
  -> HTTP 200, application/pdf, 13,893,263 bytes, %PDF-1.7
```

---

## 2. Bodies / Categories

The calendar returns events tagged with a free-form `MeetingType` string. There is no discrete "bodies list" endpoint — the body manifest is derived by enumeration over a 180-day window.

| Count (180d) | MeetingType string | Nature | CountyData2 scope |
|---:|---|---|---|
| 10 | `City Commission Meeting` | Regular legislative | ✅ primary (`haines-city-cc`) |
| 2 | `City Commission Special Meeting` | Legislative | ✅ rolled into CC via `body_filter` |
| 3 | `Planning Commission` | Planning board (LPA) | ✅ primary (`haines-city-pc`) |
| 4 | `City Commission Workshop` | Deliberative, no formal actions | ⚠ excluded (no legislative output) |
| 5 | `CRA Meeting` | Community Redevelopment Agency | ⚠ land-use-adjacent, not enabled today |
| 9 | `Code Compliance` | Enforcement / variance | ❌ BOA/ZBA-style exclusion |
| 7 | `Red Light Camera` | Traffic enforcement | ❌ enforcement only |
| 3 | `Community Engagement` | Outreach | ❌ non-legislative |
| 3 | `Lakes Advisory Board` | Advisory | ❌ non-entitlement |
| 1 | `Canvassing Board` | Elections | ❌ elections only |

**In-scope `body_filter` values per config:**
- `haines-city-cc.yaml` → `["City Commission Meeting", "City Commission Special Meeting"]`
- `haines-city-pc.yaml` → `["Planning Commission"]`

---

## 3. Public Pages (GET)

Standard ASP.NET WebForms routing. All 200 unless noted.

| Path | Purpose | Notes |
|---|---|---|
| `/` | Landing + calendar | Alias for `/Default.aspx`. Renders the Syncfusion calendar client-side, populated via the `GetCalendarMeetings` PageMethod. |
| `/Default.aspx` | Same as `/` | |
| `/MeetingsCalendarView.aspx` | Same as `/` | Host page for most PageMethods (see §5). |
| `/Meeting.aspx?Id=<uuid>` | Single-meeting hub | 302 without a view param. |
| `/Meeting.aspx?Id=<uuid>&Agenda=Agenda&lang=English` | Agenda view | 200. Embeds document links + optional public-comment widget. |
| `/Meeting.aspx?Id=<uuid>&Minutes=Minutes&lang=English` | Minutes view | 302 on Haines (no published minutes). Would 200 on tenants that publish minutes. |
| `/Meeting.aspx?Id=<uuid>&Media=Media&lang=English` | Media view | 302 on Haines (no video). |
| `/Meeting.aspx?Id=<uuid>&Video=Video…` | Video view | 302 on Haines. |
| `/bundles/Meeting?v=<hash>` | Page-specific JS bundle (~22 KB) | Source of most PageMethod references. |
| `/bundles/WebFormsJs?v=<hash>` | WebForms runtime shim | |
| `/bundles/jquery` | jQuery bundle | |
| `/bundles/modernizr?v=<hash>` | Feature detection | |
| `/Content/css?v=<hash>` | Site CSS bundle | |
| `/Content/base/css?v=<hash>` | Vendor CSS bundle | |

**Admin / login surface:** none on the public subdomain. `/Admin`, `/Admin/Login.aspx`, `/Login`, `/Login.aspx`, `/Account/Login` all 404. The admin tenant lives on a separate host.

---

## 4. File Handler (GET)

`GET /FileStream.ashx?DocumentId=<n>` — the only `.ashx` handler on the tenant. Streams the binary document directly.

**Required:** `User-Agent` header set to any non-default value (Cloudflare 403s the Python stdlib default).

**Response metadata** (sample `DocumentId=27357`, 13.9 MB Feb 5 2026 CC agenda packet):

```
HTTP/1.1 200 OK
Content-Type: application/pdf
Content-Length: 13893263
Content-Disposition: inline;filename="Agenda Package - CCRM_Feb05_2026.pdf";
Cache-Control: private
cf-cache-status: DYNAMIC
strict-transport-security: max-age=31536000
```

**`DocumentId` properties:**
- Monotonically increasing global integer per tenant.
- Observed Haines range: ~15,562 (Feb 2023) → ~29,003 (Apr 2026).
- Not guessable; must be harvested from `MeetingDocumentLink.Url` in the calendar response.

---

## 5. JSON PageMethods (POST)

ASP.NET AJAX pattern: `POST /<Page>.aspx/<MethodName>` with `Content-Type: application/json; charset=utf-8`. Responses wrap payload in `{"d": ...}`. Parameter errors return a generic `{"Message": "...", "StackTrace": "", "ExceptionType": ""}` envelope.

### 5.1 `MeetingsCalendarView.aspx` PageMethods

| Method | Body shape | Exercised? | Purpose |
|---|---|---|---|
| `GetCalendarMeetings` | `{"calendarStartDate":"YYYY-MM-DD","calendarEndDate":"YYYY-MM-DD"}` | ✅ (primary scrape surface) | Returns array of `MeetingInfo` records (see §7). |
| `PastMeetings` | (undocumented) | ⚠ requires undocumented params | Likely archival/pagination beyond calendar window. |
| `AgendaItemConflictsGetAll` | (undocumented) | ⚠ requires undocumented params | Conflict-of-interest declarations per agenda item. |
| `SubscriptionListsGetSubscriptions` | (undocumented) | — | Citizen email-subscription workflow: list available bodies. |
| `SubscriptionListsAddNewSubscriber` | (undocumented) | — | Workflow: add subscription. |
| `SubscriptionListsSaveEmailAndSendOtp` | (undocumented) | — | Workflow: send OTP. |
| `SubscriptionListsSubmitEnterOtpBtnClick` | (undocumented) | — | Workflow: verify OTP. |
| `SubscriptionListsUpdateSubscriptions` | (undocumented) | — | Workflow: commit subscription preferences. |

### 5.2 `Meeting.aspx` PageMethods

| Method | Purpose |
|---|---|
| `GeneratePublicComment` | Submit a citizen public comment on a live or pending agenda item. |
| `GeneratePublicCommentIcon` | Render a visual status icon for a submitted comment. |

---

## 6. ASMX Web Service (`/GetSearchData.asmx`)

Classic ASP.NET SOAP service exposed at `/GetSearchData.asmx`. Supports SOAP 1.1, SOAP 1.2, and HTTP POST form-encoded transports.

- `GET /GetSearchData.asmx` — HTML operation index (200)
- `GET /GetSearchData.asmx?WSDL` — WSDL 1.1 XML, 16,953 bytes
- `GET /GetSearchData.asmx?disco` — DISCO discovery XML

**Operations declared in WSDL:**

| Operation | WSDL-declared parameters | Notes |
|---|---|---|
| `GetSearchMeetingData` | `searchText`, `filterbyMeetingTypeIds`, `filterbyMeetingTypeNames`, `filterByDate`, `filterByMeetingDocumentTypes`, `filterByExtensions`, `filterByLanguage` | Requires additional undeclared params: `includeConflicts`, `includeComments` (surfaced via live errors). |
| `GetConflictsData` | `searchText`, `filterbyMeetingTypeIds`, `filterByDate`, `filterByConflictMemberIds`, `filterbyMeetingTypeNames` | Conflict-of-interest search. |
| `AgendaItemHistoryListView` | `filterbyMeetingTypeIds`, `filterbyMeetingTypeNames`, `filterByDate`, `filterByStage`, `filterByStatus`, `filterByDepartmentNames` | Per-item lifecycle tracking. |
| `GetLegislationData` | (not emitted clearly by WSDL) | Legislation cross-reference. |

**Known quirk:** the WSDL parameter list is incomplete. Live calls reveal undeclared required params (ASP.NET `[WebMethod]` attribute drift). Full signatures are only reliably captured by inspecting a real browser session.

---

## 7. Data Model

### 7.1 `MeetingInfo` record

Returned by `GetCalendarMeetings`, one per meeting. 25 fields.

| Field | Type | Sample | Notes |
|---|---|---|---|
| `ID` | UUID | `4687c376-f6be-493f-a376-1c1564c327e8` | Stable per meeting. |
| `MeetingName` | string | `City Commission Workshop` | Usually matches `MeetingType`. |
| `StartDate` | string | `2026/02/19 18:00:00` | Local time, `YYYY/MM/DD HH:MM:SS`. |
| `FormattedStart` | string | `Thursday, February 19, 2026 @ 6:00 PM` | Display-ready. |
| `EndDate` | string | `2026/02/19 19:00:00` | Local time. |
| `Description` | HTML | `City Hall...620 E. Main Street, Haines City, FL 33844<br/>Phone: 863-421-9921` | Free-form, contains `<br/>`. |
| `Url` | absolute URL | `https://.../MeetingsCalendarView.aspx/Meeting?Id=<uuid>` | Redirects to `/Meeting.aspx?Id=<uuid>`. |
| `Location` | string | `City Hall Commission Chambers` | |
| `ShareUrl` | relative URL | `Sharing.aspx?u=<url-encoded-meeting-url>` | Social-share handler. |
| `MeetingType` | string | `City Commission Meeting` | **Primary body filter key.** |
| `ClassName` | string | `mt-19-19` | CSS class for calendar rendering. |
| `LanguageName` | string | `English` | Multi-language tenants have multiple records per meeting. |
| `HasAgenda` | bool | `true` | Whether an agenda has been published. |
| `Sharing` | bool | `true` | Whether sharing is enabled. |
| `MeetingDocumentLink` | array | (see 7.2) | Documents attached to the meeting. |
| `PortalId` | int | `<int>` | Internal tenant identifier. |
| `DelegationRequestLink` | string\|null | — | Citizen-delegation signup URL. |
| `HasLiveVideo` | bool | `false` | Live video currently streaming. |
| `HasVideo` | bool | `false` | Recorded video archived. |
| `HasVideoLivePassed` | bool | `false` | Previously-live recording exists. |
| `LiveVideoStandAloneLink` | string | `""` | Direct video URL when `HasLiveVideo=true`. |
| `MeetingPassed` | bool | `true` | `true` if `EndDate < now`. |
| `AllowPublicComments` | bool | `false` | Controls `GeneratePublicComment` availability. |
| `TimeOverride` / `TimeOverrideFR` | string | `""` | Display-time override (EN/FR). |
| `IsMP3` | bool | `false` | Audio-only recording flag. |

### 7.2 `MeetingDocumentLink` record

Nested array on each `MeetingInfo`. 14 fields per document.

| Field | Type | Notes |
|---|---|---|
| `CssClass` | string | Layout hint. |
| `Format` | string | `.pdf`, `HTML`, `.mp3`, `.mp4`, etc. |
| `Image` | HTML | `<i class='las la-file-pdf fa-lg'></i>` — Line Awesome icon markup. |
| `Title` | string | `Agenda (PDF)`, `Agenda Cover Page (PDF)`, etc. |
| `Type` | string | **Filter key.** Observed: `Agenda`, `AgendaCover`, `Minutes`, `MinutesPackage`, `Video`. |
| `Url` | string | `FileStream.ashx?DocumentId=<n>` for binary, `Meeting.aspx?Id=<uuid>&Agenda=Agenda&lang=English` for HTML view. |
| `LanguageId` | int | `9` = English. |
| `MeetingName` | string | Denormalized meeting name + date + time. |
| `AriaLabel` | string | Accessibility label. |
| `HasVideo` / `HasLiveVideo` / `HasLiveVideoPassed` | bool | Per-document video status. |
| `Sequence` | int\|null | Ordering hint. |
| `HiddenText` | string | Screen-reader suffix. |
| `LanguageCode` | string | `lang='en'` (HTML attribute fragment). |

**CountyData2 filter:** `Type == "Agenda"` **and** `Format == ".pdf"`. This excludes the HTML-view duplicate and the `AgendaCover` (single-page cover sheet).

---

## 8. What's Not There

Negative findings worth recording so the next recon doesn't re-probe:

- **No REST API.** `/api`, `/api/meetings`, `/api/v1`, `/Api/Public`, `/odata` all 404.
- **No iCal or RSS feed.** `/RSS.aspx`, `/iCal.aspx`, `/Calendar.ics`, `/Feed.ashx` all 404. The calendar is pure JSON PageMethods client-side.
- **No video streaming handler on this tenant.** `/LivestreamHandler.ashx`, `/Video.ashx` 404. `HasVideo`/`HasLiveVideo` are all `false` in current data.
- **No public bodies enumeration endpoint.** Body manifest is derived only by counting distinct `MeetingType` values across a time window.
- **No per-meeting metadata endpoint.** Everything flows through `GetCalendarMeetings` + the calendar's `MeetingDocumentLink` array.
- **No admin/login surface on the public subdomain.** Admin lives on a separate tenant.
- **No sitemap.xml.** `/sitemap.xml` 404.
- **No direct minutes publishing on Haines City tenant.** (Architectural support exists per view-variant routing; this city just doesn't use it.)

---

## 9. CountyData2 Integration Status

**Adapter:** `modules/commission/scrapers/escribe.py` (Session G)

**Config fields (YAML):**

```yaml
scraping:
  platform: escribe
  tenant_host: pub-hainescity.escribemeetings.com
  body_filter:
    - "City Commission Meeting"
    - "City Commission Special Meeting"
```

**Scrape flow:**

1. `POST /MeetingsCalendarView.aspx/GetCalendarMeetings` with the requested date window.
2. For each returned `MeetingInfo`:
   - Skip if `MeetingType` not in `body_filter`.
   - Iterate `MeetingDocumentLink`:
     - Skip unless `Type == "Agenda"` and `Format == ".pdf"`.
     - Extract `DocumentId` from `Url` regex; dedup on `DocumentId`.
     - Emit `DocumentListing(url="https://{tenant_host}/{Url}", date_str=<StartDate>, document_id=<DocumentId>, document_type="agenda", file_format="pdf")`.
3. `download_document` re-fetches `FileStream.ashx?DocumentId=<n>` with explicit `User-Agent`.

**Live validation (2026-04-16, 180-day window):**

| Config | Agenda PDFs | Cadence |
|---|---:|---|
| `haines-city-cc` | 12 | Biweekly |
| `haines-city-pc` | 3 | Monthly (some skipped) |
| **Total** | **15** | |

Script: `tmp/verify_haines_city_cc.py` (ephemeral).

---

## 10. Known Quirks

1. **Cloudflare UA filter on `FileStream.ashx`.** Default Python `User-Agent` gets 403. Any explicit UA header works; the scraper uses `CommissionRadar/1.0`.
2. **TLS chain to Comodo AAA root.** eScribe tenants use a cert chain that terminates at Comodo's `AAA Certificate Services` root. Current `certifi` does not ship that root. Production hosts with up-to-date OS trust stores or the `truststore` package handle this transparently; `requests`-only environments need a combined CA bundle via `REQUESTS_CA_BUNDLE`.
3. **WSDL parameter drift.** `GetSearchData.asmx` operations require params not emitted by the WSDL. Only reliably discoverable by observing a live browser session.
4. **Generic error envelope masks real failures.** PageMethods return `{"Message":"There was an error processing the request.","StackTrace":"","ExceptionType":""}` for both parameter errors and auth errors. No differentiation — you must inspect request logs on the server side or DevTools on the client side to distinguish.
5. **HTML `Description` field.** `MeetingInfo.Description` is free-form HTML with `<br/>` line breaks. Strip tags before parsing.
6. **Multi-language tenants emit duplicate records.** Each meeting appears once per `LanguageName`. Haines is English-only, so this doesn't bite here; French-language tenants return both EN and FR records per meeting.
7. **`MeetingType` string is not stable.** Municipalities can rename bodies via the admin UI. Exact-match `body_filter` should be audited annually.
8. **No rate limiting documented.** 180-day pulls complete in <2 seconds. Be courteous on bulk-historical backfills.

---

## 11. Reproduce the Recon

```bash
BASE="https://pub-hainescity.escribemeetings.com"

# Landing + robots
curl -sI "$BASE/"
curl -s "$BASE/robots.txt"

# WSDL
curl -s "$BASE/GetSearchData.asmx?WSDL" | head -5

# Calendar (primary)
curl -s -X POST "$BASE/MeetingsCalendarView.aspx/GetCalendarMeetings" \
  -H "Content-Type: application/json; charset=utf-8" \
  -d '{"calendarStartDate":"2025-10-18","calendarEndDate":"2026-04-16"}' \
  | python -c "import sys,json; d=json.load(sys.stdin); print(len(d['d']),'meetings')"

# Bundle enumeration (endpoint references)
curl -s "$BASE/bundles/Meeting?v=" | \
  grep -oE '"/[A-Za-z][A-Za-z0-9/._-]+\.(aspx|ashx|asmx|svc)[^"]*"' | sort -u

# FileStream sanity
curl -sI "$BASE/FileStream.ashx?DocumentId=27357" \
  -H "User-Agent: CommissionRadar/1.0"
```

---

## 12. Open Items / Follow-ups

- **Reverse-engineer `PastMeetings` pagination.** Could unlock deep-archive pulls beyond the default GetCalendarMeetings window.
- **Reverse-engineer `GetConflictsData` and `AgendaItemConflictsGetAll`.** Would surface commissioner-level conflict-of-interest data currently not captured.
- **CRA enablement decision.** `CRA Meeting` MeetingType exists with 5 events/180d. Land-use-adjacent but not currently in scope. Revisit if CRA action items become a tracked signal.
- **Cross-tenant reuse check.** Confirm the `escribe` adapter works unchanged against another FL eScribe tenant when the next one is onboarded. Cross-tenant drift risk: unknown until second tenant is seeded.

---

## Template Notes

This document is the canonical shape for per-jurisdiction-per-platform API maps in `docs/api-maps/`. Applied to any new portal, the required sections are:

1. **Platform Overview** — the one-table summary (platform family, host, stack, CDN, auth, rate limiting, transport security, adapter, configs, registry status).
2. **Bodies / Categories** — body manifest with in-scope / out-of-scope classification and reasoning. Respect the BOA/ZBA skip rule.
3. **Public Pages (GET)** — routing table with purpose and quirks.
4. **File Handler(s)** — how document downloads work + response headers + ID semantics.
5. **JSON / PageMethod / REST API (POST)** — every endpoint discovered, with body shape and exercise status.
6. **SOAP / ASMX / OData** — if present, operations + WSDL/schema link + quirks.
7. **Data Model** — key response records with field-by-field notes.
8. **What's Not There** — negative findings (so re-recon doesn't duplicate probes).
9. **CountyData2 Integration Status** — adapter path, config fields, scrape flow, live validation numbers.
10. **Known Quirks** — UA requirements, TLS issues, error-envelope ambiguity, etc.
11. **Reproduce the Recon** — literal curl/bash commands that regenerate the map's findings.
12. **Open Items / Follow-ups** — unexercised endpoints, open questions, cross-tenant validation needs.

Omit sections that don't apply (e.g. no SOAP on a REST-only portal). Keep sample payloads inline — the report must stand alone without external references.
