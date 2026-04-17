# Okeechobee County FL -- LandmarkWeb (Clerk) API Map (CD2)

Last updated: 2026-04-14

## 1. Service Overview

| Property | Value |
|----------|-------|
| Platform | Pioneer Technology Group LandmarkWeb (portal version **v1.5.93**) |
| Portal URL | `https://pioneer.okeechobeelandmark.com/LandmarkWebLive` |
| Auth | Anonymous (after session + disclaimer) |
| Protocol | HTTP POST to LandmarkWeb DataTables JSON endpoints |
| Bypass method | `none` (plain `requests.Session` works) |
| Doc types filter | `''` (empty -- all types; downstream filtering in processor) |
| Column map | **Custom `_OKEECHOBEE_COLUMN_MAP`** (legal at **column 14**) |
| Parser | `county_scrapers.landmark_client.LandmarkSession(use_cffi=False)` + `processors.county_parsers.parse_okeechobee_row` |
| Status | `live` (fully automated) |

### Important: URL suffix is `/LandmarkWebLive`

The Okeechobee portal uses `/LandmarkWebLive`, not `/LandmarkWeb`. This is a Pioneer naming variant for this specific tenant (some newer tenants use the `-Live` suffix). Using the wrong suffix returns 404.

### Session handshake

```
GET  https://pioneer.okeechobeelandmark.com/LandmarkWebLive/Home/Index
POST https://pioneer.okeechobeelandmark.com/LandmarkWebLive/Search/SetDisclaimer
     (X-Requested-With: XMLHttpRequest)
```

No Cloudflare, no CAPTCHA. Plain `requests.Session` with urllib3 retries is sufficient.

---

## 2. Search Capabilities

### Request: date-range search

```
POST https://pioneer.okeechobeelandmark.com/LandmarkWebLive/Search/RecordDateSearch
Headers: X-Requested-With: XMLHttpRequest
Body:
  beginDate=MM/DD/YYYY
  endDate=MM/DD/YYYY
  doctype=                    (empty -- all types)
  recordCount=50000
  exclude=false
  ReturnIndexGroups=false
  townName=
  mobileHomesOnly=false
```

### Request: paginated result fetch

```
POST https://pioneer.okeechobeelandmark.com/LandmarkWebLive/Search/GetSearchResults
Headers: X-Requested-With: XMLHttpRequest
Body:
  draw={1..N}
  start={offset}
  length=500
```

### Session defaults

| Property | Default |
|----------|---------|
| `page_size` | 500 |
| `request_delay` | 1.0s |
| `use_cffi` | **False** (Okeechobee does NOT need TLS impersonation) |
| Retries | `Retry(total=3, backoff_factor=1.5, status_forcelist=[500,502,503,504])` |

---

## 3. Column Layout (v1.5.93-specific)

Okeechobee's LandmarkWeb portal is version 1.5.93, which uses a slightly **different column layout** than the v1.5.87 Hernando portal and the default 13-column layout. The custom map in `county_scrapers/configs.py::_OKEECHOBEE_COLUMN_MAP`:

```python
_OKEECHOBEE_COLUMN_MAP = {
    'grantor': '5',
    'grantee': '6',
    'record_date': '7',
    'doc_type': '8',
    'book_type': '9',
    'book': '10',
    'page': '11',
    'instrument': '12',
    'legal': '14',      # column 13 is a secondary instrument/case number
}
```

### Key difference from the default: legal is at column **14**, not 13

The Okeechobee portal inserts a secondary instrument / case-number column at index 13, pushing the legal description to column 14. Using `DEFAULT_COLUMN_MAP` (which has `legal: '13'`) on Okeechobee data would silently return the wrong column -- case numbers instead of legal descriptions.

### Comparison with other tenants

| County | Portal version | Legal column | Subdivision column |
|--------|----------------|--------------|---------------------|
| Bay / Citrus / Escambia / Walton | Default / older | 13 | (none) |
| Hernando | v1.5.87 | 14 | 19 (`hidden_legalfield_`) |
| **Okeechobee** | **v1.5.93** | **14** | (none) |

---

## 4. Document Type Catalog

Okeechobee is configured with `doc_types: ''` (all types). Deed filtering happens in the processor layer via `counties.yaml` -> `Okeechobee.column_mapping.instrument = "Doc Type"` (a text-match).

Typical LandmarkWeb Okeechobee doc types: DEED (D, WD, QC), MORTGAGE (M), AGREEMENT (AG), LIEN (L), NOTICE OF COMMENCEMENT, PLAT, etc.

---

## 5. What We Extract

### From `LandmarkSession._parse_row`

| Key | Notes |
|-----|-------|
| `grantor` | Column 5 |
| `grantee` | Column 6 |
| `record_date` | Column 7 |
| `doc_type` | Column 8 |
| `book_type` | Column 9 |
| `book` | Column 10 |
| `page` | Column 11 |
| `instrument` | Column 12 |
| `legal` | **Column 14** (NOT 13) |
| `document_id` | Parsed from DT_RowId |

### From `processors.county_parsers.parse_okeechobee_row` (line 1009)

The Okeechobee parser is the most custom of any FL county:

1. Splits the `legal` value on `\n` (multi-line legal descriptions).
2. Normalizes each line via `_normalize_freeform_line`.
3. Consumes leading parcel references via `_consume_leading_parcel_references` -- captures parcel IDs that appear as prefixes before the actual legal description.
4. For each cleaned line, splits into segments via `_split_okeechobee_segments`.
5. Extracts Section/Township/Range via `_extract_okeechobee_str`.
6. Consumes LOT tokens via `_consume_okeechobee_lot_tokens` (supports ranges and comma-separated lists).
7. Consumes BLK / BLOCK tokens via `_collect_block_tokens`.
8. Reads the remainder as subdivision; handles `PTN ` prefix (partial subdivision) specifically.
9. Builds subdivision details via `_build_okeechobee_unit_details` (handles condo unit / building / storage-locker specifiers).

### counties.yaml entry

```yaml
Okeechobee:
  column_mapping:
    grantor: "Grantor(s)"
    grantee: "Grantee(s)"
    date: "Record Date"
    instrument: "Doc Type"
    legal: "Legal"
  phase_keywords: [Phase, Ph.?, PH, Unit]
  lot_block_cutoffs: [Lot, Lots, Unit, Units, Blk, Block, BLK]
  skiprows: 0
  delimiters: [",", Parcel]
```

Note the parenthesized CSV header names: `"Grantor(s)"`, `"Grantee(s)"` (not `"Grantor"` / `"Grantee"` and not Escambia's `"Direct Name"` / `"Reverse Name"`).

---

## 6. Bypass Method

| Component | Detail |
|-----------|--------|
| Registry bypass label | `none` |
| `county_scrapers/configs.py` status | `working` |
| Mechanism | No Cloudflare, no CAPTCHA. Plain `LandmarkSession.connect()` succeeds after one disclaimer POST. |
| `use_cffi` | `False` |

Okeechobee is one of two fully automated FL LandmarkWeb counties in the repo (the other is Hernando).

---

## 7. ETL Quirks

- **Legal is at column 14, not 13.** The v1.5.93 portal inserts a secondary instrument/case column at 13. Any attempt to read with `DEFAULT_COLUMN_MAP` returns case numbers in the `legal` slot.
- **Multi-line parcel IDs -> `before_first_newline` on parties.** Per registry notes: "Multi-line parcel IDs need BEFORE_FIRST_NEWLINE cleanup." The LandmarkWeb grid sometimes renders multiple parcel IDs (one per line) inside a single party cell. Downstream processing truncates to the first newline to avoid mixing parties.
- **CSV headers use `(s)` suffix.** `"Grantor(s)"` and `"Grantee(s)"`, unlike Bay / Citrus (`"Grantor"` / `"Grantee"`) or Escambia (`"Direct Name"` / `"Reverse Name"`).
- **`parse_okeechobee_row` is the most custom parser** of any FL county in `processors/county_parsers.py`. It dedicates logic to section/township/range extraction, PTN (partial) subdivisions, condo unit designators, and multi-line parcel reference consumption.
- **Delimiters include `Parcel`.** Any legal line containing the word `Parcel` is treated as a segment boundary.
- **Lot tokens support ranges and comma lists.** `_consume_okeechobee_lot_tokens` handles values like `"LOT 1-3"`, `"LOTS 1,2,4"`, and `"LOT 1 & 2"`.
- **`PTN` prefix.** Subdivision names starting with `PTN ` (partial) are flagged with `subdivision_partial: True` and stripped of the `PTN ` prefix.

---

## 8. What We Extract vs What's Available

| Data Category | Currently Extracted | Source | Available but Not Extracted | Source |
|---------------|--------------------|---------|-----------------------------|--------|
| Grantor(s) | YES | Column 5 | -- | -- |
| Grantee(s) | YES | Column 6 | -- | -- |
| Record date | YES | Column 7 | -- | -- |
| Doc type | YES | Column 8 | -- | -- |
| Book type | YES | Column 9 | -- | -- |
| Book / Page | YES | Columns 10-11 | -- | -- |
| Instrument | YES | Column 12 | -- | -- |
| **Secondary instrument / case number** | NO | -- | Secondary instrument/case at column 13 (skipped in column_map) | Column 13 |
| Legal description | YES | **Column 14** | -- | -- |
| Parcel references | YES (parsed from legal) | `_consume_leading_parcel_references` | -- | -- |
| Section / Township / Range | YES (parsed) | `_extract_okeechobee_str` | -- | -- |
| Lot | YES (parsed, supports ranges) | `_consume_okeechobee_lot_tokens` | -- | -- |
| Block | YES (parsed) | `_collect_block_tokens` | -- | -- |
| Subdivision | YES (parsed, handles `PTN `) | `_build_okeechobee_unit_details` | -- | -- |
| Condo unit / building / storage locker | YES (parsed for condo subdivisions) | `_build_okeechobee_unit_details` | -- | -- |
| Consideration | NO | -- | Not on grid; requires detail page | `GetRecordDetails` (not implemented) |
| Document image (PDF) | NO | -- | LandmarkWeb per-doc PDF | Action links |

---

## 9. Known Limitations and Quirks

1. **Portal version is v1.5.93 -- legal at column 14, NOT 13.** The most important quirk. The portal inserts a secondary instrument/case-number column at index 13, pushing legal to 14. Using `DEFAULT_COLUMN_MAP` silently corrupts the legal field.

2. **URL suffix is `/LandmarkWebLive`, not `/LandmarkWeb`.** The `-Live` suffix is specific to this tenant. Do not trim it.

3. **Multi-line parcel IDs in party cells.** Per registry: "Multi-line parcel IDs need BEFORE_FIRST_NEWLINE cleanup." Grantor/grantee cells sometimes contain multiple parcel IDs separated by newlines; processing must truncate to the first newline.

4. **CSV headers are `"Grantor(s)"` / `"Grantee(s)"` (parenthesized plural).** Distinct from every other FL county's header convention. Downstream CSV readers must use these exact strings.

5. **Bypass is `none` -- plain requests work.** No Cloudflare, no CAPTCHA. Okeechobee is one of the easiest FL LandmarkWeb tenants to scrape.

6. **Doc types filter is empty.** All document types returned; filter to deeds in processor.

7. **`parse_okeechobee_row` is highly customized.** It handles PTN (partial) subdivisions, condo unit/building/storage locker tokens, leading parcel references, section/township/range extraction, and LOT-range/comma-list parsing. Porting to another county would require significant refactoring.

8. **`delimiters` includes `Parcel`.** The word `Parcel` in a legal line is treated as a segment boundary (same as other FL counties in this repo).

9. **`phase_keywords` includes `Unit`.** Like Bay and Citrus, Okeechobee plats use "Unit" as the phase-equivalent for some subdivisions.

10. **No subdivision column in CSV.** `column_mapping` has no `sub` entry. Subdivision names come from legal-field parsing, not a dedicated column.

11. **`skiprows: 0`** -- CSV has no header garbage to skip.

12. **Hostname is `pioneer.okeechobeelandmark.com`.** Note the distinctive `pioneer.` subdomain (referencing Pioneer Technology Group, the LandmarkWeb vendor) and the `okeechobeelandmark.com` apex domain (not `okeechobeeclerk.com`).

**Source of truth:** `county_scrapers/configs.py` (`LANDMARK_COUNTIES['Okeechobee']` at lines 60-66, `_OKEECHOBEE_COLUMN_MAP` at lines 33-43), `county_scrapers/landmark_client.py`, `counties.yaml` (`Okeechobee` block, lines 177-201), `processors/county_parsers.py::parse_okeechobee_row` (line 1009), `county-registry.yaml` (`okeechobee-fl.projects.cd2`)
