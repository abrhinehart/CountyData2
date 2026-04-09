# Madison County AL Probate Records Portal - Technical Findings

**Portal URL:** https://madisonprobate.countygovservices.com/  
**Date explored:** 2026-04-08  
**Authentication:** Azure AD B2C (madisoncountyalntc.b2clogin.com)

---

## 1. Authentication Flow

### B2C Configuration
- **Tenant:** madisoncountyalntc.onmicrosoft.com
- **Policy:** B2C_1_signupsignin1
- **Client ID:** 39401322-58ff-4dac-ad77-e7f86e31306b
- **Redirect URI:** https://madisonprobate.countygovservices.com/signin-oidc
- **Response type:** code (authorization code flow, NOT implicit)
- **Response mode:** form_post
- **Scopes:** openid profile offline_access
- **Client library:** ID_NET8_0 v8.7.0.0 (ASP.NET Core OpenID Connect)

### Login Steps
1. `GET /` returns 302 to B2C authorize URL with state + nonce. Sets cookies: `.AspNetCore.OpenIdConnect.Nonce.*`, `.AspNetCore.Correlation.*`, `ARRAffinity`, `ARRAffinitySameSite`.
2. `GET` the B2C authorize URL returns the login HTML page. The page uses a **custom UI** hosted at `https://tagitnitorco.blob.core.windows.net/adbc2customui/Madison/MSA/unified.html`. Sets B2C cookies: `x-ms-cpim-sso`, `x-ms-cpim-csrf`, `x-ms-cpim-cache|*`, `x-ms-cpim-trans`.
3. Extract from page JS: `SETTINGS.csrf` (CSRF token), `SETTINGS.transId` (transaction ID), `SA_FIELDS` (login field definitions).
4. **POST** to `/SelfAsserted?tx={transId}&p=B2C_1_signupsignin1` with:
   - Headers: `X-CSRF-TOKEN`, `X-Requested-With: XMLHttpRequest`, `Content-Type: application/x-www-form-urlencoded`
   - Body: `request_type=RESPONSE&email={email}&password={password}`
   - **IMPORTANT:** Field name is `email` (not `signInName` or `logonIdentifier`). The SA_FIELDS config confirms `ID=email`.
   - Success response: `{"status":"200"}`
5. **GET** `/api/CombinedSigninAndSignup/confirmed?rememberMe=false&csrf_token={csrf}&tx={tx}&p=B2C_1_signupsignin1`
   - Returns an HTML auto-submit form with `action=https://madisonprobate.countygovservices.com/signin-oidc`
   - Hidden fields: `state` and `code` (authorization code, ~879 chars)
6. **POST** the code and state to `/signin-oidc`
   - Returns 302 -> `/` -> 302 -> `/Home/Requirements`
   - Sets `.AspNetCore.Cookies` (session cookie) and `.AspNetCore.Antiforgery.cdV5uW_Ejgc`

### Terms Acceptance
- Landing page after auth: `/Home/Requirements` (terms and conditions)
- Must POST to `/Home/Requirements` with `TermsAccepted=true` and `__RequestVerificationToken`
- After acceptance, redirects to `/Search/Menu`
- Terms text: "Documents on this site are free to search and view."

### No MFA
- No MFA/2FA was encountered during authentication.

---

## 2. Application Architecture

- **Framework:** ASP.NET Core (.NET 8)
- **UI Components:** Telerik Kendo UI for ASP.NET Core (v2025.4.1111)
- **JS Libraries:** jQuery 3.7.1, jQuery UI 1.13.2, jQuery Validate, Modernizr 2.8.3
- **Real-time:** SignalR (used for download progress notifications via `/pwnotifyhub`)
- **Hosting:** Azure (IIS 10.0), ARR Affinity enabled
- **Telemetry:** Application Insights
- **Notification toasts:** toastr.js 2.1.4
- **Phone input:** intl-tel-input 23.8.0
- **Icons:** Font Awesome Pro
- **CSS framework:** Bootstrap 5.3.8

---

## 3. Search Types (Categories)

### Page 1
| Key | Title | Description | Date Range |
|-----|-------|-------------|------------|
| `all_books` | ALL RECORDS | Search All Records | (all available) |
| `all_recorded_docs` | RECORDED DOCUMENTS | Search All Recorded Documents and Historical Records | 5/1/1991 - 4/7/2026 |
| `probate_court` | COURT CASES | Search Public Court Cases | (error - not available) |

### Page 2
| Key | Title | Description | Date Range |
|-----|-------|-------------|------------|
| `deed` | DEEDS | Search Deeds | 5/1/1991 - 4/7/2026 |
| `mortgage` | MORTGAGES | Search the Mortgages Book | 5/1/1991 - 4/7/2026 |
| `judgment` | JUDGMENTS | Search Judgments | 5/1/1991 - 4/7/2026 |
| `ucc` | UCC | Search UCC Filings | 5/1/1991 - 4/7/2026 |
| `misc` | MISCELLANEOUS | Search Miscellaneous Book | 5/1/1991 - 4/7/2026 |
| `tax_sales` | TAX SALES | Search Tax Sales | 5/1/1991 - 4/7/2026 |
| `marriage` | MARRIAGE LICENSES | Search Marriage Licenses | 4/19/2004 - 4/7/2026 |
| `bond` | BONDS | Search Probate Bonds | 5/1/1991 - 4/7/2026 |
| `plat` | PLATS | Search Plat Diagrams and Maps | 5/2/1991 - 4/7/2026 |
| `military_discharge` | MILITARY DISCHARGES | Search Military Discharges | 5/1/1991 - 4/7/2026 |
| `historical_indexes` | ARCHIVED INDEXES | Search Archived Land & Marriage Indexes | 1/1/1800 - 4/30/2004 |
| `all_pages` | ARCHIVED NON-INDEXED BOOKS | Search Archived Non-Indexed Record Books | (varies) |

### Page 3
| Key | Title |
|-----|-------|
| `all_books` | (same as page 1) |
| `all_recorded_docs` | (same as page 1) |
| `probate_court` | (same as page 1) |
| `names` | Names search |

### Special: Names Search (`/Search/Names`)
- Separate search page for cross-referencing names
- Fields: `AllNamesOne` (name), `StartDate`, `EndDate`
- Uses `__RequestVerificationToken` (POST-based)

---

## 4. Search Form Parameters

### Standard Search Form (e.g., `all_books`, `deed`, `mortgage`)
Form action: `GET /Search/SearchResults`

| Field Name | Type | Description | Notes |
|-----------|------|-------------|-------|
| `SearchQueryId` | hidden | GUID for the search session | Auto-generated per page load |
| `SearchType` | hidden | Search category key | e.g., `deed`, `mortgage`, `all_books` |
| `AllNamesOne` | text | First name search | Placeholder: "Last First Middle", max 100 chars |
| `AllNameOneMatchType` | select | Match type for name 1 | Values: `begins`, `contains`, `exact` |
| `AllNameOneDirectionID` | dropdown | Name direction filter | 0=ANY, 1=DIRECT, 2=REVERSE |
| `AllNamesTwo` | text | Second name search | Same format as AllNamesOne |
| `AllNameTwoMatchType` | select | Match type for name 2 | Same options |
| `AllNameTwoDirectionID` | dropdown | Name direction filter | Same options |
| `Description` | text | Legal description search | max 255 chars |
| `BookNumber` | text | Book number | max 25 chars |
| `DocNumber` | text | First page number | max 25 chars (labeled "First Page #") |
| `InstrumentTypeID` | dropdown | Instrument type filter | Kendo DropDownList, 725 types total |
| `StartDate` | date | Date range start | Kendo DatePicker, format MM/dd/yyyy |
| `EndDate` | date | Date range end | Kendo DatePicker, format MM/dd/yyyy |
| `ShowIndividuals` | checkbox | Show doc names on separate rows | Default: false |

### Grid Columns (Deed Search)
| Field | Header | Width |
|-------|--------|-------|
| `iID` | Actions (VIEW button) | 5% |
| `bkNAME` | Book # | 5% |
| `iNUMBER` | First Page # | 5% |
| `Name1` | Grantor | 22% |
| `Name2` | Grantee | 23% |
| `itNAME` | Instrument | 10% |
| `iPAGES` | Pages | 5% |
| `iRECORDED` | Recorded On | 5% |
| `iDESC` | Legal Description | (remaining) |

### Grid Columns (All Books Search)
| Field | Header | Width |
|-------|--------|-------|
| `iID` | Actions | 5% |
| `bktNAME` | Book | 5% |
| `bkNAME` | Book # | 5% |
| `iNUMBER` | First Page # | 5% |
| `bNAME` | Name | 15% |
| `btNAME` | Class | 5% |
| `OtherNames` | Other Names | 25% |
| `itNAME` | Instrument | 20% |
| `iDESC` | Legal Description | 20% |
| `iRECORDED` | Recorded On | 5% |
| `iPAGES` | Pages | (auto) |

---

## 5. Search Results API

### Endpoint
**POST** `/Search/SearchResultsGrid`

### Critical Parameters
The Kendo Grid uses `aspnetmvc-ajax` transport type. The `query` and `qid` parameters are **required** and must be extracted from the results page HTML.

```
POST /Search/SearchResultsGrid
Content-Type: application/x-www-form-urlencoded
X-Requested-With: XMLHttpRequest

sort=&page=1&pageSize=50&group=&filter=&query={encoded_query}&qid={search_query_id}
```

### Query Parameter Format
The `query` parameter is a colon-separated key=value string, URL-encoded:
```
SearchType=deed:AllNamesOne=:AllNamesTwo=:NameOne=:NameTwo=:NameThree=:
DocNumber=:SubDiv=:Debtor=:Secured=:CaseTypeID=:CaseYear=:CaseNumber=:
CaseDec=:Description=:BookNumber=:InstrumentTypeID=0:BookTypeID=0:
IndexBookTypeID=:BookID=0:StartDate=4/1/2026:EndDate=4/8/2026:
IncludeMarriageIndex=true:IncludeProbateIndex=true:
IncludeAllLandRecords=false:ShowIndividuals=false:bkName=:
AllNameOneDirectionID=0:AllNameTwoDirectionID=0:
AllNameOneMatchType=begins:AllNameTwoMatchType=begins:
NameOneMatchType=:NameTwoMatchType=:NameThreeMatchType=
```

The `qid` is the `SearchQueryId` GUID from the `data-searchqueryid` attribute on the results page.

### Workflow
1. `GET /Search/SearchType?key={key}` to get search form with `SearchQueryId`
2. `GET /Search/SearchResults?{params}` to submit search and get results page
3. Extract `query` string and `qid` from the Kendo Grid config in the results page HTML
4. `POST /Search/SearchResultsGrid` with `query`, `qid`, and pagination params to get JSON data

### Response Format
```json
{
  "Data": [ ... ],
  "Total": 613,
  "AggregateResults": null,
  "Errors": null
}
```

### Result Row Fields (Complete)
| Field | Type | Description |
|-------|------|-------------|
| `total_count` | int | Total result count (in every row) |
| `iID` | int | Instrument ID (primary key, used for VIEW) |
| `iNUMBER` | string | First page number |
| `iPAGES` | int | Number of pages in document |
| `iRECORDED` | string | Recording date/time (ISO 8601) |
| `iDESC` | string | Legal description |
| `iPAGES_TOTAL` | int | Total pages |
| `idVALUE_MORT` | float | Mortgage value |
| `idVALUE_SUBDIV` | string | Subdivision value |
| `idVALUE_UCC` | float | UCC value |
| `idVALUE_JUDG` | float | Judgment value |
| `bktNAME` | string | Book type name (e.g., "Deed", "Mortgage") |
| `bktID` | int | Book type ID |
| `bktPRIVATE` | bool | Whether book is private |
| `bkID` | int | Book ID |
| `bkNAME` | string | Book name (typically year, e.g., "2026") |
| `itID` | int | Instrument type ID |
| `itNAME` | string | Instrument type name |
| `iltID` | int | Instrument life type ID |
| `iltNAME` | string | Instrument life type name (e.g., "Active") |
| `iltISACTIVE` | bool | Whether instrument is active |
| `iltISVOID` | bool | Whether instrument is void |
| `Claim_Amt` | float | Claim amount |
| `Terminated` | string | Termination status |
| `TerminationDate` | string | Termination date |
| `Lots` | string | Lot numbers |
| `Slide` | string | Slide reference |
| `pcID` | int | Probate case ID |
| `pcNUM` | string | Probate case number |
| `pctID` | int | Probate case type ID |
| `pcsID` | int | Probate case status ID |
| `pctNAME` | string | Probate case type name |
| `FileDate` | string | File date (ISO 8601) |
| `Finalized` | string | Finalization date |
| `Redeem` | string | Redemption info |
| `WeddingDate` | string | Wedding date (for marriage records) |
| `bID` | int | Binding/entity ID |
| `bNAME` | string | Primary name (first name on instrument) |
| `btNAME` | string | Name class (e.g., "Grantor", "Grantee") |
| `OtherNames` | string | Other names on instrument |
| `Name1` | string | First party names (HTML, `<br/>` separated) |
| `Name2` | string | Second party names (HTML, `<br/>` separated) |

### Pagination
- Page sizes: 50, 100, 500
- Default page size: 500 (configured in grid)
- Pageable with refresh button
- Sort: multiple column sort supported, default sort by `iRECORDED` ascending
- Filter: column-level filtering supported via Kendo column menu

---

## 6. Document Viewing

### View Instrument
`GET /Search/ViewInstrument?iID={instrumentId}`

Returns an HTML page with:
- Instrument metadata (book name, book number, instrument type, first page #, page count, recorded date)
- Forward/Reverse name lists (Grantor/Grantee)
- Legal description
- **Thumbnail images** of each page

### Page Images
`GET /Search/Image?pageId={pageId}&thumbnail=true` - thumbnail image
`GET /Search/Image?pageId={pageId}` - likely full-size image (inferred)

### Document Actions (from data-* attributes)
| Endpoint | Description |
|----------|-------------|
| `/Document/HandleDownloadPage` | Download single page |
| `/Document/HandlePrintPage` | Print single page |
| `/Document/HandleDownloadInstrument` | Download full instrument |
| `/Document/HandlePrintInstrument` | Print full instrument |
| `/Document/AddPageToCart` | Add page to shopping cart |
| `/Document/AccountPurchasePage` | Purchase page via account |
| `/Document/AddInstrumentToCart` | Add instrument to cart |
| `/Document/AccountPurchaseInst` | Purchase instrument via account |
| `/Search/ViewNextInstFromPage` | Navigate to next instrument |
| `/Search/ViewPrevInstFromPage` | Navigate to previous instrument |

---

## 7. Additional Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/Search/Menu` | GET | Search type menu page |
| `/Search/SearchType?key={key}` | GET | Search form for a specific type |
| `/Search/SearchResults` | GET | Submit search and render results page |
| `/Search/SearchResultsGrid` | POST | AJAX grid data (JSON) |
| `/Search/GetIndexBooks?bktID={id}` | GET | Get books for a book type (index search) |
| `/Search/GetAllPagesBooks?bktID={id}` | GET | Get books for a book type (all pages search) |
| `/Search/UpdateSearchTypeOrder` | POST | Save user's menu card order |
| `/Search/UpdateGridSorting` | POST | Save grid sort state |
| `/Search/UpdateGridPaging` | POST | Save grid page index |
| `/Search/DownloadResults` | POST | Export results to Excel (uses SignalR for progress) |
| `/Search/ViewInstrument?iID={id}` | GET | View instrument detail page |
| `/Search/ViewPage?ipID={id}` | GET | View single page |
| `/Search/Image?pageId={id}` | GET | Get page image |
| `/Search/Names` | GET/POST | Cross-reference name search |
| `/ProbateCourt/Public/ViewCasePublic?pcID={id}` | GET | View public court case |

---

## 8. Rate Limiting

- **No rate limiting detected.** Two consecutive search requests completed in ~0.5s each with no throttling or 429 responses.
- SignalR is used for download progress (not for search results delivery - searches are synchronous).

---

## 9. Instrument Types Summary

725 total instrument types across 16 book categories:

| Category | Count | Examples |
|----------|-------|---------|
| (HISTORICAL) LAND RECORDS | 313 | Deed, Mortgage, Assignment, Affidavit, Plat, etc. |
| DEED | 86 | Deed, Warranty Deed, Quit Claim, Affidavit of Death & Heirship |
| MISCELLANEOUS | 67 | Power of Attorney, Articles of Organization, Certificate |
| JUDGMENT | 49 | Certificate of Judgment, Tax Lien, Lis Pendens |
| PROBATE | 48 | Will, Bond, Petition, Letters of Administration |
| MORTGAGE | 46 | Mortgage, Assignment, Release, Subordination |
| MINUTES | 46 | Order, Notice, Decree, Motion |
| BOND | 13 | Oath of Office, Notary Bond, Contractors Bond |
| PLAT | 12 | Plat, Amended Plat, Vacation of Plat |
| (HISTORICAL) FINANCE STATEMENTS | 9 | UCC1, UCC3, Voided Financing Statement |
| MARRIAGE | 8 | Marriage Certificate, Marriage Correction |
| UCC | 7 | UCC1, UCC3 Amend/Assign/Term |
| TAX SALE | 6 | Tax Sale, Land Redemption, Certificate of Redemption |
| WILL | 5 | Last Will and Testament, Copy of Will |
| CLAIMS | 4 | Claim Against Estate, Satisfaction of Claim |
| (HISTORICAL) MCRC | 2 | Chancery Court, Probate |
| (HISTORICAL) NOTARY | 2 | Official Bond - Notary |
| (HISTORICAL) SUBDIVISION RESTRICTION | 1 | Subdivision Restrictions |

---

## 10. Key Technical Notes for Automation

1. **Cookie jar is essential.** The session uses `.AspNetCore.Cookies` for auth and `ARRAffinity` for server affinity.
2. **Terms must be accepted** each session via POST with anti-forgery token.
3. **Grid data requires `query` + `qid` parameters** extracted from the results page HTML. Without these, the grid returns Total: 0.
4. **The `query` parameter uses colon-separated key=value format**, not standard query string format.
5. **Names in results use `<br/>` as separator** for multiple names on one side of a transaction.
6. **Instrument IDs (`iID`) are large integers** (e.g., 174904136) used as primary keys for document viewing.
7. **Page IDs** from the ViewInstrument page are used to fetch images.
8. **No PKCE or client_secret** is needed - the app uses server-side authorization code flow.
9. **Documents appear to be free** to search and view (per terms page text).
10. **SignalR hub at `/pwnotifyhub`** is used for Excel export progress notifications only.
