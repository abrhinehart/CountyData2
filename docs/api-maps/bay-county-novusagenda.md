# Bay County FL -- NovusAgenda API Map (CR)

Last updated: 2026-04-14

## 1. Platform Overview

| Property | Value |
|----------|-------|
| Platform | NovusAgenda (Novus AGENDA, Inc.) |
| Portal URL | `https://baycounty.novusagenda.com/agendapublic` |
| Protocol | Server-rendered ASP.NET WebForms (HTML scraping; no public OData API) |
| Auth | Anonymous |
| Document format | HTML agendas (per `scraping.document_formats: [html]`) |
| Jurisdiction config | `modules/commission/config/jurisdictions/FL/bay-county-bcc.yaml` |
| Registry status | `portal_down` (as of 2026-04-13, revisit monthly) |
| Parser | NovusAgenda scraper (built; server currently errors) |

### Probe (2026-04-14)

```
GET https://baycounty.novusagenda.com/agendapublic/
-> HTTP 200, body 1,453 bytes

GET https://baycounty.novusagenda.com/agendapublic/Meetings.aspx
-> HTTP 200, body 1,453 bytes (same error page)
```

Body contents (excerpt): the page renders the NovusAgenda error stub:

> An HTTP error occurred. . Please try again.

The `__VIEWSTATE` token is present, but the server returns an `Error.aspx?handler=Application_Error+-Global.asax` form target instead of the `Meetings.aspx` grid. This matches the registry annotation `portal_down`.

---

## 2. Bodies / Categories

Per the jurisdiction configs for Bay County:

| Body | Config slug | Scraping platform | Status |
|------|-------------|-------------------|--------|
| BCC (Board of County Commissioners) | `bay-county-bcc` | **novusagenda** (this doc) | Adapter built, portal errored |
| Planning Commission | `bay-county-pc` | **manual** -- CivicPlus AgendaCenter | Out of scope for this doc (`https://www.baycountyfl.gov/AgendaCenter`) |

The Planning Commission is NOT on NovusAgenda. Its documents are published through the county website's CivicPlus AgendaCenter and are classified as `platform: manual` in `bay-county-pc.yaml`. The BCC is the only Bay body scoped to this platform.

---

## 3. Events Endpoint (NovusAgenda public surface)

When operational, NovusAgenda public portals expose the following URL patterns (from other live NovusAgenda instances observed across Florida jurisdictions):

```
GET {base}/
GET {base}/Meetings.aspx
GET {base}/MeetingView.aspx?MeetingID={id}&MinutesMeetingID={id}&doctype=Agenda
GET {base}/AttachmentViewer.aspx?AttachmentID={id}&ItemID={id}
GET {base}/Boards.aspx
GET {base}/BoardMembers.aspx
```

There is no documented OData/JSON API; all responses are server-rendered HTML requiring `__VIEWSTATE` and `__EVENTVALIDATION` propagation for form POSTs. Because the Bay County instance is currently throwing errors at the entry point, none of these endpoints are reachable today.

### Expected GET payload pattern (for reference)

The `Meetings.aspx` page presents a grid of meetings filtered by Year / Board. Server-side state is driven via:

| Field | Purpose |
|-------|---------|
| `__VIEWSTATE` | Serialized page state (base64, 100-200+ KB) |
| `__VIEWSTATEGENERATOR` | `B005743D` (observed on the current error page) |
| `__EVENTVALIDATION` | Per-postback anti-CSRF token |
| `ctl00$ContentPlaceHolder1$ddlYear` | Year dropdown |
| `ctl00$ContentPlaceHolder1$ddlBoard` | Board filter |

---

## 4. Event Fields

The scraper (not currently running against a live portal) is designed to extract, per meeting row from the Meetings.aspx grid:

| Field | Type | Source |
|-------|------|--------|
| `meeting_id` | string | Link query param |
| `meeting_date` | date | Grid "Date" column |
| `meeting_time` | string | Grid "Time" column |
| `body_name` | string | Grid "Board" column (typically `"Board of County Commissioners"`) |
| `meeting_title` | string | Grid "Title" column |
| `agenda_url` | URL | `MeetingView.aspx?...&doctype=Agenda` link |
| `minutes_url` | URL (nullable) | `MeetingView.aspx?...&doctype=Minutes` link when present |
| `attachment_urls` | list[URL] | `AttachmentViewer.aspx` links inside the agenda view |

---

## 5. What We Extract

| DocumentListing Field | Source | Value Pattern |
|-----------------------|--------|---------------|
| `title` | Computed | `"Bay County BCC Agenda - {date}"` / `"Bay County BCC Minutes - {date}"` |
| `url` | Agenda / minutes link | `agendapublic/MeetingView.aspx?...` (HTML, not PDF) |
| `date_str` | Grid date column | `YYYY-MM-DD` |
| `document_id` | meeting_id | Numeric ID from `MeetingID` query param |
| `document_type` | Hardcoded | `"agenda"` or `"minutes"` |
| `file_format` | Hardcoded | `"html"` |
| `filename` | Computed | `"Agenda_{date}_{meeting_id}.html"` etc. |

No real-time test runs are possible until the portal returns to service.

---

## 6. Unused / Additional Endpoints

| Endpoint | Purpose | Used? |
|----------|---------|-------|
| `Boards.aspx` | Full board list | NO (single body hardcoded) |
| `BoardMembers.aspx` | Member roster | NO |
| `ImageLibrary.ashx?path=...` | Public logo / images | NO |
| Individual agenda item attachments (`AttachmentViewer.aspx?AttachmentID=N`) | Staff reports, backup | NO (agenda document only) |

---

## 7. What We Extract vs What's Available

| Data Category | Currently Extracted | Source | Available but Not Extracted | Source |
|---------------|--------------------|---------|-----------------------------|--------|
| Meeting Date | Would-be YES | Grid date | -- | -- |
| Meeting Time | NO | -- | Grid time column | Grid |
| Agenda HTML | Would-be YES | MeetingView link | -- | -- |
| Minutes HTML | Would-be YES | MeetingView link (when posted) | -- | -- |
| Individual agenda items | NO | -- | MeetingView renders items inline | MeetingView.aspx body |
| Staff report / attachment PDFs | NO | -- | AttachmentViewer.aspx links | Agenda HTML |
| Video / audio | NO | -- | Novus provides if jurisdiction uploads | Agenda HTML |
| Vote records | NO | -- | Generally NOT published on NovusAgenda public | -- |

Every row in this table is effectively blocked today because the portal returns the error stub before any grid loads.

---

## 8. Known Limitations and Quirks

1. **Portal is down (2026-04-13 -> 2026-04-14).** `https://baycounty.novusagenda.com/agendapublic/` returns HTTP 200 but the body is NovusAgenda's generic `Error.aspx` stub with the message "An HTTP error occurred. . Please try again." The `Meetings.aspx` endpoint returns the same error. Registry status is `portal_down`; revisit monthly.

2. **Planning Commission is not on NovusAgenda.** Bay County's Planning Commission publishes agendas through CivicPlus AgendaCenter (`baycountyfl.gov/AgendaCenter`) and is configured as `platform: manual` in `bay-county-pc.yaml`. This doc does not cover it; any future Planning Commission scraper must target the AgendaCenter layout.

3. **NovusAgenda has no public OData API.** Unlike Legistar, NovusAgenda exposes only ASP.NET WebForms pages. Any scraper must handle `__VIEWSTATE`, `__VIEWSTATEGENERATOR`, and `__EVENTVALIDATION` token propagation to paginate or filter the grid.

4. **Document format is HTML, not PDF.** NovusAgenda renders agendas as server-side HTML (`MeetingView.aspx`), so downstream downstream processing must handle HTML parsing rather than PDF text extraction. Some items may link out to PDF attachments via `AttachmentViewer.aspx`.

5. **Case numbers use `PZ YY-###` format.** Per extraction notes in `bay-county-bcc.yaml`: land-use and zoning items use case numbers of the form `PZ 22-218`. Paired items (companion amendments) use sequential numbers.

6. **Agendas are detail-poor.** Per the extraction notes: "Agendas are detail-poor: include case numbers and addresses but typically omit acreage, lot counts, and applicant names." Downstream enrichment via tax parcel / Property Appraiser is required for those fields.

7. **LDR text amendments.** Per extraction notes, Land Development Regulation text amendments are regulatory changes, not project-specific; the scraper sets `approval_type: text_amendment` on those items.

8. **County body cannot annex.** Unlike a city commission, a BCC cannot annex land. Any "annexation" keyword hit is a false positive and should be filtered out.

9. **Revisit cadence.** Because the portal has been down since at least 2026-04-13, this doc reflects the as-built scraper and expected endpoint shapes rather than a live field inventory. When NovusAgenda recovers, re-run the adapter and update Sections 3-5 with actual field names / XPath selectors.

10. **No scraper-side rate limiting documented.** NovusAgenda does not publish rate limits, but because each page load requires the full `__VIEWSTATE` round-trip, the scraper is implicitly self-limited by server responsiveness (~1s per page under normal load).

**Source of truth:** `modules/commission/config/jurisdictions/FL/bay-county-bcc.yaml`, `modules/commission/config/jurisdictions/FL/bay-county-pc.yaml`, `county-registry.yaml` (`bay-fl.projects.cr`), live probe against `https://baycounty.novusagenda.com/agendapublic/Meetings.aspx` returning the NovusAgenda error stub
