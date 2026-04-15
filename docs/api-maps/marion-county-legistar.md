# Marion County FL -- Legistar OData API Map (CR)

Last updated: 2026-04-14

## 1. Platform Overview

| Property | Value |
|----------|-------|
| Platform | Legistar (Granicus) |
| API Base URL | `https://webapi.legistar.com/v1` |
| Client Slug | `marionfl` |
| Portal URL | `https://marionfl.legistar.com` |
| Auth | Anonymous |
| Protocol | OData v3 over REST (JSON) |
| User-Agent | `CommissionRadar/1.0` |
| Page size | 100 (`$top`) |
| Request delay | 0.5s |
| Registry status | `cr: live` per `county-registry.yaml` L211-215 |
| Registry note | "Legistar OData API. 4 listings in 60-day window (agendas only — minutes not yet posted for recent meetings). PDF download validated." |

### Configured bodies (CountyData2)

| Slug | Body | `body_names` | `commission_type` | `scraping.platform` |
|------|------|--------------|-------------------|---------------------|
| `marion-county-bcc` | Marion County BCC | `["Board of County Commissioners"]` | `bcc` | `legistar` |
| `marion-county-pz` | Marion County P&Z | `["Planning & Zoning Commission"]` | `planning_board` | `legistar` |
| `marion-county-boa` | Marion County BOA | -- | `board_of_adjustment` | **`manual`** |

## 2. Probe (2026-04-14)

```
GET https://webapi.legistar.com/v1/marionfl/bodies
-> HTTP 200, 11,591 bytes, application/json
   Array of 21 body objects.
```

### Bodies on Legistar (21 total)

| BodyId | Body Name | Type | Tracked |
|--------|-----------|------|---------|
| 138 | Board of County Commissioners | Primary Legislative Body | **YES** (`marion-county-bcc`) |
| 139 | Planning & Zoning Commission | Planning & Zoning Commission | **YES** (`marion-county-pz`) |
| 191 | Board of County Commissioners Workshop | Workshop | NO |
| 193 | Board of County Commissioners Budget Meeting | Primary Legislative Body | NO |
| 194 | Board of County Commissioners Public Hearing Meeting | Public Hearings | NO |
| 203 | Tourist Development Council | Tourist Development Council | NO |
| 204 | License Review Board | License Review Board | NO |
| 205 | Code Enforcement Board | Code Enforcement Board | NO |
| 206 | **Board of Adjustment** | Board of Adjustment | **NO** — on Legistar but YAML is `platform: manual` |
| 207 | Land Development Regulation Commission | Land Development Regulation Commission | NO |
| 208 | Community Redevelopment Agency | Community Redevelopment Agency | NO |
| 209 | Development Review Committee | Development Review Committee | NO |
| 219 | Fire Rescue and EMS Advisory Board | Fire Rescue and EMS Advisory Board | NO |
| 220 | Districts 5 & 24 Medical Examiner Advisory Committee | Districts 5 and 24 Medical Examiner Advisory Committee | NO |
| 221 | Parks & Recreation Advisory Council | Parks & Recreation Advisory Council | NO |
| 222 | Dog Classification Board | Dog Classification Board | NO |
| 223 | Public Safety Coordinating Council | Public Safety Coordinating Council | NO |
| 225 | Tourist Development Council Workshop | Tourist Development Council Workshop | NO |
| 229 | Board of County Commissioners Planning and Zoning | Board of County Commissioners Planning and Zoning | NO |
| 231 | Special Board Meeting | Special Board Meeting | NO |
| 232 | Local Mitigation Strategies | Local Mitigation Strategies | NO |

## 3. Events Endpoint

### Request

```
GET https://webapi.legistar.com/v1/marionfl/events
```

Per-run iteration: once for BCC, once for P&Z. (BOA skipped — `platform: manual` per YAML.)

### OData parameters

| Parameter | Used | Value |
|-----------|------|-------|
| `$filter` | YES | `EventDate ge datetime'{start}' and EventDate le datetime'{end}' and EventBodyName eq '{body}'` |
| `$orderby` | YES | `EventDate desc` |
| `$top` | YES | 100 |
| `$skip` | YES | paginated offset |

### Headers

```
User-Agent: CommissionRadar/1.0
Accept: application/json
```

## 4. Event Fields

Same contract as all Legistar tenants (see `polk-county-legistar.md` Section 3 for the canonical field table). Key fields used by CommissionRadar: `EventId`, `EventBodyName`, `EventDate`, `EventAgendaFile`, `EventMinutesFile`, `EventAgendaStatusName`, `EventMinutesStatusName`.

## 5. What We Extract / What a Future Adapter Would Capture

One `DocumentListing` per non-null agenda/minutes PDF per event:

| DocumentListing field | Source | Value pattern |
|-----------------------|--------|---------------|
| `title` | Computed | `"{EventBodyName} Agenda - {meeting_date}"` / `"... Minutes - ..."` |
| `url` | `EventAgendaFile` / `EventMinutesFile` | Direct PDF URL |
| `date_str` | `EventDate[0:10]` | `YYYY-MM-DD` |
| `document_id` | `EventId` | Stringified |
| `document_type` | Hardcoded | `"agenda"` / `"minutes"` |
| `file_format` | Hardcoded | `"pdf"` |
| `filename` | Computed | `"Agenda_{date}_{EventId}.pdf"` |

Dedup key: `"agenda-{EventId}"` / `"minutes-{EventId}"`.

## 6. Auth / Bypass

Anonymous. No API key, no cookies, no captcha.

## 7. What We Extract vs What's Available

| Data Category | Extracted | Source | Not Extracted | Notes |
|---------------|-----------|--------|---------------|-------|
| Event ID, date, body | YES | Event* fields | GUID, row version | -- |
| Agenda / Minutes PDF | YES | EventAgendaFile / EventMinutesFile | Status, last-published timestamp | EventAgendaStatusName, etc. |
| Location, portal URL, video | NO | -- | Available | EventLocation, EventInSiteURL, EventVideoPath |
| Agenda items, votes, matters | NO | -- | Via `/eventitems`, `/votes`, `/matters` | Separate endpoints |

## 8. Known Limitations and Quirks

1. **BOA is on Legistar but configured as `platform: manual`.** BodyId 206 `"Board of Adjustment"` is active on the Marion Legistar instance (MeetFlag=1, Active=1). However `marion-county-boa.yaml` has `scraping.platform: manual` — the scraper skips it. Reason: BOA documents are uploaded manually per extraction_notes ("Board of Adjustment — handles variances and appeals, outside core tracking scope."). **If tracking scope expands to BOA, the YAML can flip to `legistar` with `body_names: ["Board of Adjustment"]`.**
2. **Four BCC variants (138, 191, 193, 194).** Regular BCC (138), Workshop (191), Budget (193), Public Hearing (194). We track only 138. Public Hearings (194) in particular often carry zoning / land-use items that overlap with P&Z scope — consider augmenting sweeps if land-use coverage is required.
3. **"Board of County Commissioners Planning and Zoning" (229).** A distinct body from 139 (`Planning & Zoning Commission`). Body 229 is the BCC sitting in its P&Z capacity — often the final-decision body on items the P&Z Commission (139) recommended. NOT tracked currently; adding would capture final-approval events.
4. **Registry note: 4 listings in 60-day window, agendas only.** Per `county-registry.yaml` L215: "minutes not yet posted for recent meetings". Expect `EventMinutesFile: null` on recent events — the scraper handles this by emitting only the agenda listing.
5. **PDF download validated.** Marion's Legistar CDN serves PDFs directly; no additional auth/redirect needed to fetch the file at `EventAgendaFile`.
6. **21 bodies — largest count among the 4 Legistar-tenant counties in this batch.** Marion exposes a richer committee structure on Legistar. Of the 21, most advisory bodies (Dog Classification, Parks & Rec Advisory, etc.) are not candidates for CountyData2 tracking.
7. **Ampersand vs. "and".** Marion uses `"Planning & Zoning Commission"` (ampersand). Seminole uses `"Planning and Zoning Commission"` (word). Body-name filters MUST match exactly — Hernando and Marion share the ampersand form.
8. **`has_duplicate_page_bug: false`** in both YAMLs — no mitigation needed for the Legistar agenda-pagination bug seen on some tenants.
9. **No rate limit documented.** 0.5s inter-request delay is conservative; Marion's 21 bodies × multiple months of pagination will still complete quickly.
10. **MPO not present.** Marion does not have a Metropolitan Planning Organization listed on its Legistar instance; Hernando does. If transportation planning coverage becomes a goal, Marion would require a separate source (state DOT regional office).

Source of truth: `county-registry.yaml` L211-215 (`marion-fl.projects.cr`), `modules/commission/config/jurisdictions/FL/marion-county-bcc.yaml`, `modules/commission/config/jurisdictions/FL/marion-county-pz.yaml`, `modules/commission/config/jurisdictions/FL/marion-county-boa.yaml`, live probe of `https://webapi.legistar.com/v1/marionfl/bodies` (2026-04-14, HTTP 200, 21 bodies), Legistar contract shared per `docs/api-maps/polk-county-legistar.md`.
