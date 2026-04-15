# Santa Rosa County FL -- AcclaimWeb (Clerk) API Map (CD2)

Last updated: 2026-04-14

## 1. Service Overview

| Property | Value |
|----------|-------|
| Platform | Harris Recording Solutions AcclaimWeb |
| Portal URL | `https://acclaim.srccol.com/AcclaimWeb/` |
| Auth | Anonymous (cookie-based session) |
| Protocol | HTTP POST to Telerik-grid JSON endpoints |
| Bypass method | `none` (plain session works; `AcclaimWebSession` in repo uses `curl_cffi.requests.Session(impersonate='chrome')` regardless) |
| Doc types filter | `'79'` (DEED (D) -- single type covers all deeds) |
| CSV column mapping | `grantor: Name`, `grantee: First Crossparty Name`, `date: Record Date`, `instrument: Doc Type`, `price: Consideration`, `legal: Legal` (per `counties.yaml` L230-255) |
| Parser | `county_scrapers.acclaimweb_client.AcclaimWebSession` + `processors.county_parsers.parse_santarosa_row` |
| Status | `live` (per `county-registry.yaml` L346 -- "263 records/week verified 2026-04-12") |

### Session handshake

```
GET  https://acclaim.srccol.com/AcclaimWeb/search/SearchTypeDocType
POST https://acclaim.srccol.com/AcclaimWeb/search/SearchTypeDocType?Length=6
     (seeds server-side search state: DocTypes=79, RecordDateFrom, RecordDateTo,
      ShowAllNames=true, ShowAllLegals=true)
```

No Cloudflare blocking has been reported; the repo still uses `curl_cffi` impersonation prophylactically.

### Probe (2026-04-14)

```
GET https://acclaim.srccol.com/AcclaimWeb/
-> HTTP 200, body ~21 KB
Title/body contains "AcclaimWeb" (Harris branding). Standard portal HTML with Telerik assets.
```

---

## 2. Search Capabilities

### Request: paginated grid fetch

```
POST https://acclaim.srccol.com/AcclaimWeb/Search/GridResults?Length=6
Headers: X-Requested-With: XMLHttpRequest
Body:
  page={1..N}
  size=500
  orderBy=~
  groupBy=~
  filter=~
```

Return is JSON: `{ total: N, data: [ { TransactionItemId, DirectName, IndirectName, DocType, DocTypeDescription, RecordDate, BookPage, BookType, TransactionId, Consideration, Comments, DocLegalDescription, ... } ] }`.

### Session defaults (`AcclaimWebSession`)

| Property | Default |
|----------|---------|
| `page_size` | 500 |
| `request_delay` | 1.0s |
| Impersonation | `chrome` (via `curl_cffi`) |
| Doc types | `'79'` (single-type: DEED) |

---

## 3. Row Parsing (`_parse_row` in `acclaimweb_client.py`)

| Output key | Source JSON key | Notes |
|------------|-----------------|-------|
| `instrument` | `TransactionItemId` | -- |
| `grantor` | `DirectName` (cleaned) | `<br>` -> `"; "`, strip HTML tags |
| `grantee` | `IndirectName` (cleaned) | same |
| `doc_type` | `DocType` OR `DocTypeDescription` | Santa Rosa returns `DocTypeDescription` -- see Quirks |
| `record_date` | `RecordDate` | `/Date(epoch_ms)/` -> `MM/DD/YYYY` |
| `legal` | `DocLegalDescription` OR `Comments` | **Santa Rosa uses `Comments`** (not `DocLegalDescription`) |
| `book` / `page` | parsed from `BookPage` (`"BOOK / PAGE"`) | -- |
| `book_type` | `BookType` | -- |
| `transaction_id` | `TransactionId` | -- |
| `consideration` | `Consideration` | **Santa Rosa populates this (FL full-disclosure sale prices)** |

---

## 4. Document Type Catalog

Santa Rosa is configured for a single doc type:

| Doc type ID | Doc type label | Extracted? |
|-------------|----------------|-----------|
| **79** | **DEED (D)** | YES (sole configured type) |

All deed varieties (Warranty Deed, Quit Claim Deed, Corrective Deed, etc.) flow through the single `79` selector on Santa Rosa's portal. Downstream text-matching on `Doc Type` (CSV column) further refines.

---

## 5. What We Extract

### From `AcclaimWebSession._parse_row`

(as Section 3)

### From `processors.county_parsers.parse_santarosa_row` (line 1728)

Santa Rosa has the second-most customized parser in `county_parsers.py` after Okeechobee. Highlights:

1. Splits `legal` on `\n`, iterates line-by-line.
2. For each line, splits into clauses via `_split_santarosa_clauses`.
3. Per clause:
   - **Strips `UNREC` anywhere** via `re.sub(r'(?i)\bUNREC\b', '', clause)` -- and later marks the segment with `subdivision_flags=['unrecorded']` if present.
   - Calls `_consume_leading_parcel_references` to peel parcel-ID prefixes off the clause.
   - Tries in order: slash-clause (e.g., `LOT 1/BLK 2/PHASE 3`) -> explicit-lot clause -> tract clause -> descriptor clause -> bare-subdivision clause.
4. Cross-clause `current_subdivision` persists so later clauses inherit the subdivision parsed from earlier clauses on the same line.

### `counties.yaml` entry (`Santa Rosa` block, L230-255)

```yaml
"Santa Rosa":
  column_mapping:
    grantor: Name
    grantee: First Crossparty Name
    date: Record Date
    instrument: Doc Type
    price: Consideration     # FL full-disclosure: Santa Rosa has sale prices
    legal: Legal
  phase_keywords: [Phase, Ph.?, PH, Unit]
  lot_block_cutoffs: [Lot, Lots, Unit, Units, Blk, Block, BLK]
  skiprows: 0
  delimiters: [",", Parcel]
```

Note the CSV headers: `Name` (not `Grantor`/`Direct Name`), `First Crossparty Name` (not `Grantee`). These are Harris-portal CSV export conventions.

---

## 6. Diff vs Okeechobee LandmarkWeb (the closest CD2 peer)

Both are Pioneer/Harris-family clerk portals, but Santa Rosa is AcclaimWeb while Okeechobee is LandmarkWeb.

| Attribute | Santa Rosa (AcclaimWeb) | Okeechobee (LandmarkWeb v1.5.93) |
|-----------|-------------------------|-----------------------------------|
| Vendor | Harris Recording Solutions | Pioneer Technology Group |
| Portal skin | AcclaimWeb | LandmarkWeb |
| Protocol | Telerik grid POST (`GridResults`) | DataTables POST (`GetSearchResults`) |
| Doc-type filter | Single `'79'` = all deeds | Empty, filter in processor |
| Sale price | YES (`Consideration` column) | NO (not on grid) |
| Legal field source | `Comments` JSON key | Column 14 in DataTables row |
| Grantor JSON/column | `DirectName` | column 5 |
| CSV header for grantor | `Name` | `Grantor(s)` |
| CSV header for grantee | `First Crossparty Name` | `Grantee(s)` |
| Parser | `parse_santarosa_row` | `parse_okeechobee_row` |
| Cloudflare | none reported | none |

---

## 7. What We Extract vs What's Available

| Data Category | Currently Extracted | Source | Available but Not Extracted | Source |
|---------------|--------------------|---------|-----------------------------|--------|
| Grantor | YES | DirectName | -- | -- |
| Grantee | YES | IndirectName | -- | -- |
| Record date | YES | RecordDate | -- | -- |
| Doc type | YES | DocType/DocTypeDescription | -- | -- |
| Book / Page | YES | BookPage parsed | -- | -- |
| Book type | YES | BookType | -- | -- |
| Instrument | YES | TransactionItemId | -- | -- |
| Transaction ID | YES | TransactionId | -- | -- |
| **Consideration (sale price)** | **YES** | Consideration | -- | -- |
| Legal description | YES | Comments | Document deep-link / image | Portal per-doc detail page |
| Parcel references | YES (parsed from legal) | `_consume_leading_parcel_references` | -- | -- |
| Document image (PDF) | NO | -- | Deep-link PDF | Per-doc viewer |
| Grantor party-type | NO | -- | Party type (e.g., grantor/grantee role) | Per-doc detail |

---

## 8. Known Limitations and Quirks

1. **Historical `configs.py` bug: Santa Rosa pointed at Walton's URL.** Per `FL-ONBOARDING.md` L286: "Santa Rosa's URL is misconfigured. `configs.py` currently points to Walton's clerk domain. This must be fixed before Santa Rosa automation can work." As of the current tree (2026-04-14), `county_scrapers/configs.py` L181-186 correctly points to `https://acclaim.srccol.com/AcclaimWeb` for Santa Rosa. **Before trusting any historical `configs.py` commit, verify this line has not regressed to Walton's `orsearch.clerkofcourts.co.walton.fl.us/LandmarkWeb` URL.** FL-ONBOARDING.md table at L311 still labels Santa Rosa status as "misconfigured" (stale row).

2. **`UNREC` token is stripped AND preserved as a flag.** `parse_santarosa_row` strips the word `UNREC` from each clause before lot/block parsing, then tags the resulting segment with `subdivision_flags: ['unrecorded']`. Downstream consumers should look at the flags, NOT the cleaned legal text, to tell whether the subdivision was unrecorded.

3. **Party-type convention on "to".** Per `FL-ONBOARDING.md` L133: "Party swap on 'to' in Party Type; 'unrec' removed; unit refs cleaned." When a party type contains the literal word "to", Santa Rosa's Harris export swaps grantor/grantee positions before writing the CSV. The CSV headers the ETL then reads (`Name`, `First Crossparty Name`) reflect the post-swap order.

4. **Legal in `Comments`, not `DocLegalDescription`.** The `_parse_row` method tries `DocLegalDescription` first, then falls back to `Comments`. Santa Rosa's export has the legal in `Comments`; this is the OPPOSITE of DeSoto MS (which uses `DocLegalDescription`).

5. **Doc type `79` = DEED.** The single numeric ID `79` covers all deed variants on the Santa Rosa portal. Text-matching on `DocTypeDescription` further refines (WD, QC, etc.) downstream.

6. **Consideration is a Number with no currency.** The `_parse_row` emits it as a stringified integer: `f'{consideration:.0f}'`. No `$` or thousand separators. Empty/null values become empty strings.

7. **Sale price is THE differentiator.** FL full-disclosure means Santa Rosa's `Consideration` column has real dollar amounts. Santa Rosa and Marion are the only FL counties in this repo's `counties.yaml` whose `column_mapping` includes a `price` key.

8. **`curl_cffi` is used even without Cloudflare.** `AcclaimWebSession.__init__` hardcodes `cf_requests.Session(impersonate='chrome')`. Even though Santa Rosa's portal doesn't currently block plain `requests`, the impersonation pre-empts any future TLS fingerprint policy.

9. **Harris CSV export column names.** `Name` (grantor), `First Crossparty Name` (grantee) are Harris-specific. LandmarkWeb portals use `Grantor(s)` / `Grantee(s)`; Escambia/Hernando use `Direct Name` / `Reverse Name`. Do not mix conventions across counties.

10. **263 records/week cadence.** Per registry note: "263 records/week verified 2026-04-12." This is the baseline sanity check for a weekly-chunked sweep.

11. **`parse_santarosa_row` tries clause kinds in strict order.** Slash-clause -> explicit-lot -> tract -> descriptor -> bare-subdivision. An unparseable clause lands in `unparsed_lines`. The chain is preserved via `current_subdivision` across clauses on the same line.

12. **Unit references cleaned before lot parsing.** Per ONBOARDING: "unit refs cleaned". The parser normalizes `UNIT n` tokens before the lot/block walker to avoid mis-classifying condo units as lots.

**Source of truth:** `county_scrapers/configs.py` (`ACCLAIMWEB_COUNTIES['Santa Rosa']`, L181-186), `county_scrapers/acclaimweb_client.py` (L67-201, the AcclaimWebSession class and `_parse_row`), `counties.yaml` (`"Santa Rosa"` block, L230-255), `processors/county_parsers.py::parse_santarosa_row` (line 1728), `county-registry.yaml` (`santa-rosa-fl.projects.cd2`, L342-347), `FL-ONBOARDING.md` L133 and L286 (historical misconfiguration warning) and L311.
