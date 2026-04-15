# Sumter County FL -- CivicPlus AgendaCenter API Map (CR)

Last updated: 2026-04-14

## 1. Platform Overview

| Property | Value |
|----------|-------|
| Platform | CivicPlus AgendaCenter (CivicEngage) |
| Portal URL | `https://sumtercountyfl.gov/AgendaCenter` |
| Protocol | Server-rendered ASP.NET with category-id filtered listings; documents are PDFs fetched from `AgendaCenter/ViewFile/...` |
| Auth | Anonymous |
| Document format | PDF (agendas + minutes) |
| Jurisdiction configs | `modules/commission/config/jurisdictions/FL/sumter-county-bcc.yaml` (category_id: 5), `sumter-county-pz.yaml` (category_id: 2), `sumter-county-boa.yaml` (platform: manual) |
| Registry status | **ABSENT -- Sumter is not in `county-registry.yaml` (no `sumter-fl` block)** |
| Bodies configured | 3 (BCC, P&Z, BOA); **BCC + P&Z on CivicPlus, BOA manual** |

### Probe (2026-04-14)

```
GET https://sumtercountyfl.gov/AgendaCenter
-> HTTP 200, ~194 KB rendered HTML (after following redirects)
  <title>Agenda Center • Sumter County, FL • CivicEngage</title>
  HTML includes `<input ... name="chkCategoryID" value="N">` elements for live categories:
    2, 3, 4, 5, 6, 18, 20, 21, 22, 23, 24
```

Both `category_id=5` (BCC) and `category_id=2` (P&Z) appear as live checkbox values in the AgendaCenter landing HTML -- confirming the IDs in the YAMLs are still recognized by the portal.

---

## 2. Bodies / Categories

Three commission YAMLs reference this portal:

| Slug | Body | `commission_type` | `scraping.platform` | `category_id` | Portal |
|------|------|-------------------|---------------------|---------------|--------|
| `sumter-county-bcc` | Sumter County BCC | `bcc` | **`civicplus`** | **5** | `sumtercountyfl.gov/AgendaCenter` |
| `sumter-county-pz` | Sumter County P&Z | `planning_board` | **`civicplus`** | **2** | `sumtercountyfl.gov/AgendaCenter` |
| `sumter-county-boa` | Sumter County BOA | `board_of_adjustment` | **`manual`** | n/a | (no `base_url` in YAML) |

BCC and P&Z are auto-scraped via CivicPlus. BOA is `platform: manual`.

### Inline config comments on the category IDs

- `sumter-county-bcc.yaml` declares `category_id: 5` with the trailing inline comment `# Board of County Commissioners Regular Meeting`, anchoring the numeric ID to a human-readable category name.
- `sumter-county-pz.yaml` declares `category_id: 2` with an inline comment that flags the P&Z category_id as carrying an unverified-in-repo note -- it is declared in the YAML with a comment asking a future reader to confirm the numeric ID against the live AgendaCenter page (the comment is preserved in the YAML but is not a blocker for the scrape). The 2026-04-14 live probe against `sumtercountyfl.gov/AgendaCenter` returned `chkCategoryID` checkboxes for both `value="5"` and `value="2"`, confirming both IDs are still recognized by the portal.
- `sumter-county-boa.yaml` declares `platform: manual` and carries no `category_id`.

### Detection patterns

| Slug | header_keywords | require_also | header_zone |
|------|-----------------|---------------|-------------|
| `sumter-county-bcc` | `COUNTY COMMISSIONERS`, `BOARD OF COUNTY COMMISSIONERS` | `SUMTER COUNTY` | wide |
| `sumter-county-pz` | `PLANNING` | `SUMTER COUNTY` | wide |
| `sumter-county-boa` | `ADJUSTMENT`, `APPEALS` | `SUMTER COUNTY` | wide |

---

## 3. Events Endpoint

CivicPlus AgendaCenter is an ASP.NET server-rendered HTML surface. Public surfaces:

```
GET https://sumtercountyfl.gov/AgendaCenter                                 # landing page (all categories)
GET https://sumtercountyfl.gov/AgendaCenter?CID={category_id}               # per-category listing
GET https://sumtercountyfl.gov/AgendaCenter/Search/?term=&CIDs={ids}&startDate=&endDate=&dateRange=&dateSelector=
                                                                             # federated search
GET https://sumtercountyfl.gov/AgendaCenter/ViewFile/Agenda/_{meetingId}    # PDF (agenda)
GET https://sumtercountyfl.gov/AgendaCenter/ViewFile/Minutes/_{meetingId}   # PDF (minutes)
```

The CivicPlus Search page accepts a comma-separated `CIDs` (plural) parameter. Our config uses a singular `category_id` per body; the scraper converts this to a single-value CIDs query.

### Expected scraper flow

1. Load `AgendaCenter` with `CID={category_id}` (5 for BCC, 2 for P&Z).
2. Parse the resulting HTML for meeting tiles (title, date, links).
3. Download agenda / minutes PDFs via `ViewFile/Agenda/` and `ViewFile/Minutes/`.

CivicPlus does NOT expose a REST or OData API for AgendaCenter; scraping is HTML-only.

---

## 4. Event Fields

Expected per-meeting fields (CivicPlus standard HTML schema):

| Field | Source | Notes |
|-------|--------|-------|
| `meeting_date` | Meeting tile header | Parsed to ISO `YYYY-MM-DD` |
| `meeting_title` | Tile heading | Free text (e.g. "Regular Meeting") |
| `body_name` | YAML body `name` | Per config |
| `agenda_url` | `ViewFile/Agenda/_{id}` link | PDF |
| `minutes_url` | `ViewFile/Minutes/_{id}` link (nullable) | PDF |
| `category_id` | YAML config | 5 or 2 |

---

## 5. What We Extract

Per-document `DocumentListing` shape:

| Field | Source |
|-------|--------|
| `title` | Computed from YAML `name` + date |
| `url` | PDF link |
| `date_str` | Meeting date |
| `document_type` | `"agenda"` or `"minutes"` |
| `file_format` | `"pdf"` |

BOA events are NOT scraped; documents are staged manually.

---

## 6. Diff vs Santa Rosa / Walton (CivicPlus peers)

| Attribute | Sumter | Santa Rosa | Walton |
|-----------|--------|------------|--------|
| Host | `sumtercountyfl.gov/AgendaCenter` | `www.santarosafl.gov/AgendaCenter` | `www.mywaltonfl.gov/AgendaCenter` |
| Bodies on CivicPlus | **BCC + P&Z (both `civicplus`)** | BCC + ZB (both `civicplus`, ZB = combined LPA+BOA) | 0 (all three bodies `manual`) |
| BCC `category_id` | **5** | 1 | n/a (manual) |
| P&Z `category_id` | **2** | 2 (ZB) | n/a (manual) |
| BOA handling | `manual` (separate YAML) | n/a (ZB combines LPA+BOA) | `manual` (separate YAML, no base_url) |
| P&Z `category_id` state | Declared with in-repo verification note (see Quirks) | live | n/a |
| Registry entry | **ABSENT** | `cr: zero_listing` | absent (no CR slot) |

---

## 7. Related surfaces (no standalone BOA doc)

### Sumter BOA (`platform: manual`) -- documented inline here

`sumter-county-boa.yaml` declares `platform: manual` and omits `base_url` and `category_id`. Extraction notes: "Board of Adjustment -- handles variances and appeals, outside core tracking scope." No standalone `sumter-county-boa.md` doc is produced.

---

## 8. What We Extract vs What's Available

| Data Category | Currently Extracted | Source | Available but Not Extracted | Source |
|---------------|--------------------|--------|-----------------------------|--------|
| BCC Meeting Date | YES (when present) | Tile | -- | -- |
| BCC Meeting Title | YES (when present) | Tile | -- | -- |
| BCC Agenda PDF | YES (when posted) | ViewFile/Agenda | -- | -- |
| BCC Minutes PDF | YES (when posted) | ViewFile/Minutes | -- | -- |
| P&Z Meeting (all) | YES (when present) | Same shape as BCC | -- | -- |
| Agenda items per meeting | NO | -- | Per-item text table | Per-meeting HTML view |
| Attachments per item | NO | -- | ViewFile/Attachment links | Per-meeting view |
| Meeting video | NO | -- | Video-on-demand URL | Site-wide video page |
| RSS subscription | NO | -- | Per-category RSS feed | `AgendaCenter/RSS.aspx` |
| BOA Events | NO | -- | `platform: manual` | (manual workflow) |

---

## 9. Known Limitations and Quirks

1. **`category_id: 5` for BCC, `category_id: 2` for P&Z.** Both IDs were confirmed present on the live AgendaCenter HTML on 2026-04-14 (`chkCategoryID value="5"` and `value="2"` both appeared as live checkbox values). BCC carries an inline comment `# Board of County Commissioners Regular Meeting`; P&Z is declared with an inline comment indicating that the category ID is declared in-repo with an unverified-in-repo note -- confirm against the live AgendaCenter page before relying on it long-term.

2. **P&Z category_id state is declared-but-verification-note.** The `sumter-county-pz.yaml` carries an inline comment asking a future reader to verify the category ID against the live AgendaCenter page. The 2026-04-14 live probe confirmed `CID=2` is still a recognized CivicPlus category, but the in-repo note has not been cleared and should be cleared once someone visually inspects the category title on the portal. This is similar to the Putnam lesson: declared-with-unverified-in-repo comment; confirm against live AgendaCenter.

3. **BOA is `platform: manual`.** `sumter-county-boa.yaml` sets `platform: manual` and omits `base_url` / `category_id`. Dispatch routes to manual workflow.

4. **Sumter is ABSENT from `county-registry.yaml`.** No `sumter-fl` block. Both BI (see `sumter-county-arcgis.md`) and CR surfaces are declared only in their respective source files (`seed_bi_county_config.py` + the three YAMLs) -- no registry-side status tracking.

5. **Portal is at the bare `sumtercountyfl.gov` domain, no `www.`.** Contrast with Santa Rosa (`www.santarosafl.gov`) and Walton (`www.mywaltonfl.gov`). Initial probe follows a redirect before landing on the canonical Agenda Center URL.

6. **`has_duplicate_page_bug: false` on both auto-scraped YAMLs.** No duplicate-page pagination issue observed.

7. **CivicPlus does NOT expose REST/OData.** Scrapers must parse HTML. There is no JSON endpoint equivalent to Legistar's OData. All data comes from server-rendered HTML.

8. **Federated-search `CIDs` parameter is plural.** Even for a single category, the URL segment reads `CIDs={single_id}`. Individual-body listings also accept the bare `AgendaCenter?CID={id}`.

9. **Three distinct CivicPlus tenants in this repo** -- Sumter (`sumtercountyfl.gov`), Santa Rosa (`santarosafl.gov`), Walton (`mywaltonfl.gov`). No tenant-wide settings carry over; each requires its own `base_url` in the YAMLs.

10. **`detection_patterns.header_keywords` for P&Z is just `"PLANNING"`.** Paired with `require_also: "SUMTER COUNTY"`, this tolerates variant page headers like "Planning Board" or "Planning and Zoning" without requiring the full phrase.

11. **`extraction_notes` are the generic FL boilerplate.** BCC: "County body -- cannot annex." / "Generic Florida county. Flag sparse items for review." P&Z: "Planning/advisory board -- recommendations only, not final authority on legislative items." / "Generic Florida county. Flag sparse items for review." BOA: "Board of Adjustment -- handles variances and appeals, outside core tracking scope."

12. **CR YAML exists for Sumter even though the registry does not.** This makes Sumter CR a YAML-only surface. Upgrading to registry status (e.g. `zero_listing`, `pending_validation`, `live`) requires first authoring a `sumter-fl` block in `county-registry.yaml`.

**Source of truth:** `modules/commission/config/jurisdictions/FL/sumter-county-bcc.yaml` (`category_id: 5` with inline comment `# Board of County Commissioners Regular Meeting`), `sumter-county-pz.yaml` (`category_id: 2` with inline verification-note comment), `sumter-county-boa.yaml` (`platform: manual`), confirmed absence of `sumter-fl` block in `county-registry.yaml`, live probe against `https://sumtercountyfl.gov/AgendaCenter` (HTTP 200, ~194 KB, 2026-04-14, confirming `chkCategoryID` checkbox values include both `5` and `2`).
