# Charlotte County FL -- Accela Citizen Access API Map (PT)

Last updated: 2026-04-14

## 1. Portal Overview

| Property | Value |
|----------|-------|
| Platform | Accela Citizen Access (ACA) |
| Portal URL (primary) | `https://aca-prod.accela.com/BOCC/Default.aspx` |
| Portal URL (alternate) | `https://aca-prod.accela.com/CHARLOTTE/Default.aspx` (BOTH paths return HTTP 200 at probe time; the **authoritative** agency path is `BOCC` because the adapter's `agency_code = "BOCC"` is the literal path Accela routes on) |
| Agency code | `BOCC` (unique in repo -- every other county uses a county-named code like `POLKCO`, `CITRUS`) |
| Adapter | `modules.permits.scrapers.adapters.charlotte_county.CharlotteCountyAdapter` |
| Base class | `AccelaCitizenAccessAdapter` |
| Module | `Building` (inherited default) |
| Target record type | `""` (empty string -- BOCC portal has NO record-type dropdown; search runs across ALL Building permits) |
| `permit_type_filter` | `("Residential Single Family",)` (post-search tuple filter to keep only new-construction rows) |
| `detail_request_delay` | `0.5` seconds (BOCC portal rate-limits aggressively) |
| Registry status | **ABSENT -- no entry in `county-registry.yaml`** |
| Adapter registration | **NOT registered in `modules/permits/scrapers/adapters/__init__.py`** (the `__init__.py` file is empty, 1 line) -- see Quirks §9.1 |
| Auth | Anonymous search and detail view |

```python
# modules/permits/scrapers/adapters/charlotte_county.py -- full file (11 lines)
from modules.permits.scrapers.adapters.accela_citizen_access import AccelaCitizenAccessAdapter


class CharlotteCountyAdapter(AccelaCitizenAccessAdapter):
    slug = "charlotte-county"
    display_name = "Charlotte County"
    agency_code = "BOCC"
    target_record_type = ""  # BOCC portal has no record-type dropdown; search all Building permits
    permit_type_filter = ("Residential Single Family",)  # post-search filter for new-construction
    detail_request_delay = 0.5  # BOCC portal rate-limits aggressively
```

### Difference from Polk / Citrus Accela

| Item | Polk (`POLKCO`) | Citrus (`CITRUS`) | Charlotte (`BOCC`) |
|------|-----------------|-------------------|--------------------|
| Agency code | `POLKCO` | `CITRUS` | **`BOCC`** |
| Target record type | `Building/Residential/New/NA` | `Building/Residential/NA/NA` | **`""`** (empty) |
| Post-search filter | none | none | **`permit_type_filter=("Residential Single Family",)`** |
| Detail request delay | 0.0s | 0.0s | **0.5s** (rate-limit courtesy) |
| `__init__.py` registration | YES | YES | **NO (orphan)** |

---

## 2. Search Capabilities

### Search URL (derived from base adapter `search_url` property)

```
https://aca-prod.accela.com/BOCC/Cap/CapHome.aspx?module=Building&TabName=Building
```

### Search form types (General Search only is used)

#### Record Information (from base adapter)
| Field | Type | Used by Charlotte? |
|-------|------|--------------------|
| Permit Number | text | -- |
| Record Type | dropdown | **NO -- Charlotte BOCC portal has no record-type dropdown; `target_record_type=""` posts an empty value** |
| Project Name | text | -- |
| Start Date | date picker (MM/DD/YYYY) | YES |
| End Date | date picker (MM/DD/YYYY) | YES |

#### Post-search tuple filter (`permit_type_filter`)

The base adapter applies `permit_type_filter` to each search-result row BEFORE issuing the (expensive) detail-page GET. Charlotte's tuple is `("Residential Single Family",)` -- only rows whose `Record Type` column contains "Residential Single Family" (case-insensitive substring match, per base adapter L237-241) are kept; all other rows (commercial, trade, mobile home, etc.) are silently skipped.

```python
# From AccelaCitizenAccessAdapter._parse_search_results (base L237-241)
if self.permit_type_filter and (
    permit_type is None
    or not any(f.lower() in permit_type.lower() for f in self.permit_type_filter)
):
    continue
```

### Search results grid

Grid element ID: `ctl00_PlaceHolderMain_dgvPermitList_gdvPermitList` (inherited Accela layout).

Pagination: "Showing X-Y of Z" with Next/Prev `__doPostBack` postbacks. Binary date-range splitting engages when a page returns >= 100 results.

### Rate limiting

`detail_request_delay = 0.5` causes a `time.sleep(0.5)` between each detail-page GET (after the post-search filter passes). At ~2 req/s this is half the tempo of Polk / Citrus detail fetching.

---

## 3. Record Types (Charlotte BOCC Building module)

The BOCC Accela tree does NOT expose a record-type dropdown on the General Search form (which is why `target_record_type = ""` is posted). The adapter relies on the post-search `Record Type` column matching `"Residential Single Family"` to identify new-construction permits.

Other record types expected in the Charlotte BOCC Accela instance (NOT extracted): Commercial, Mobile Home, Trade (Electric, Plumbing, Mechanical, Gas, Re-Roof), Land Development, Right-of-Way permits. Any row whose `Record Type` grid cell does not contain the substring "Residential Single Family" is skipped.

---

## 4. Permit Detail Fields

Detail page URL pattern:

```
https://aca-prod.accela.com/BOCC/Cap/CapDetail.aspx?Module=Building&TabName=Building&capID1=...&capID2=...&capID3=...&agencyCode=BOCC
```

The inherited `AccelaCitizenAccessAdapter._fetch_detail_fields` flattens the detail HTML and extracts via regex. Same extraction surface as Polk/Citrus:

| Field | Extracted? | Method |
|-------|-----------|--------|
| Record Number | YES | Grid TH |
| Record Type | YES | Grid cell + `permit_type_filter` |
| Status | YES | Grid cell |
| Address | YES | Grid cell + `_format_address` |
| Project Name | YES (partial) | Grid cell / detail regex |
| Parcel Number | YES | Detail regex `Parcel Number:\s*([A-Z0-9-]+)` |
| Applicant Name | PARTIAL | Detail regex |
| Licensed Professional Name | PARTIAL | Detail regex |
| Job Value | YES | Detail regex on `Job Value($):` |
| Subdivision | YES (partial) | Detail regex |
| Inspections | YES (via `_parse_inspections`) | Table-based or div-based parse |

**Inspection extraction is present in the base adapter** (ref: commit `b16df13` `feat: add Accela inspection extraction and Legistar event items/votes`). The `_parse_inspections` method tries a table layout first, then a div layout; each row yields `{type, status, scheduled_date, result, inspector}`.

---

## 5. Inspections

Portal location: Record Info dropdown > Inspections.

**Currently extracted?** **YES -- via base adapter** `_parse_inspections` (commit `b16df13`). Returns a list of dicts per record with keys `type`, `status`, `scheduled_date`, `result`, `inspector`. Falls back to `None` when no inspection section is found.

---

## 6. Contacts, Documents, Fees, Processing Status, Related Records

Same surfaces as Citrus / Polk:

| Tab | Extracted? |
|-----|-----------|
| Contacts (Applicant / Licensed Pro / Owner) | PARTIAL (applicant + licensed pro via regex; owner NO) |
| Attachments | NO |
| Fees | NO |
| Processing Status | NO (only grid-level `status` captured) |
| Related Records | NO |

---

## 7. REST API

Same Accela REST surface (`https://apis.accela.com`). Public-citizen auth pattern requires header `x-accela-agency: BOCC` (NOT `CHARLOTTE`). Not currently used -- the adapter scrapes HTML.

---

## 8. What We Currently Extract vs What's Available

| Data Point | Currently Extracted | Source | Notes |
|-----------|--------------------|--------|-------|
| Permit Number | YES | Grid link | -- |
| Address | YES | Grid cell, formatted | -- |
| Parcel ID | YES | Detail regex | -- |
| Issue Date | YES | Grid cell | -- |
| Status | YES | Grid cell | -- |
| Permit Type | YES | Grid cell | `permit_type_filter=("Residential Single Family",)` applied |
| Valuation | YES | Detail regex (`Job Value($):`) | -- |
| Subdivision | PARTIAL | Detail regex | Falls back to `project_name` if regex misses |
| Applicant | PARTIAL | Detail regex | -- |
| Licensed Professional | PARTIAL | Detail regex | -- |
| Owner | NO | -- | Not extracted |
| Inspections | YES | `_parse_inspections` (commit `b16df13`) | List of `{type, status, scheduled_date, result, inspector}` |
| Documents | NO | -- | -- |
| Fees | NO | -- | -- |
| Processing Status workflow | NO | -- | Only grid-level status |
| Related Records | NO | -- | -- |
| Lat / Lon | NO (always null) | -- | -- |

---

## 9. Known Limitations and Quirks

1. **Adapter is NOT registered in `modules/permits/scrapers/adapters/__init__.py` -- it is an orphan.** The `__init__.py` file is empty (1 line, 0 bytes of exports). `CharlotteCountyAdapter` exists as a class in `charlotte_county.py` but is not surfaced through the package's public namespace. Any runner that imports adapters by registry-based discovery will NOT instantiate Charlotte. The adapter can be imported directly via its fully-qualified module path, but is orphaned from automated wiring.

2. **`agency_code = "BOCC"` is unique in the repo.** Every other Accela-backed adapter uses a county-named code (`POLKCO`, `CITRUS`). Charlotte's Accela instance is filed under the "Board of County Commissioners" acronym `BOCC` -- a generic three-letter agency code that could collide with other Accela tenants if cross-agency routing ever becomes ambiguous. URL paths, form postbacks, and REST calls must all use `BOCC`.

3. **Both `/CHARLOTTE/` and `/BOCC/` URL paths return HTTP 200 at probe time.** The Charlotte County Accela landing page appears to resolve under both agency slugs. The adapter's `agency_code = "BOCC"` is the definitive routing value (used to build form postback URLs and the REST `x-accela-agency` header); `/CHARLOTTE/` appears to be a human-friendly redirect. Always use `BOCC` in production calls.

4. **`target_record_type = ""` (empty string).** The BOCC portal has NO record-type dropdown on the General Search form. Posting an empty value retrieves ALL Building permits for the date range. Filtering to residential new-construction happens AFTER the search via the `permit_type_filter` tuple.

5. **`permit_type_filter = ("Residential Single Family",)` is a post-search filter.** Unlike Polk's server-side `target_record_type=Building/Residential/New/NA` filter, Charlotte filters client-side by substring match against the `Record Type` grid column. This wastes bandwidth (all Building permits fetched from the grid) but is the only option because the form lacks a dropdown.

6. **`detail_request_delay = 0.5` is unique to Charlotte.** Every other Accela adapter uses 0.0s. The inline comment "BOCC portal rate-limits aggressively" in `charlotte_county.py` documents the reason. A scraper that pays this delay on every detail-page GET for a 120-day bootstrap window may run materially slower than Polk/Citrus.

7. **Registry absence: Charlotte has no entry in `county-registry.yaml`.** There is no `charlotte-fl.projects.pt` block. The sole sources of truth are `modules/permits/scrapers/adapters/charlotte_county.py` (11 lines) and the base class `accela_citizen_access.py`.

8. **Same regex brittleness as Polk / Citrus Accela.** Parcel, applicant, licensed professional, project description, job value, and subdivision are all extracted via regex against flattened HTML. An HTML change breaks silently (field becomes null).

9. **Same ViewState / binary-date-splitting machinery.** `__VIEWSTATE` postbacks propagate via session cookies; when a page returns >= 100 results the adapter recursively halves the date range.

10. **No Charlotte-specific permit-number format documented.** Do NOT assume Polk's `BR-YYYY-NNNN` / `BT-YYYY-NNNN` patterns apply.

11. **Inspection extraction is inherited from the base adapter (commit `b16df13`).** Charlotte automatically benefits from `_parse_inspections` without any subclass override. Inspection rows are attached to each permit's `inspections` key.

12. **Related commits:** `b16df13` (Accela inspection extraction), `c33a871` (Polk ArcGIS field mappings), `00434af` (Polk Accela surface map). The base-adapter inspection machinery added in `b16df13` is what gives Charlotte inspection data without any Charlotte-specific code.

**Source of truth:** `modules/permits/scrapers/adapters/charlotte_county.py` (11 lines, lines 1-11), `modules/permits/scrapers/adapters/accela_citizen_access.py` (490-line base class), `modules/permits/scrapers/adapters/__init__.py` (empty -- confirms orphan status), live probe against `https://aca-prod.accela.com/BOCC/Default.aspx` (HTTP 200) and `https://aca-prod.accela.com/CHARLOTTE/Default.aspx` (HTTP 200) on 2026-04-14, absence from `county-registry.yaml`
