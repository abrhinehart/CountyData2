# Citrus County FL -- LandmarkWeb (Clerk) API Map (CD2)

Last updated: 2026-04-14

## 1. Service Overview

| Property | Value |
|----------|-------|
| Platform | Pioneer Technology Group LandmarkWeb |
| Portal URL | `https://search.citrusclerk.org/LandmarkWeb` |
| Auth | Anonymous (after session + disclaimer) |
| Protocol | HTTP POST to LandmarkWeb DataTables JSON endpoints |
| Bypass method | **`cloudflare` (requires `curl_cffi` TLS impersonation)** |
| Doc types filter | `'17'` (**DEED only**) |
| Column map | `DEFAULT_COLUMN_MAP` (legal at column 13) |
| Parser | `county_scrapers.landmark_client.LandmarkSession(use_cffi=True)` + `processors.county_parsers.parse_citrus_row` |
| Weekly chunking | Yes (per registry notes) |
| Status | `live` |

### Session handshake

```
GET  https://search.citrusclerk.org/LandmarkWeb/Home/Index
POST https://search.citrusclerk.org/LandmarkWeb/Search/SetDisclaimer   (X-Requested-With: XMLHttpRequest)
```

**IMPORTANT:** Plain `requests.Session` fails because Citrus's front door is behind Cloudflare with TLS-fingerprint inspection. The adapter MUST use `curl_cffi.requests.Session(impersonate='chrome')` (set `use_cffi=True` when constructing `LandmarkSession`).

---

## 2. Search Capabilities

### Request: date-range search

```
POST https://search.citrusclerk.org/LandmarkWeb/Search/RecordDateSearch
Headers: X-Requested-With: XMLHttpRequest
Body:
  beginDate=MM/DD/YYYY
  endDate=MM/DD/YYYY
  doctype=17                     (<- DEED only)
  recordCount=50000
  exclude=false
  ReturnIndexGroups=false
  townName=
  mobileHomesOnly=false
```

### Request: paginated result fetch

```
POST https://search.citrusclerk.org/LandmarkWeb/Search/GetSearchResults
Headers: X-Requested-With: XMLHttpRequest
Body:
  draw={1..N}
  start={offset}
  length=500
```

### Chunking strategy

The registry note says "Weekly chunking". Each request to `RecordDateSearch` covers a 7-day window, with sequential weeks batched to stay under the 50,000-row `recordCount` cap and to minimize risk of Cloudflare rate-limiting.

### Session defaults

| Property | Default |
|----------|---------|
| `page_size` | 500 |
| `request_delay` | 1.0s |
| `use_cffi` | **True** (required) |
| Impersonation | `chrome` (via `curl_cffi`) |

---

## 3. Column Layout

Citrus uses `DEFAULT_COLUMN_MAP` (same as Bay):

| Field | JSON key |
|-------|----------|
| `grantor` | `5` |
| `grantee` | `6` |
| `record_date` | `7` |
| `doc_type` | `8` |
| `book_type` | `9` |
| `book` | `10` |
| `page` | `11` |
| `instrument` | `12` |
| `legal` | `13` |

Value cleanup is the standard LandmarkWeb path: strip `nobreak_`/`hidden_`/`unclickable_` prefixes, replace `nameSeperator` divs with `"; "`, strip HTML tags, `html.unescape`, whitespace collapse.

---

## 4. Document Type Catalog

Citrus is configured for a single doc type:

| Doc type ID | Doc type label | Extracted? |
|-------------|----------------|-----------|
| `17` | DEED | **YES** |
| (all others) | Mortgage, lien, etc. | NO -- filtered out server-side by `doctype=17` |

This is the strictest filter of any FL LandmarkWeb county in the repo. Every row returned from the portal is a deed, which simplifies downstream processing (no need for client-side doc-type filtering).

---

## 5. What We Extract

### From `LandmarkSession._parse_row`

Same 10-field output as Bay / other LandmarkWeb counties:

| Key | Notes |
|-----|-------|
| `grantor` | Multi-party joined with `"; "` |
| `grantee` | Multi-party joined with `"; "` |
| `record_date` | MM/DD/YYYY |
| `doc_type` | `"DEED"` (only possibility given server-side filter) |
| `book_type` | Book-type label |
| `book` | Book number |
| `page` | Page number |
| `instrument` | Instrument / clerk file number |
| `legal` | Legal description (raw portal text) |
| `document_id` | Parsed from DT_RowId |

### From `processors.county_parsers.parse_citrus_row`

Citrus uses a labeled-line legal parser via `_parse_labeled_row(legal_value, _CITRUS_LABEL_ALIASES, _parse_citrus_special_line)`. The parser recognizes:

- **Labeled fields** -- `LOT`, `BLK`, `BLOCK`, `UNIT`, `SUBDIVISION`, etc., with per-county aliases
- **Redaction lines** -- via `_REDACTION_RE`
- **Case references** -- via `_CITRUS_CASE_RE`
- **Metes-and-bounds notes** -- via `_CITRUS_METES_RE`
- **Part-lot** -- via `_CITRUS_PART_LOT_RE`

Unit refs like `83/C` are stripped during parsing (per registry note).

### counties.yaml entry (processor-level config)

```yaml
Citrus:
  column_mapping:
    grantor: Grantor
    grantee: Grantee
    date: Record Date
    instrument: Doc Type
    legal: Legal
  phase_keywords: [Phase, Ph.?, PH, Unit]
  lot_block_cutoffs: [Lot, Lots, Unit, Units, Blk, Block, BLK]
  skiprows: 0
  delimiters: [",", Parcel]
```

---

## 6. Bypass Method

| Component | Detail |
|-----------|--------|
| Registry bypass label | `cloudflare` |
| `county_scrapers/configs.py` status | `cloudflare` |
| Mechanism | Citrus's `search.citrusclerk.org` is fronted by Cloudflare with TLS-fingerprint inspection. A plain `requests.Session` request is rejected (HTTP 403 / challenge page). |
| Solution | `LandmarkSession(use_cffi=True)` constructs a `curl_cffi.requests.Session(impersonate='chrome')`, which negotiates a Chrome TLS fingerprint that Cloudflare accepts. |
| Challenge solving | Not required -- Cloudflare accepts the impersonated Chrome TLS handshake without an interactive challenge. |
| Cookies | Persistent within the session object. |

**Do NOT use plain `requests` for Citrus.** Registry explicitly flags this.

---

## 7. ETL Quirks

- **`doc_types: '17'`** -- single deed doc type, server-side filtered. No other types are returned.
- **Weekly chunking** -- the 50,000-row cap is rarely hit, but weekly windows keep each response small and fast.
- **Unit refs like `83/C` stripped** -- per registry note. The parser removes trailing unit designators so the subdivision name is not polluted by unit codes.
- **`skiprows: 0`** -- the exported CSV has no header garbage to skip.
- **`delimiters: [",", Parcel]`** -- the word `Parcel` in a legal line terminates the subdivision token.
- **Phase keywords include `Unit`** -- Citrus plats sometimes use "Unit" as the phase-equivalent.
- **Special-line parser** -- `_parse_citrus_special_line` handles redactions, case references, metes-and-bounds notes, and part-lot records (rare elsewhere but common in Citrus).

---

## 8. What We Extract vs What's Available

| Data Category | Currently Extracted | Source | Available but Not Extracted | Source |
|---------------|--------------------|---------|-----------------------------|--------|
| Grantor | YES | Column 5 | -- | -- |
| Grantee | YES | Column 6 | -- | -- |
| Record date | YES | Column 7 | -- | -- |
| Doc type | YES (always DEED) | Column 8 | Other doc types (mortgage, lien) | Remove `doctype=17` server-side filter |
| Book / Page / Instrument | YES | Columns 10-12 | -- | -- |
| Book type | YES | Column 9 | -- | -- |
| Legal description | YES | Column 13 | -- | -- |
| Subdivision (structured) | PARTIAL (parsed from legal) | `_parse_labeled_row` | -- | -- |
| Lot / Block / Unit (structured) | YES (parsed) | `_parse_labeled_row` | -- | -- |
| Consideration | NO | -- | Not on grid; requires detail page | `GetRecordDetails` (not implemented) |
| Document image | NO | -- | LandmarkWeb per-doc PDF | Action links in grid |
| Case references | YES (as labeled_line `kind: case_reference`) | `_parse_citrus_special_line` | -- | -- |
| Metes-and-bounds notes | YES (as `kind: metes_bounds_note`) | `_parse_citrus_special_line` | -- | -- |
| Redaction flags | YES | `_parse_citrus_special_line` | -- | -- |

---

## 9. Known Limitations and Quirks

1. **Requires `curl_cffi` TLS impersonation.** Cloudflare inspects TLS fingerprints at `search.citrusclerk.org`. A plain `requests.Session` fails. The adapter MUST construct `LandmarkSession(use_cffi=True)` which internally uses `curl_cffi.requests.Session(impersonate='chrome')`. Plain `requests` is NOT sufficient.

2. **Server-side filter to DEED only.** `doc_types: '17'` ensures only deeds are returned. Changing this requires modifying `county_scrapers/configs.py::LANDMARK_COUNTIES['Citrus'].doc_types`.

3. **Weekly chunking.** Searches are issued in 7-day windows to avoid Cloudflare rate-limiting and to keep each response small. The `recordCount=50000` cap is per search, not per window.

4. **`LandmarkSession.page_size = 500`.** Results are paginated in 500-row chunks via `GetSearchResults`. Inter-page sleep = 1.0s.

5. **Unit designators like `83/C` are stripped.** The Citrus legal parser removes these before writing `subdivision`, so downstream joins must not expect them.

6. **Special-line parser is Citrus-specific.** `_parse_citrus_special_line` handles redactions, case refs, metes-and-bounds, and part-lot entries. Removing it (e.g., accidentally using `_parse_labeled_row` without the special-line parser) will silently mis-parse those rows as unlabeled free-text.

7. **URL is `search.citrusclerk.org`, not `records.citrusclerk.org` or `citrusclerk.org`.** The `search.` subdomain is specific and required.

8. **`column_map: None` -> falls back to `DEFAULT_COLUMN_MAP`.** The `get_landmark_config` helper substitutes `dict(DEFAULT_COLUMN_MAP)` when the per-county `column_map` is `None`. This means any future extended-column version of Citrus's portal requires an explicit override in `configs.py`.

9. **No `hidden_legalfield_` subdivision column.** Unlike Hernando (which uses a v1.5.87 extended layout with a structured subdivision column at index 19), Citrus uses the default 9-column layout. Subdivision extraction is entirely from the free-text `legal` field.

10. **Do NOT retry Cloudflare-blocked responses in a tight loop.** If the impersonation fails (e.g., `curl_cffi` version mismatch), retrying will just get more 403s. Fix the impersonation layer first.

**Source of truth:** `county_scrapers/configs.py` (`LANDMARK_COUNTIES['Citrus']` at lines 67-73), `county_scrapers/landmark_client.py`, `counties.yaml` (`Citrus` block, lines 43-67), `processors/county_parsers.py::parse_citrus_row` (line 368), `county-registry.yaml` (`citrus-fl.projects.cd2`)
