# Polk County FL -- Legistar OData API Map (CR)

Last updated: 2026-04-14

## 1. Platform Overview

| Property | Value |
|----------|-------|
| Platform | Legistar (Granicus) |
| API Base URL | `https://webapi.legistar.com/v1` |
| Client Slug | `polkcountyfl` |
| Portal URL | `https://polkcountyfl.legistar.com` |
| Auth | Anonymous -- no API key or token required |
| Protocol | OData v3 over REST (JSON) |
| User-Agent | `CommissionRadar/1.0` |
| Page Size | 100 (`$top`) |
| Request Delay | 0.5s between paginated requests |

### Bodies on Legistar

12 bodies are registered on the Polk County Legistar instance:

| BodyId | Body Name | Type | MeetFlag | ActiveFlag | Tracked by Us? |
|--------|-----------|------|----------|------------|----------------|
| 138 | Board of County Commissioners | Primary Legislative Body | 1 | 1 | **YES** (polk-county-bcc) |
| 139 | Polk Regional Water Cooperative | PRWC | 1 | 1 | NO |
| 140 | Polk County Land Use Hearing Officer | Land Use Hearing | 1 | 1 | NO |
| 228 | Planning Commission | Planning Commission | 1 | 1 | **YES** (polk-county-pz) |
| 239 | BCC (Organizational) | Legislative Body (Organizational) | 1 | 1 | NO |
| 240 | BCC (Budget) | Legislative Body (Tentative Budget) | 1 | 1 | NO |
| 241 | BCC (Final Budget) | Legislative Body (Final Budget) | 1 | 1 | NO |
| 246 | Transportation Planning Organization (TPO) | TPO Board | 1 | 1 | NO |
| 251 | TPO Technical Advisory Committee (TAC) | TPO TAC Committee | 1 | 1 | NO |
| 252 | TPO Transportation Disadvantaged Local Coordinating Board | TPO TD LCB | 1 | 1 | NO |
| 254 | Budget Office Documents | Legislative Body (Tentative Budget) | 0 | 1 | NO |
| 258 | Citizen's Healthcare Oversight Committee | Citizen's Healthcare Oversight Committee | 1 | 1 | NO |

### Bodies NOT on Legistar

| Body | Platform | Config Slug | Notes |
|------|----------|-------------|-------|
| Board of Adjustment | manual | polk-county-boa | Polk County uses a Land Use Hearing Officer instead of a traditional BOA. Config exists but platform is `manual`. |

---

## 2. Events Endpoint

### Request

```
GET https://webapi.legistar.com/v1/polkcountyfl/events
```

### OData Query Parameters

| Parameter | Used by Us? | Our Value | Notes |
|-----------|-------------|-----------|-------|
| `$filter` | YES | `EventDate ge datetime'{start}' and EventDate le datetime'{end}' and EventBodyName eq '{body}'` | OData filter expression |
| `$orderby` | YES | `EventDate desc` | Newest events first |
| `$top` | YES | `100` | Page size |
| `$skip` | YES | Incremented by 100 per page | Pagination offset |

### Headers

```
User-Agent: CommissionRadar/1.0
Accept: application/json
```

### Pagination

The scraper fetches pages of 100 events. If a page returns fewer than `PAGE_SIZE` (100) events, pagination stops. Otherwise, `$skip` is incremented by 100 and the next page is fetched after a 0.5s delay.

### Body Iteration

The scraper iterates over each body name in the config's `body_names` list and fetches events for each body separately. A `seen_ids` set prevents duplicate documents when the same event appears across multiple body queries.

---

## 3. Event Fields

Complete field inventory from a live API response:

| Field Name | Type | Sample Value | Notes |
|------------|------|-------------|-------|
| EventId | integer | `1816` | Unique event identifier |
| EventGuid | string | `"707269D1-15E1-4A37-970E-4ED3C94F2251"` | GUID |
| EventLastModifiedUtc | datetime | `"2026-04-13T16:19:07.1"` | Last modification timestamp |
| EventRowVersion | string | `"AAAAAADdfms="` | Concurrency token |
| EventBodyId | integer | `138` | Foreign key to body |
| EventBodyName | string | `"Board of County Commissioners"` | Body display name |
| EventDate | datetime | `"2026-04-21T00:00:00"` | Meeting date (time always midnight) |
| EventTime | string | `"9:00 AM"` | Meeting start time (text, not datetime) |
| EventVideoStatus | string | `"Public"` | Video availability status |
| EventAgendaStatusId | integer | `13` | Agenda workflow status ID |
| EventAgendaStatusName | string | `"Closed"` | Agenda workflow status name |
| EventMinutesStatusId | integer | `9` | Minutes workflow status ID |
| EventMinutesStatusName | string | `"Draft"` | Minutes workflow status name |
| EventLocation | string | `"Board Room"` | Meeting location |
| EventAgendaFile | string/null | `null` | Direct URL to agenda PDF (when published) |
| EventMinutesFile | string/null | `null` | Direct URL to minutes PDF (when published) |
| EventAgendaLastPublishedUTC | datetime/null | `"2026-04-13T12:51:54.823"` | Last agenda publication timestamp |
| EventMinutesLastPublishedUTC | datetime/null | `null` | Last minutes publication timestamp |
| EventComment | string | `"DRAFT for STAFF REVIEW ONLY 4-13-26"` | Staff comments / notes |
| EventVideoPath | string/null | `null` | URL to meeting video |
| EventMedia | string/null | `null` | Additional media |
| EventInSiteURL | string | `"https://polkcountyfl.legistar.com/MeetingDetail.aspx?..."` | Portal detail page URL |
| EventItems | array | `[]` | Inline event items (usually empty in list responses) |

---

## 4. What We Extract

The scraper converts each event into `DocumentListing` objects -- one for the agenda PDF and one for the minutes PDF, when their respective URLs are non-null.

| DocumentListing Field | Source | Value Pattern |
|-----------------------|--------|---------------|
| `title` | Computed | `"{EventBodyName} Agenda - {meeting_date}"` or `"{EventBodyName} Minutes - {meeting_date}"` |
| `url` | `EventAgendaFile` / `EventMinutesFile` | Direct PDF download URL |
| `date_str` | `EventDate` | First 10 chars parsed to `YYYY-MM-DD` |
| `document_id` | `EventId` | Stringified event ID |
| `document_type` | Hardcoded | `"agenda"` or `"minutes"` |
| `file_format` | Hardcoded | `"pdf"` |
| `filename` | Computed | `"Agenda_{date}_{EventId}.pdf"` or `"Minutes_{date}_{EventId}.pdf"` |

### Deduplication

Each document gets a composite key (`"agenda-{EventId}"` or `"minutes-{EventId}"`) checked against a `seen_ids` set. This prevents duplicates when the same event appears in overlapping body queries.

---

## 5. Additional Endpoints Not Used

The Legistar OData API exposes additional endpoints that our scraper does not currently query:

| Endpoint | What It Returns | Potential Use |
|----------|----------------|---------------|
| `GET /v1/{client}/events/{id}/eventitems` | Individual agenda items with action text, vote info, matter references | Extract specific motions, rezoning actions, vote outcomes |
| `GET /v1/{client}/matters` | Legislative matters (ordinances, resolutions, items) with sponsors, history | Track lifecycle of specific proposals |
| `GET /v1/{client}/matters/{id}/histories` | Status history of a matter | Track when items were introduced, amended, voted on |
| `GET /v1/{client}/matters/{id}/attachments` | Attachments on a specific matter | Staff reports, backup materials, exhibits |
| `GET /v1/{client}/bodies` | All legislative bodies with contacts | Discover new bodies, get meeting schedules |
| `GET /v1/{client}/persons` | Council members, commissioners, staff | Build member roster with terms |
| `GET /v1/{client}/votes/{id}` | Individual vote records | Yea/nay/abstain per member per item |
| `GET /v1/{client}/eventitems/{id}/votes` | Votes on a specific agenda item | Same as above, scoped to item |
| `GET /v1/{client}/codefiles` | Code sections referenced by matters | Link items to municipal code |

---

## 6. What We Extract vs What's Available

| Data Category | Currently Extracted | Source | Available but Not Extracted | Source |
|--------------|--------------------|---------|-----------------------------|--------|
| Event ID | YES | EventId | GUID, row version | EventGuid, EventRowVersion |
| Meeting Date | YES | EventDate (first 10 chars) | Full datetime, meeting time | EventDate, EventTime |
| Body Name | YES | EventBodyName | Body ID, body type | EventBodyId (join to /bodies) |
| Agenda PDF URL | YES | EventAgendaFile | Agenda status, last published time | EventAgendaStatusName, EventAgendaLastPublishedUTC |
| Minutes PDF URL | YES | EventMinutesFile | Minutes status, last published time | EventMinutesStatusName, EventMinutesLastPublishedUTC |
| Meeting Location | NO | -- | Location text | EventLocation |
| Staff Comments | NO | -- | Internal notes | EventComment |
| Video | NO | -- | Video URL and status | EventVideoPath, EventVideoStatus |
| Portal URL | NO | -- | Direct link to Legistar meeting page | EventInSiteURL |
| Agenda Items | NO | -- | Individual action items with text and references | /events/{id}/eventitems |
| Vote Records | NO | -- | Per-member vote outcomes | /eventitems/{id}/votes |
| Matters | NO | -- | Legislative items with sponsors, history, attachments | /matters |
| Member Roster | NO | -- | Commissioner names, terms, contact info | /persons |

---

## 7. Known Limitations and Quirks

1. **BOA is manual.** The Polk County Board of Adjustment (polk-county-boa.yaml) uses `platform: manual` because the BOA is handled by a Land Use Hearing Officer whose documents are not published through Legistar. The Land Use Hearing Officer body (BodyId 140) does exist on Legistar but may not have consistent agenda/minutes uploads.

2. **No vote extraction.** The scraper only pulls agenda and minutes PDFs. Individual vote records, motion text, and agenda item details are available via `/events/{id}/eventitems` and `/eventitems/{id}/votes` but are not queried.

3. **OData datetime format.** The `$filter` parameter uses the OData v3 datetime literal format: `datetime'YYYY-MM-DD'`. The response datetime format is ISO 8601 with time component (`2026-04-21T00:00:00`). The scraper parses only the first 10 characters.

4. **EventTime is a string, not a time.** Meeting time is returned as free text (e.g., `"9:00 AM"`) and is not a parseable datetime. Not currently extracted.

5. **0.5s polite delay.** The scraper enforces a 0.5-second delay between paginated requests. This is a fixed delay, not adaptive like the GIS engine.

6. **EventAgendaFile can be null even when agenda exists.** The `EventAgendaFile` field is null when the agenda has not been published as a PDF, even if the agenda items exist in Legistar's structured data. The `EventAgendaStatusName` indicates the workflow state ("Closed" = finalized, "Draft" = in progress).

7. **EventItems inline array is usually empty.** In list responses, the `EventItems` array is empty. To get agenda items, a separate request to `/events/{id}/eventitems` is required.

8. **Multiple BCC body variants.** The BCC appears under three separate body IDs: 138 (regular), 239 (organizational sessions), 240/241 (budget hearings). We only track BodyId 138 via `body_names: ["Board of County Commissioners"]`. Organizational and budget sessions are separate bodies and would need explicit inclusion.

9. **No rate limiting documented.** The Legistar API does not document rate limits, but the 0.5s delay provides a conservative ~120 requests/minute ceiling. No API key is required.

10. **Portal URL is available but not stored.** The `EventInSiteURL` field provides a direct link to the meeting detail page on the Legistar portal. This could be useful for user-facing citation but is not currently captured.
