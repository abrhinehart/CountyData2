# Escambia County FL -- LandmarkWeb (Clerk) API Map (CD2)

Last updated: 2026-04-14

## 1. Service Overview

| Property | Value |
|----------|-------|
| Platform | Pioneer Technology Group LandmarkWeb |
| Portal URL | `https://dory.escambiaclerk.com/LandmarkWeb` |
| Auth | Anonymous (after session + disclaimer) |
| Protocol | HTTP POST to LandmarkWeb DataTables JSON endpoints |
| Bypass method | **`cloudflare` (requires `curl_cffi` TLS impersonation)** |
| Doc types filter | `''` (empty -- all doc types; downstream filtering by processor) |
| Column map | `DEFAULT_COLUMN_MAP` (legal at column 13) |
| Parser | `county_scrapers.landmark_client.LandmarkSession(use_cffi=True)` + `processors.county_parsers.parse_escambia_row` |
| Party-field labels | **`Direct Name` / `Reverse Name`** (NOT `Grantor` / `Grantee`) |
| Status | `live` |

### Session handshake

```
GET  https://dory.escambiaclerk.com/LandmarkWeb/Home/Index
POST https://dory.escambiaclerk.com/LandmarkWeb/Search/SetDisclaimer   (X-Requested-With: XMLHttpRequest)
```

Both requests MUST go through `curl_cffi` with Chrome impersonation; Cloudflare blocks plain `requests.Session` at the TLS-fingerprint level.

---

## 2. Search Capabilities

### Request: date-range search

```
POST https://dory.escambiaclerk.com/LandmarkWeb/Search/RecordDateSearch
Headers: X-Requested-With: XMLHttpRequest
Body:
  beginDate=MM/DD/YYYY
  endDate=MM/DD/YYYY
  doctype=                      (empty -- all types)
  recordCount=50000
  exclude=false
  ReturnIndexGroups=false
  townName=
  mobileHomesOnly=false
```

### Request: paginated result fetch

```
POST https://dory.escambiaclerk.com/LandmarkWeb/Search/GetSearchResults
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
| `use_cffi` | **True** (required) |
| Impersonation | `chrome` |

---

## 3. Column Layout

Escambia uses `DEFAULT_COLUMN_MAP`:

| Field (LandmarkWeb key) | JSON column index |
|-------------------------|-------------------|
| `grantor` | `5` |
| `grantee` | `6` |
| `record_date` | `7` |
| `doc_type` | `8` |
| `book_type` | `9` |
| `book` | `10` |
| `page` | `11` |
| `instrument` | `12` |
| `legal` | `13` |

### IMPORTANT: CSV column labels are different

While the scraper's `column_map` uses the keys `grantor` and `grantee` internally, the downstream CSV export column headers are `Direct Name` and `Reverse Name`, not `Grantor` and `Grantee`. `counties.yaml` captures this:

```yaml
Escambia:
  column_mapping:
    grantor: Direct Name
    grantee: Reverse Name
    date: Record Date
    instrument: Doc Type
    legal: Legal
```

Any downstream script that reads the Escambia CSV must look up the headers `Direct Name` and `Reverse Name`, NOT `Grantor` / `Grantee`.

---

## 4. Document Type Catalog

Escambia is configured with `doc_types: ''` (server returns all types). Downstream deed filtering occurs in the processor layer via a text match on `Doc Type` (the CSV column mapped from `instrument`).

Typical LandmarkWeb Escambia doc types include DEED, MORTGAGE, AGREEMENT, LIEN, NOTICE OF COMMENCEMENT, PLAT, and many others.

---

## 5. What We Extract

### From `LandmarkSession._parse_row`

Same 10 fields as other LandmarkWeb counties:

| Key | Notes |
|-----|-------|
| `grantor` | From column 5; mapped from Escambia's "Direct Name" data |
| `grantee` | From column 6; mapped from Escambia's "Reverse Name" data |
| `record_date` | MM/DD/YYYY |
| `doc_type` | Text label |
| `book_type` | Text label |
| `book` | |
| `page` | |
| `instrument` | Clerk file number |
| `legal` | Raw legal text |
| `document_id` | Parsed from DT_RowId |

### From `processors.county_parsers.parse_escambia_row`

```python
def parse_escambia_row(row: pd.Series, cols: dict) -> dict:
    legal_value = row.get(cols.get('legal', ''), pd.NA)
    return _parse_labeled_row(legal_value, _ESCAMBIA_LABEL_ALIASES)
```

Escambia uses a labeled-line legal parser with `_ESCAMBIA_LABEL_ALIASES`. No special-line handler (unlike Citrus). The parser recognizes LOT / BLK / UNIT / SUBDIVISION / SECTION / TOWNSHIP / RANGE labels when present, and emits `kind: unparsed` for lines without recognizable labels.

---

## 6. Bypass Method

| Component | Detail |
|-----------|--------|
| Registry bypass label | `cloudflare` |
| `county_scrapers/configs.py` status | `cloudflare` |
| Mechanism | Cloudflare with TLS fingerprint inspection at `dory.escambiaclerk.com`. Plain `requests.Session` is rejected. |
| Solution | `LandmarkSession(use_cffi=True)` -> `curl_cffi.requests.Session(impersonate='chrome')`. |
| Challenge solving | Not required (Cloudflare accepts Chrome TLS fingerprint). |

---

## 7. ETL Quirks

- **Party labels are `Direct Name` / `Reverse Name`.** NOT `Grantor` / `Grantee`. Downstream CSV readers must use these exact headers.
- **`doc_types: ''`** -- all types returned server-side. Filter to deeds in the processor.
- **LOT / BLK / SUB stripping** per `counties.yaml`:
  - `phase_keywords: [Phase, Ph.?, PH, Unit]`
  - `lot_block_cutoffs: [Lot, Lots, Unit, Units, Blk, Block, BLK]`
  - `delimiters: [",", Parcel]`
- **`skiprows: 0`** -- no header rows to skip.
- **No subdivision column in CSV.** `column_mapping` has no `sub` entry (unlike Hernando, MS counties). Subdivision is extracted from the free-text `legal` field during processor parsing.
- **LandmarkWeb cleanup applies.** `_clean_value` strips `nobreak_`, `hidden_`, `unclickable_` prefixes; replaces nameSeperator divs with `"; "`; strips HTML tags; `html.unescape`; whitespace-collapses.

---

## 8. What We Extract vs What's Available

| Data Category | Currently Extracted | Source | Available but Not Extracted | Source |
|---------------|--------------------|---------|-----------------------------|--------|
| Direct Name (grantor) | YES | Column 5 | -- | -- |
| Reverse Name (grantee) | YES | Column 6 | -- | -- |
| Record date | YES | Column 7 | -- | -- |
| Doc type | YES | Column 8 | -- | -- |
| Book type | YES | Column 9 | -- | -- |
| Book / Page / Instrument | YES | Columns 10-12 | -- | -- |
| Legal description | YES | Column 13 | -- | -- |
| Subdivision (structured) | PARTIAL (parsed from legal) | `_parse_labeled_row` | -- | -- |
| Lot / Block / Unit (structured) | YES (parsed) | `_parse_labeled_row` | -- | -- |
| Consideration | NO | -- | Not on grid; would need detail page | `GetRecordDetails` (not implemented) |
| Document image (PDF) | NO | -- | LandmarkWeb per-doc PDF | Action links |
| Case references / metes-bounds | NO | -- | Would require Escambia-specific special-line parser (not implemented; Citrus has one) | -- |

---

## 9. Known Limitations and Quirks

1. **Party labels are `Direct Name` and `Reverse Name`.** This is the single biggest gotcha for Escambia -- the CSV column headers exported from LandmarkWeb are NOT `Grantor` / `Grantee`. `counties.yaml` `Escambia.column_mapping` points `grantor -> Direct Name` and `grantee -> Reverse Name`. Downstream CSV consumers that look up `Grantor` / `Grantee` headers will find nothing and silently skip rows.

2. **Requires `curl_cffi` TLS impersonation.** Cloudflare at `dory.escambiaclerk.com` inspects TLS fingerprints. Plain `requests.Session` fails. Adapter MUST set `use_cffi=True`.

3. **Subdomain is `dory.escambiaclerk.com`.** Note the `dory.` prefix -- this is Pioneer's LandmarkWeb hosted at a specific subdomain. The root `escambiaclerk.com` is the clerk's marketing site, not the LandmarkWeb instance.

4. **URL suffix is `/LandmarkWeb`.** Unlike Bay (which uses `/Recording`), Escambia uses the canonical `/LandmarkWeb` suffix.

5. **Doc types filter is empty (all types).** Deed filtering happens downstream, not at the portal. For volume-bounded queries, consider adding a doc-type filter.

6. **No special-line parser.** `parse_escambia_row` calls `_parse_labeled_row` without a special-line parser, so redactions / case references / metes-and-bounds notes are emitted as `kind: unparsed` rather than structured entries. Citrus has a dedicated `_parse_citrus_special_line`; Escambia does not.

7. **No `hidden_legalfield_` subdivision column.** Escambia uses `DEFAULT_COLUMN_MAP`; subdivision names come from free-text parsing, not a structured column.

8. **Default `DEFAULT_COLUMN_MAP` -> legal at column 13.** If Escambia upgrades to a newer LandmarkWeb version (e.g., Hernando's v1.5.87), the legal column may shift to 14 and extended fields at 15-25. Verify before assuming.

9. **Weekly chunking is NOT configured for Escambia.** Unlike Citrus (which explicitly chunks weekly per the registry note), Escambia is not flagged for weekly chunking. However, the same 50,000-row `recordCount` cap applies, and operators should self-chunk for very large date ranges.

10. **Do NOT retry Cloudflare-blocked responses in a tight loop.** If impersonation fails, retrying yields more 403s. Fix the `curl_cffi` version mismatch first.

**Source of truth:** `county_scrapers/configs.py` (`LANDMARK_COUNTIES['Escambia']` at lines 74-80), `county_scrapers/landmark_client.py`, `counties.yaml` (`Escambia` block, lines 69-93 -- `Direct Name` / `Reverse Name` labels), `processors/county_parsers.py::parse_escambia_row` (line 373), `county-registry.yaml` (`escambia-fl.projects.cd2`)
