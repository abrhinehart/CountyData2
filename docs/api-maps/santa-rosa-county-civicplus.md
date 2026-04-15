# Santa Rosa County FL -- CivicPlus AgendaCenter API Map (CR)

Last updated: 2026-04-14

## 1. Platform Overview

| Property | Value |
|----------|-------|
| Platform | CivicPlus AgendaCenter (CivicEngage) |
| Portal URL | `https://www.santarosafl.gov/AgendaCenter` |
| Protocol | Server-rendered ASP.NET with category-id filtered listings; documents are PDFs fetched from `AgendaCenter/ViewFile/...` |
| Auth | Anonymous |
| Document format | PDF (agendas + minutes) |
| Jurisdiction configs | `modules/commission/config/jurisdictions/FL/santa-rosa-county-bcc.yaml` (category_id: 1) and `modules/commission/config/jurisdictions/FL/santa-rosa-county-zb.yaml` (category_id: 2) |
| Registry status | **`zero_listing`** (per `santa-rosa-fl.projects.cr`, `county-registry.yaml` L354-356) |
| Bodies configured | BCC + Zoning Board (a combined LPA / BOA body per 2011 ordinance) |

### What "`zero_listing`" means

The scraper is configured and runs without error, but returns **zero listings** on the current window. This can be because:

- AgendaCenter category IDs (1 and 2) are configured but the underlying categories have no published meetings in the probed window
- The CivicPlus page structure has changed and the scraper's selector is no longer finding meeting tiles
- The county is publishing meetings under a different category ID that has not been added to the YAML

All three hypotheses must be re-checked on each run. The status is NOT `blocked` (fetch works), NOT `pending_validation` (fetch has been done), and NOT `live` (no listings ever returned).

---

## 2. Bodies / Categories

Two commission YAMLs reference this portal:

| Slug | Body | commission_type | `scraping.platform` | `category_id` |
|------|------|-----------------|---------------------|---------------|
| `santa-rosa-county-bcc` | Santa Rosa County BCC | `bcc` | `civicplus` | **1** |
| `santa-rosa-county-zb` | Santa Rosa County Zoning Board | `planning_board` | `civicplus` | **2** |

```yaml
# santa-rosa-county-bcc.yaml (verbatim)
slug: santa-rosa-county-bcc
name: "Santa Rosa County BCC"
state: FL
county: Santa Rosa
municipality: null
commission_type: bcc
scraping:
  platform: civicplus
  base_url: "https://www.santarosafl.gov/AgendaCenter"
  category_id: 1
  document_formats: [pdf]
  has_duplicate_page_bug: false
detection_patterns:
  header_keywords:
    - "COUNTY COMMISSIONERS"
    - "BOARD OF COUNTY COMMISSIONERS"
  require_also:
    - "SANTA ROSA COUNTY"
  header_zone: wide
extraction_notes:
  - "County body -- cannot annex."
  - "Generic Florida county. Flag sparse items for review."
```

```yaml
# santa-rosa-county-zb.yaml (verbatim)
slug: santa-rosa-county-zb
name: "Santa Rosa County Zoning Board"
state: FL
county: Santa Rosa
municipality: null
commission_type: planning_board
scraping:
  platform: civicplus
  base_url: "https://www.santarosafl.gov/AgendaCenter"
  category_id: 2
  document_formats: [pdf]
  has_duplicate_page_bug: false
detection_patterns:
  header_keywords:
    - "ZONING"
  require_also:
    - "SANTA ROSA COUNTY"
  header_zone: wide
extraction_notes:
  - "Combined Zoning Board -- serves as both Local Planning Agency (LPA) and Board of Adjustment (BOA) per 2011 ordinance."
  - "Generic Florida county. Flag sparse items for review."
```

Note: Santa Rosa's Zoning Board is **a single consolidated body** (LPA + BOA per 2011 ordinance), rather than separate Planning Commission and Board of Adjustment YAMLs as other FL counties use.

---

## 3. Events Endpoint

CivicPlus AgendaCenter is an ASP.NET server-rendered HTML surface. The public surfaces:

```
GET https://www.santarosafl.gov/AgendaCenter                                  # landing page
GET https://www.santarosafl.gov/AgendaCenter/{slug}-{category_id}             # per-category listing
GET https://www.santarosafl.gov/AgendaCenter/Search/?term=&CIDs={ids}&startDate=&endDate=&dateRange=&dateSelector=
                                                                              # federated search
GET https://www.santarosafl.gov/AgendaCenter/ViewFile/Agenda/_{meetingId}     # PDF (agenda)
GET https://www.santarosafl.gov/AgendaCenter/ViewFile/Minutes/_{meetingId}    # PDF (minutes)
```

The CivicPlus Search page accepts a comma-separated `CIDs` (plural) parameter. Our config uses a singular `category_id` per body; the scraper converts this to a single-value CIDs query.

### Expected scraper flow

1. Load `AgendaCenter` with `CID={category_id}` (e.g., 1 for BCC, 2 for ZB).
2. Parse the resulting HTML for meeting tiles (title, date, links).
3. Download agenda / minutes PDFs via `ViewFile/Agenda/` and `ViewFile/Minutes/`.

CivicPlus does NOT expose a REST or OData API for AgendaCenter; scraping is HTML-only.

---

## 4. Event Fields

Expected per-meeting fields (CivicPlus standard HTML schema):

| Field | Source | Notes |
|-------|--------|-------|
| `meeting_date` | Meeting tile header | Parsed to ISO `YYYY-MM-DD` |
| `meeting_title` | Tile heading | Free text (e.g., "Regular Meeting") |
| `body_name` | YAML body `name` | Per config |
| `agenda_url` | `ViewFile/Agenda/_{id}` link | PDF |
| `minutes_url` | `ViewFile/Minutes/_{id}` link (nullable) | PDF |
| `category_id` | YAML config | 1 or 2 |

---

## 5. What We Extract

Per-document `DocumentListing` shape (hypothetical under `zero_listing`):

| Field | Source |
|-------|--------|
| `title` | Computed from YAML `name` + date |
| `url` | PDF link |
| `date_str` | Meeting date |
| `document_type` | `"agenda"` or `"minutes"` |
| `file_format` | `"pdf"` |

At current `zero_listing` status, the scraper emits an empty list every run.

---

## 6. Diff vs Okeechobee Granicus (CR peer)

Both are HTML-scraped ASP.NET portals, but vendor and detection shape differ.

| Attribute | Santa Rosa (CivicPlus) | Okeechobee (Granicus IQM2) |
|-----------|-------------------------|-----------------------------|
| Vendor | CivicPlus / CivicEngage | Granicus IQM2 |
| Portal URL | `santarosafl.gov/AgendaCenter` | `okeechobeecountyfl.iqm2.com/Citizens` |
| Routing | `?CID={category_id}` on AgendaCenter | `Board.aspx?Board={boardId}&Year={year}` |
| Federated search | `AgendaCenter/Search/?CIDs=...` | `Services/GetFederatedSearch.aspx?q=...` |
| Bodies configured | 2 (BCC, ZB) | 1 (BCC) |
| Status | **`zero_listing`** | `pending_validation` |
| Special body | ZB = combined LPA + BOA (2011 ordinance) | (none) |
| Calendar feed | n/a | `Services/Calendar.ashx` |

---

## 7. Unused / Additional Endpoints

| Endpoint | What it returns | Used? |
|----------|-----------------|-------|
| `AgendaCenter/Search/?CIDs=...` | Federated search across categories | NO (category-specific listing used) |
| `AgendaCenter/RSS.aspx` | RSS feed per category | NO |
| `AgendaCenter/ViewFile/Attachment/_{id}` | Per-item PDF exhibits | NO |
| `AgendaCenter/UpdateViewList` | AJAX partial view refresh | NO |

---

## 8. What We Extract vs What's Available

| Data Category | Currently Extracted | Source | Available but Not Extracted | Source |
|---------------|--------------------|---------|-----------------------------|--------|
| Meeting date | YES (when present) | Tile | -- | -- |
| Meeting title | YES (when present) | Tile | -- | -- |
| Agenda PDF | YES (when posted) | ViewFile/Agenda | -- | -- |
| Minutes PDF | YES (when posted) | ViewFile/Minutes | -- | -- |
| Zero listings currently | -- | -- | -- | Status = `zero_listing` |
| Agenda items | NO | -- | Embedded table in HTML | AgendaCenter per-meeting view |
| Attachments per item | NO | -- | ViewFile/Attachment links | Per-meeting view |
| Meeting video | NO | -- | Often a separate video-on-demand URL | Site-wide video page |
| RSS subscription | NO | -- | Per-category RSS feed | `AgendaCenter/RSS.aspx` |

---

## 9. Known Limitations and Quirks

1. **Status is `zero_listing`.** The scraper fetches without error but returns zero listings. Triage steps: (a) verify category IDs 1 and 2 still map to BCC and ZB respectively, (b) hit `AgendaCenter/Search/?CIDs=1,2&dateRange=6M` and confirm tiles exist, (c) compare HTML selector used by the scraper vs the current page structure.

2. **Santa Rosa Zoning Board is a single consolidated body.** Per 2011 ordinance, the ZB serves as BOTH the Local Planning Agency (LPA) and the Board of Adjustment (BOA). Do NOT create separate `santa-rosa-county-pz.yaml` or `santa-rosa-county-boa.yaml` -- `santa-rosa-county-zb.yaml` with category_id=2 is the ONLY second body.

3. **No `santa-rosa-county-pz.yaml`.** Because the ZB is combined, there is no Planning Commission YAML. Do not create one.

4. **CivicPlus does NOT expose REST/OData.** Scrapers must parse HTML. There is no JSON endpoint equivalent to Legistar's OData.

5. **Federated-search `CIDs` parameter is plural.** Even for a single category, the URL segment reads `CIDs={single_id}`. Individual-body listings also accept the bare `AgendaCenter` with category filters baked into the page route (rather than a query string).

6. **`has_duplicate_page_bug: false`.** No duplicate-page pagination issue on this portal.

7. **`detection_patterns.header_keywords` for BCC is `"COUNTY COMMISSIONERS"` / `"BOARD OF COUNTY COMMISSIONERS"`, for ZB is just `"ZONING"`.** The ZB detection is broader; paired with `require_also: "SANTA ROSA COUNTY"`, it tolerates page titles like "Zoning Board Meeting" without the full `"ZONING BOARD OF ADJUSTMENT"` phrase.

8. **`extraction_notes` include annexation warning only for BCC.** The ZB notes are about its combined LPA/BOA role and sparse-item review. County body cannot annex (per BCC notes); zoning changes flow through ZB.

9. **Jurisdiction-config domain is `santarosafl.gov`** (no hyphen). Do NOT confuse with `srccol.com` (the clerk's AcclaimWeb domain) or with `santarosa.fl.us` (hypothetical US-TLD variant).

10. **Underlying adapter module is CivicPlus-generic.** Any fix for this `zero_listing` status lives in the generic CivicPlus scraper (`modules/commission/...`), not in county-specific code. The two YAMLs are the only county-specific artifacts.

11. **Two-YAML pattern (BCC + ZB) is distinctive among FL counties.** Most other FL CivicPlus / Granicus configs have 3 YAMLs (BCC + P&Z + BOA) or 1 YAML (BCC only). The combined ZB at category_id=2 is a structural one-off.

12. **No calendar feed / Services endpoint** -- CivicPlus AgendaCenter does not publish the `.ashx` style calendars Granicus IQM2 exposes.

**Source of truth:** `modules/commission/config/jurisdictions/FL/santa-rosa-county-bcc.yaml`, `modules/commission/config/jurisdictions/FL/santa-rosa-county-zb.yaml`, `county-registry.yaml` (`santa-rosa-fl.projects.cr`, L354-356, status = `zero_listing`).
