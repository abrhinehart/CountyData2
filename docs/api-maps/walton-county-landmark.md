# Walton County FL -- LandmarkWeb (Clerk) API Map (CD2)

Last updated: 2026-04-14

## 1. Service Overview

| Property | Value |
|----------|-------|
| Platform | Pioneer Technology Group LandmarkWeb |
| Portal URL | `https://orsearch.clerkofcourts.co.walton.fl.us/LandmarkWeb` |
| Auth | Anonymous (after session + disclaimer) |
| Protocol | HTTP POST to LandmarkWeb DataTables JSON endpoints |
| Bypass method | **`cloudflare` (requires `curl_cffi` TLS impersonation)** |
| Doc types filter | `''` (empty -- all types; downstream filtering in processor) |
| Column map | `DEFAULT_COLUMN_MAP` (legal at column 13) |
| Parser | `county_scrapers.landmark_client.LandmarkSession(use_cffi=True)` + `processors.county_parsers.parse_walton_row` |
| Weekly chunking | Yes (per registry notes) |
| Status | `live` (per `county-registry.yaml` L363-368) |

### Session handshake

```
GET  https://orsearch.clerkofcourts.co.walton.fl.us/LandmarkWeb/Home/Index
POST https://orsearch.clerkofcourts.co.walton.fl.us/LandmarkWeb/Search/SetDisclaimer
     (X-Requested-With: XMLHttpRequest)
```

**DO NOT probe this portal during Wave 1 research or any CD2 work.** Walton's front door is behind Cloudflare with TLS-fingerprint inspection. Plain `requests.Session` gets 403'd. The adapter MUST use `curl_cffi.requests.Session(impersonate='chrome')` (set `use_cffi=True` when constructing `LandmarkSession`). Research-grade probes (`curl ...`) without TLS impersonation will trigger Cloudflare 403 responses that contribute to the domain's reputation score.

---

## 2. Search Capabilities

### Request: date-range search

```
POST https://orsearch.clerkofcourts.co.walton.fl.us/LandmarkWeb/Search/RecordDateSearch
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
POST https://orsearch.clerkofcourts.co.walton.fl.us/LandmarkWeb/Search/GetSearchResults
Headers: X-Requested-With: XMLHttpRequest
Body:
  draw={1..N}
  start={offset}
  length=500
```

### Chunking strategy

Per registry and peer counties (Citrus, Escambia): **weekly chunking.** Each `RecordDateSearch` call covers a 7-day window; sequential weeks are batched to stay under the 50,000-row `recordCount` cap and to minimize Cloudflare rate-limiting risk.

### Session defaults

| Property | Default |
|----------|---------|
| `page_size` | 500 |
| `request_delay` | 1.0s |
| `use_cffi` | **True** (required by Cloudflare) |
| Impersonation | `chrome` (via `curl_cffi`) |

---

## 3. Column Layout

Walton uses `DEFAULT_COLUMN_MAP` (same as Bay / Citrus / Escambia):

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
| `legal` | **`13`** (default-layout LandmarkWeb tenant) |

Value cleanup is the standard LandmarkWeb path: strip `nobreak_` / `hidden_` / `unclickable_` prefixes, replace `nameSeperator` divs with `"; "`, strip HTML tags, `html.unescape`, whitespace collapse.

---

## 4. Document Type Catalog

Walton is configured with `doc_types: ''` (all types). Deed filtering happens downstream via `counties.yaml` -> `Walton.column_mapping.instrument = "Doc Type"` (text-match).

Typical LandmarkWeb Walton doc types: DEED, MORTGAGE, LIEN, ASSIGNMENT, etc.

---

## 5. What We Extract

### From `LandmarkSession._parse_row` (DEFAULT_COLUMN_MAP)

| Key | Column |
|-----|--------|
| `grantor` | 5 |
| `grantee` | 6 |
| `record_date` | 7 |
| `doc_type` | 8 |
| `book_type` | 9 |
| `book` | 10 |
| `page` | 11 |
| `instrument` | 12 |
| `legal` | 13 |
| `document_id` | Parsed from `DT_RowId` |

### From `processors.county_parsers.parse_walton_row` (line 1927)

```python
def parse_walton_row(row: pd.Series, cols: dict) -> dict:
    legal_value = row.get(cols.get('legal', ''), pd.NA)
    return _parse_freeform_row(legal_value, strip_legal_prefix=True)
```

The defining characteristic: **`strip_legal_prefix=True`**. Inside `_normalize_freeform_line` (L810-816):

```python
def _normalize_freeform_line(text: str, strip_legal_prefix: bool = False) -> str:
    normalized = str(text).replace('\r', ' ').replace('\n', ' ').strip()
    if strip_legal_prefix:
        normalized = re.sub(r'(?i)^LEGAL\s+', '', normalized)   # <-- Walton-specific
    normalized = re.sub(r'(?i)^L(?=\d)', 'L ', normalized)
    normalized = re.sub(r'\s+', ' ', normalized)
    return normalized.strip()
```

The `(?i)^LEGAL\s+` regex removes a **leading `"Legal "` prefix** (case-insensitive) from each legal line before lot/block/subdivision extraction. This is the one county-specific transformation Walton performs.

### `counties.yaml` entry (L257-281)

```yaml
Walton:
  column_mapping:
    grantor: Grantor
    grantee: Grantee
    instrument: Doc Type
    date: Record Date
    legal: Legal
  delimiters: [",", Parcel]
  phase_keywords: [Phase, Ph.?, PH, Unit]
  lot_block_cutoffs: [Lot, Lots, Unit, Units, Blk, Block, BLK]
  skiprows: 0
```

CSV headers are the plain `Grantor` / `Grantee` (not `Grantor(s)` / `Grantee(s)` like Okeechobee, not `Direct Name` / `Reverse Name` like Escambia).

---

## 6. Bypass Method

| Component | Detail |
|-----------|--------|
| Registry bypass label | `cloudflare` |
| `county_scrapers/configs.py` status | `cloudflare` (L81-87) |
| Mechanism | Cloudflare TLS fingerprint inspection blocks standard `requests`. `curl_cffi` with `impersonate='chrome'` passes. |
| `use_cffi` | `True` (REQUIRED) |

---

## 7. Diff vs Okeechobee LandmarkWeb (no-Cloudflare peer) + Citrus (same Cloudflare)

| Attribute | Walton | Okeechobee | Citrus |
|-----------|--------|------------|--------|
| URL suffix | `/LandmarkWeb` (default) | `/LandmarkWebLive` (with `-Live`) | `/LandmarkWeb` (default) |
| Portal version | default / older | v1.5.93 | default / older |
| Cloudflare | **YES (requires `curl_cffi`)** | NO (plain `requests` works) | YES (requires `curl_cffi`) |
| Doc-type filter | `''` (all) | `''` (all) | `'17'` (DEED only) |
| Column map | DEFAULT (legal at 13) | custom `_OKEECHOBEE_COLUMN_MAP` (legal at 14) | DEFAULT (legal at 13) |
| Legal-prefix strip | **YES (`"Legal "` stripped)** | NO | NO |
| Dedicated parser | YES (`parse_walton_row`) | YES (`parse_okeechobee_row`) | YES (`parse_citrus_row`) |
| CSV headers | `Grantor` / `Grantee` | `Grantor(s)` / `Grantee(s)` | `Grantor` / `Grantee` |
| Status | `live` | `live` | `live` |

---

## 8. What We Extract vs What's Available

| Data Category | Currently Extracted | Source | Available but Not Extracted | Source |
|---------------|--------------------|---------|-----------------------------|--------|
| Grantor | YES | Column 5 | -- | -- |
| Grantee | YES | Column 6 | -- | -- |
| Record date | YES | Column 7 | -- | -- |
| Doc type | YES | Column 8 | -- | -- |
| Book type | YES | Column 9 | -- | -- |
| Book / Page | YES | Columns 10-11 | -- | -- |
| Instrument | YES | Column 12 | -- | -- |
| Legal description | YES (after `"Legal "` strip) | Column 13 | -- | -- |
| Lot / Block / Subdivision | YES (parsed from legal) | `_parse_freeform_row` | -- | -- |
| Consideration | NO | -- | Not on grid; per-doc detail | `GetRecordDetails` (not implemented) |
| Document image (PDF) | NO | -- | Per-doc viewer | Action links |

---

## 9. Known Limitations and Quirks

1. **`"Legal "` prefix is stripped from every legal line.** The canonical Walton quirk. `parse_walton_row` calls `_parse_freeform_row(legal_value, strip_legal_prefix=True)`, which in `_normalize_freeform_line` applies `re.sub(r'(?i)^LEGAL\s+', '', normalized)` to each line. Without this, legal descriptions show up as e.g. `"LEGAL LOT 3 BLK 12 OAKHAVEN PH 2"` instead of `"LOT 3 BLK 12 OAKHAVEN PH 2"`, and the lot-block walker would mis-classify the leading `"LEGAL"` as subdivision noise.

2. **Cloudflare TLS fingerprint blocking requires `curl_cffi`.** Plain `requests.Session` returns 403. Use `curl_cffi.requests.Session(impersonate='chrome')` via `LandmarkSession(use_cffi=True)`. **Do NOT scrape the live portal during documentation Wave 1** -- repeated failed requests without impersonation inflate Cloudflare's bot-score for the repo's IP.

3. **Weekly chunking, 50k-row cap.** Each `RecordDateSearch` call is scoped to a 7-day window. Larger windows risk hitting the 50,000-row `recordCount` cap, which truncates the result set silently.

4. **`DEFAULT_COLUMN_MAP` applies -- legal at column 13.** Unlike Okeechobee (v1.5.93, legal at 14) or Hernando (v1.5.87, legal at 14), Walton uses the standard 13-column layout.

5. **CSV headers are plain `Grantor` / `Grantee`.** Not `Grantor(s)` / `Grantee(s)` (Okeechobee), not `Direct Name` / `Reverse Name` (Escambia / Hernando). Downstream CSV readers must use the plain form.

6. **No `sub` / subdivision column in CSV.** Subdivision names come from legal-field parsing, not a dedicated column.

7. **`FL-ONBOARDING.md` L134 documents the prefix-strip.** "Walton | `\"Legal \"` prefix stripped from legal description | `parse_walton_row`". This is the authoritative reference.

8. **Weekly-chunk overlap with other Cloudflare counties.** Walton, Citrus, and Escambia all share the `bypass: cloudflare` + `use_cffi: True` pattern. Walton's `parse_walton_row` is simpler than Citrus's `parse_citrus_row` because Citrus filters to DEED-only (doc_type=17) while Walton accepts all types and filters downstream.

9. **Hostname uses a long, un-abbreviated path: `orsearch.clerkofcourts.co.walton.fl.us`.** Five-segment FQDN in the .us TLD -- distinctive and easy to typo. Do NOT abbreviate to `orsearch.waltonclerk.fl.us` or similar.

10. **`use_cffi=True` MUST be set in `LandmarkSession` constructor.** The default is `False`; forgetting the flag silently fails every request. `county_scrapers/configs.py` L81-87 sets `status: 'cloudflare'`, which the session-building factory in `LandmarkSession` inspects.

11. **`skiprows: 0`.** No CSV header garbage to skip at ingestion time.

12. **Registry status is `live`.** Walton is one of 4 LandmarkWeb FL counties currently `live` in `county-registry.yaml` (alongside Okeechobee, Citrus, Escambia).

**Source of truth:** `county_scrapers/configs.py` (`LANDMARK_COUNTIES['Walton']`, L81-87), `county_scrapers/landmark_client.py`, `counties.yaml` (`Walton` block, L257-281), `processors/county_parsers.py::parse_walton_row` (line 1927), `processors/county_parsers.py::_normalize_freeform_line` (lines 810-816, strip-legal-prefix logic), `county-registry.yaml` (`walton-fl.projects.cd2`, L363-368), `FL-ONBOARDING.md` L134 and L312.
