# Indian River County FL -- Legistar OData API Map (CR)

Last updated: 2026-04-14

## 1. Platform Overview

| Property | Value |
|----------|-------|
| Platform | Legistar (Granicus) |
| API Base URL | `https://webapi.legistar.com/v1` |
| Client Slug (legistar_client) | `ircgov` (NOT `indian-river`, NOT `irc`, NOT `indianrivercountyfl`) |
| Portal URL | `https://ircgov.legistar.com` |
| Calendar URL | `https://ircgov.legistar.com/Calendar.aspx` |
| Auth | Anonymous -- no API key or token required |
| Protocol | OData v3 over REST (JSON) |
| User-Agent | `CommissionRadar/1.0` |
| Page Size | 100 (`$top`) |
| Request Delay | 0.5s between paginated requests |
| Registry status | `cr: usable_seed` (verbatim) per `county-registry.yaml` L431-442 (`indian-river-fl.projects.cr`, slug `indian-river-county-bcc`) |

### Probe (2026-04-14)

```
GET https://ircgov.legistar.com/Calendar.aspx
-> HTTP 200, ~176.5 KB rendered Calendar page (ASP.NET)
```

---

## 2. Bodies configured

Three commission YAMLs reference this Legistar instance under `modules/commission/config/jurisdictions/FL/`:

| Slug | Body | `commission_type` | `scraping.platform` | `body_names` | Notes |
|------|------|-------------------|---------------------|-------------|-------|
| `indian-river-county-bcc` | Indian River County BCC | `bcc` | **`legistar`** | `["Board of County Commissioners"]` | Registry-tracked (`usable_seed`) |
| `indian-river-county-pz` | Indian River County P&Z | `planning_board` | **`legistar`** | `["Planning and Zoning Commission"]` | Auto-scraped |
| `indian-river-county-boa` | Indian River County BOA | `board_of_adjustment` | **`manual`** | -- | Documents staged manually |

### Detection patterns

| Slug | header_keywords | require_also | header_zone |
|------|-----------------|---------------|-------------|
| `indian-river-county-bcc` | `COUNTY COMMISSIONERS`, `BOARD OF COUNTY COMMISSIONERS` | `INDIAN RIVER COUNTY` | wide |
| `indian-river-county-pz` | `PLANNING`, `ZONING` | `INDIAN RIVER COUNTY` | wide |
| `indian-river-county-boa` | `ADJUSTMENT`, `APPEALS` | `INDIAN RIVER COUNTY` | wide |

---

## 3. Events Endpoint (BCC + P&Z)

### Request

```
GET https://webapi.legistar.com/v1/ircgov/events
```

Two iterations per run:
- `body_names=["Board of County Commissioners"]` (BCC)
- `body_names=["Planning and Zoning Commission"]` (P&Z)

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

`seen_ids` deduplicates documents when the same `EventId` appears under multiple body queries.

---

## 4. Event Fields

Standard Legistar event shape (same as Polk / Martin / Brevard):

| Field Name | Type | Notes |
|------------|------|-------|
| EventId | integer | Unique event identifier |
| EventGuid | string | GUID |
| EventLastModifiedUtc | datetime | Last modification timestamp |
| EventBodyId | integer | FK to body |
| EventBodyName | string | `"Board of County Commissioners"` or `"Planning and Zoning Commission"` |
| EventDate | datetime | Meeting date (time always midnight) |
| EventTime | string | Meeting start (text, not datetime) |
| EventLocation | string | Meeting location |
| EventAgendaFile | string/null | Direct URL to agenda PDF when published |
| EventMinutesFile | string/null | Direct URL to minutes PDF when published |
| EventAgendaLastPublishedUTC | datetime/null | Last agenda publication timestamp |
| EventMinutesLastPublishedUTC | datetime/null | Last minutes publication timestamp |
| EventInSiteURL | string | Direct link to Legistar meeting detail page |
| EventItems | array | Inline items (usually empty in list responses) |

---

## 5. What We Extract

Each event -> 0, 1, or 2 `DocumentListing` records (agenda + minutes):

| DocumentListing Field | Source | Value Pattern |
|-----------------------|--------|---------------|
| `title` | Computed | `"Indian River County BCC Agenda - {meeting_date}"` (or P&Z; or minutes) |
| `url` | `EventAgendaFile` / `EventMinutesFile` | Direct PDF URL |
| `date_str` | `EventDate` | First 10 chars -> `YYYY-MM-DD` |
| `document_id` | `EventId` | Stringified event ID |
| `document_type` | Hardcoded | `"agenda"` or `"minutes"` |
| `file_format` | Hardcoded | `"pdf"` |

BOA events are NOT fetched programmatically.

---

## 6. Diff vs Polk / Martin / Brevard (Legistar peers)

| Attribute | Indian River | Polk | Martin | Brevard |
|-----------|--------------|------|--------|---------|
| Legistar client | **`ircgov`** | `polkcountyfl` | `martin` | `brevardfl` |
| Portal URL | `ircgov.legistar.com` | `polkcountyfl.legistar.com` | `martin.legistar.com` | `brevardfl.legistar.com` |
| BCC body name | `"Board of County Commissioners"` | `"Board of County Commissioners"` | `"Board of County Commissioners"` | `"Brevard County Board of County Commissioners"` (full prefix) |
| Planning body name | `"Planning and Zoning Commission"` | `"Planning Commission"` | `"Local Planning Agency"` (LPA) | `"Planning and Zoning Board / Local Planning Agency"` |
| Planning YAML slug | `indian-river-county-pz` | `polk-county-pz` | `martin-county-lpa` | `brevard-county-pz` |
| Registry CR entry | **`usable_seed`** (verbatim) | -- | ABSENT | ABSENT |
| BOA handling | `manual` | `manual` | `manual` | `manual` |

---

## 7. Related surfaces (no standalone BOA doc)

### Indian River BOA (`platform: manual`) -- documented inline here

`indian-river-county-boa.yaml` declares `platform: manual` and omits `base_url`, `legistar_client`, and `body_names`. Extraction notes: "Board of Adjustment -- handles variances and appeals, outside core tracking scope." No standalone `indian-river-county-boa.md` doc is produced.

---

## 8. What We Extract vs What's Available

| Data Category | Currently Extracted | Source | Available but Not Extracted | Source |
|---------------|--------------------|--------|-----------------------------|--------|
| Event ID | YES | EventId | GUID | EventGuid |
| Meeting Date | YES | EventDate (10 chars) | Full datetime, time | EventDate, EventTime |
| Body Name | YES | EventBodyName | Body ID | EventBodyId |
| Agenda PDF | YES | EventAgendaFile | Status + last published | EventAgendaStatusName, EventAgendaLastPublishedUTC |
| Minutes PDF | YES | EventMinutesFile | Status + last published | EventMinutesStatusName, EventMinutesLastPublishedUTC |
| Meeting Location / Comments / Video | NO | -- | -- | EventLocation, EventComment, EventVideoPath |
| Agenda Items / Votes | NO | -- | Per-item text, votes | `/events/{id}/eventitems`, `/eventitems/{id}/votes` |
| Matters / History | NO | -- | Legislative items | `/matters`, `/matters/{id}/histories` |
| Member Roster | NO | -- | Commissioners, terms | `/persons` |

---

## 9. Known Limitations and Quirks

1. **Legistar client is `ircgov`** -- not `indian-river`, `irc`, `indianrivercountyfl`, or any other variant. The "IRC" initials + "gov" suffix is unique to this county. Copy verbatim.

2. **Registry CR status is `usable_seed`** -- a specific in-repo status meaning the slug/platform/client is declared correctly but the full scrape has not yet been validated end-to-end. Do NOT upgrade to `live` or downgrade to `pending_validation` without explicit verification.

3. **Registry slug is `indian-river-county-bcc`** (with dashes and the `-bcc` suffix), matching the YAML slug. The `county-registry.yaml` entry lives at L431-442 under `indian-river-fl` -- note the registry key uses `indian-river-fl` (hyphen + `-fl` state suffix), NOT `ircgov`.

4. **Planning body is `"Planning and Zoning Commission"`** -- standard FL naming. Unlike Martin (LPA) or Brevard (combined P&Z Board / LPA), Indian River uses the plain "Planning and Zoning Commission" pattern.

5. **BOA is `platform: manual`.** `indian-river-county-boa.yaml` sets `platform: manual` and omits `base_url` / `legistar_client` / `body_names`. The dispatch layer routes it to the manual workflow.

6. **BCC body name is the unprefixed `"Board of County Commissioners"`** -- NOT `"Indian River County Board of County Commissioners"`. Contrast Brevard, which does prefix the county name.

7. **0.5s polite delay between paginated requests.** Fixed, not adaptive.

8. **`EventTime` is free text, not a parseable datetime.** Not currently extracted.

9. **OData datetime literal format** for `$filter`: `datetime'YYYY-MM-DD'` (v3 style). Response datetimes are ISO 8601; scraper parses first 10 chars.

10. **Tenant slug mismatch between Legistar (`ircgov`) and YAML (`indian-river-county-*`).** The YAML-side slug uses the long-form county name; the Legistar-side client is the three-letter county initials + `gov`. Both must be specified correctly.

11. **No vote / matter extraction.** The scraper only pulls agenda and minutes PDFs.

12. **BI side cross-references.** See `indian-river-county-arcgis.md` for the parcels surface. `PP_PIN` (the PA parcel field) and Legistar event IDs have no structural relationship -- BI and CR are independent pipelines.

**Source of truth:** `modules/commission/config/jurisdictions/FL/indian-river-county-bcc.yaml`, `indian-river-county-pz.yaml`, `indian-river-county-boa.yaml`, `county-registry.yaml` (`indian-river-fl.projects.cr`, L439-442 with status `usable_seed`, slug `indian-river-county-bcc`), live probe against `https://ircgov.legistar.com/Calendar.aspx` (HTTP 200, ~176.5 KB, 2026-04-14).
