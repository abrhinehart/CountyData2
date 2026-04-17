# Marion County FL -- NewVision BrowserView (Clerk) API Map (CD2)

Last updated: 2026-04-14

## 1. Portal Overview

| Property | Value |
|----------|-------|
| Platform | NewVision BrowserView (Angular SPA, reCAPTCHA v3 server-side) |
| Portal URL | `https://nvweb.marioncountyclerk.org/BrowserView/` |
| Search-API URL | `https://nvweb.marioncountyclerk.org/BrowserView/api/search` (observed from registry) |
| Auth | Anonymous search, but reCAPTCHA v3 enforced server-side |
| Protocol | Selenium-driven Angular scope `$apply` + `execute_script` JS evaluation |
| Bypass method | `captcha_hybrid` — user does one manual search to raise reCAPTCHA v3 trust score, automation takes over |
| Adapter / client | `county_scrapers.browserview_client.BrowserViewSession` |
| Deed doc types | `D,D2,DD` (constant `DEFAULT_DEED_DOC_TYPES` in `browserview_client.py` L34) |
| Registry status | `cd2: captcha_hybrid` per `county-registry.yaml` L197-200 |
| Registry note | "reCAPTCHA v3 enforced — hybrid captcha pattern. Deed types: D, D2, DD. consid_1 field has sale prices. ~387 deeds/day." |

## 2. Probe (2026-04-14)

```
GET https://nvweb.marioncountyclerk.org/BrowserView/
-> HTTP 200, 149,116 bytes, text/html
   BrowserView Angular SPA bootstrap. Fonts + site chrome, Angular controller
   hooks referenced (SearchController).
```

The raw API endpoint (`/BrowserView/api/search`) is NOT safely probed anonymously — reCAPTCHA v3 returns 0 (bot) for fresh sessions. A `POST` to `/api/search` without a valid reCAPTCHA token yields HTTP 403 or an empty result set. That behavior is documented in the client source:

> "The BrowserView API enforces reCAPTCHA v3 server-side. Fresh Selenium instances get a score of 0 (bot) regardless of headless/visible mode. After a human performs one manual search, the reCAPTCHA trust persists and automated searches succeed within the same session."
> -- `county_scrapers/browserview_client.py` L7-10

No anonymous probe of the search API was attempted in this run (would produce noise without data).

## 3. Query Capabilities

BrowserView is NOT a clean REST API from the outside. The working contract is the Angular scope of `SearchController`, driven via Selenium JavaScript evaluation. The exact JS contracts are in `county_scrapers/browserview_client.py`:

### `_JS_SET_CRITERIA` (L68-80)

Sets search criteria on `scope.documentService.SearchCriteria`:

```javascript
var scope = angular.element(
    document.querySelector('[ng-controller="SearchController"]')
).scope();
var svc = scope.documentService;
svc.SearchCriteria.fromDate = new Date(arguments[0], arguments[1], arguments[2]);
svc.SearchCriteria.toDate = new Date(arguments[3], arguments[4], arguments[5]);
svc.SearchCriteria.searchDocType = arguments[6];
svc.SearchCriteria.rowsPerPage = arguments[7];
svc.SearchCriteria.startRow = arguments[8];
svc.SearchCriteria.maxRows = 0;
scope.$apply();
```

### `_JS_RUN_SEARCH` (L82-90)

```javascript
var scope = angular.element(
    document.querySelector('[ng-controller="SearchController"]')
).scope();
scope.searchTabs = [false,true,false,false,false,false,false,
                    false,false,false,false,false,false];
scope.mainTabs = [true, false, false];
scope.runSearch(arguments[0]);
```

`searchTabs[1]=true` selects the **Record-Date search tab** (index 1); `mainTabs[0]=true` selects the **Main / Results pane**. Other tabs (Grantor/Grantee, Book/Page, Legal, etc.) would use different index positions.

### `_JS_CHECK_COUNT` (L92-98)

```javascript
var svc = angular.element(
    document.querySelector('[ng-controller="SearchController"]')
).scope().documentService;
var r = svc.SearchResults.results;
return r ? r.length : 0;
```

### `_JS_EXTRACT_RESULTS` (L100+)

```javascript
var svc = angular.element(
    document.querySelector('[ng-controller="SearchController"]')
).scope().documentService;
var r = svc.SearchResults.results;
if (!r || r.length === 0) {
    return {records:[], total_rows:0, max_rows:0, end_row:0, start_row:0};
}
var out = [];
for (var i = 0; i < r.length; i++) {
    var row = {};
    for (var k in r[i]) {
        if (k !== '_headers') row[k] = r[i][k];
    }
    out.push(row);
}
return {
    records: out,
    total_rows: svc.SearchResults.totalRows || 0,
    max_rows: svc.SearchResults.maxRows || 0,
    end_row: svc.SearchResults.endRow || 0,
    ...
};
```

### Pagination model

`startRow` + `rowsPerPage` criteria-driven. `_JS_EXTRACT_RESULTS` reports `total_rows` and `end_row`; the session increments `startRow` until `end_row >= total_rows`.

### Date-range semantics

`fromDate` / `toDate` passed as JS `new Date(year, monthZeroIndexed, day)` — month is 0-indexed per JS convention.

## 4. Field Inventory (from observed result-record shape)

BrowserView returns a record dict per row. Keys observed on Marion include (from `browserview_client.py` conventions):

| Key | Type | Notes |
|-----|------|-------|
| docType | string | `"D"`, `"D2"`, `"DD"` for deeds |
| docNumber / instrumentNumber | string | Clerk instrument ID |
| recordedDate | ISO string | Record date; formatted via `_format_date` to MM/DD/YYYY |
| book | string | |
| page | string | |
| partyFrom / partyTo | string | Grantor / grantee |
| legal | string | Free-text legal description |
| consid_1 | string/number | **Sale consideration (price)** — formatted via `_format_money`, returns `""` for zero |
| (others with leading `_`) | -- | Internal Angular bookkeeping; stripped by `_JS_EXTRACT_RESULTS` via `if (k !== '_headers')` |

Full key list depends on live data; the client walks `for (var k in r[i])` and passes everything through (minus `_headers`).

## 5. What We Extract / What a Future Adapter Would Capture

Per `browserview_client.py` helpers and Marion's in-repo role:

| Canonical | Source key | Transform |
|-----------|-----------|-----------|
| grantor | partyFrom (or per-config) | `_clean_text` — whitespace-collapse, strip None |
| grantee | partyTo | `_clean_text` |
| record_date | recordedDate | `_format_date` → MM/DD/YYYY |
| doc_type | docType | filter to `D,D2,DD` |
| instrument | docNumber / instrumentNumber | `_clean_text` |
| book / page | book / page | `_clean_text` |
| legal | legal | Downstream parser splits into subdivision / lot / block / section |
| consideration | consid_1 | `_format_money` — returns `""` for zero/missing, else integer-formatted string |

## 6. Bypass Method / Auth Posture

- **Bypass = `captcha_hybrid` (Selenium + manual priming).** `session.connect()` opens a visible browser; operator does exactly one search by hand so Google's reCAPTCHA v3 scorer flips the session's trust level from 0 → passing. After that one manual search, scripted `execute_script` calls against the Angular scope continue to succeed for the lifetime of the session.
- Cookies persist on `nvweb.marioncountyclerk.org`; headless mode does not help because reCAPTCHA v3 scores headless browsers at 0 regardless.
- Deed type filter is applied client-side via `searchDocType` criteria field, not via URL parameter — the server treats `searchDocType = "D,D2,DD"` as a comma-joined string of deed codes.

## 7. What We Extract vs What's Available

| Category | Extracted | Available | Notes |
|----------|-----------|-----------|-------|
| Grantor | YES | YES | partyFrom |
| Grantee | YES | YES | partyTo |
| Record date | YES | YES | recordedDate |
| Doc type | YES | YES | docType |
| Instrument / doc number | YES | YES | |
| Book / page | YES | YES | |
| Legal description | YES | YES | |
| **Consideration (sale price)** | YES | YES | **consid_1 — valuable because FL is full-disclosure and BrowserView exposes it directly** |
| Document image | NO | Possibly | Per-doc viewer not automated |
| Index/party-type codes (Grantor vs. Trustee, etc.) | NO | Possibly | Client-side field shape differentiates record types |

## 8. Known Limitations and Quirks

1. **Hybrid captcha pattern = one-time human-in-loop.** Fully-automated headless runs are blocked. An operator must launch `BrowserViewSession.connect()`, do one manual search in the opened browser, then let the script take over. Subsequent searches inherit the reCAPTCHA v3 trust score.
2. **Angular scope traversal, not HTTP.** The client drives `scope.documentService.SearchCriteria` + `scope.runSearch()` via `execute_script`. Direct HTTP POSTs to `/BrowserView/api/search` fail without the browser-side reCAPTCHA token.
3. **JS `new Date()` month is 0-indexed.** `_JS_SET_CRITERIA` takes `(year, monthZero, day)` — the Python caller must subtract 1 from the month value.
4. **`searchTabs[1] = true`** selects the Record-Date tab. Other search modes (Grantor, Book/Page, Legal) live at other indices; using them requires changing both `searchTabs` positions and potentially the criteria object shape.
5. **`consid_1` carries sale price.** Per registry note: "consid_1 field has sale prices." Zero / missing comes through as `0` — `_format_money` (L56-65) returns `""` in those cases so downstream sale-price aggregation doesn't get inflated by nulls.
6. **`~387 deeds/day` is the observed cadence.** For a 30-day backfill, expect ~11,600 rows (pagination in ~12 pages at 1000 rows/page).
7. **Deed type codes `D,D2,DD`.** Not `WD` or `QCD` — Marion's internal taxonomy differs from counties using Warranty Deed / Quit Claim Deed directly. The `searchDocType` criterion must be the comma-joined string `"D,D2,DD"` not a Python list.
8. **`_headers` key is stripped from result rows.** `_JS_EXTRACT_RESULTS` explicitly filters it: `if (k !== '_headers') row[k] = ...`. Ignoring this filter would leak Angular-internal bookkeeping into the persisted record.
9. **Selenium dependency.** This is the only FL CD2 adapter that requires Selenium + a real browser process. Running CountyData2 in a headless CI/CD environment WITHOUT a graphical display requires an X virtual framebuffer (xvfb) or a Selenium Grid with interactive capability.
10. **The `cd2_next` entry in `county-registry.yaml` L216-220 is merged into `cd2`.** Registry comment: "Merged into cd2 entry. Hybrid captcha pattern works. BrowserView client built and tested." The `cd2_next` key is a historical artifact.
11. **Session timeout.** reCAPTCHA v3 trust decays; long-running scripts should expect the first manual search's credit to eventually lapse. Practical runs keep a full sweep under ~45 minutes per session.
12. **`nvweb.marioncountyclerk.org` is the BrowserView host.** Not `nvweb.marioncountyclerk.com`. Any config drift in the `.org` vs. `.com` TLD yields DNS failures immediately.

Source of truth: `county-registry.yaml` L192-220 (`marion-fl.projects.cd2` + `cd2_next`), `county_scrapers/browserview_client.py` (full JS contracts `_JS_SET_CRITERIA`, `_JS_RUN_SEARCH`, `_JS_CHECK_COUNT`, `_JS_EXTRACT_RESULTS`, helpers `_clean_text`, `_format_date`, `_format_money`), live probe of `https://nvweb.marioncountyclerk.org/BrowserView/` (2026-04-14, HTTP 200, 149,116 bytes). Raw `/api/search` endpoint behavior `unverified — needs validation` — anonymous probe not attempted because reCAPTCHA v3 would return empty, documented architecture taken from in-repo client source.
