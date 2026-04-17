# Brevard County FL -- Legistar OData API Map (CR)

Last updated: 2026-04-14

## 1. Platform Overview

| Property | Value |
|----------|-------|
| Platform | Legistar (Granicus) |
| API Base URL | `https://webapi.legistar.com/v1` |
| Client Slug (legistar_client) | `brevardfl` (both county prefix AND `fl` suffix) |
| Portal URL | `https://brevardfl.legistar.com` |
| Calendar URL | `https://brevardfl.legistar.com/Calendar.aspx` |
| Auth | Anonymous -- no API key or token required |
| Protocol | OData v3 over REST (JSON) |
| User-Agent | `CommissionRadar/1.0` |
| Page Size | 100 (`$top`) |
| Request Delay | 0.5s between paginated requests |
| Registry status | **CR not tracked -- Brevard is ABSENT from `county-registry.yaml`** |

### Probe (2026-04-14)

```
GET https://brevardfl.legistar.com/Calendar.aspx
-> HTTP 200, ~701.8 KB rendered Calendar page (ASP.NET, unusually large)
```

The large rendered size (~702 KB) reflects an active meetings calendar with many historical entries visible client-side. The underlying API is the same OData surface as the other FL Legistar tenants.

---

## 2. Bodies configured

Three commission YAMLs reference this Legistar instance under `modules/commission/config/jurisdictions/FL/`:

| Slug | Body | `commission_type` | `scraping.platform` | `body_names` | Notes |
|------|------|-------------------|---------------------|-------------|-------|
| `brevard-county-bcc` | Brevard County BCC | `bcc` | **`legistar`** | `["Brevard County Board of County Commissioners"]` | **Full county prefix in body name** |
| `brevard-county-pz` | Brevard County P&Z | `planning_board` | **`legistar`** | `["Planning and Zoning Board / Local Planning Agency"]` | **Space-slash-space combining two bodies** |
| `brevard-county-boa` | Brevard County BOA | `board_of_adjustment` | **`manual`** | -- | Documents staged manually |

### Detection patterns

| Slug | header_keywords | require_also | header_zone |
|------|-----------------|---------------|-------------|
| `brevard-county-bcc` | `COUNTY COMMISSIONERS`, `BOARD OF COUNTY COMMISSIONERS` | `BREVARD COUNTY` | wide |
| `brevard-county-pz` | `PLANNING`, `ZONING` | `BREVARD COUNTY` | wide |
| `brevard-county-boa` | `ADJUSTMENT`, `APPEALS` | `BREVARD COUNTY` | wide |

---

## 3. Events Endpoint (BCC + P&Z)

### Request

```
GET https://webapi.legistar.com/v1/brevardfl/events
```

Two iterations per run:
- `body_names=["Brevard County Board of County Commissioners"]` (BCC -- full county prefix)
- `body_names=["Planning and Zoning Board / Local Planning Agency"]` (P&Z -- combined body)

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

`seen_ids` deduplicates when the same `EventId` appears under multiple body queries. The combined P&Z body name (`"Planning and Zoning Board / Local Planning Agency"`) is a single string literal (space-slash-space), NOT two separate body filters.

---

## 4. Event Fields

Standard Legistar event shape (same as Polk / Martin / Indian River):

| Field Name | Type | Notes |
|------------|------|-------|
| EventId | integer | Unique event identifier |
| EventGuid | string | GUID |
| EventLastModifiedUtc | datetime | Last modification timestamp |
| EventBodyId | integer | FK to body |
| EventBodyName | string | `"Brevard County Board of County Commissioners"` or `"Planning and Zoning Board / Local Planning Agency"` |
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
| `title` | Computed | `"Brevard County BCC Agenda - {meeting_date}"` (or P&Z; or minutes) |
| `url` | `EventAgendaFile` / `EventMinutesFile` | Direct PDF URL |
| `date_str` | `EventDate` | First 10 chars -> `YYYY-MM-DD` |
| `document_id` | `EventId` | Stringified event ID |
| `document_type` | Hardcoded | `"agenda"` or `"minutes"` |
| `file_format` | Hardcoded | `"pdf"` |

BOA events are NOT fetched programmatically.

---

## 6. Diff vs Polk / Martin / Indian River (Legistar peers)

| Attribute | Brevard | Polk | Martin | Indian River |
|-----------|---------|------|--------|--------------|
| Legistar client | **`brevardfl`** (county + `fl` suffix) | `polkcountyfl` | `martin` | `ircgov` |
| Portal URL | `brevardfl.legistar.com` | `polkcountyfl.legistar.com` | `martin.legistar.com` | `ircgov.legistar.com` |
| BCC body name | **`"Brevard County Board of County Commissioners"` (full county prefix)** | `"Board of County Commissioners"` | `"Board of County Commissioners"` | `"Board of County Commissioners"` |
| Planning body name | **`"Planning and Zoning Board / Local Planning Agency"` (combined, space-slash-space)** | `"Planning Commission"` | `"Local Planning Agency"` (LPA) | `"Planning and Zoning Commission"` |
| Planning YAML slug | `brevard-county-pz` | `polk-county-pz` | `martin-county-lpa` | `indian-river-county-pz` |
| BOA handling | `manual` | `manual` (Land Use Hearing Officer) | `manual` | `manual` |
| Registry CR entry | **ABSENT (no `brevard-fl` block)** | -- | ABSENT | `usable_seed` |

---

## 7. Related surfaces (no standalone BOA doc)

### Brevard BOA (`platform: manual`) -- documented inline here

`brevard-county-boa.yaml` declares `platform: manual` and omits `base_url`, `legistar_client`, and `body_names`. Extraction notes: "Board of Adjustment -- handles variances and appeals, outside core tracking scope." No standalone `brevard-county-boa.md` doc is produced; BOA is covered here under this section and directly in the YAML.

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

1. **BCC body_name carries the FULL `"Brevard County"` prefix.** Literal value: `"Brevard County Board of County Commissioners"`. Contrast every other FL Legistar client in this repo (Polk, Martin, Indian River), which uses the unprefixed `"Board of County Commissioners"`. Preserving the full prefix is mandatory -- Legistar's `EventBodyName eq` match is exact, and dropping `"Brevard County "` would filter to zero events.

2. **P&Z body_name is the combined `"Planning and Zoning Board / Local Planning Agency"`.** Single string, space-slash-space (`" / "` with surrounding spaces). Brevard consolidates its Planning & Zoning Board and Local Planning Agency functions under one body name that embeds both phrases. Do NOT try to split into two separate `body_names` list entries -- the body is literally named `"Planning and Zoning Board / Local Planning Agency"` in Legistar, and only an exact-string match against that full name returns events.

3. **Legistar client is `brevardfl`** -- county + `fl` suffix. Differs from Polk (`polkcountyfl` -- county + `countyfl`), Martin (`martin` -- just county), and Indian River (`ircgov` -- initials + `gov`). No consistent FL Legistar slug convention.

4. **BOA is `platform: manual`.** `brevard-county-boa.yaml` sets `platform: manual` and omits `base_url` / `legistar_client` / `body_names`. Routed to manual workflow.

5. **Brevard is ABSENT from `county-registry.yaml`.** CR status cannot be tracked via `brevard-fl.projects.cr` because no `brevard-fl` block exists. The YAMLs are the only repo-level declaration of CR for Brevard.

6. **Calendar.aspx shell is ~702 KB.** The unusually large rendered HTML reflects a rich multi-year archive. The OData API is the preferred surface; HTML scraping of Calendar.aspx is NOT used.

7. **0.5s polite delay between paginated requests.** Fixed, not adaptive.

8. **`EventTime` is free text, not a parseable datetime.** Not currently extracted.

9. **OData datetime literal format** for `$filter`: `datetime'YYYY-MM-DD'` (v3 style). Response datetimes are ISO 8601; scraper parses first 10 chars.

10. **No vote / matter extraction.** The scraper only pulls agenda and minutes PDFs. Per-item votes and matter histories are untouched.

11. **Cross-reference to `brevard-county-accela.md`.** The permits surface runs on Accela (agency code `BOCC`) -- NOT Escambia despite the generic `BOCC` name. See `brevard-county-accela.md` for the full PT picture.

12. **Cross-reference to `brevard-county-arcgis.md`.** The BI surface lives on `gis.brevardfl.gov` with EPSG:2881 (NAD83/HARN Florida East, ft). Legistar event IDs and parcel IDs have no structural relationship -- BI and CR are independent pipelines.

**Source of truth:** `modules/commission/config/jurisdictions/FL/brevard-county-bcc.yaml` (body_name = `"Brevard County Board of County Commissioners"`), `brevard-county-pz.yaml` (body_name = `"Planning and Zoning Board / Local Planning Agency"`), `brevard-county-boa.yaml` (`platform: manual`), confirmed absence of `brevard-fl` block in `county-registry.yaml`, live probe against `https://brevardfl.legistar.com/Calendar.aspx` (HTTP 200, ~701.8 KB, 2026-04-14).
