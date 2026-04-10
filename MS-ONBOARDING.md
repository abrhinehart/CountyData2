# Mississippi County Onboarding Guide

How to add a new Mississippi county to CountyData2. Covers investigation, portal identification, GIS evaluation, and configuration — informed by lessons learned from onboarding 6 counties across 4 portal types.

---

## Step 1: Investigate the GIS Layer First

Before touching the deed portal, check the county's ArcGIS parcel layer. This is the single most important step — Jackson County taught us that a rich GIS layer can replace a difficult portal entirely.

### 1a. Find the Parcel Layer

Search for `{county} mississippi GIS parcels` or check the county website for a GIS viewer. Common hosts by region:

| Region | Host | Counties |
|--------|------|----------|
| Jackson metro | `gis.cmpdd.org` (CMPDD) | Madison, Rankin, Hinds |
| Gulf Coast | County-hosted (`geo.co.{name}.ms.us`, `webmap.co.{name}.ms.us`) | Harrison, Jackson |
| Memphis metro | ArcGIS Online (`services6.arcgis.com`) | DeSoto |

### 1b. Check What Fields Exist

```bash
curl -s "{gis_url}?f=json" | python -c "
import sys, json
data = json.load(sys.stdin)
print(f'Layer: {data.get(\"name\")}  Max records: {data.get(\"maxRecordCount\")}')
for f in data.get('fields', []):
    print(f'  {f[\"name\"]:25s} {f[\"type\"]}')" | grep -iE 'deed|book|page|owner|addr|acre|value|sub|sale|samt|sdat|legal|desc|loc'
```

Look for these critical fields:

| Field | Why It Matters | Example Names |
|-------|---------------|---------------|
| **Deed book/page** | Cross-ref to deed portal records | `deed_book`/`deed_page`, `DB`/`DP`, `DEED_BOOK1`/`DEED_PAGE1` |
| **Sale date** | Query by date range (GIS-only approach) | `SDAT`, `sale_date` |
| **Sale amount** | Actual prices (rare in non-disclosure state) | `SAMT`, `sale_amount`, `sales_amt` |
| **Owner** | Current parcel owner | `NAME`, `name`, `OWNER_NAME`, `ownerCalc` |
| **Address** | Situs/physical address | `LOCATION`, `FULL_ADDR`, `addCalc`, `street_number`+`street_name` |
| **Subdivision** | Platted subdivision name | `SUBD`, `sub_name`, `SUBD_NAME`, `description_1` |
| **Legal description** | Free text legal | `DESC1`, `legal1`, `extended_legal001`, `LEGLDESC` |
| **Acreage** | Parcel size | `ACREAGE`, `CALC_ACRE`, `arcacres`, `total_acres` |

### 1c. Test a Query

```bash
# Check total parcel count
curl -s "{gis_url}/query?where=1%3D1&returnCountOnly=true&f=json"

# Sample data quality (skip to mid-dataset to avoid empty header records)
curl -s "{gis_url}/query" -d "where=1=1" -d "outFields=*" -d "f=json" -d "resultRecordCount=5" -d "resultOffset=5000"
```

### 1d. Evaluate: Can GIS Be the Primary Source?

The GIS layer can replace the deed portal when it has:
- Sale date field for date-range queries
- Owner names
- Deed book/page (for dedup and cross-referencing)
- Legal descriptions or subdivision names
- Polygon geometry (centroid lat/lon)

**Jackson County example**: GIS had all of the above plus sale amounts. The deed portal (Aumentum Recorder with ASP.NET WebForms/Infragistics) would have required a complex new client. GIS-only was the right call — simpler code, richer data.

---

## Step 2: Identify the Deed Portal Type

Visit the county Chancery Clerk website and find their online land records search. Known portal types in Mississippi:

| Portal | How to Identify | Automation | Counties |
|--------|----------------|------------|----------|
| **DuProcess** | URL contains `/DuProcessWebInquiry`. Infragistics grid, JSON API at `/Home/CriteriaSearch`. | Straightforward — JSON API, auto-detected book types | Madison, Rankin, Harrison + Forrest, Pearl River, George, Monroe, Lee, Noxubee |
| **AcclaimWeb** | URL contains `/AcclaimWeb`. Telerik grid, ASP.NET MVC. | Moderate — 3-step POST flow, `curl_cffi` needed | DeSoto |
| **GIndex** | URL contains `/gindex_query.asp`. Bare HTML tables, ASP Classic. | Simple HTML scraping, `curl_cffi` for TLS | Hinds |
| **Aumentum Recorder** | ASP.NET WebForms, Infragistics controls, ViewState postbacks. | **Too complex** — check GIS layer instead | Jackson (skipped in favor of GIS) |
| **GIS Parcel** | No portal used. ArcGIS parcel layer queried directly by sale date. | Simplest — standard ArcGIS REST queries | Jackson |

If you encounter a portal type not listed here, check the GIS layer first. If the GIS has sale dates and deed references, use the GIS Parcel approach. Only build a new portal client if the GIS layer is insufficient.

---

## Step 3: Test Access

```bash
# DuProcess
curl -s "http://{portal_url}/" | head -5
curl -s "http://{portal_url}/Lookup/BookTypeLookup" | python -m json.tool

# AcclaimWeb
curl -s "https://{portal_url}/search/SearchTypeDocType" | head -5

# GIndex
curl -s "https://{portal_url}/gindex_query.asp" | head -5

# GIS layer
curl -s "{gis_url}/query?where=1%3D1&returnCountOnly=true&f=json"
```

**TLS check**: If `curl` works but Python `requests` gets `ConnectionResetError`, the site rejects Python's TLS fingerprint. Use `curl_cffi` with `impersonate='chrome'`. This happened with Hinds (GIndex) and Jackson (GIS). Set `status: 'cloudflare'` in config.

---

## Step 4: Decision Tree

```
Does the GIS layer have sale dates + deed book/page + owner + legal?
├── YES → Does the deed portal look simple (DuProcess/AcclaimWeb)?
│         ├── YES → Use deed portal + GIS enrichment (Madison, DeSoto)
│         └── NO  → Use GIS Parcel approach (Jackson)
└── NO  → Does the GIS have deed book/page for enrichment?
          ├── YES → Use deed portal + GIS enrichment (Madison, DeSoto)
          └── NO  → Use deed portal only (Rankin, Harrison, Hinds)
```

---

## Step 5: Portal-Specific Setup

### 5a. DuProcess

The most common MS portal. `DuProcessSession` handles everything — book type IDs are auto-detected.

**Book type labels vary per county** (auto-detected via `/Lookup/BookTypeLookup`):

| County | Deed Key | Deed ID | Trust Key | Trust ID |
|--------|----------|---------|-----------|----------|
| Madison | "Deed" | 71 | "Deed Of Trust" | 70 |
| Rankin | "Deed" | 1 | "Deed of Trust" | 21 |
| Harrison | "Deed Book" | 1 | "Trust Book" | 2 |

If a new county uses a label not in `_resolve_book_type()`, add it to the lookup chain in `duprocess_client.py`.

**Result cap**: Check the `Max` field from `CriteriaSearchCount`. Madison caps at 2,000 (auto-chunks weekly), Harrison at 8,000.

**Config** — add to `DUPROCESS_COUNTIES` in `configs.py`:

```python
'CountyName MS': {
    'base_url': 'http://{portal_url}',
    'search_type': 'deed',
    'doc_types': '',
    'status': 'working',
    'portal': 'duprocess',
    'gis_url': '{gis_url}',             # if GIS enrichment available
    'gis_fields': '{field_map_name}',   # 'madison', 'desoto', or omit for default
},
```

**Seed subdivisions** (DuProcess only — portal provides a lookup endpoint):

```python
from county_scrapers.duprocess_client import DuProcessSession
session = DuProcessSession('{portal_url}')
session.connect()
subs = session.fetch_subdivisions()
session.close()
```

Then run the grouping script (see `reference_data/subdivisions.yaml` for format).

### 5b. AcclaimWeb

Harris Recording Solutions portal. Uses `curl_cffi`, 3-step search flow.

**Find doc type IDs** from the search page combo box:

```python
from curl_cffi import requests as cf_requests
import re, json
session = cf_requests.Session(impersonate='chrome')
resp = session.get('{portal_url}/search/SearchTypeDocType')
combo = re.findall(r'DocTypesDisplay.*?data:\s*(\[.*?\])', resp.text, re.DOTALL)
items = json.loads(combo[0])
for i in items:
    if any(k in i['Text'][:5] for k in ['WAR','QCL','DEE']):
        print(f'{i["Value"]:>5s}  {i["Text"]}')
```

**Config** — add to `ACCLAIMWEB_COUNTIES`:

```python
'CountyName MS': {
    'base_url': 'https://{portal_url}',
    'doc_types': '{comma_separated_ids}',   # e.g. '1509,1342,1080'
    'status': 'working',
    'portal': 'acclaimweb',
    'gis_url': '{gis_url}',
    'gis_fields': '{field_map_name}',
},
```

### 5c. GIndex

Bare-bones ASP Classic portal. Minimal data — names, instrument type, book/page, date only. No legal descriptions, no subdivisions.

**Config** — add to `GINDEX_COUNTIES`:

```python
'CountyName MS': {
    'base_url': 'https://{county_url}/pgs/apps',
    'book_type': '2',                       # 1=DoT only, 2=Deed only, 3=Both
    'status': 'cloudflare',                 # almost always needs curl_cffi
    'portal': 'gindex',
},
```

### 5d. GIS Parcel (Portal Bypass)

When the deed portal is too complex but the GIS layer has everything. Queries ArcGIS by sale date range.

**Verify the approach works**:

```bash
# Check that sale date queries return data
curl -s "{gis_url}/query" \
  -d "where=SDAT >= date '2025-03-01' AND SDAT < date '2025-04-01'" \
  -d "returnCountOnly=true" -d "f=json"
```

**Add a field map** in `gis_parcel_client.py` if field names differ from Jackson:

```python
NEWCOUNTY_FIELDS = {
    'owner': '{owner_field}',
    'address': '{address_field}',
    'deed_book': '{book_field}',
    'deed_page': '{page_field}',
    'subdivision': '{sub_field}',
    'lot': '{lot_field}',
    'acreage': '{acreage_field}',
    'total_value': '{value_field}',
    'sale_amount': '{sale_field}',
    'sale_date': '{date_field}',
    'legal': '{legal_field}',
    'parcel_id': '{parcel_field}',
}
```

**Config** — add to `GIS_PARCEL_COUNTIES`:

```python
'CountyName MS': {
    'layer_url': '{gis_mapserver_or_featureserver_url}',
    'gis_fields': '{field_map_name}',
    'status': 'working',
    'portal': 'gis_parcel',
},
```

---

## Step 6: GIS Enrichment (for Portal-Based Counties)

For counties using a deed portal (DuProcess, AcclaimWeb, GIndex), the GIS layer can enrich deed records with addresses, acreage, values, and centroid lat/lon — but only if the GIS has deed book/page fields for cross-referencing.

### Does Cross-Referencing Work?

| GIS has deed_book/deed_page? | Result |
|------------------------------|--------|
| Yes (Madison, DeSoto) | Enrichment works — adds address, acreage, value, lat/lon |
| No (Rankin, Harrison, Hinds) | Enrichment skipped — no join key |
| Deed refs removed (Hinds) | `DEED_REFERENCE_REMOVED` field — intentionally stripped |

### GIS Data Lag

GIS snapshots trail current deed records by months. Madison GIS goes through Dec 2024, DeSoto through mid-2025. Enrichment rates for current-month pulls will be low (~0%). Historical pulls within the GIS date range get 30-40% enrichment.

### Add a Field Map

If the GIS field names don't match an existing map, add one in `gis_enrichment.py`:

```python
NEWCOUNTY_FIELDS = {
    'deed_book': '{book_field}',
    'deed_page': '{page_field}',
    'address': '{addr_field}',          # string or ['num_field', 'name_field']
    'acreage': '{acreage_field}',       # string or ['primary', 'fallback']
    'value': '{value_field}',
}
```

Reference it in `pull_records.py`'s `_GIS_FIELD_MAPS` dict and set `gis_fields` in the county config.

---

## Step 7: Common Configuration

Regardless of portal type, every county needs these entries.

**`counties.yaml`**:

```yaml
  "CountyName MS":
    input_folder: "output"
    column_mapping:
      grantor: Direct Name
      grantee: Reverse Name
      date: Record Date
      instrument: Doc Type
      legal: Legal
      sub: Subdivision           # omit for GIndex (no subdivision data)
    phase_keywords:
      - Phase
      - Ph.?
      - PH
    lot_block_cutoffs:
      - Lot
      - Lots
      - Unit
      - Units
      - Blk
      - Block
      - BLK
    skiprows: 0
    delimiters:
      - ","
```

**`county-registry.yaml`** — add under the Mississippi section:

```yaml
  countyname-ms:
    name: County Name
    state: MS
    fips: "28XXX"
    projects:
      cd2:
        portal: duprocess | acclaimweb | gindex | gis_parcel
        url: {portal_or_gis_url}
        bypass: none | cloudflare
        status: live
        notes: ""
```

---

## Step 8: Verify

```bash
python -m county_scrapers --county "CountyName MS" --begin 03/01/2025 --end 03/31/2025 --no-filter

python -c "
import csv
with open('output/CountyName MS_03_2025.csv') as f:
    rows = list(csv.DictReader(f))
print(f'Records: {len(rows)}')
has_legal = sum(1 for r in rows if r.get('Legal','').strip())
has_sub = sum(1 for r in rows if r.get('Subdivision','').strip())
has_addr = sum(1 for r in rows if r.get('Situs Address','').strip())
has_sale = sum(1 for r in rows if r.get('Sale Amount','').strip())
has_latlon = sum(1 for r in rows if r.get('Latitude','').strip())
print(f'Legal: {has_legal} ({100*has_legal//len(rows)}%)')
print(f'Subdivision: {has_sub} ({100*has_sub//len(rows)}%)')
print(f'Address: {has_addr} ({100*has_addr//len(rows)}%)')
print(f'Sale amount: {has_sale} ({100*has_sale//len(rows)}%)')
print(f'Lat/lon: {has_latlon} ({100*has_latlon//len(rows)}%)')
"
```

---

## Current MS County Status

| County | Portal | Records/mo | Legal | Subdivision | Address | Lat/Lon | Sale $ |
|--------|--------|:---:|:---:|:---:|:---:|:---:|:---:|
| Madison | DuProcess | 1,072 | 95% | 50% | 40%* | 40%* | no |
| Rankin | DuProcess | 620 | 99% | 64% | no | no | no |
| Harrison | DuProcess | 1,573 | 94% | 94% | no | no | no |
| Hinds | GIndex | 1,698 | 0% | 0% | no | no | no |
| DeSoto | AcclaimWeb | 528 | 100% | in legal | 0%* | 0%* | no |
| Jackson | GIS Parcel | 531 | 100% | 67% | 100% | 100% | 26% |

*GIS enrichment limited by data lag — GIS snapshots trail current deeds by months.

---

## Expected Coverage by Portal Type

| Metric | DuProcess | AcclaimWeb | GIndex | GIS Parcel |
|--------|-----------|------------|--------|------------|
| Legal description | 94-99% | 100% | 0% | 100% |
| Subdivision | 50-94% | in legal text | 0% | 67% |
| Situs address | GIS-dependent | GIS-dependent | 0% | 100% |
| Lat/lon | GIS-dependent | GIS-dependent | 0% | 100% |
| Sale amount | no | no | no | 26%+ (if GIS has it) |
| Grantor (seller) | yes | yes | yes | no (current owner only) |

Note: GIS Parcel counties show the current owner as "grantee" but have no grantor (seller) — the GIS only knows who owns the parcel now, not who sold it.

---

## Gotchas

**Subdivision codes don't match across systems.** Harrison County's DuProcess subdivision codes (Chancery Clerk) use a completely different numbering system than the GIS subdivision codes (Tax Assessor). Don't assume they can be joined.

**GIS data lags deed records.** Madison GIS is current through Dec 2024, DeSoto through mid-2025. If you pull March 2026 deeds and try to enrich from GIS, the match rate will be ~0%. Historical pulls within the GIS date range get 30-40%.

**TLS fingerprinting is common.** Hinds and Jackson reject Python `requests` but work with `curl_cffi`. Always test with `curl` first, then try Python. If Python fails, set `status: 'cloudflare'` in config.

**Some GIS layers hide data in related tables.** Harrison County's parcel geometry layer has only 10 fields, but a related LandRoll table (FeatureServer/3) has addresses, values, and subdivision codes. Always check for related tables.

**Deed references are sometimes intentionally removed.** Hinds County GIS has a field literally named `DEED_REFERENCE_REMOVED`. Don't waste time trying to find deed cross-references in the GIS if they've been stripped.

**"Non-disclosure" doesn't mean no prices anywhere.** Jackson County GIS has sale amounts for 45% of parcels despite Mississippi being a non-disclosure state. Always check for SAMT/sale_amount fields.

**Book type labels are unpredictable.** Three DuProcess counties, three different labels: "Deed"/"Deed Of Trust", "Deed"/"Deed of Trust", "Deed Book"/"Trust Book". The auto-detect in `_resolve_book_type()` handles known variants. If you find a new one, add it to the lookup chain.

**The 500/2000/8000 caps vary.** GIndex caps at 500 (daily chunking needed), DuProcess at 2000 or 8000 (weekly chunking), GIS layers at 1000-2000 (offset pagination). The clients handle this automatically.

---

## MS-Specific Notes

- Mississippi is a **non-disclosure state**. No sale prices on deeds. Some GIS layers have sale amounts anyway.
- Survey system is **PLSS** (St. Stephens Meridian). Legal descriptions use Section/Township/Range.
- Mississippi uses **Deed of Trust** instead of Mortgage. Labels vary per county.
- The 82 counties are served by **Chancery Clerks** (not Circuit Clerks or Clerks of Court).
- DuProcess portals auto-detect book type IDs via `/Lookup/BookTypeLookup` and offer `/Lookup/SubdivisionLookup` for seeding reference data.

---

## Quick Reference: Files to Touch

| File | What to Add |
|------|------------|
| `county_scrapers/configs.py` | Entry in the appropriate `*_COUNTIES` dict |
| `counties.yaml` | Column mapping entry |
| `county-registry.yaml` | County block under Mississippi section |
| `reference_data/subdivisions.yaml` | Subdivision seed data (DuProcess only) |
| `county_scrapers/gis_enrichment.py` | New field map (only if GIS enrichment with novel field names) |
| `county_scrapers/gis_parcel_client.py` | New field map (only if GIS Parcel approach with novel field names) |
| `county_scrapers/pull_records.py` | New field map reference in `_GIS_FIELD_MAPS` or `_GIS_PARCEL_FIELD_MAPS` |
| `county_scrapers/duprocess_client.py` | New book type label in `_resolve_book_type()` (only if novel label) |
