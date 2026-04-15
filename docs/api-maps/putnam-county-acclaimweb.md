# Putnam County FL -- AcclaimWeb (Clerk) API Map (CD2)

Last updated: 2026-04-14

## 1. Service Overview

| Property | Value |
|----------|-------|
| Platform | Harris Recording Solutions AcclaimWeb |
| Portal URL | `https://acclaim.putnamcountyrecorder.com/acclaimweb/` |
| Auth | Anonymous (cookie-based session) |
| Protocol | HTTP POST to Telerik-grid JSON endpoints |
| Bypass method | `none` (plain session works; `AcclaimWebSession` uses `curl_cffi` prophylactically) |
| Doc types filter | `''` (**empty -- needs live portal inspection to identify deed codes**) |
| CSV column mapping | `grantor: Name`, `grantee: First Crossparty Name`, `date: Record Date`, `instrument: Doc Type`, `price: Consideration`, `legal: Legal` (per `counties.yaml` L203-228) |
| Parser | `county_scrapers.acclaimweb_client.AcclaimWebSession` + `parse_freeform_row`-family (no dedicated `parse_putnam_row`) |
| Status | `research_done` (per `county-registry.yaml` L295-305 -- "AcclaimWeb portal. 10 search modes. Records from Jan 1993 onward.") |
| Onboarding | Commit `53dff7d` -- "feat: onboard Putnam County FL (BI+CD2) and update Escambia PT research" |

### Session handshake

```
GET  https://acclaim.putnamcountyrecorder.com/acclaimweb/search/SearchTypeDocType
POST https://acclaim.putnamcountyrecorder.com/acclaimweb/search/SearchTypeDocType?Length=6
     (seeds server-side search state: DocTypes="" (empty pending live identification
      of Putnam's deed-code catalog), RecordDateFrom, RecordDateTo,
      ShowAllNames=true, ShowAllLegals=true)
```

### Probe (2026-04-14)

```
GET https://acclaim.putnamcountyrecorder.com/acclaimweb/
-> HTTP 200, body ~21 KB
Body contains "AcclaimWeb" (Harris branding). Standard portal HTML with Telerik assets.
```

---

## 2. Search Capabilities

AcclaimWeb exposes 10 search modes per registry notes:

1. Name
2. Book / Page
3. Simple
4. Instrument Number
5. Document Type
6. Record Date
7. Advanced Legal
8. Parcel ID
9. Consideration
10. Legal / Comments

The ETL uses date-range search with an optional document-type filter (currently empty for Putnam pending deed-code identification).

### Request: paginated grid fetch

```
POST https://acclaim.putnamcountyrecorder.com/acclaimweb/Search/GridResults?Length=6
Headers: X-Requested-With: XMLHttpRequest
Body:
  page={1..N}
  size=500
  orderBy=~
  groupBy=~
  filter=~
```

Returns JSON: `{ total: N, data: [...] }` where each row has `TransactionItemId`, `DirectName`, `IndirectName`, `DocType`, `DocTypeDescription`, `RecordDate`, `BookPage`, `BookType`, `TransactionId`, `Consideration`, `Comments`, `DocLegalDescription`, ...

### Session defaults (`AcclaimWebSession`)

| Property | Default |
|----------|---------|
| `page_size` | 500 |
| `request_delay` | 1.0s |
| Impersonation | `chrome` (via `curl_cffi`) |
| Doc types | **`''` (empty -- filter downstream)** |

---

## 3. Row Parsing

Same `_parse_row` logic as other AcclaimWeb counties:

| Output key | Source JSON key |
|------------|-----------------|
| `instrument` | `TransactionItemId` |
| `grantor` | `DirectName` (HTML-cleaned) |
| `grantee` | `IndirectName` (HTML-cleaned) |
| `doc_type` | `DocType` OR `DocTypeDescription` |
| `record_date` | `RecordDate` (`/Date(ms)/` -> `MM/DD/YYYY`) |
| `legal` | `DocLegalDescription` OR `Comments` |
| `book` / `page` | parsed from `BookPage` |
| `book_type` | `BookType` |
| `transaction_id` | `TransactionId` |
| `consideration` | `Consideration` |

Which of `DocLegalDescription` or `Comments` holds the legal on Putnam is **pending live portal inspection** (the heuristic in `acclaimweb_client.py` is "first-non-empty"; Putnam may behave like Santa Rosa (Comments) or like DeSoto MS (DocLegalDescription)).

---

## 4. Document Type Catalog

Putnam is configured with `doc_types: ''` (empty) in both `configs.py` L187-192 and downstream. **This is a known open item** -- the deed-type numeric IDs must be discovered by manually loading the portal's doc-type dropdown and capturing the values corresponding to Warranty Deed, Quit Claim Deed, etc. As of 2026-04-14, the registry note reads: "needs live portal inspection".

Typical Harris AcclaimWeb deed IDs in peer counties:
- DeSoto MS: `'1509,1342,1080'` (WAR + QCL + DEE)
- Santa Rosa: `'79'` (single DEED)

Putnam's IDs are **not yet identified** and MUST be discovered before production use. Until they are, the scraper would need to fetch all doc types and filter by `DocTypeDescription` in the processor.

---

## 5. What We Extract

### `counties.yaml` entry (`Putnam` block, L203-228)

```yaml
Putnam:
  column_mapping:
    grantor: Name
    grantee: First Crossparty Name
    date: Record Date
    instrument: Doc Type
    price: Consideration
    legal: Legal
  phase_keywords: [Phase, Ph.?, PH, Unit]
  lot_block_cutoffs: [Lot, Lots, Unit, Units, Blk, Block, BLK]
  skiprows: 0
  delimiters: [",", Parcel]
```

Same Harris-export CSV headers as Santa Rosa (`Name`, `First Crossparty Name`).

### Parser

Putnam does NOT have a dedicated `parse_putnam_row` in `processors/county_parsers.py`. The generic `_parse_freeform_row` (called by `parse_bay_row`-style fallthrough) would be used pending county-specific legal-description quirks, if any.

---

## 6. Other Clerk Surfaces (non-AcclaimWeb)

### Custom OR viewer at `apps.putnam-fl.com/peas/`

Per registry: "County also has a custom OR viewer at `apps.putnam-fl.com/peas/` (limited functionality)." Not used by the ETL. Limited search capabilities compared to AcclaimWeb.

### Civitek OCRS (court records, NOT deeds)

`civitekflorida.com/ocrs/county/54/` (Civitek Official Court Records Search) is court-only for Putnam. Do NOT point the deed scraper at this URL.

---

## 7. Diff vs Okeechobee LandmarkWeb (closest CD2 peer)

Putnam AcclaimWeb vs Okeechobee LandmarkWeb -- both "easy FL" (no Cloudflare required) but structurally very different.

| Attribute | Putnam (AcclaimWeb) | Okeechobee (LandmarkWeb v1.5.93) |
|-----------|---------------------|-----------------------------------|
| Vendor | Harris Recording Solutions | Pioneer Technology Group |
| Portal hostname | `acclaim.putnamcountyrecorder.com` | `pioneer.okeechobeelandmark.com` |
| URL path | `/acclaimweb` (lowercase) | `/LandmarkWebLive` (mixed case with `Live` suffix) |
| Protocol | Telerik grid POST (`GridResults`) | DataTables POST (`GetSearchResults`) |
| Doc-type filter | `''` (pending live inspection) | `''` (all types) |
| Records from | 1993 | N/A (LandmarkWeb start date differs) |
| Sale price | YES (Consideration column) | NO |
| Dedicated parser | NO (generic freeform) | YES (`parse_okeechobee_row`) |
| Status | `research_done` | `live` |

---

## 8. What We Extract vs What's Available

| Data Category | Currently Extracted | Source | Available but Not Extracted | Source |
|---------------|--------------------|---------|-----------------------------|--------|
| Grantor | YES | DirectName | -- | -- |
| Grantee | YES | IndirectName | -- | -- |
| Record date | YES | RecordDate | -- | -- |
| Doc type | YES | DocType/DocTypeDescription | -- | -- |
| Book / Page | YES | BookPage parsed | -- | -- |
| Instrument | YES | TransactionItemId | -- | -- |
| Transaction ID | YES | TransactionId | -- | -- |
| Consideration | YES | Consideration | -- | -- |
| Legal description | YES | DocLegalDescription OR Comments (pending live inspection) | -- | -- |
| Advanced Legal search | NO | -- | Mode 7 search | Portal advanced legal search |
| Parcel ID search | NO | -- | Mode 8 search | Portal parcel search |
| Consideration search | NO | -- | Mode 9 search (by $ amount) | Portal consideration search |
| Legal/Comments search | NO | -- | Mode 10 search | Portal |
| Document image (PDF) | NO | -- | Per-doc viewer PDF | Portal detail page |

---

## 9. Known Limitations and Quirks

1. **Doc-type codes pending discovery.** `doc_types: ''` in `county_scrapers/configs.py` L187-192. Before go-live the deed-type numeric IDs (analogous to Santa Rosa's `'79'` or DeSoto MS's `'1509,1342,1080'`) must be captured from the live portal's Document Type dropdown. The scraper will currently return ALL recorded documents, not just deeds, until this is filled in.

2. **Onboarded in commit `53dff7d`.** "feat: onboard Putnam County FL (BI+CD2) and update Escambia PT research". All three of the Putnam entries (BI, CD2 Acclaim, and the supporting `counties.yaml` block) landed in this single commit. When reviewing history, look at that commit for the minimal Putnam footprint.

3. **Records go back to January 1993.** Per registry notes. Practical backfill lower bound is 1993-01-01.

4. **Civitek OCRS is NOT deeds.** `civitekflorida.com/ocrs/county/54/` is court records only -- do not point deed scraping at it.

5. **Custom OR viewer `apps.putnam-fl.com/peas/` has limited search** per registry. Useful for manual spot-checks; not an automation target.

6. **No dedicated `parse_putnam_row`.** Unlike Santa Rosa, Walton, Okaloosa, or Okeechobee, Putnam will fall through to generic freeform parsing. Add a custom parser only if legal-description quirks emerge during live sweeps.

7. **Legal-field source is pending live inspection.** `_parse_row` picks `DocLegalDescription` OR `Comments` (first non-empty). Putnam's export has NOT been inspected to determine which is canonical.

8. **URL path is lowercase `/acclaimweb`.** Contrast with Santa Rosa's `/AcclaimWeb/` (mixed case with trailing slash). Both spellings work on their respective portals, but treat case and trailing-slash as significant when configuring a client.

9. **`curl_cffi` is used prophylactically.** No Cloudflare observed; `AcclaimWebSession` uses Chrome impersonation anyway.

10. **Harris CSV export headers: `Name`, `First Crossparty Name`.** Same as Santa Rosa. Different from LandmarkWeb's `Grantor(s)` / `Grantee(s)` and Escambia's `Direct Name` / `Reverse Name`.

11. **Sale-price (Consideration) column exists.** Putnam is FL full-disclosure; `Consideration` carries real dollar amounts. The `counties.yaml` `column_mapping` includes `price: Consideration`, so the ETL DOES flow prices through -- same as Santa Rosa and Marion.

12. **Status is `research_done`, not `live`.** The scraper infrastructure is staged (configs, counties.yaml, seed), but no validated production sweep exists yet. Doc-type inspection + first-week verify are blockers for promotion to `live`.

**Source of truth:** `county_scrapers/configs.py` (`ACCLAIMWEB_COUNTIES['Putnam']`, L187-192), `county_scrapers/acclaimweb_client.py`, `counties.yaml` (`Putnam` block, L203-228), `county-registry.yaml` (`putnam-fl.projects.cd2`, L295-305), onboarding commit `53dff7d`.
