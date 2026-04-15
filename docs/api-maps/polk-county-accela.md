# Polk County FL -- Accela Citizen Access API Map

Last updated: 2026-04-14

## 1. Portal Overview

| Property | Value |
|----------|-------|
| Platform | Accela Citizen Access (ACA) |
| Portal URL | `https://aca-prod.accela.com/POLKCO/` |
| Agency code | `POLKCO` |
| Modules | Home, **Building**, Enforcement, Land Dev |
| Auth | Anonymous search + detail view; login required for application submission, inspection scheduling, fee payment, document upload |
| User guide | [Building ACA Manual (PDF)](https://www.polkfl.gov/wp-content/uploads/2023/07/building-accela-user-guide.pdf) |
| Support phone | (863) 534-6080 |

The portal is operated by Polk County Building Division. Three east-Polk municipalities (Town of Dundee, Fort Meade, Polk City) issue permits through the same portal but cannot accept online fee payments.

### Modules

- **Building** -- primary permit module; our adapter targets this
- **Enforcement** -- code enforcement complaints and lien searches
- **Land Dev** -- land development / planning applications (DRC, BOCC, BOA, PC actions)
- **Home** -- dashboard with links to all modules; logged-in users see My Records, Collections, Cart

### Permit Number Formats

Observed patterns from the portal and user guide:
- `BR-YYYY-NNNN` -- Building Residential (e.g., BR-2024-1234)
- `BT-YYYY-NNNN` -- Building Trade (mechanical, plumbing, electric, etc.)
- `BC-YYYY-NNNN` -- Building Commercial
- `BLD-H-NNNNNN` -- Legacy Hansen-era permits (prefixed with `%` in search)

---

## 2. Search Capabilities

### Search URL

```
https://aca-prod.accela.com/POLKCO/Cap/CapHome.aspx?module=Building&TabName=Building
```

### Search Form Types

The Building module offers six search approaches selectable via dropdown:

1. **General Search** (default -- what our adapter uses)
2. Search by Address
3. Search by Licensed Professional Information
4. Search by Record Information
5. Search for Trade Name
6. Search by Contact

### General Search Fields

#### Record Information
| Field | Type | Notes |
|-------|------|-------|
| Permit Number | text | Prefix with `%` for legacy Hansen permits |
| Record Type | dropdown | See Section 3 for full list |
| Project Name | text | |
| Start Date | date picker | MM/DD/YYYY; our adapter uses this |
| End Date | date picker | MM/DD/YYYY; our adapter uses this |

#### Licensed Professional
| Field | Type |
|-------|------|
| License Type | dropdown (50+ values) |
| State License Number | text |
| First Name | text |
| Last Name | text |

#### Business Information
| Field | Type |
|-------|------|
| Name of Business | text |
| Business License # | text |

#### Address
| Field | Type | Options |
|-------|------|---------|
| Street No. | range (From/To) | |
| Direction | dropdown | E, N, NE, NW, S, SE, SW, W |
| Street Name | text | |
| Street Type | dropdown | AVE, BLVD, BND, CIR, CT, CV, DR, HWY, LN, LNDG, LOOP, MNR, PASS, PATH, PKWY, PL, PT, RD, RDG, RUN, SQ, ST, TER, TRL, WAY, WY |
| Unit Type | dropdown | Apt, Bldg, Lot, Suite, Tangible Unit |
| Unit No. | text | |
| Parcel No. | text | No dashes |
| City | text | |
| State | text | |
| Zip | text | |
| Country | dropdown | 200+ countries |

### Search Results Grid

Grid element ID: `ctl00_PlaceHolderMain_dgvPermitList_gdvPermitList`

| Column | Notes |
|--------|-------|
| Date | Issue/file date; our adapter parses this |
| Record Number | Link to CapDetail.aspx |
| Record Type | e.g., "Residential New Permit" |
| Address | Street + city + state + zip |
| Project Name | Subdivision or project name (when present) |
| Status | Current record status |
| Description | Work description (varies by agency) |

Pagination: "Showing X-Y of Z" pattern; Next/Prev links via `__doPostBack`. Our adapter handles pagination and uses binary date-range splitting when result count >= 100.

---

## 3. Record Types (Building Module)

Full hierarchy as exposed in the Record Type dropdown. Our adapter currently targets only `Building/Residential/New/NA`.

### Administrative
- Building Administrative Permit
- Contractor Licensing/MH Parks Renewal

### Commercial
- Commercial Fire Permit
- Commercial Multi-Family Permit
- Commercial New Permit
- Commercial Renovation Permit
- Commercial Sign Permit
- Commercial Tent Permit

### Residential
- Residential Accessory Permit (sheds, detached carports, guest houses, screen/pool enclosures)
- Residential Driveway Permit
- **Residential New Permit** (new houses) -- **currently extracted**
- Residential Renovation/Addition Permit (window/door, screen room, solid roof)

### Mobile Home
- Mobile Home Permit
- Mobile Home Skirting Permit

### Single Trade
- Demolition Permit
- Electric Permit
- Fence or Wall Permit
- Gas Permit
- Mechanical Permit
- Plumbing Permit
- Pool Permit
- Re-Roof Permit
- Window and Door Permit

### Other
- Pre-Permit or Power Release Request (MH and Damage Pre-inspection)
- Permit Search Request
- Temporary Use Permit (beverage license, food/produce stands, special events)

### Enforcement Module Record Types
- Complaint
- Lien Search Request

### Land Dev Module Record Types
Access Solely By Easement, Admin-Administrative Action, Admin-Administrative Determination, Admin-Administrative Interpretation, Admin-Non-Conforming Use, BOA-Special Exception, BOA-Temporary Special Exception, BOA-Variance, BOCC-Community Development District, BOCC-Conditional Use, BOCC-CPA Large, BOCC-CPA Small, BOCC-Developer's Agreement, BOCC-Development of Regional Impact, BOCC-Infrastructure Agreement, BOCC-LDC District Change, BOCC-LDC Text Change, BOCC-Planned Development, BOCC-Waiver, DRC-Action, DRC-Driveway Only, DRC-Non-Residential Site Plan, DRC-Plat Review, DRC-Residential Site Review, DRC-Waivers In Fill Lots Application, LUHO-Special Exception, LUHO-Temporary Special Exception, LUHO-Variance, PC-Conditional Use-New Or Mobile Home, PC-Major Modifications, PC-Planned Development, PC-Sign Plan Review, PC-Sign Variance, PC-Suburban Planned Development, Plan Revision, Prescriptive Planned Development, RENEWAL-Annual Reports, Surety

---

## 4. Permit Detail Fields (Full Inventory)

Detail page URL pattern:
```
https://aca-prod.accela.com/POLKCO/Cap/CapDetail.aspx?Module=Building&TabName=Building&capID1=...&capID2=...&capID3=...&agencyCode=POLKCO
```

### Header
| Field | Extracted? | Notes |
|-------|-----------|-------|
| Record Number | YES | e.g., BT-2024-2125 |
| Record Type / Permit Type | YES | e.g., "Mechanical Permit" |
| Record Status | YES | e.g., "Closed-Complete", "Inspections", "Fees Due" |

### Work Location
| Field | Extracted? | Notes |
|-------|-----------|-------|
| Address | YES | Full street, city, state, zip |

### Applicant
| Field | Extracted? | Notes |
|-------|-----------|-------|
| Name | YES (partial) | Via regex on flattened text |
| Company | NO | Visible on detail page |
| Street Address | NO | Full mailing address shown |
| City/State/Zip | NO | |
| Work Phone | NO | |
| Email | NO | |
| Mailing Address | NO | Separate from street address |

### Licensed Professional
| Field | Extracted? | Notes |
|-------|-----------|-------|
| Name | YES (partial) | Via regex on flattened text |
| Email | NO | |
| Company | NO | |
| Address | NO | |
| Fax | NO | |
| License Type + Number | NO | e.g., "Air Condition Class A CAC057633" |
| "View Additional Licensed Professionals>>" link | NO | Shows subcontractors |

### Owner
| Field | Extracted? | Notes |
|-------|-----------|-------|
| Name | YES (regex) | `owner_name_pattern`; split on blue asterisk glyph (ACCELA-03) |
| Address | YES (regex) | `owner_address_pattern`; terminates at duplicate `OWNER:` label (ACCELA-03) |

### Project Description
| Field | Extracted? | Notes |
|-------|-----------|-------|
| Project Description | YES (partial) | Via regex; e.g., "Replace 2ton system- no new duct" |

### Additional Information (expandable "More Details" section)
| Field | Extracted? | Notes |
|-------|-----------|-------|
| Job Value($) | YES | Via regex; e.g., "$8,445.00" |

### Application Information (expandable)

#### General Information
| Field | Extracted? |
|-------|-----------|
| Is a Gate Code Required for Access | NO |
| Gate Code | NO |
| Is this Application a result of a Code Violation | NO |
| Code Violation Case Number | NO |
| Is the Applicant the Owner | NO |
| Notice of Commencement (NOC) | NO |
| Permit Packet Submission | NO |
| FS 119 Status | NO |
| Construction Waste Acknowledgement | NO |
| Commercial Franchise Holder Name | NO |
| Commercial Franchise Holder Phone | NO |
| Disposal Equipment | NO |
| Disposal Frequency | NO |
| Nearest cross street or special instructions | NO |
| How are plans submitted | NO |

#### Private Provider Information
| Field | Extracted? |
|-------|-----------|
| Will Private Provider conduct Plans Review/Inspections | NO |

#### Trade Information
| Field | Extracted? |
|-------|-----------|
| Work Type | NO |
| Property Type | NO |

#### Mechanical-specific (varies by permit type)
| Field | Extracted? |
|-------|-----------|
| Permit Type (HVAC, etc.) | NO |
| Is this a mini split | NO |
| AC Changeout | NO |

### Application Information Table (expandable)

#### Power Provider
| Field | Extracted? | Notes |
|-------|-----------|-------|
| Power Provider | NO | e.g., "Duke Energy" |
| Type | NO | e.g., "T-Pole", "Pre-Power" |
| Release Date | NO | |
| Release By | NO | Staff name |

### Parcel Information
| Field | Extracted? | Notes |
|-------|-----------|-------|
| Parcel Number | YES | Via regex; 18-digit format without dashes |
| Block | NO | Often "--" |
| Lot | NO | Often "--" |
| Subdivision | YES | Via regex |

---

## 5. Inspection Data

### Portal Location

Record Info dropdown > Inspections. Publicly visible without login.

### Inspection List Structure

Two sections on the Inspections tab:

**Upcoming** -- inspections available to be scheduled or already scheduled
- Format: `{Inspection Type} ({ID}) - {Status} {Date}`
- Example: "Demolition Final (1186453) - Scheduled 08/14/2018"
- Inspector line: "Inspector: {name}" or "Inspector: unassigned"
- Actions dropdown: View Details, Schedule, Reschedule, Cancel

**Completed** -- finished inspections with results
- Same format with result status

### Inspection Fields (from portal)
| Field | Visible? | Notes |
|-------|----------|-------|
| Inspection Type | YES | e.g., "Demolition Final" |
| Inspection ID | YES | Numeric ID in parentheses |
| Status | YES | Pending TBD, Scheduled, Completed |
| Scheduled Date | YES | |
| Inspector Name | YES | May be "unassigned" |
| Result | YES | For completed inspections |

### Inspection Types (from Permit Card)

The permit card PDF reveals the standard inspection sequence for residential permits:
- MH Setup, MH Skirting, Driveway, Site Drainage
- Footing, Plumbing 1st, Plumbing 2nd, Plumbing Final
- (Additional types vary by permit type)

### Auth Requirements

- **Viewing** inspections: No login required (public detail page)
- **Scheduling** inspections: Login required; cancellation/reschedule before 06:00 AM same day
- **Inspection scheduling fields**: Inspection type, date (calendar picker), time slot ("All Day"), location, contact

### Currently Extracted?

**Inspections are unavailable for anonymous viewers; the adapter emits `[]`.** April 2026 live recon established that Polk's "Inspections sub-tab" is not a separate page — it is a hash-anchored `<div id="tab-inspections">` already inline in the CapDetail HTML, whose rows are populated by a `__doPostBack` to `ctl00$PlaceHolderMain$InspectionList$btnRefreshGridView`. For anonymous users (the only mode our scraper supports) that postback returns an MS-AJAX delta with empty `panelsToRefreshIDs` and the inline panel renders "There are no completed inspections on this record." regardless of the permit's true inspection state. Identical behavior was observed on BREVARD and BOCC, confirming the gate is platform-wide, not agency-specific.

`PolkCountyAdapter` therefore sets `inspections_on_separate_tab = True`, which short-circuits the base adapter to emit `inspections: []` (ACCELA-05). If Polk's ACA admin ever enables the anonymous-user toggle in Civic Platform (the same gate that blocks ACCELA-02), flip the attribute to False and the base `_parse_inspections_from_table()` will pick up the now-populated grid without further code changes. Until then, ACCELA-06 is BLOCKED — see `docs/api-maps/polk-county-improvement-report.md`.

### REST API Inspection Fields (informational; gated)

The `GET /v4/records/{recordId}/inspections` endpoint returns 60+ fields per inspection (id, type, status, category, resultType, completedDate, scheduleDate, inspectorFullName, requestComment, resultComment, grade, totalScore, latitude, longitude, full address/contact objects). Token-gated; see `accela-rest-probe-findings.md`.

---

## 6. Contacts / Parties

### Applicant
| Field | Available | Extracted |
|-------|-----------|-----------|
| First/Last Name | YES | YES (partial, via regex) |
| Company / Business Name | YES | NO |
| Street Address | YES | NO |
| City/State/Zip | YES | NO |
| Work Phone | YES | NO |
| Mobile Phone | YES | NO |
| Email | YES | NO |
| Mailing Address | YES | NO |

### Licensed Professional (Primary Contractor)
| Field | Available | Extracted |
|-------|-----------|-----------|
| Name | YES | YES (partial, via regex) |
| Email | YES | NO |
| Company | YES | NO |
| Address | YES | NO |
| Fax | YES | NO |
| License Type | YES | NO |
| License Number | YES | NO |
| Additional Licensed Professionals | YES (via link) | NO |

### Owner
| Field | Available | Extracted |
|-------|-----------|-----------|
| Name | YES | YES (regex, ACCELA-03) |
| Address | YES | YES (regex, ACCELA-03) |

### Contact Information Grid (Account Management)
Columns: First Name, Middle Name, Last Name, Business Name, SSN, FEIN, Contact Type, Status, Action, Full Name

---

## 7. Documents / Attachments

### Portal Location

Record Info dropdown > Attachments

### Attachment List Columns
| Column | Notes |
|--------|-------|
| Record ID | Permit number |
| Record Type | Full permit type description |
| Name | Clickable filename (downloads document) |
| Type | Document category (e.g., "Construction Plans", "Documents (NOC, Utility Receipts, Septic Permits, etc.)") |
| Latest Update | Date |
| Action | Actions dropdown |

### Document Properties
- Maximum file size: 100 MB
- Disallowed file types: asp, aspx, bat, cgi, chm, cmd, com, cpl, crt, dat, eml, exe, hlp, hta, htm, html, inf, ins, isp, jse?, jsp, lnk, mdb, msi, msp, mst, pcd, pif, reg, scr, sct, shs, vbe, vbs, wsf, wsh, wsc
- Documents can be viewed via "View People Attachments" link

### Auth Requirements
- **Viewing** attachment list: No login required
- **Downloading** attachments: Clickable by public users (per user guide)
- **Uploading** documents: Login required

### Digital Plan Room
Separate interface accessible from permit detail page with tabs: Record Details, Summary, Uploads, Issues, Conditions, Approved Plans. Review Packages show Date, Name, Description, Status, Updated By, Action.

### Currently Extracted?

**NO.** The adapter does not visit the Attachments tab.

---

## 8. Fees

### Portal Location

Payments dropdown > Fees

### Fee List Structure

**Outstanding Fees:**
| Column | Notes |
|--------|-------|
| Date | Assessment date |
| Invoice Number | Numeric invoice ID |
| Amount | Dollar amount |
| Pay Fees | Button (requires login) |

Total outstanding fees shown at bottom.

**Application Fees (checkout view):**
| Column | Notes |
|--------|-------|
| Fees | Fee description (e.g., "B Demolition / Accessory Structure") |
| Qty. | Quantity |
| Amount | Dollar amount |

### Fee Categories Observed
- B Demolition / Accessory Structure
- B Demolition / Primary Structure - Residential
- B Surcharge BCAIB 1.5%
- B Surcharge FBC 1%
- (Additional inspection fees may be assessed later)

### Payment Methods
- Credit Card
- Bank Account (eCheck)
- Trust Account

### Auth Requirements
- **Viewing** fee summary: Appears on detail page without login (Outstanding section)
- **Paying** fees: Login required
- **Note**: Town of Dundee, Fort Meade, and Polk City permits cannot pay online

### Currently Extracted?

**NO.** The adapter does not visit the Fees tab. The `valuation` field comes from the "Job Value($)" in Additional Information, not from fee data.

---

## 9. Processing Status / Workflow

### Portal Location

Record Info dropdown > Processing Status

### Content

Shows the current workflow stage of the record. The user guide describes this as showing "what status the record is on."

### Known Record Statuses (observed)
- Fees Due
- Inspections
- Closed-Complete
- Closed-CO Issued (Certificate of Occupancy)
- Closed-CC Issued (Certificate of Completion)
- Plan Review
- (Others likely exist)

### REST API Workflow Fields

`GET /v4/records/{recordId}/workflowTasks` returns: task ID, task name, status, assignee, due date, comments, custom forms. History available via `/workflowTasks/histories`.

### Currently Extracted?

**NO.** The adapter extracts `status` from the search results grid only (the header-level status like "Inspections"), not the detailed processing status/workflow steps.

---

## 10. Related Records

### Portal Location

Record Info dropdown > Related Records

### Content

Shows parent/child record relationships with "View Entire Tree" option. For example, a Residential New Permit may have related trade permits (Electric, Plumbing, Mechanical) as child records.

### REST API

`GET /v4/records/{recordId}/related` returns linked record IDs and relationship types.

### Currently Extracted?

**NO.**

---

## 11. REST API

### Base URL

```
https://apis.accela.com
```

### Authentication Types

| Type | Headers Required | Use Case |
|------|-----------------|----------|
| Access Token | `Authorization: {token}` | Authenticated user data |
| App Credentials | `x-accela-appid`, `x-accela-appsecret` | App settings |
| Public/Anonymous | `x-accela-appid`, `x-accela-agency`, `x-accela-environment` | Public citizen app data |

### App Registration

- Register at [developer.accela.com](https://developer.accela.com)
- Choose "Citizen App" for public-facing access
- Receive App ID + App Secret
- Free tier available (no pricing documented)

### Key Endpoints for Our Use Case

| Endpoint | Method | Auth | What It Returns |
|----------|--------|------|-----------------|
| `/v4/search/records` | POST | Public* | Search records by type, date, address, etc. |
| `/v4/records/{ids}` | GET | Public* | Full record details including jobValue, status, type hierarchy |
| `/v4/records/{id}/addresses` | GET | Public* | Addresses linked to record |
| `/v4/records/{id}/parcels` | GET | Public* | Parcel numbers, legal description, land value |
| `/v4/records/{id}/contacts` | GET | Public* | Applicant, owner, contractor contacts |
| `/v4/records/{id}/professionals` | GET | Public* | Licensed professionals with license numbers |
| `/v4/records/{id}/owners` | GET | Public* | Property owners |
| `/v4/records/{id}/inspections` | GET | Public* | All inspections with type, date, result, inspector |
| `/v4/records/{id}/fees` | GET | Public* | Fee line items with amounts, dates, invoice numbers |
| `/v4/records/{id}/documents` | GET | Public* | Document list with filenames, categories, dates |
| `/v4/documents/{id}/download` | GET | Public* | Download document content |
| `/v4/records/{id}/workflowTasks` | GET | Public* | Processing status / workflow steps |
| `/v4/records/{id}/related` | GET | Public* | Parent/child record relationships |
| `/v4/records/{id}/conditions` | GET | Public* | Conditions on the record |
| `/v4/records/{id}/customForms` | GET | Public* | ASI (Additional Information) custom fields |
| `/v4/records/{id}/customTables` | GET | Public* | ASI Tables (e.g., Power Provider data) |
| `/v4/settings/records/types` | GET | App Creds | Full record type hierarchy |
| `/v4/settings/inspections/types` | GET | App Creds | All inspection type definitions |
| `/v4/geo/geocode/reverse` | GET | Public* | Reverse geocoding |

*\*"Public" = requires registered App ID + agency code, but no user login.*

### Viability Assessment

**The REST API is the single biggest opportunity for improving our data extraction.** Currently we scrape HTML with regex, which is fragile and misses most fields. The REST API would provide:

1. **Structured JSON** instead of regex-parsed HTML text
2. **All contacts** with full details (name, company, license, phone, email)
3. **Inspection data** (type, date, result, inspector) -- completely unavailable via current scraping
4. **Fee data** with line items and amounts
5. **Document metadata** and download capability
6. **Workflow status** with step-by-step processing history
7. **Related records** (parent/child permit relationships)
8. **Geocoding** (lat/lon currently always null)
9. **Pagination** via offset/limit instead of ViewState postback
10. **Lower breakage risk** -- JSON schema is stable; HTML markup changes break regex

**Blockers**: Requires registering a Citizen App on the Accela Developer Portal to obtain an App ID. The registration is free and self-service. Anonymous/public access is limited to what the agency has configured for anonymous users in Civic Platform -- we would need to test which endpoints POLKCO exposes publicly.

---

## 12. What We Currently Extract vs What's Available

| Data Point | Currently Extracted | Source | Available but Not Extracted | Source |
|-----------|-------------------|--------|---------------------------|--------|
| Permit Number | YES | Search grid link text | -- | -- |
| Address | YES | Search grid cell | Full structured address (street, city, state, zip, unit, direction) | Detail page / REST API |
| Parcel ID | YES | Detail page regex | Block, Lot, Subdivision, Legal Description, Land Value | Detail page / REST API |
| Issue Date | YES | Search grid cell | Opened Date, Closed Date, Completed Date, Estimated Due Date | REST API |
| Status | YES | Search grid cell | Full workflow task history | Processing Status tab / REST API |
| Permit Type | YES | Search grid cell | Full 4-level hierarchy (Group/Type/SubType/Category) | REST API |
| Valuation (Job Value) | YES | Detail page regex | Total Fee, Balance, Total Pay | REST API fees endpoint |
| Subdivision | YES (partial) | Detail page regex | -- | -- |
| Contractor Name | PARTIAL | Detail page regex (often null) | Full name, company, license type, license number, phone, email, fax, address | Detail page / REST API |
| Applicant Name | PARTIAL | Detail page regex | Full name, company, phone, email, mailing address | Detail page / REST API |
| Licensed Professional Name | PARTIAL | Detail page regex | + all subcontractors via "View Additional Licensed Professionals" | Detail page / REST API |
| Latitude/Longitude | ALWAYS NULL | -- | Available via REST API geocoding or address xCoordinate/yCoordinate | REST API |
| Owner Name | YES (regex) | Detail page regex (ACCELA-03) | -- | -- |
| Owner Address | YES (regex) | Detail page regex (ACCELA-03) | Email, phone, owner type (Primary/Secondary/Trust) | REST API owners endpoint |
| Project Description | PARTIAL | Detail page regex | Full text | Detail page / REST API |
| Inspections | NO | -- | Type, date, status, result, inspector, comments | Inspections tab / REST API |
| Fees | NO | -- | Line items, amounts, dates, invoice numbers | Fees tab / REST API |
| Documents | NO | -- | Filenames, types, dates, downloadable content | Attachments tab / REST API |
| Processing Status | NO | -- | Workflow steps, assignees, dates | Processing Status tab / REST API |
| Related Records | NO | -- | Parent/child permit tree | Related Records tab / REST API |
| Conditions | NO | -- | Condition type, status, description | Conditions tab / REST API |
| Application Information (ASI) | NO | -- | Gate code, code violation, NOC, waste acknowledgement, plan submission method, private provider, work type, property type | Detail page expandable sections |
| Power Release Info | NO | -- | Provider, type, release date, released by | Application Information Table |

---

## 13. Known Limitations and Quirks

### Scraping Quirks

1. **Regex extraction is fragile.** The adapter flattens the detail page HTML to text and uses regex to extract parcel, subdivision, applicant, licensed professional, and job value. Any HTML structure change breaks extraction silently (returns null).

2. **Contractor name is often null.** The `raw_contractor_name` falls back from `licensed_professional` to `applicant`, but the regex patterns frequently fail to match because of variations in label text and whitespace.

3. **No coordinates.** Latitude/longitude are always null because the ACA HTML does not expose geocoded coordinates. The REST API does have xCoordinate/yCoordinate on address objects.

4. **ViewState postback pagination.** Search uses ASP.NET postback with `__VIEWSTATE` fields that can be very large (100+ KB). The adapter must maintain a session and replay form fields for each page.

5. **Binary date-range splitting.** When a date range returns >= 100 results (the `search_result_cap`), the adapter recursively splits the range in half. This works but is slow for wide date ranges with many permits.

6. **Search requires record type.** Our adapter sends `Building/Residential/New/NA` as the `ddlGSPermitType`. To expand to other record types, we'd need either multiple passes or the REST API.

7. **Legacy permits require `%` prefix.** Permits from the old Hansen system must be searched with `%` before the number.

### Portal Quirks

8. **Winter Haven (COWH) requires auth.** The Winter Haven Accela portal requires login to access the Building module search. This is an agency-level configuration, not a platform limitation.

9. **Detail page errors.** Some `capID` combinations return a generic error page instead of permit details. The detail page requires valid `capID1`, `capID2`, `capID3` parameters.

10. **Rate limiting.** The Charlotte County (BOCC) portal rate-limits aggressively, requiring a 0.5s delay between detail-page requests. POLKCO does not currently appear to rate-limit but this could change.

11. **Digital Plan Room is separate.** The Digital Plan Room (for plan review documents) is a separate interface from the Attachments tab. It has its own tabs (Record Details, Summary, Uploads, Issues, Conditions, Approved Plans) and review cycle workflow.

12. **Fee data is session-dependent.** The Fees section appears to lazy-load ("Loading...") on the detail page, meaning a simple GET may not capture fee data without JavaScript execution. The REST API would bypass this entirely.

13. **Inspection scheduling requires login.** While inspection data is *viewable* without login, scheduling/rescheduling/canceling requires authentication. Cancellation and reschedule cutoff is 06:00 AM same day.

14. **Reports require login.** The Reports dropdown (11 report types including Permit Card, CO/CC certificates, customer request lists) requires a logged-in session. Reports generate PDFs via a separate report server at `aca.polk-county.net/aca/Report/`.

### Available Reports (login required)
- Building Comment
- Commercial Multi-Family Customer Request
- Commercial New Customer Request
- Commercial Renovation Customer Request
- Permit Card
- Residential Accessory Customer Request
- Residential New Customer Request
- Residential Renovation Customer Request
- Solid Waste Impact Fees
- Trade Pool Customer Request
- Trust Account Transactions
