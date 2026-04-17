# Martin County FL -- Legistar OData API Map (CR)

Last updated: 2026-04-14

## 1. Platform Overview

| Property | Value |
|----------|-------|
| Platform | Legistar (Granicus) |
| API Base URL | `https://webapi.legistar.com/v1` |
| Client Slug (legistar_client) | `martin` |
| Portal URL | `https://martin.legistar.com` |
| Calendar URL | `https://martin.legistar.com/Calendar.aspx` |
| Auth | Anonymous -- no API key or token required |
| Protocol | OData v3 over REST (JSON) |
| User-Agent | `CommissionRadar/1.0` |
| Page Size | 100 (`$top`) |
| Request Delay | 0.5s between paginated requests |
| Registry status | **CR not tracked -- Martin County is ABSENT from `county-registry.yaml`** |

### Probe (2026-04-14)

```
GET https://martin.legistar.com/Calendar.aspx
-> HTTP 200, ~274.5 KB rendered Calendar page (ASP.NET)
```

---

## 2. Bodies configured

Three commission YAMLs reference this Legistar instance under `modules/commission/config/jurisdictions/FL/`:

| Slug | Body | `commission_type` | `scraping.platform` | `body_names` | Notes |
|------|------|-------------------|---------------------|-------------|-------|
| `martin-county-bcc` | Martin County BCC | `bcc` | **`legistar`** | `["Board of County Commissioners"]` | Auto-scraped |
| `martin-county-lpa` | Martin County LPA | `planning_board` | **`legistar`** | `["Local Planning Agency"]` | Auto-scraped -- Martin uses LPA, NOT P&Z |
| `martin-county-boa` | Martin County BOA | `board_of_adjustment` | **`manual`** | -- | Documents staged manually |

**Martin uses the Local Planning Agency (LPA) model, not the P&Z / Planning Commission model seen in most other FL counties.** The YAML slug is `martin-county-lpa` (not `-pz`), and `body_names` is `["Local Planning Agency"]` (not `"Planning and Zoning Commission"`). This is a deliberate structural difference -- do NOT rename to `pz`.

BCC and LPA are scraped via the Legistar OData API; BOA is `platform: manual` and routes to the manual workflow (no `base_url` or `legistar_client` in its YAML).

### Detection patterns

| Slug | header_keywords | require_also | header_zone |
|------|-----------------|---------------|-------------|
| `martin-county-bcc` | `COUNTY COMMISSIONERS`, `BOARD OF COUNTY COMMISSIONERS` | `MARTIN COUNTY` | wide |
| `martin-county-lpa` | `PLANNING`, `ZONING` | `MARTIN COUNTY` | wide |
| `martin-county-boa` | `ADJUSTMENT`, `APPEALS` | `MARTIN COUNTY` | wide |

---

## 3. Events Endpoint (BCC + LPA)

### Request

```
GET https://webapi.legistar.com/v1/martin/events
```

Two iterations per run:
- `body_names=["Board of County Commissioners"]` (BCC)
- `body_names=["Local Planning Agency"]` (LPA)

BOA is skipped because `scraping.platform: manual`.

### OData Query Parameters

| Parameter | Used by Us? | Our Value | Notes |
|-----------|-------------|-----------|-------|
| `$filter` | YES | `EventDate ge datetime'{start}' and EventDate le datetime'{end}' and EventBodyName eq '{body}'` | OData v3 filter |
| `$orderby` | YES | `EventDate desc` | Newest events first |
| `$top` | YES | `100` | Page size |
| `$skip` | YES | Incremented by 100 per page | Pagination offset |

### Headers

```
User-Agent: CommissionRadar/1.0
Accept: application/json
```

### Pagination

If a page returns fewer than 100 events, pagination stops. Otherwise `$skip` advances by 100 after a 0.5s delay.

### Body Iteration

`seen_ids` deduplicates documents when the same `EventId` appears under multiple body queries (rare).

---

## 4. Event Fields

Standard Legistar event shape (same as Polk / Brevard / Indian River):

| Field Name | Type | Sample | Notes |
|------------|------|--------|-------|
| EventId | integer | -- | Unique event identifier |
| EventGuid | string | -- | GUID |
| EventLastModifiedUtc | datetime | -- | Last modification timestamp |
| EventBodyId | integer | -- | FK to body |
| EventBodyName | string | `"Board of County Commissioners"` or `"Local Planning Agency"` | Body display name |
| EventDate | datetime | -- | Meeting date (time component always midnight) |
| EventTime | string | -- | Meeting start time (text, not datetime) |
| EventLocation | string | -- | Meeting location |
| EventAgendaFile | string/null | -- | Direct URL to agenda PDF when published |
| EventMinutesFile | string/null | -- | Direct URL to minutes PDF when published |
| EventAgendaLastPublishedUTC | datetime/null | -- | Last agenda publication timestamp |
| EventMinutesLastPublishedUTC | datetime/null | -- | Last minutes publication timestamp |
| EventInSiteURL | string | -- | Direct link to Legistar meeting detail page |
| EventItems | array | -- | Inline items (usually empty in list responses) |

---

## 5. What We Extract

Each event -> 0, 1, or 2 `DocumentListing` records (agenda + minutes):

| DocumentListing Field | Source | Value Pattern |
|-----------------------|--------|---------------|
| `title` | Computed | `"Martin County BCC Agenda - {meeting_date}"` (or LPA; or minutes) |
| `url` | `EventAgendaFile` / `EventMinutesFile` | Direct PDF URL |
| `date_str` | `EventDate` | First 10 chars -> `YYYY-MM-DD` |
| `document_id` | `EventId` | Stringified event ID |
| `document_type` | Hardcoded | `"agenda"` or `"minutes"` |
| `file_format` | Hardcoded | `"pdf"` |

BOA events are NOT fetched programmatically. Documents are staged manually.

---

## 6. Diff vs Polk / Brevard / Indian River (Legistar peers)

| Attribute | Martin | Polk | Brevard | Indian River |
|-----------|--------|------|---------|--------------|
| Legistar client | **`martin`** | `polkcountyfl` | `brevardfl` | `ircgov` |
| Portal URL | `martin.legistar.com` | `polkcountyfl.legistar.com` | `brevardfl.legistar.com` | `ircgov.legistar.com` |
| Planning body name | **`"Local Planning Agency"` (LPA)** | `"Planning Commission"` | `"Planning and Zoning Board / Local Planning Agency"` | `"Planning and Zoning Commission"` |
| Planning YAML slug | `martin-county-lpa` | `polk-county-pz` | `brevard-county-pz` | `indian-river-county-pz` |
| BCC body name | `"Board of County Commissioners"` | `"Board of County Commissioners"` | `"Brevard County Board of County Commissioners"` (full county prefix) | `"Board of County Commissioners"` |
| BOA handling | `manual` | `manual` (Land Use Hearing Officer) | `manual` | `manual` |
| Registry CR entry | **ABSENT** (no `martin-fl` block) | -- | -- | `usable_seed` |

---

## 7. Related surfaces (no standalone BOA doc)

### Martin BOA (`platform: manual`) -- documented inline here

`martin-county-boa.yaml` declares `platform: manual` and omits `base_url`, `legistar_client`, and `body_names`. Extraction notes read: "Board of Adjustment -- handles variances and appeals, outside core tracking scope." No standalone `martin-county-boa.md` doc is produced; BOA is covered here under this section and directly in the YAML.

---

## 8. What We Extract vs What's Available

| Data Category | Currently Extracted | Source | Available but Not Extracted | Source |
|---------------|--------------------|--------|-----------------------------|--------|
| Event ID | YES | EventId | GUID, row version | EventGuid |
| Meeting Date | YES | EventDate (10 chars) | Full datetime, meeting time | EventDate, EventTime |
| Body Name | YES | EventBodyName | Body ID | EventBodyId (join to `/bodies`) |
| Agenda PDF | YES | EventAgendaFile | Agenda status, publication time | EventAgendaStatusName, EventAgendaLastPublishedUTC |
| Minutes PDF | YES | EventMinutesFile | Minutes status, publication time | EventMinutesStatusName, EventMinutesLastPublishedUTC |
| Meeting Location / Comments / Video | NO | -- | -- | EventLocation, EventComment, EventVideoPath |
| Portal URL | NO | -- | Direct link to meeting detail | EventInSiteURL |
| Agenda Items / Votes | NO | -- | Per-item action text, vote outcomes | `/events/{id}/eventitems`, `/eventitems/{id}/votes` |
| Matters / History | NO | -- | Legislative items lifecycle | `/matters`, `/matters/{id}/histories` |
| Member Roster | NO | -- | Commissioners, terms | `/persons` |

---

## 9. Known Limitations and Quirks

1. **Martin uses LPA, not P&Z.** The Local Planning Agency is a distinct FL planning-body model codified under FS 163.3174. Martin's YAML slug is `martin-county-lpa` and `body_names` is `["Local Planning Agency"]`. Do NOT rename to `pz` or substitute `"Planning and Zoning Commission"` -- the Legistar body lookup would miss the LPA entirely.

2. **Legistar client is `martin` -- short, unsuffixed.** Martin is the only FL county in this repo with an unsuffixed Legistar client (contrast `polkcountyfl`, `brevardfl`, `ircgov`). Do NOT assume `martinfl`, `martincountyfl`, or `martincofl`.

3. **BOA is `platform: manual`.** `martin-county-boa.yaml` sets `platform: manual` and omits `base_url`, `legistar_client`, and `body_names`. The dispatch layer routes it to the manual workflow. Martin does not publish BOA agendas on Legistar.

4. **Martin is ABSENT from `county-registry.yaml`.** Grep for `martin-fl` in the registry returns no hits. CR status cannot be tracked via `martin-fl.projects.cr` because no `martin-fl` block exists. The YAMLs are the only declaration.

5. **BCC body name is the unprefixed `"Board of County Commissioners"`** -- NOT `"Martin County Board of County Commissioners"`. Contrast Brevard, which uses the full `"Brevard County Board of County Commissioners"` prefix.

6. **0.5s polite delay between paginated requests.** Fixed, not adaptive.

7. **`EventTime` is free text, not a parseable datetime** (e.g. `"9:00 AM"`). Not currently extracted.

8. **OData datetime literal format** for `$filter`: `datetime'YYYY-MM-DD'` (v3 style). Response datetimes are ISO 8601 (`2026-04-21T00:00:00`); scraper parses first 10 chars.

9. **`EventAgendaFile` / `EventMinutesFile` can be null even when agenda items exist.** Null means no PDF has been published; the agenda may still be assembled in Legistar's structured data. `EventAgendaStatusName` ("Closed", "Draft") indicates workflow state.

10. **No vote / matter extraction.** The scraper only pulls agenda and minutes PDFs. Per-item votes (`/eventitems/{id}/votes`) and matter histories (`/matters/{id}/histories`) are untouched.

11. **Portal URL is `martin.legistar.com` (no county / state suffix).** Contrast with `brevardfl.legistar.com`, `polkcountyfl.legistar.com`, `ircgov.legistar.com`. This is the single-word client seen less commonly across Granicus tenants.

12. **The `martin.legistar.com/Calendar.aspx` shell is ~274 KB of rendered HTML** (probed 2026-04-14). The OData API is the preferred surface; HTML scraping of Calendar.aspx is NOT used.

**Source of truth:** `modules/commission/config/jurisdictions/FL/martin-county-bcc.yaml`, `martin-county-lpa.yaml`, `martin-county-boa.yaml`, confirmed absence of `martin-fl` block in `county-registry.yaml`, live probe against `https://martin.legistar.com/Calendar.aspx` (HTTP 200, ~274.5 KB, 2026-04-14).
