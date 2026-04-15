# Charlotte County FL -- Accela Citizen Access API Map (PT)

Last updated: 2026-04-14

> **Status: Not Implemented.** The `charlotte_county.py` adapter referenced throughout this document was intentionally deleted during the 2026-04-14 project-reload registry audit (see `docs/sessions/2026-04-14-project-reload.md` item 14) -- it was mis-coded with `agency_code='BOCC'` (ambiguous abbreviation; Charlotte FL's correct agency code is `CHARLOTTEFL`) and was an orphan across all three metadata sources (`county-registry.yaml`, `modules/permits/scrapers/adapters/__init__.py`, and `seed_pt_jurisdiction_config.py`). This document is retained as portal-surface reconnaissance for a future re-implementation; references to a "CharlotteCountyAdapter" class are historical or aspirational and do NOT describe code that currently exists under `modules/`. No Charlotte permit extraction is currently running.

## 1. Portal Overview

| Property | Value |
|----------|-------|
| Platform | Accela Citizen Access (ACA) |
| Portal URL (primary) | `https://aca-prod.accela.com/BOCC/Default.aspx` |
| Portal URL (alternate) | `https://aca-prod.accela.com/CHARLOTTE/Default.aspx` (BOTH paths return HTTP 200 at probe time; the **authoritative** agency path is `BOCC` because the adapter's `agency_code = "BOCC"` is the literal path Accela routes on) |
| Agency code | `BOCC` (unique in repo -- every other county uses a county-named code like `POLKCO`, `CITRUS`) |
| Adapter | None -- `modules/permits/scrapers/adapters/charlotte_county.py` was deleted 2026-04-14; see Status banner above |
| Base class | `AccelaCitizenAccessAdapter` |
| Module | `Building` (inherited default) |
| Target record type | `""` (empty string -- BOCC portal has NO record-type dropdown; search runs across ALL Building permits) |
| `permit_type_filter` | `("Residential Single Family",)` (post-search tuple filter to keep only new-construction rows) |
| `detail_request_delay` | `0.5` seconds (BOCC portal rate-limits aggressively) |
| Registry status | **ABSENT -- no entry in `county-registry.yaml`** |
| Adapter registration | N/A -- adapter file deleted; `__init__.py` is empty (confirms no Charlotte registration) |
| Auth | Anonymous search and detail view |

**Historical adapter shape (for future re-implementation reference only -- this file no longer exists in the repo):**

```python
# Deleted 2026-04-14. Previously at:
# modules/permits/scrapers/adapters/charlotte_county.py (11 lines)
#
# class CharlotteCountyAdapter(AccelaCitizenAccessAdapter):
#     slug = "charlotte-county"
#     display_name = "Charlotte County"
#     agency_code = "BOCC"           # mis-coded; should be "CHARLOTTEFL"
#     target_record_type = ""
#     permit_type_filter = ("Residential Single Family",)
#     detail_request_delay = 0.5
```

### Difference from Polk / Citrus Accela

| Item | Polk (`POLKCO`) | Citrus (`CITRUS`) | Charlotte (`BOCC`) |
|------|-----------------|-------------------|--------------------|
| Agency code | `POLKCO` | `CITRUS` | **`BOCC`** |
| Target record type | `Building/Residential/New/NA` | `Building/Residential/NA/NA` | **`""`** (empty) |
| Post-search filter | none | none | **`permit_type_filter=("Residential Single Family",)`** |
| Detail request delay | 0.0s | 0.0s | **0.5s** (rate-limit courtesy) |
| `__init__.py` registration | YES | YES | **NO (orphan)** |
| Adapter file exists | YES | YES | **NO -- deleted 2026-04-14** |

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
| Inspections | N/A -- adapter does not exist (base method `_parse_inspections` would be inherited IF re-implemented) | Table or div parse |

**If Charlotte is re-implemented as a minimal `AccelaCitizenAccessAdapter` subclass, inspection extraction would be inherited from the base** (ref: commit `b16df13`). On Charlotte's live portal (BOCC), whether `_parse_inspections` returns rows depends on whether the CapDetail page renders inspections inline or on a separate tab (same question as open for Polk/Citrus; see `docs/api-maps/polk-county-improvement-report.md` ACCELA-05).

---

## 5. Inspections

Portal location: Record Info dropdown > Inspections.

**Currently extracted?** **N/A -- no Charlotte adapter currently exists.** If re-implemented as a trivial base-class subclass, inherited `_parse_inspections` would attempt extraction on each CapDetail response and return rows or `None` depending on BOCC portal layout. See Status banner at top and `docs/api-maps/polk-county-improvement-report.md` ACCELA-05 for the shared separate-tab caveat.

---

## 6. Contacts, Documents, Fees, Processing Status, Related Records

Same surfaces as Citrus / Polk:

> Note: the "Extracted?" column below reflects the pre-deletion behavior of the now-removed Charlotte adapter (deleted 2026-04-14) -- it does NOT describe a currently-running integration. See Status banner at top.

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

> Note: the "Currently Extracted" column below reflects the pre-deletion behavior of the now-removed Charlotte adapter (deleted 2026-04-14) -- it does NOT describe a currently-running integration. Charlotte is not presently producing any permit data. See Status banner at top.

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

1. **Adapter deleted 2026-04-14 -- this map documents a planning/recon surface, not a live integration.** The adapter file `modules/permits/scrapers/adapters/charlotte_county.py` was removed during the project-reload registry audit; see `docs/sessions/2026-04-14-project-reload.md` item 14 for the deletion rationale (mis-coded `agency_code='BOCC'` + orphan across all three metadata sources). Any runner that attempts to import a Charlotte adapter by name will fail. References to "CharlotteCountyAdapter" elsewhere in this document are historical (describing the deleted shape) or aspirational (describing the shape a future re-implementation should take).

2. **The deleted adapter used `agency_code = "BOCC"` -- mis-coded.** Every other Accela-backed adapter uses a county-named code (`POLKCO`, `CITRUS`). Charlotte's Accela instance is filed under the "Board of County Commissioners" acronym `BOCC` -- a generic three-letter agency code. A future re-implementation should prefer `CHARLOTTEFL` as the canonical agency code per the 2026-04-14 project-reload audit. URL paths, form postbacks, and REST calls must use the agency slug that Accela actually routes on (both `/BOCC/` and `/CHARLOTTE/` return HTTP 200 at probe time).

3. **Both `/CHARLOTTE/` and `/BOCC/` URL paths return HTTP 200 at probe time.** The Charlotte County Accela landing page resolves under both agency slugs. The deleted adapter's `agency_code = "BOCC"` was used to build form postback URLs and the REST `x-accela-agency` header; a future re-implementation should verify which slug Accela actually routes search postbacks on before committing to either. `/CHARLOTTE/` may be a human-friendly redirect to `/BOCC/` or vice-versa.

4. **The deleted adapter used `target_record_type = ""` (empty string).** The BOCC portal has NO record-type dropdown on the General Search form. Posting an empty value retrieves ALL Building permits for the date range. Filtering to residential new-construction happened (pre-deletion) AFTER the search via the `permit_type_filter` tuple.

5. **The deleted adapter used `permit_type_filter = ("Residential Single Family",)` as a post-search filter.** Unlike Polk's server-side `target_record_type=Building/Residential/New/NA` filter, Charlotte filtered client-side by substring match against the `Record Type` grid column. This wastes bandwidth (all Building permits fetched from the grid) but was the only option because the form lacks a dropdown. A re-implementation should keep this pattern.

6. **The deleted adapter set `detail_request_delay = 0.5` (unique to Charlotte).** Every other Accela adapter uses 0.0s. The inline comment "BOCC portal rate-limits aggressively" in the former `charlotte_county.py` documented the reason. A future re-implementation should preserve this delay; a scraper that pays this delay on every detail-page GET for a 120-day bootstrap window will run materially slower than Polk/Citrus.

7. **Registry absence: Charlotte has no entry in `county-registry.yaml`.** There is no `charlotte-fl.projects.pt` block. Combined with the 2026-04-14 deletion of the adapter file, this means there is currently no persistent source of truth for a Charlotte PT integration -- only this document and the base class `accela_citizen_access.py`.

8. **Same regex brittleness as Polk / Citrus Accela.** Parcel, applicant, licensed professional, project description, job value, and subdivision are all extracted via regex against flattened HTML. An HTML change breaks silently (field becomes null).

9. **Same ViewState / binary-date-splitting machinery.** `__VIEWSTATE` postbacks propagate via session cookies; when a page returns >= 100 results the adapter recursively halves the date range.

10. **No Charlotte-specific permit-number format documented.** Do NOT assume Polk's `BR-YYYY-NNNN` / `BT-YYYY-NNNN` patterns apply.

11. **Inspection extraction would be inherited from the base adapter (commit `b16df13`) IF Charlotte were re-implemented.** A trivial `AccelaCitizenAccessAdapter` subclass would automatically invoke `_parse_inspections` on each CapDetail; whether it actually returns rows depends on BOCC's portal layout (see §5 note and the Polk improvement-report ACCELA-05 caveat about separate-tab rendering).

12. **Related commits:** `b16df13` (Accela inspection extraction, still present in base class), `c33a871` (Polk ArcGIS field mappings), `00434af` (Polk Accela surface map). The base-adapter inspection machinery added in `b16df13` would give any future Charlotte re-implementation inspection data without Charlotte-specific code. See also `docs/sessions/2026-04-14-project-reload.md` item 14 for the Charlotte adapter deletion.

**Source of truth (historical, pre-deletion):** former `modules/permits/scrapers/adapters/charlotte_county.py` (11 lines; deleted 2026-04-14 -- recorded in `docs/sessions/2026-04-14-project-reload.md` item 14), `modules/permits/scrapers/adapters/accela_citizen_access.py` (490-line base class -- still in repo), `modules/permits/scrapers/adapters/__init__.py` (empty -- confirms no Charlotte registration), live portal probes against `https://aca-prod.accela.com/BOCC/Default.aspx` (HTTP 200) and `https://aca-prod.accela.com/CHARLOTTE/Default.aspx` (HTTP 200) on 2026-04-14, absence from `county-registry.yaml`.
