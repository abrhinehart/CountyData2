# Okaloosa County FL -- Tyler Technologies Self-Service (Clerk) API Map (CD2)

Last updated: 2026-04-14

## 1. Service Overview

| Property | Value |
|----------|-------|
| Platform | Tyler Technologies Self-Service (Clerk Official Records) |
| Portal URL | `https://okaloosacountyfl-web.tylerhost.net/web` |
| Portal version | **Version 2025.1.31** (per live HTML probe) |
| Auth | Anonymous |
| Protocol | Unknown / not reverse-engineered (no Tyler Self-Service scraper client exists yet) |
| Bypass method | Not yet characterized (pending client implementation) |
| CSV column mapping | `grantor: Grantor`, `grantee: Grantee`, `date: Record Date`, `instrument: Doc Type`, `legal: Legal` (existing historical shape per `FL-ONBOARDING.md` L309) |
| Parser | `processors.county_parsers.parse_okaloosa_row` (line 474) |
| Status | **`needs_client`** (per `county-registry.yaml` L226-231, commit `cc489d2`) |

### Probe (2026-04-14)

```
GET https://okaloosacountyfl-web.tylerhost.net/web
-> HTTP 200, body ~16 KB
<title>Self-Service</title>
Version string visible in HTML: 2025.1.31
Additional versioned assets: 1.11.0, 1.4.5, 4.1.0
```

### Commit history

```
cc489d2 docs: update Okaloosa CD2 from blocked to needs_client (Tyler migration)
```

This commit (authoritative for Okaloosa CD2 status) records the transition from "LandmarkWeb decommissioned" to "Tyler Self-Service v2025.1.31 is up but no scraper client exists in this repo yet." The status is NOT `blocked` and NOT `live` -- it is explicitly **`needs_client`**, meaning the portal is ready, the parser logic is preserved, but the HTTP client code that talks to the new Tyler Self-Service portal has not been written.

---

## 2. Migration from LandmarkWeb -> Tyler Self-Service

Prior to the migration, Okaloosa recorded deeds through a Pioneer LandmarkWeb tenant. That portal was decommissioned. Per `county-registry.yaml` notes:

> "LandmarkWeb decommissioned, migrated to Tyler Technologies self-service (Version 2025.1.31). New portal is live and functional. No Tyler self-service scraper client exists yet."

Consequently `county_scrapers/configs.py` L88-90 reflects the removal:

```python
# Okaloosa: removed from LANDMARK_COUNTIES -- LandmarkWeb decommissioned.
# Migrated to Tyler Technologies self-service: https://okaloosacountyfl-web.tylerhost.net/web
# Status: needs_client (no Tyler self-service scraper exists yet).
```

The historical parser (`parse_okaloosa_row`) is preserved in `processors/county_parsers.py` so that when a Tyler Self-Service client is written, the legal-description post-processing is ready.

---

## 3. Additional Surfaces (not primary)

### Kiosk variant

```
https://okaloosacountyfl-kiosk.tylerhost.net
```

Per registry: "Kiosk variant at `okaloosacountyfl-kiosk.tylerhost.net`." This is the in-courthouse kiosk URL -- same Tyler back-end, different front-end flow. Not the automation target.

### ClerkQuest (court records only)

```
https://clerkapps.okaloosaclerk.com/ClerkQuest
```

Per registry: "ClerkQuest at `clerkapps.okaloosaclerk.com/ClerkQuest` is court records only, not deeds." Do NOT point a deed scraper at this URL.

---

## 4. What We Extract (parser is ready; client is pending)

### `processors.county_parsers.parse_okaloosa_row` (line 474)

The parser is one of the most complex in the repo (only Okeechobee exceeds it). Key behaviors:

1. Splits the `legal` value on `\n` (multi-line legal descriptions).
2. For each line, splits on commas via `re.split(r'\s*,\s*', text)`.
3. For each comma-separated clause, calls `_build_okaloosa_clause_entry` which classifies the clause as:
   - `labeled_line` (has `lot:`, `block:`, etc. labels)
   - `subdivision_only` (just a subdivision name)
   - (unparseable -> lands in `unparsed_lines`)
4. Extracts per-clause: `lot`, `block`, `unit`, `subdivision`, `section`, `township`, `range`, `parcel`, `legal_remarks`, `quarter_section`, `location_prefix`.
5. Accumulates with `_unique_preserve_order`; expands lot/unit identifiers via `_expand_identifier_value`.
6. Returns `lot_count` as `sum(_count_lot_value(v) for v in lot_values)`.

### counties.yaml entry (existing historical shape, to be re-confirmed post client)

Expected:

```yaml
Okaloosa:
  column_mapping:
    grantor: Grantor
    grantee: Grantee
    date: Record Date
    instrument: Doc Type
    legal: Legal
  phase_keywords: [Phase, Ph.?, PH, Unit]
  lot_block_cutoffs: [Lot, Lots, Unit, Units, Blk, Block, BLK]
  skiprows: 1                     # <-- Okaloosa-specific: one header row to skip
  delimiters: [",", Parcel, Section]   # <-- Okaloosa-specific: "Section" delimiter
```

---

## 5. Parser Quirks (inherited from pre-migration Okaloosa)

From `FL-ONBOARDING.md` L131:

> Okaloosa | `skiprows=1`; text after "Parcel" and "Section" removed | `parse_okaloosa_row`

### `skiprows: 1`

Unlike Walton/Santa Rosa/Putnam (all `skiprows: 0`), Okaloosa's CSV export has **one leading header row** that must be skipped. This was a LandmarkWeb-era artifact; whether Tyler Self-Service preserves it is a live inspection task.

### Delimiter includes `Parcel` AND `Section`

Okaloosa's legal descriptions commonly insert `Parcel` and `Section` as clause boundaries. The CSV delimiter list includes both words, so the processor splits legal at those tokens AND at commas.

### "Text after `Parcel` and `Section` removed"

When `Parcel` or `Section` appears in a legal line, the processor **truncates the line** at that token (everything from `Parcel` onward, or from `Section` onward, is discarded). This is a destructive cleanup unique to Okaloosa; other counties treat these as segment separators but preserve the trailing text.

---

## 6. Diff vs Okeechobee LandmarkWeb (the nearest FL CD2 peer in same CD2 ecosystem)

This is a rough structural diff until the Tyler Self-Service protocol is reverse-engineered.

| Attribute | Okaloosa (Tyler Self-Service v2025.1.31) | Okeechobee (LandmarkWeb v1.5.93) |
|-----------|-------------------------------------------|-----------------------------------|
| Vendor | Tyler Technologies | Pioneer Technology Group |
| Portal status | `needs_client` | `live` |
| Portal URL | `okaloosacountyfl-web.tylerhost.net/web` | `pioneer.okeechobeelandmark.com/LandmarkWebLive` |
| Protocol | Unknown (not reverse-engineered) | LandmarkWeb DataTables POST |
| Column map | N/A (no client yet) | custom `_OKEECHOBEE_COLUMN_MAP` |
| Skiprows | 1 | 0 |
| Delimiters | `,`, `Parcel`, `Section` | `,`, `Parcel` |
| Text truncation | After `Parcel` / `Section` | None |
| Cloudflare | Unknown | None |
| CSV headers | `Grantor` / `Grantee` | `Grantor(s)` / `Grantee(s)` |
| Parser | `parse_okaloosa_row` | `parse_okeechobee_row` |

---

## 7. What We Extract vs What's Available

Because no client exists yet, this table is prospective -- based on what Tyler Self-Service v2025.1.31 typically exposes and what `parse_okaloosa_row` is prepared to read.

| Data Category | Parser-ready? | Source (expected) | Currently Extracted | Notes |
|---------------|---------------|-------------------|---------------------|-------|
| Grantor | YES | Grantor column | NO (no client) | -- |
| Grantee | YES | Grantee column | NO (no client) | -- |
| Record date | YES | Record Date column | NO | -- |
| Doc type | YES | Doc Type column | NO | -- |
| Legal description | YES | Legal column, multi-line | NO | `parse_okaloosa_row` handles splitting/cleanup |
| Lot / Block / Unit / Subdivision | YES (parsed) | Legal | NO | -- |
| Section / Township / Range | YES (parsed) | Legal (via `quarter_section` extraction) | NO | -- |
| Consideration (sale price) | Unknown | Likely a separate column (FL full-disclosure) | NO | Test on first live sweep |
| Document image | NO | Per-doc viewer | NO | Not implemented |

---

## 8. Known Limitations and Quirks

1. **Status is `needs_client` (commit `cc489d2`).** The portal is live; what's missing is the Python HTTP client that can talk to Tyler Self-Service's (undocumented) protocol. Until such a client exists, no deeds are scraped from Okaloosa, period.

2. **Tyler Self-Service v2025.1.31.** The version string is visible in the HTML (`/web` page source). Tyler updates the Self-Service platform roughly quarterly; any client will need to be resilient to minor-version bumps (e.g., 2025.1.31 -> 2025.2.x).

3. **`skiprows=1`.** Okaloosa CSV exports historically had one leading header row. Preserve this in any new client/config unless live inspection shows Tyler's export starts at row 0.

4. **Text after "Parcel" is removed.** `parse_okaloosa_row` / `_build_okaloosa_clause_entry` destroy any legal content that appears after the word `Parcel` on a line. This is a legal-parsing convention -- the portion after `Parcel` is typically a Parcel ID, not part of the subdivision legal.

5. **Text after "Section" is also removed.** Similarly destructive. Both cleanups are documented in `FL-ONBOARDING.md` L131.

6. **LandmarkWeb URL is dead.** Any historical doc or code that references `https://clerk.okaloosaclerk.com/LandmarkWeb` (or similar) is stale. The only live URL is `https://okaloosacountyfl-web.tylerhost.net/web`.

7. **Kiosk variant is a separate URL.** `okaloosacountyfl-kiosk.tylerhost.net` is an in-courthouse kiosk front-end. Don't confuse with the public `-web` subdomain.

8. **ClerkQuest is NOT deeds.** `clerkapps.okaloosaclerk.com/ClerkQuest` is court-records-only. Any deed scraping must ignore this URL.

9. **`FL-ONBOARDING.md` L309 has Okaloosa as `untested`.** Historical table row: "| Okaloosa | untested | untested | no | skiprows=1; multi-delimiter issue |". The migration note and `cc489d2` commit update this to `needs_client`.

10. **Multi-delimiter issue is unresolved.** Per `FL-ONBOARDING.md` L288: "Okaloosa is untested. The config entry exists but has `status: 'untested'`. The multi-delimiter issue (commas, Parcel, Section all used as delimiters in legal text) needs resolution before it can go live." The parser handles it; the issue is whether CSV export from Tyler Self-Service preserves commas or flattens to spaces.

11. **Tyler Self-Service hostname pattern: `{county}countyfl-web.tylerhost.net/web`.** Note the hyphen between `countyfl` and `web`. If new Tyler Self-Service counties are onboarded, expect the same pattern.

12. **No `county_scrapers/configs.py` entry for Okaloosa.** The historical LandmarkWeb entry was removed in the migration commit. Re-adding an entry under a new `TYLER_SELF_SERVICE_COUNTIES` (or similar) registry will be part of the `needs_client` work.

**Source of truth:** `county-registry.yaml` (`okaloosa-fl.projects.cd2`, L226-231), `county_scrapers/configs.py` L88-90 (removal comment), commit `cc489d2` (status transition: "docs: update Okaloosa CD2 from blocked to needs_client (Tyler migration)"), `processors/county_parsers.py::parse_okaloosa_row` (line 474), `FL-ONBOARDING.md` L131 (parser quirks) and L309 (historical status table), live probe of `https://okaloosacountyfl-web.tylerhost.net/web` (HTTP 200, version string `2025.1.31`).

---

## Implementation

**Status flipped from `needs_client` to `live` on 2026-04-15.** Adapter module is `county_scrapers/tyler_selfservice_client.py` (`TylerSelfServiceSession`). Registered in `county_scrapers/configs.py` under `TYLER_SELFSERVICE_COUNTIES` and wired into the `pull_records.pull()` dispatch chain as `portal_type == 'tyler_selfservice'`.

### Verified endpoint recipe

All requests are anonymous. Two cookies carry the session: `JSESSIONID` (set on the initial GET) and `disclaimerAccepted=true` (set by POSTing an empty body to the disclaimer endpoint). No CSRF token, no captcha observed, no rate limiting hit at a 1.0s inter-request delay.

1. `GET {base_url}` -> 200, sets `JSESSIONID`.
2. `POST {base_url}/user/disclaimer` (no body) -> returns `true`, sets `disclaimerAccepted=true`.
3. `GET {base_url}/search/{search_id}` -> renders the search form HTML (we discard the content).
4. `POST {base_url}/searchPost/{search_id}` with a 20-field URL-encoded form body (all `field_*` keys listed in the module docstring) -> JSON shell `{"validationMessages": {}, "totalPages": N, "currentPage": 1, ...}`. Dates go in as `M/D/YYYY` (no zero-padding).
5. `GET {base_url}/searchResults/{search_id}?page=N` for `N` in `1..totalPages` -> HTML page with up to 100 `<li class="ss-search-row">` entries per page.

For Okaloosa specifically, `search_id = DOCSEARCH138S1`.

### Parse shape

Each `<li class="ss-search-row">` carries:

- `data-documentid="DOC549S1614"` on the opening tag -> `document_id`.
- `<h1>` with the instrument number and doc type separated by a bullet entity (`&nbsp;&#149;&nbsp;`).
- Four `<div class="searchResultFourColumn">` blocks in fixed order: Recording Date, Grantor/Party 1, Grantee/Party 2, Legal. Each column renders its values inside `<b>...</b>` tags; multi-party names or multi-line legals simply add more `<b>` values, which the client joins with `; ` (names) or `\n` (legal).
- Parcel ID appears as a sub-value inside the Legal column, prefixed with `Parcel:` -- extracted into a separate `parcel` field.

### Gotcha: `ajaxRequest: true` header on searchPost

The `searchPost` endpoint returns an HTML error page (not JSON) if the request omits the `ajaxRequest: true` header. The client sets this unconditionally and there is a regression-guard test (`AjaxHeaderRegressionTest` in `tests/test_tyler_selfservice_client.py`). If this client ever starts raising `Tyler searchPost returned non-JSON response` in the wild, this header is the first thing to check -- Tyler may have renamed or repurposed it.

### Limitations

- **Consideration / sale price is not surfaced.** Tyler self-service exposes the sale-price field only on the per-document PDF viewer; the search-results HTML does not carry it. `consideration` is emitted as `''` for every row.
- **Book / page / book type are blank.** Tyler assigns a global instrument number (`3808515`, etc.); the old LandmarkWeb book/page numbering is not present in the self-service view.
- **Doc-type filter is deferred.** The portal's doc-type input is autocomplete-backed; rather than wiring the autocomplete endpoint for v1, the client pulls all document types and relies on the existing `entity_filter` downstream to select deeds.
- **`counties.yaml` `skiprows` flipped from 1 to 0.** `pull_records.py` writes a header row at row 0 (unlike the LandmarkWeb-era Excel export which carried a title row). The processor was reading Okaloosa with `skiprows=1`; updating it here aligns it with the other `pull_records` outputs.

### Reference

- Client: `county_scrapers/tyler_selfservice_client.py`
- Tests: `tests/test_tyler_selfservice_client.py` (28 tests including the `ajaxRequest` regression guard)
- Fixture: `tests/fixtures/tyler_selfservice_results_sample.html`
- Config registration: `county_scrapers/configs.py::TYLER_SELFSERVICE_COUNTIES`
- Dispatch: `county_scrapers/pull_records.py::pull` (`portal_type == 'tyler_selfservice'` branch)
