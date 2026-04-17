# Hernando County FL -- LandmarkWeb (Clerk) API Map (CD2)

Last updated: 2026-04-14

## 1. Portal Overview

| Property | Value |
|----------|-------|
| Platform | Pioneer Technology Group LandmarkWeb v1.5.87 |
| Portal URL | `https://or.hernandoclerk.com/LandmarkWeb` |
| Auth | Anonymous search after session handshake |
| Protocol | HTTP POST to LandmarkWeb DataTables JSON endpoints |
| Bypass method | `none` — plain requests work (no captcha, no Cloudflare) |
| Doc types filter | `''` (empty — all doc types returned; downstream filter in `processors/`) |
| Column map | Custom `_HERNANDO_COLUMN_MAP` (extended v1.5.87 layout) |
| Adapter / client | `county_scrapers.landmark_client.LandmarkSession` + `county_scrapers.configs.LANDMARK_COUNTIES['Hernando']` |
| Registry status | `cd2: live` per `county-registry.yaml` L170-174 |

### Session handshake (v1.5.87)

```
GET  https://or.hernandoclerk.com/LandmarkWeb/Home/Index
POST https://or.hernandoclerk.com/LandmarkWeb/Search/SetDisclaimer   (X-Requested-With: XMLHttpRequest)
```

Disclaimer POST unlocks the search endpoints. No CAPTCHA or Cloudflare TLS impersonation required (`use_cffi=False`).

## 2. Probe (2026-04-14)

```
GET https://or.hernandoclerk.com/LandmarkWeb/Home/Index
-> HTTP 200, 25,857 bytes, text/html
   <title>Landmark Web Official Records Search</title>
   Pioneer Technology Group LandmarkWeb — version strings in HTML confirm v1.5.87.
```

No anonymous probe of the search POSTs is performed here (would require disclaimer cookie and would return live record data); the existing `LandmarkSession` live-tested 2026-04-03 per `county_scrapers/configs.py` header comment.

## 3. Search Capabilities

### Request: date-range search

```
POST https://or.hernandoclerk.com/LandmarkWeb/Search/RecordDateSearch
Headers: X-Requested-With: XMLHttpRequest
Body (form-encoded):
  beginDate=MM/DD/YYYY
  endDate=MM/DD/YYYY
  doctype=         (empty — all types)
  recordCount=50000
  exclude=false
  ReturnIndexGroups=false
  townName=
  mobileHomesOnly=false
```

### Request: paginated result fetch

```
POST https://or.hernandoclerk.com/LandmarkWeb/Search/GetSearchResults
Headers: X-Requested-With: XMLHttpRequest
Body:
  draw={1..N}
  start={row offset}
  length=500     (from LandmarkSession.page_size default)
```

### Pagination

`LandmarkSession` increments `start` by `page_size` until response `data` array is empty or `start >= recordsTotal`. Inter-page sleep = `request_delay` (default 1.0s).

### Session defaults

| Property | Default |
|----------|---------|
| `page_size` | 500 |
| `request_delay` | 1.0s |
| `use_cffi` | False |
| Retries | `Retry(total=3, backoff_factor=1.5, status_forcelist=[500,502,503,504])` |

## 4. Field Inventory (DataTables JSON column layout — v1.5.87 extended)

From `county_scrapers/configs.py` L18-30:

```python
# Hernando (v1.5.87) has extended legal fields in columns 14-25, doc_id at 26.
_HERNANDO_COLUMN_MAP = {
    'grantor': '5',
    'grantee': '6',
    'record_date': '7',
    'doc_type': '8',
    'book_type': '9',
    'book': '10',
    'page': '11',
    'instrument': '12',
    'legal': '14',       # column 13 is empty; 14 has the full L/Blk/Un/Sub format
    'subdivision': '19', # hidden_legalfield_ — subdivision name from structured legal
}
```

| JSON index | Field | Notes |
|------------|-------|-------|
| 5 | Grantor | |
| 6 | Grantee | |
| 7 | Record date | |
| 8 | Doc type | |
| 9 | Book type | |
| 10 | Book | |
| 11 | Page | |
| 12 | Instrument number | |
| 13 | (empty) | Placeholder column |
| 14 | Legal (full L/Blk/Un/Sub) | Extended v1.5.87 format; supersedes DEFAULT_COLUMN_MAP column 13 |
| 19 | **Subdivision name** | `hidden_legalfield_` — unique among FL LandmarkWeb tenants |
| 26 | Doc ID | Referenced in header comment at `configs.py` L18 |

## 5. What We Extract / What a Future Adapter Would Capture

Per `county_scrapers.landmark_client.LandmarkSession.search_by_date_range()` and the shared row-to-dict shape used in CountyData2 deed ingestion:

| Canonical field | Hernando column | Pipeline role |
|-----------------|-----------------|---------------|
| grantor | col 5 | Entity rollup |
| grantee | col 6 | Entity rollup |
| record_date | col 7 | Date-window filtering |
| doc_type | col 8 | Deed-type filter (D, WD, QCD, etc.) |
| instrument | col 12 | Unique doc identifier for dedup |
| legal (extended) | col 14 | Parsed into lot/block/unit/subdivision via processor |
| **subdivision (structured)** | col 19 | Directly populates `subdivision` on the deed record — no legal-parse fallback needed |
| book / page | cols 10 / 11 | Citation fields |

## 6. Bypass Method / Auth Posture

- `status: working` (configs.py L57) — **no captcha, no Cloudflare**, plain `requests` session works.
- Session cookie required: set via `Home/Index` + `SetDisclaimer` POST.
- Compared to Bay County (same LandmarkWeb platform, but `captcha_hybrid`) and Walton/Citrus (Cloudflare + curl_cffi) — Hernando is the easiest LandmarkWeb posture in FL.

## 7. What We Extract vs What's Available

| Data Category | Currently Extracted | Source | Notes |
|---------------|---------------------|--------|-------|
| Grantor / grantee | YES | cols 5/6 | |
| Record date | YES | col 7 | |
| Doc type | YES | col 8 | |
| Book / page / instrument | YES | cols 10/11/12 | |
| Legal description (full text) | YES | col 14 | Processor extracts lot/block/unit |
| **Subdivision (structured)** | YES | col 19 | **Unique: direct field, no parse needed** |
| Doc ID | Parsed | col 26 | Used internally by LandmarkSession |
| Consideration / sale price | NO | N/A or separate column | Not mapped; FL disclosure but Hernando places it elsewhere in row |
| Document image | NO | Per-doc viewer | Not automated |
| Book type | Unused | col 9 | Available; not in downstream pipeline |

## 8. Known Limitations and Quirks

1. **Hernando is the only FL LandmarkWeb tenant with a dedicated Subdivision column.** Every other FL LandmarkWeb county parses subdivision names out of the free-text legal field; Hernando v1.5.87 exposes it as `hidden_legalfield_` at column 19. Any adapter changes that normalize subdivision logic across counties should explicitly special-case or preserve this short-circuit.
2. **Extended column layout differs from DEFAULT_COLUMN_MAP.** Bay uses `DEFAULT_COLUMN_MAP` (legal at col 13). Hernando puts legal at col 14 and leaves col 13 empty. Do NOT fall back to the default for Hernando.
3. **Portal version v1.5.87.** Future Pioneer version bumps may reshuffle columns — verify column indices on first run after a Hernando portal update.
4. **No Cloudflare, no captcha.** The `use_cffi=False` setting is intentional; do not switch on curl_cffi here (it changes headers and sometimes degrades throughput).
5. **`doc_types = ''` (empty filter).** All document types are returned from the portal; the CountyData2 pipeline filters to deed types downstream. If/when deed filtering migrates upstream, the Hernando entry should still preserve the empty filter until the Clerk's numeric doc-type IDs are verified live.
6. **Session requires the `SetDisclaimer` POST even though it is a cookie-only acceptance.** Skipping this step yields 302 redirects on search endpoints.
7. **`page_size = 500`, `request_delay = 1.0s`.** Conservative defaults; Hernando has not shown throttling symptoms.
8. **Verified working 2026-04-03.** Column indices confirmed on live data that date; status `working` in `configs.py`.
9. **Portal `/Home/Index` returns HTML with a minor encoding typo (`charset=utf-9`).** Harmless — LandmarkWeb standard markup, no impact on session handshake.
10. **Registry note matches reality.** "Fully automated. Portal v1.5.87 has extended legal fields. Dedicated Subdivision column (unique among FL)." (`county-registry.yaml` L174) — no divergence detected on 2026-04-14 probe.

Source of truth: `county-registry.yaml` L164-190 (`hernando-fl.projects.cd2`), `county_scrapers/configs.py` L18-30 (`_HERNANDO_COLUMN_MAP`) and L53-59 (`LANDMARK_COUNTIES['Hernando']` entry), `county_scrapers/landmark_client.py` (LandmarkSession), live probe of `https://or.hernandoclerk.com/LandmarkWeb/Home/Index` (2026-04-14, HTTP 200, 25,857 bytes).
