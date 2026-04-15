# Citrus County FL -- Accela Citizen Access API Map (PT)

Last updated: 2026-04-14

## 1. Portal Overview

| Property | Value |
|----------|-------|
| Platform | Accela Citizen Access (ACA) |
| Portal URL | `https://aca-prod.accela.com/CITRUS/Default.aspx` |
| Agency code | `CITRUS` |
| Adapter | `modules.permits.scrapers.adapters.citrus_county.CitrusCountyAdapter` |
| Base class | `AccelaCitizenAccessAdapter` |
| Module | `Building` |
| Target record type | `Building/Residential/NA/NA` |
| Migration | Migrated from a JSF-Primefaces portal to Accela Citizen Access in September 2025 |
| Auth | Anonymous search and detail view |

The adapter is a minimal subclass of `AccelaCitizenAccessAdapter`, overriding only `slug`, `display_name`, `agency_code`, `module_name`, and `target_record_type`. All scraping logic is inherited from the base.

```python
class CitrusCountyAdapter(AccelaCitizenAccessAdapter):
    slug = "citrus-county"
    display_name = "Citrus County"
    agency_code = "CITRUS"
    module_name = "Building"
    target_record_type = "Building/Residential/NA/NA"
```

### Difference from Polk Accela

| Item | Polk (`POLKCO`) | Citrus (`CITRUS`) |
|------|-----------------|-------------------|
| Agency code | `POLKCO` | `CITRUS` |
| Target record type | `Building/Residential/New/NA` | `Building/Residential/NA/NA` |
| Permit number format | `BR-YYYY-NNNN`, `BT-YYYY-NNNN`, `BC-YYYY-NNNN`, `BLD-H-NNNNNN` | Agency-specific (Citrus-issued; do NOT assume Polk's `BR-YYYY-NNNN` pattern applies) |
| Pre-migration platform | Hansen (prefixed with `%` in legacy search) | JSF-Primefaces |

---

## 2. Search Capabilities

### Search URL

```
https://aca-prod.accela.com/CITRUS/Cap/CapHome.aspx?module=Building&TabName=Building
```

### Search form types (General Search only is used)

The adapter targets the General Search form. Per the inherited Accela Citizen Access scraper, the following fields are available (same as Polk):

#### Record Information
| Field | Type | Used by adapter? |
|-------|------|------------------|
| Permit Number | text | -- |
| Record Type | dropdown | YES (`Building/Residential/NA/NA`) |
| Project Name | text | -- |
| Start Date | date picker (MM/DD/YYYY) | YES |
| End Date | date picker (MM/DD/YYYY) | YES |

#### Licensed Professional / Address / Business (available, unused)
| Group | Fields |
|-------|--------|
| Licensed Professional | License Type, State License Number, First Name, Last Name |
| Business | Name of Business, Business License # |
| Address | Street No. (From/To), Direction, Street Name, Street Type, Unit Type/No., Parcel No., City, State, Zip, Country |

### Search results grid

Grid element ID: `ctl00_PlaceHolderMain_dgvPermitList_gdvPermitList` (inherited Accela layout).

Columns: Date, Record Number, Record Type, Address, Project Name, Status, Description.

Pagination: "Showing X-Y of Z" with Next/Prev `__doPostBack` postbacks. The base adapter handles pagination and uses binary date-range splitting when result count >= 100 (the Accela search result cap).

---

## 3. Record Types (Citrus Building module)

Citrus's Accela tree differs from Polk's. The adapter targets only:

```
Building / Residential / NA / NA
```

This 4-level hierarchy (Group/Type/SubType/Category) is the Citrus schema for residential building permits. The `NA/NA` leaves indicate Citrus has not subdivided the Residential type into sub-types or categories in their Accela configuration -- unlike Polk, which distinguishes `Residential/New/NA` from `Residential/Renovation/NA`, etc.

Other record types observed in the Citrus Accela tree (not currently extracted): Commercial / *, Mobile Home / *, Trade (Electric, Plumbing, Mechanical, Gas, Re-Roof, Fence, Demolition), Land Development actions.

---

## 4. Permit Detail Fields

Detail page URL pattern:

```
https://aca-prod.accela.com/CITRUS/Cap/CapDetail.aspx?Module=Building&TabName=Building&capID1=...&capID2=...&capID3=...&agencyCode=CITRUS
```

The inherited `AccelaCitizenAccessAdapter` flattens the detail page HTML and extracts via regex. Same extraction surface as Polk:

| Field | Extracted? | Method |
|-------|-----------|--------|
| Record Number | YES | Grid TH |
| Record Type | YES | Grid cell |
| Status | YES | Grid cell |
| Address | YES | Grid cell |
| Project Name | YES (partial) | Grid cell / detail regex |
| Parcel Number | YES | Detail regex (numeric, no dashes) |
| Applicant Name | PARTIAL | Detail regex |
| Licensed Professional Name | PARTIAL | Detail regex |
| Job Value | YES | Detail regex on "Job Value($)" |
| Subdivision | YES (partial) | Detail regex |

Not extracted (visible on detail page): owner name, owner address, full applicant info, full licensed-professional info (company, license number, phone, email, fax), all Additional Information (gate code, code violation, NOC, waste acknowledgement), Private Provider info, Work Type, Power Provider, Block, Lot, Legal Description.

---

## 5. Inspections

Portal location: Record Info dropdown > Inspections. Visible without login.

Structure (inherited Accela layout):
- **Upcoming** inspections (Schedule / Reschedule / Cancel dropdown)
- **Completed** inspections (with result status)

Format per row: `{Inspection Type} ({ID}) - {Status} {Date}`, with an `Inspector: {name}` line.

### Currently Extracted?

**Intentionally skipped.** The base adapter defines `_parse_inspections(soup)` but `CitrusCountyAdapter` sets `inspections_on_separate_tab = True`, which short-circuits the base to emit `inspections: []` and skip the parse. Citrus (like Polk) renders inspections on a separate Record Info tab rather than inline, so the parser would always return `None` -- the old code emitted `None` with no log, which was the silent-None bug (ACCELA-05). Real inspection capture is deferred to the REST migration (ACCELA-06).

---

## 6. Contacts

Three contact types on every detail page:

| Contact | Extracted? |
|---------|-----------|
| Applicant (name, company, address, phone, email) | PARTIAL (name via regex) |
| Licensed Professional (name, email, company, address, license type + number) | PARTIAL (name via regex) |
| Owner (name, address) | NO |

The regex extraction is the same brittle pattern described in the Polk Accela doc. Any HTML change breaks it silently.

---

## 7. Documents / Attachments

Portal location: Record Info dropdown > Attachments.

Columns: Record ID, Record Type, Name, Type, Latest Update, Action.

### Currently Extracted?

**NO.** The adapter does not visit the Attachments tab.

---

## 8. Fees

Portal location: Payments dropdown > Fees.

Structure: Outstanding Fees (Date, Invoice Number, Amount, Pay Fees button) + Application Fees (Fees, Qty., Amount).

Citrus-specific fee categories are not enumerated in the adapter; whatever Citrus's configured fee schedule emits on the portal is what would appear.

### Currently Extracted?

**NO.** The adapter does not visit the Fees tab.

---

## 9. Processing Status

Portal location: Record Info dropdown > Processing Status.

Inherited Accela behavior: shows the current workflow stage text (e.g., "Plan Review", "Fees Due", "Inspections", "Closed-Complete").

### Currently Extracted?

Only the grid-level `status` (single field) is captured. The detailed processing-status workflow is NOT visited.

---

## 10. Related Records

Portal location: Record Info dropdown > Related Records.

Shows parent/child relationships (e.g., Residential New Permit with child Electric / Plumbing / Mechanical permits).

### Currently Extracted?

**NO.**

---

## 11. REST API

The same Accela REST surface at `https://apis.accela.com` is available for Citrus as for Polk. All three public auth patterns are supported:

| Auth type | Headers | Use case |
|-----------|---------|----------|
| Access Token | `Authorization: {token}` | Logged-in user data |
| App Credentials | `x-accela-appid`, `x-accela-appsecret` | App settings |
| Public / Anonymous | `x-accela-appid`, `x-accela-agency: CITRUS`, `x-accela-environment` | Public citizen app data |

Key endpoints (same as Polk, but pointed at agency `CITRUS`):

| Endpoint | Returns |
|----------|---------|
| `POST /v4/search/records` | Search |
| `GET /v4/records/{id}` | Full record |
| `GET /v4/records/{id}/inspections` | Inspections |
| `GET /v4/records/{id}/contacts` | Applicant / owner / contractor |
| `GET /v4/records/{id}/professionals` | Licensed professionals |
| `GET /v4/records/{id}/fees` | Fee line items |
| `GET /v4/records/{id}/documents` | Documents |
| `GET /v4/records/{id}/parcels` | Parcel metadata |
| `GET /v4/records/{id}/workflowTasks` | Processing status |

### Currently Used?

**NO.** The adapter scrapes HTML with regex like the Polk adapter. Migrating to the REST API requires registering a Citizen App on developer.accela.com and setting `x-accela-agency: CITRUS`.

---

## 12. What We Currently Extract vs What's Available

| Data Point | Currently Extracted | Source | Available but Not Extracted | Source |
|-----------|--------------------|--------|-----------------------------|--------|
| Permit Number | YES | Grid link | -- | -- |
| Address | YES | Grid cell | Structured address, unit, zip | Detail / REST |
| Parcel ID | YES | Detail regex | Block, Lot, Subdivision code, Legal, Land Value | Detail / REST |
| Issue Date | YES | Grid cell | Opened, Closed, Completed, Estimated Due | REST |
| Status | YES | Grid cell | Full workflow task history | Processing Status tab / REST |
| Permit Type | YES | Grid cell | 4-level hierarchy | REST |
| Valuation | YES | Detail regex | Total Fee, Balance, Total Pay | REST fees |
| Subdivision | PARTIAL | Detail regex | -- | -- |
| Contractor name | PARTIAL | Detail regex | Full contractor record | Detail / REST |
| Applicant | PARTIAL | Detail regex | Full applicant record | Detail / REST |
| Owner | NO | -- | Name + address | Detail / REST |
| Project Description | PARTIAL | Detail regex | Full text | Detail / REST |
| Inspections | NO | -- | Type, date, status, result, inspector | Inspections / REST |
| Fees | NO | -- | Line items, amounts | Fees / REST |
| Documents | NO | -- | Filenames, types, downloads | Attachments / REST |
| Processing status | NO | -- | Workflow steps | Processing Status / REST |
| Related records | NO | -- | Parent/child tree | Related Records / REST |
| Lat / Lon | NO (always null) | -- | REST address xCoord/yCoord | REST |

---

## 13. Known Limitations and Quirks

1. **Agency code is `CITRUS`, NOT `POLKCO`.** This is the most important distinction from the Polk adapter. URL paths, form postbacks, and REST calls must all include `CITRUS` (or `agency: CITRUS` in REST headers). Do not copy a POLKCO URL and expect it to work.

2. **Target record type is `Building/Residential/NA/NA`.** Polk uses `Building/Residential/New/NA`. Citrus's Accela instance uses `NA` for both SubType and Category on residential permits. Do not assume Polk's slash hierarchy applies.

3. **Permit-number format is NOT `BR-YYYY-NNNN`.** The Polk formats (`BR-YYYY-NNNN`, `BT-YYYY-NNNN`, `BC-YYYY-NNNN`, `BLD-H-NNNNNN`) apply ONLY to agency `POLKCO`. Citrus has its own internal numbering scheme; do not hard-code Polk patterns in downstream parsing.

4. **Migrated from JSF-Primefaces in September 2025.** Citrus previously ran a JSF-Primefaces portal. Legacy permits carried across the migration may still exist; any adapter that encounters pre-Sep 2025 permits should assume the record key exists in Accela but may have reduced detail-page completeness relative to post-migration permits.

5. **Same regex-brittleness as Polk Accela.** All detail-page fields are extracted via regex against flattened HTML. An HTML change breaks silently (field becomes null).

6. **Same ViewState postback pagination.** `__VIEWSTATE` tokens on the search grid can be 100+ KB; the adapter must propagate the session and replay form fields.

7. **Same binary date-range splitting.** When the grid returns >= 100 results, the adapter recursively halves the date range.

8. **No coordinates.** Lat / Lon are always null from the HTML scrape. The REST API `addresses` endpoint has `xCoordinate` / `yCoordinate` but is not wired in.

9. **Cannot use Polk's `%`-prefix legacy-search trick.** The `%` legacy-permit search trick is specific to Polk's Hansen migration. Citrus migrated from JSF-Primefaces, not Hansen.

10. **No owner data in HTML scrape.** Owner is visible on the Accela detail page but is not captured by the regex extractor.

11. **Fees tab may show "Loading..." without JS.** The detail-page Fees section can lazy-load via JavaScript. A simple `requests.get` may not capture fee data -- the REST API would bypass this entirely.

12. **No Citrus-specific Accela reports.** Reports dropdown access (like Polk's Permit Card, CO/CC) requires logged-in session. The adapter does not authenticate.

**Source of truth:** `modules/permits/scrapers/adapters/citrus_county.py` (10 lines, lines 1-10), `modules/permits/scrapers/adapters/accela_citizen_access.py` (base class), `modules/permits/data/source_research.json` (key `citrus-county`), `county-registry.yaml` (`citrus-fl.projects.pt`)
