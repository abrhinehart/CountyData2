# Polk County FL -- iWorQ Permit Portals API Map (PT: East Polk Cities)

Last updated: 2026-04-14

## 1. Portal Overview

| Property | Value |
|----------|-------|
| Platform | iWorQ (permit management SaaS) |
| Protocol | HTML scraping (no REST API) |
| Auth | Anonymous search and detail view |
| Parser | BeautifulSoup (html.parser) |

### East Polk Cities -- Platform Summary

Five east Polk County municipalities were onboarded for permit tracking. Three use iWorQ; two use Accela Citizen Access.

| City | Platform | Adapter | Search URL / Agency Code | Notes |
|------|----------|---------|--------------------------|-------|
| Davenport | **iWorQ** | `DavenportAdapter` | `https://portal.iworq.net/DAVENPORT/permits/600` | Live, 10-column layout |
| Haines City | **iWorQ** | `HainesCityAdapter` | `https://haines.portal.iworq.net/HAINES/permits/600` | Live, 10-column layout (no type column) |
| Lake Hamilton | **iWorQ** | `LakeHamiltonAdapter` | `https://townoflakehamilton.portal.iworq.net/LAKEHAMILTON/permits/600` | `scrape_mode='fixture'` — portal uses reCAPTCHA and has no date-range search; needs browser-based scraper |
| Lake Alfred | Accela (ACA) | `LakeAlfredAdapter` | Agency code `COLA` | See polk-county-accela.md |
| Winter Haven | Accela (ACA) | `WinterHavenAdapter` | Agency code `COWH` | Requires auth; returns 0 permits until auth support added |

**This document covers only the three iWorQ cities.** Lake Alfred and Winter Haven use the same Accela Citizen Access platform documented in `polk-county-accela.md`.

---

## 2. Search Capabilities

### URL Pattern

```
https://{subdomain}.portal.iworq.net/{TENANT}/permits/600?searchField=permit_dt_range&startDate={YYYY-MM-DD}&endDate={YYYY-MM-DD}&page={N}
```

For Davenport, the subdomain pattern differs slightly:
```
https://portal.iworq.net/DAVENPORT/permits/600
```

### Query Parameters

| Parameter | Required? | Value | Notes |
|-----------|-----------|-------|-------|
| `searchField` | YES | `permit_dt_range` | Fixed; search by date range |
| `startDate` | YES | `YYYY-MM-DD` | Start of date range |
| `endDate` | YES | `YYYY-MM-DD` | End of date range |
| `page` | NO | Integer >= 2 | Omitted for page 1 |

### Pagination

The adapter extracts the max page number from `ul.pagination a[href]` links by parsing the `page` query parameter. It iterates from page 1 through max page, fetching each page as a full HTML document.

### Default Date Ranges

| Mode | Lookback |
|------|----------|
| Bootstrap | 120 days (`bootstrap_lookback_days`) |
| Rolling | 14 days overlap (`rolling_overlap_days`) |

### Request Headers

```
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ...
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8
Accept-Language: en-US,en;q=0.9
```

---

## 3. Search Results Grid

The search results page renders an HTML `table.table.table-sm`. Each result row has a `<th>` cell (permit number) and `<td>` cells for remaining columns. The column layout varies by city.

### Davenport (10 columns)

| Index | Column | Extracted? | Maps To |
|-------|--------|-----------|---------|
| TH | Permit # | YES | `permit_number` |
| 0 | Date | YES | `issue_date_str` |
| 1 | Primary Contractor | YES | `contractor_hint` |
| 2 | Applicant Name | NO (at grid level) | -- |
| 3 | Site Address | YES | `address` |
| 4 | Lot | NO | -- |
| 5 | Description | YES | `permit_type` (type filter) |
| 6 | Project Cost | YES | `valuation_hint` |
| 7 | Permit Status | YES | `status` |
| 8 | Request An Inspection | NO | -- |
| 9 | View | NO | -- |

### Haines City (10 columns)

| Index | Column | Extracted? | Maps To |
|-------|--------|-----------|---------|
| TH | Permit # | YES | `permit_number` |
| 0 | Date | YES | `issue_date_str` |
| 1 | Planning/Zoning Status | NO | -- |
| 2 | Application Status | YES | `status` |
| 3 | Fire Marshall Review Status | NO | -- |
| 4 | Building Plan Review Status | NO | -- |
| 5 | Site Address | YES | `address` (combined with col 6) |
| 6 | Site City/State/Zip | YES | Appended to `address` |
| 7 | Project Name | NO (at grid level) | -- |
| 8 | Request Inspection | NO | -- |
| 9 | View | NO | -- |

**No permit type column.** Type filtering is deferred to the detail page -- the adapter checks the `Description` or `Permit Type` field from the detail page.

**No contractor column.** Contractor name is only available on the detail page.

### Lake Hamilton (default IworqAdapter layout)

Uses the base `IworqAdapter._extract_row_fields` with a minimum of 6 columns:

| Index | Column | Extracted? | Maps To |
|-------|--------|-----------|---------|
| TH | Permit # | YES | `permit_number` |
| 0 | Date | YES | `issue_date_str` |
| 1 | Type | YES | `permit_type` |
| 2 | Address | YES | `address` |
| 3 | (unknown) | NO | -- |
| 4 | Status | YES | `status` |
| 5 | Contractor | YES | `contractor_hint` |

**Note:** This column mapping is the default base class assumption and has not been verified against the live Lake Hamilton portal.

---

## 4. Detail Page Fields

Detail pages are fetched for every matching row and parsed by selecting `div.row > div.col` pairs (label-value).

### Extraction Pattern

```python
for row in soup.select("div.row"):
    cols = row.select(":scope > div.col")
    if len(cols) != 2:
        continue
    label = cols[0].get_text(" ", strip=True).rstrip(":")
    value = cols[1].get_text(" ", strip=True)
```

Additionally, `Parcel #` is extracted via regex: `Parcel #:\s*([A-Z0-9-]+)`.

### Known Detail Page Fields (from adapter code)

These are the field labels the adapter explicitly reads from detail pages:

| Detail Field Label | Extracted? | Maps To | Notes |
|--------------------|-----------|---------|-------|
| Parcel # | YES | `parcel_id` | Via regex, not div.row pattern |
| Issued/Paid Date | YES | `issue_date` (fallback) | Parsed to YYYY-MM-DD |
| Permit Date | YES | `issue_date` (fallback) | Parsed to YYYY-MM-DD |
| Status | YES | `status` (override) | Overrides grid status |
| Permit Type | YES | `permit_type` (override/filter) | Used when grid has no type column |
| Description | YES | `permit_type` (fallback for filter) | Alternative type label |
| Valuation | YES | `valuation` | Cleaned of `$` and `,`, parsed to float |
| NSFR Construction Cost | YES | `valuation` (fallback) | New Single Family Residential cost |
| Project Name | YES | `raw_subdivision_name` | Subdivision or development name |
| Applicant | YES | `raw_contractor_name` (fallback) | When grid contractor is empty |
| Applicant Name | YES | `raw_contractor_name` (fallback) | Alternative label |

### Fields Available but Not Extracted

Detail pages typically contain additional div.row label-value pairs that the adapter does not specifically target. Because the parsing captures all pairs into a `fields` dict, any label-value pair present on the page is technically accessible. However, only the labels listed above are explicitly used to populate output fields. Other commonly observed labels on iWorQ detail pages include: Owner, Lot, Block, Subdivision, Square Footage, Number of Stories, Bedrooms, Bathrooms, and various inspection status fields.

---

## 5. Type Filtering Logic

The adapter uses a two-stage type filter to identify residential new construction permits.

### Excluded Terms (skip if present)

```
plumbing, mechanical, electrical, change out, sign, pool, spa, solar, roof,
reroof, demo, demolition, repair, renov, alter, addition, fence, dock,
seawall, gas
```

### Residential Terms (require at least one)

```
single family, residential building, res new, new dwelling, dwelling, house,
home, new sfr, sfr
```

A permit passes the filter if it contains **none** of the excluded terms AND **at least one** of the residential terms. Matching is case-insensitive.

When the search results grid has a type column (Davenport, Lake Hamilton default), filtering happens at the grid level. When the grid has no type column (Haines City), filtering is deferred to the detail page `Description` or `Permit Type` field.

---

## 6. What We Extract

Final permit output from the iWorQ adapter:

| Output Field | Primary Source | Fallback Source(s) |
|-------------|---------------|-------------------|
| `permit_number` | Grid TH cell | -- |
| `address` | Grid address cell | -- |
| `parcel_id` | Detail page `Parcel #` regex | -- |
| `issue_date` | Detail `Issued/Paid Date` or `Permit Date` | Grid date cell (MM/DD/YYYY -> ISO) |
| `status` | Detail `Status` | Grid status cell |
| `permit_type` | Detail `Permit Type` | Grid type cell or Detail `Description` |
| `valuation` | Detail `Valuation` | Detail `NSFR Construction Cost` or Grid `valuation_hint` |
| `raw_subdivision_name` | Detail `Project Name` | -- |
| `raw_contractor_name` | Grid contractor cell | Detail `Applicant` or `Applicant Name` |
| `latitude` | -- | Always `None` |
| `longitude` | -- | Always `None` |

---

## 7. What We Extract vs What's Available

| Data Category | Currently Extracted | Source | Available but Not Extracted | Source |
|--------------|--------------------|---------|-----------------------------|--------|
| Permit Number | YES | Grid TH | -- | -- |
| Address | YES | Grid cell | City/State/Zip (Haines City has separate columns) | Grid cell 6 (HC) |
| Parcel ID | YES | Detail regex | -- | -- |
| Issue Date | YES | Detail or grid | -- | -- |
| Status | YES | Detail or grid | Planning/Zoning status, Fire Marshall status, Building Plan Review status | Grid cells (HC) |
| Permit Type | YES | Detail or grid | -- | -- |
| Valuation | YES | Detail page | -- | -- |
| Subdivision | YES | Detail `Project Name` | -- | -- |
| Contractor | PARTIAL | Grid (Davenport) | Only on detail page for Haines City | Detail page |
| Applicant Name | PARTIAL (as contractor fallback) | Detail page | Full applicant info | Detail page |
| Lot | NO | -- | Lot number | Grid cell 4 (Davenport), Detail page |
| Owner | NO | -- | Property owner name | Detail page |
| Square Footage | NO | -- | Building square footage | Detail page |
| Inspection Status | NO | -- | Inspection request links, statuses | Grid cells, Detail page |
| Coordinates | NO (always null) | -- | Not available from portal | No geocoding service |

---

## 8. Known Limitations and Quirks

1. **No API.** iWorQ does not provide a REST or SOAP API. All data is obtained by scraping HTML search results and detail pages. This makes the adapter fragile to markup changes.

2. **No geocoding.** The iWorQ portal does not provide latitude/longitude coordinates. The adapter always returns `null` for both. Unlike Accela (which has a REST API with coordinates) or ArcGIS (which provides geometry), there is no built-in way to geocode iWorQ permits without an external geocoding service.

3. **Column layout varies by city.** Each city's iWorQ portal has a different column layout in the search results table. Davenport has contractor and cost columns; Haines City has multiple review status columns but no type or contractor column. Each city subclass overrides `_extract_row_fields` to handle its layout.

4. **Lake Hamilton blocked by reCAPTCHA.** Deployed as `scrape_mode='fixture'` with `fragile_note='iWorQ portal uses reCAPTCHA and has no date-range search. Needs browser-based scraper.'` (see `seed_pt_jurisdiction_config.py:72`). The search URL `https://townoflakehamilton.portal.iworq.net/LAKEHAMILTON/permits/600` follows the standard iWorQ pattern, and the research found a landing page at `townoflakehamilton.portal.iworq.net/portalhome/townoflakehamilton`, but the path cannot be exercised programmatically without a browser-based captcha solver. The HTTP-based `LakeHamiltonAdapter` is kept in-tree for when that blocker is resolved; until then the jurisdiction runs off fixtures.

5. **Lake Hamilton uses default column mapping.** The `LakeHamiltonAdapter` does not override `_extract_row_fields`, so it uses the base class's 6-column assumption. If the actual portal has a different layout (like Haines City's 10-column layout), extraction will be wrong or will skip rows. This cannot be verified until the reCAPTCHA blocker above is resolved.

6. **Detail page fetch for every row.** The adapter fetches the detail page for every search result row, even rows that will be filtered out by type. For Haines City (no type column in grid), this is unavoidable. For Davenport, type filtering happens at the grid level, so detail pages are only fetched for rows that pass the filter.

7. **Date format assumption.** The adapter assumes `MM/DD/YYYY` format for grid dates and detail page dates. If a city's portal uses a different format, parsing will fail silently and return the raw string.

8. **No pagination delay.** Unlike the Legistar scraper (0.5s) and the GIS engine (adaptive delay), the iWorQ adapter does not insert delays between page fetches or detail page requests. This could be problematic at scale but has not caused issues with the small permit volumes in these east Polk cities.

9. **Valuation field name varies.** Davenport's grid shows "Project Cost" in the table and the detail page may use "Valuation" or "NSFR Construction Cost". The adapter checks both labels, but other cities might use yet another label.

10. **Winter Haven (Accela) requires auth.** Although listed as an east Polk city, Winter Haven uses Accela with agency code COWH, which requires login to access the Building module search. The `WinterHavenAdapter` currently returns 0 permits. This is an Accela limitation, not an iWorQ limitation, but is noted here for completeness.

11. **Haines City address concatenation.** Haines City splits the address across two columns (Site Address + Site City/State/Zip). The adapter concatenates them with a comma separator, but if either column is empty the result may have a leading or trailing comma (mitigated by `.strip(", ")`).
