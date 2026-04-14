# Bay County FL -- LandmarkWeb (Clerk) API Map (CD2)

Last updated: 2026-04-14

## 1. Service Overview

| Property | Value |
|----------|-------|
| Platform | Pioneer Technology Group LandmarkWeb |
| Portal URL | `https://records2.baycoclerk.com/Recording` |
| Auth | Anonymous search after session + disclaimer handshake |
| Protocol | HTTP POST to LandmarkWeb DataTables JSON endpoints |
| Bypass method | `captcha_hybrid` (cookie hand-off; see Bypass section) |
| Doc types filter | `''` (empty -- all doc types returned; downstream filtering in `processors/`) |
| Column map | `DEFAULT_COLUMN_MAP` (legal at column 13) |
| Portal version | Pioneer standard (no extended legal columns like Hernando v1.5.87) |
| Client | `county_scrapers.landmark_client.LandmarkSession` |

**Important URL suffix:** Bay uses `/Recording`, NOT `/LandmarkWeb`. Applying the wrong suffix returns 404.

### Session handshake

```
GET  https://records2.baycoclerk.com/Recording/Home/Index
POST https://records2.baycoclerk.com/Recording/Search/SetDisclaimer   (X-Requested-With: XMLHttpRequest)
```

Once the disclaimer POST returns 200, the session cookie unlocks `/Search/RecordDateSearch` and `/Search/GetSearchResults`.

---

## 2. Search Capabilities

### Request: date-range search

```
POST https://records2.baycoclerk.com/Recording/Search/RecordDateSearch
Headers: X-Requested-With: XMLHttpRequest
Body (form-encoded):
  beginDate=MM/DD/YYYY
  endDate=MM/DD/YYYY
  doctype=          (empty -- all types)
  recordCount=50000
  exclude=false
  ReturnIndexGroups=false
  townName=
  mobileHomesOnly=false
```

### Request: paginated result fetch

```
POST https://records2.baycoclerk.com/Recording/Search/GetSearchResults
Headers: X-Requested-With: XMLHttpRequest
Body:
  draw={1..N}
  start={row offset}
  length=500            (from LandmarkSession.page_size)
```

### Pagination

The LandmarkSession drives pagination by incrementing `start` by the page length until either the response returns an empty `data` array or `start >= recordsTotal`. Inter-page sleep = `request_delay` (default 1.0s).

### Session defaults

| Property | Default |
|----------|---------|
| `page_size` | 500 |
| `request_delay` | 1.0s |
| `use_cffi` | False (plain requests + urllib3 retries) |
| Retries | `Retry(total=3, backoff_factor=1.5, status_forcelist=[500,502,503,504])` |

---

## 3. Column Layout (DataTables JSON)

Bay uses `DEFAULT_COLUMN_MAP` from `county_scrapers.landmark_client`:

| Field | JSON key (column index) |
|-------|-------------------------|
| `grantor` | `5` |
| `grantee` | `6` |
| `record_date` | `7` |
| `doc_type` | `8` |
| `book_type` | `9` |
| `book` | `10` |
| `page` | `11` |
| `instrument` | `12` |
| `legal` | `13` |

Row IDs carry the document_id: `DT_RowId` is of the form `row_{DOCUMENT_ID}_...`, and `LandmarkSession._parse_row` splits on `_` to pull the second element as `document_id`.

### Value cleanup

`_clean_value` applies (in order):
1. Strip LandmarkWeb internal prefixes (`nobreak_`, `hidden_`, `hidden_legalfield_`, `unclickable_`) via `_VALUE_PREFIX_RE`.
2. Replace `<div class='nameSeperator'></div>` with `; ` (for multi-party rows).
3. Strip remaining HTML tags.
4. `html.unescape(...)`.
5. Collapse internal whitespace runs to single spaces.

---

## 4. Document Type Catalog

Bay is configured with `doc_types: ''` (all types). Downstream deed filtering happens in the processor layer via `counties.yaml` -> `Bay.column_mapping.instrument = "Doc Type"` (a string label, not a numeric ID).

Typical LandmarkWeb Bay County doc types (as exposed in the portal's Document Type lookup):
- DEED (D / D1 / D2 / etc.)
- MORTGAGE (M)
- AGREEMENT (AG)
- LIEN (L)
- NOTICE OF COMMENCEMENT (NOC)
- CLAIM OF LIEN (COL)
- PLAT
- (Many more -- LandmarkWeb supports 100+ doc types per jurisdiction)

The downstream processor reads `Doc Type` as a text column (not a numeric ID), so doc-type filtering is a string-level `in`-check on the parsed CSV column.

---

## 5. What We Extract

Each LandmarkSession row (`_parse_row`) yields the following dict:

| Key | Notes |
|-----|-------|
| `grantor` | Cleaned from column 5; multi-grantor separated by `"; "` |
| `grantee` | Cleaned from column 6; multi-grantee separated by `"; "` |
| `record_date` | MM/DD/YYYY as presented by the portal |
| `doc_type` | Text label, e.g., `"DEED"`, `"MORTGAGE"` |
| `book_type` | Text label (e.g., `"Official Records"`) |
| `book` | Book number |
| `page` | Starting page number |
| `instrument` | Instrument / clerk file number |
| `legal` | Legal description (plain text; may contain `Phase`, `Lot`, `Blk`, `Sub`, etc.) |
| `document_id` | Numeric ID parsed from `DT_RowId` |

### Downstream processing (from `counties.yaml` + `processors/county_parsers.py::parse_bay_row`)

Bay's legal column is parsed via `_parse_freeform_row(legal_value)` (the generic freeform parser). Counties.yaml declares:

```yaml
Bay:
  column_mapping:
    grantor: Grantor
    grantee: Grantee
    date: Record Date Search
    legal: Legal
    instrument: Doc Type
  cleanup_patterns:
    - '^L\s*\d+(?:-\d+)?\s*'
    - '^LOTS?\s*\d+(?:-\d+)?\s*'
```

The `cleanup_patterns` strip a leading `L{digits}` or `LOT{s} {digits}` prefix from each legal line before further parsing.

---

## 6. Bypass Method

| Component | Detail |
|-----------|--------|
| Registry bypass label | `captcha_hybrid` |
| `county_scrapers/configs.py` status | `captcha_hybrid` |
| Mechanism | The adapter performs a normal session connect (GET Home + POST SetDisclaimer); the Bay portal presents a CAPTCHA challenge server-side only under certain heuristics. When challenged, the operator drives one manual search in a browser, then `LandmarkSession.from_cookies(...)` imports the browser cookies into the scraper's session to unlock subsequent automated queries. |
| Helper | `county_scrapers/cookie_session.py::apply_cookies_to_session` |
| `use_cffi` | `False` (Bay does not need curl_cffi TLS impersonation) |

Note on scope: Bay is the only LandmarkWeb-style county in the `county-registry.yaml` that uses the `/Recording` suffix and the `captcha_hybrid` flow. Citrus, Escambia, and Walton all use `cloudflare` (curl_cffi impersonation).

---

## 7. ETL Quirks

From `counties.yaml` Bay block:

- **`date` column is `"Record Date Search"`**, not `"Record Date"`. This differs from Citrus / Escambia / Hernando / Okeechobee / Walton, which all use `"Record Date"`. Downstream CSV ingestion must know the exact header or columns will misalign.
- **`instrument` column is `"Doc Type"`.** The deed-type filter in the transformer is a string match on that column.
- **`delimiters` in the legal parser include `,` and `Parcel`.** Any legal line containing the word `Parcel` is treated as a boundary token, not a subdivision substring.
- **`phase_keywords`:** `Phase`, `Ph.?`, `PH`, `Unit`. `Unit` is included because Bay's plats frequently use `Unit` as the phase-equivalent.
- **`lot_block_cutoffs`:** `Lot`, `Lots`, `Unit`, `Units`, `Blk`, `Block`, `BLK`. These terminate parsing of the subdivision portion of a legal line.
- **`cleanup_patterns`** remove a leading `L\d+` or `LOTS?\s*\d+` prefix. Example: `"L2 PINE GROVE PHASE 3"` -> `"PINE GROVE PHASE 3"`.

---

## 8. What We Extract vs What's Available

| Data Category | Currently Extracted | Source | Available but Not Extracted | Source |
|---------------|--------------------|---------|-----------------------------|--------|
| Grantor (primary) | YES | Column 5 | Additional parties beyond first | Column 5 joined `; ` |
| Grantee (primary) | YES | Column 6 | -- | -- |
| Record date | YES | Column 7 | -- | -- |
| Doc type | YES | Column 8 | -- | -- |
| Book / Page / Instrument | YES | Columns 10-12 | Book type | Column 9 (used, but not surfaced as a deed field) |
| Legal description | YES | Column 13 | Subdivision, section, township, range (structured) | Would require v1.5.87-style extended columns; Bay does NOT expose those |
| Consideration / sale price | NO | -- | Not in the default grid; requires detail page | Per-document `GetRecordDetails` (not implemented) |
| Document image (PDF) | NO | -- | LandmarkWeb offers per-doc PDF downloads | `Document` action links in grid |
| Subdivision (dedicated column) | NO | -- | Not present on default column map | -- |
| Phase / Lot / Block (structured) | NO (parsed from free-text `legal` only) | -- | Would require v1.5.87-style extended columns | -- |

Bay's LandmarkWeb grid is the older / standard flavor (9 fields), not the Hernando v1.5.87 extended layout (`legal` at col 14, subdivision at col 19). Any future upgrade that extends columns will require a county-specific `column_map` override in `county_scrapers/configs.py`.

---

## 9. Known Limitations and Quirks

1. **URL suffix is `/Recording`, not `/LandmarkWeb`.** The adapter config at `county_scrapers/configs.py` has `base_url: 'https://records2.baycoclerk.com/Recording'`. Do NOT append `/LandmarkWeb` -- Bay does not use that suffix.

2. **Bypass = `captcha_hybrid`.** Bay occasionally presents a CAPTCHA to automated sessions. The workaround is a manual-in-browser first search to obtain cookies, then `LandmarkSession.from_cookies(...)` replays them. Plain `LandmarkSession.connect()` is NOT guaranteed to succeed standalone.

3. **Legal column is at index 13.** Bay uses `DEFAULT_COLUMN_MAP` (legal at 13, no subdivision column). If a field shift is observed, re-verify column indices via live DataTables JSON inspection.

4. **`date` column header is unique.** Counties.yaml uses `"Record Date Search"` for Bay vs `"Record Date"` for other FL counties. This is the exact CSV header expected from the downstream export.

5. **Cleanup patterns strip leading `L\d+` and `LOTS?\s*\d+`.** These are county-specific pre-processing steps on the legal field. Example transformation: `"LOTS 1-3 PINE GROVE"` -> `"PINE GROVE"`.

6. **No curl_cffi.** Bay does NOT require `use_cffi=True`. Plain `requests.Session` with the standard retry policy is sufficient once the disclaimer is accepted.

7. **Doc types filter is empty.** `doc_types: ''` means all doc types are returned. Downstream filtering (to deeds only) happens in the processor layer via `instrument: "Doc Type"` string matching.

8. **`bay_price_extract.py` uses a separate scraping flow.** The standalone `bay_price_extract.py` script reads deed records from `records2.baycoclerk.com/Recording/` to extract consideration (sale price) data. It references the same portal but runs as a price-enrichment pass, not part of the standard `LandmarkSession` pipeline.

9. **No structured subdivision column.** Bay's grid does not publish the `hidden_legalfield_` subdivision helper column that Hernando exposes. Subdivision names must be parsed from the free-text `legal` field via the cleanup patterns + freeform parser.

10. **Portal is at `records2.baycoclerk.com`.** Note the `records2` subdomain -- the bare `records.baycoclerk.com` may exist but is not the scraper target.

**Source of truth:** `county_scrapers/configs.py` (`LANDMARK_COUNTIES['Bay']` at lines 91-97), `county_scrapers/landmark_client.py` (`LandmarkSession`, `DEFAULT_COLUMN_MAP`), `counties.yaml` (`Bay` block, lines 14-42), `FL-ONBOARDING.md`, `bay_price_extract.py`, `county-registry.yaml` (`bay-fl.projects.cd2`), `processors/county_parsers.py::parse_bay_row`
