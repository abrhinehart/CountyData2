# Mississippi County Onboarding Guide

How to add a new Mississippi county to CountyData2. Mississippi has three portal types in use — identify which one the county uses, then follow the matching section.

---

## Step 1: Identify the Portal Type

Visit the county Chancery Clerk website and find their online land records search. Mississippi counties use one of three portal types:

| Portal | How to Identify | Counties Using It |
|--------|----------------|-------------------|
| **DuProcess** | URL contains `/DuProcessWebInquiry`. Search page has Infragistics grid, instrument type dropdowns, date pickers. JSON API at `/Home/CriteriaSearch`. | Madison, Rankin, Harrison, plus Forrest, Pearl River, George, Monroe, Lee, Noxubee |
| **AcclaimWeb** | URL contains `/AcclaimWeb`. Search page has Telerik grid, doc type combo box. ASP.NET MVC with `.aspx`-style views. | DeSoto |
| **General Index (GIndex)** | URL contains `/gindex_query.asp`. Bare HTML form, server-rendered table results. ASP Classic from 2008. | Hinds |

If you find a fourth portal type, you'll need to build a new client class. The existing patterns (`duprocess_client.py`, `acclaimweb_client.py`, `gindex_client.py`) provide templates.

---

## Step 2: Test Access

Before writing any code, verify the portal works:

```bash
# DuProcess — check if the home page loads and BookTypeLookup returns data
curl -s "http://{portal_url}/" | head -5
curl -s "http://{portal_url}/Lookup/BookTypeLookup" | python -m json.tool

# AcclaimWeb — check if the search form loads
curl -s "https://{portal_url}/search/SearchTypeDocType" | head -5

# GIndex — check if the search form loads (may need curl_cffi for TLS)
curl -s "https://{portal_url}/gindex_query.asp" | head -5
```

Check for connection issues. If `curl` works but Python `requests` gets `ConnectionResetError`, the county needs `curl_cffi` TLS impersonation (set `status: 'cloudflare'` in config).

---

## Step 3: DuProcess County Setup

DuProcess is the most common MS portal. The `DuProcessSession` client handles everything automatically — book type IDs are auto-detected at connect time.

### 3a. Get the FIPS Code

Look up the county at census.gov or search "FIPS code [county] Mississippi". Format: `28XXX`.

### 3b. Find the Book Type IDs

```bash
curl -s "http://{portal_url}/Lookup/BookTypeLookup" | python -m json.tool
```

The response maps book type names to IDs. Common patterns:

| County | Deed Key | Deed ID | Trust Key | Trust ID |
|--------|----------|---------|-----------|----------|
| Madison | "Deed" | 71 | "Deed Of Trust" | 70 |
| Rankin | "Deed" | 1 | "Deed of Trust" | 21 |
| Harrison | "Deed Book" | 1 | "Trust Book" | 2 |

The client auto-detects these. If the county uses a new label variant not covered by `_resolve_book_type()` in `duprocess_client.py`, add it to the lookup chain.

### 3c. Test a Search

```bash
# Get record count for a recent month
CRITERIA='[{"direction":"","name_direction":false,"full_name":"","file_date_start":"03/01/2026","file_date_end":"03/31/2026","inst_type":"","inst_book_type_id":"{DEED_ID}","location_id":"","book_reel":"","page_image":"","greater_than_page":false,"inst_num":"","description":"","consideration_value_min":"","consideration_value_max":"","parcel_id":"","legal_section":"","legal_township":"","legal_range":"","legal_square":"","subdivision_code":"","block":"","lot_from":"","q_ne":false,"q_nw":false,"q_se":false,"q_sw":false,"q_q_ne":false,"q_q_nw":false,"q_q_se":false,"q_q_sw":false,"q_q_search_type":false,"address_street":"","address_number":"","address_parcel":"","address_ppin":"","patent_number":""}]'

curl -s -G "{portal_url}/Home/CriteriaSearchCount" \
  --data-urlencode "criteria_array=$CRITERIA" \
  --data-urlencode "user_id="
```

Note the result cap (`Max` field). If a typical month exceeds it, the client auto-chunks into weekly ranges.

### 3d. Add Configuration

**`county_scrapers/configs.py`** — add to `DUPROCESS_COUNTIES`:

```python
'CountyName MS': {
    'base_url': 'http://{portal_url}',
    'search_type': 'deed',
    'doc_types': '',
    'status': 'working',
    'portal': 'duprocess',
    'gis_url': '{gis_featureserver_url}',     # if GIS available
    'gis_fields': '{field_map_name}',         # 'madison', 'desoto', or omit
},
```

**`counties.yaml`** — add county entry:

```yaml
  "CountyName MS":
    input_folder: "output"
    column_mapping:
      grantor: Direct Name
      grantee: Reverse Name
      date: Record Date
      instrument: Doc Type
      legal: Legal
      sub: Subdivision
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
        portal: duprocess
        url: http://{portal_url}
        bypass: none
        status: live
        notes: ""
```

### 3e. Seed Subdivisions

```python
from county_scrapers.duprocess_client import DuProcessSession
session = DuProcessSession('{portal_url}')
session.connect()
subs = session.fetch_subdivisions()
session.close()
print(f'{len(subs)} subdivisions')
```

Then run the grouping/seeding script pattern used for Madison/Rankin/Harrison (see session history or `reference_data/subdivisions.yaml` for format).

### 3f. Live Test

```bash
python -m county_scrapers --county "CountyName MS" --begin 03/01/2026 --end 03/31/2026 --no-filter
```

Check the output CSV for:
- Record count is reasonable (hundreds for a typical month)
- Legal descriptions are populated (95%+ for DuProcess)
- Subdivision names present for platted lots

---

## Step 4: AcclaimWeb County Setup

AcclaimWeb is used by DeSoto County and potentially other Harris Recording Solutions clients.

### 4a. Find Doc Type IDs

Load the search form page and extract the combo box data:

```bash
curl -s "{portal_url}/search/SearchTypeDocType" | python -c "
import sys, re, json
html = sys.stdin.read()
combo = re.findall(r'DocTypesDisplay.*?data:\s*(\[.*?\])', html, re.DOTALL)
if combo:
    items = json.loads(combo[0])
    for i in items:
        if any(k in i['Text'][:5] for k in ['WAR','QCL','DEE']):
            print(f'{i[\"Value\"]:>5s}  {i[\"Text\"]}')
"
```

Common deed-related types: WAR (warranty deed), QCL (quitclaim), DEE (deed).

### 4b. Test the 3-Step Search Flow

AcclaimWeb requires: GET form → POST search → POST GridResults.

```python
from curl_cffi import requests as cf_requests

session = cf_requests.Session(impersonate='chrome')
session.get('{portal_url}/search/SearchTypeDocType')
session.post('{portal_url}/search/SearchTypeDocType?Length=6',
             data={'DocTypes': '{ids}', 'RecordDateFrom': '3/1/2026',
                   'RecordDateTo': '3/7/2026', 'ShowAllNames': 'true',
                   'ShowAllLegals': 'true'})
resp = session.post('{portal_url}/Search/GridResults?Length=6',
                    data={'page': '1', 'size': '5', 'orderBy': '~',
                          'groupBy': '~', 'filter': '~'},
                    headers={'X-Requested-With': 'XMLHttpRequest'})
import json
data = json.loads(resp.text)
print(f"Total: {data['total']}, fields: {list(data['data'][0].keys())}")
```

### 4c. Add Configuration

**`county_scrapers/configs.py`** — add to `ACCLAIMWEB_COUNTIES`:

```python
'CountyName MS': {
    'base_url': 'https://{portal_url}',
    'doc_types': '{comma_separated_ids}',
    'status': 'working',
    'portal': 'acclaimweb',
    'gis_url': '{gis_url}',
    'gis_fields': '{field_map_name}',
},
```

**`counties.yaml`** and **`county-registry.yaml`** — same pattern as DuProcess (see Step 3d).

---

## Step 5: GIndex County Setup

GIndex is the bare-bones ASP Classic portal. Only Hinds County uses it so far.

### 5a. Verify the Portal

```bash
curl -s "https://{county_url}/pgs/apps/gindex_query.asp" | head -5
```

If this fails with a connection reset, the county needs `curl_cffi` (set `status: 'cloudflare'`).

### 5b. Check Search Form Fields

Look for the `sn2` radio buttons (book type selection):
- `sn2=1` — Deed of Trust only
- `sn2=2` — Deed Book only
- `sn2=3` — Both

### 5c. Add Configuration

**`county_scrapers/configs.py`** — add to `GINDEX_COUNTIES`:

```python
'CountyName MS': {
    'base_url': 'https://{county_url}/pgs/apps',
    'book_type': '2',
    'status': 'cloudflare',  # or 'working' if plain requests works
    'portal': 'gindex',
},
```

GIndex portals have no legal descriptions, no subdivisions, and no GIS cross-reference. Output is limited to names, instrument type, book/page, and date.

---

## Step 6: GIS Parcel Layer

Find the county's ArcGIS parcel layer. Common hosts for MS:

| Region | Host | Counties |
|--------|------|----------|
| Jackson metro | `gis.cmpdd.org` (CMPDD) | Madison, Rankin, Hinds |
| Gulf Coast | County-hosted (`geo.co.{name}.ms.us`) | Harrison |
| Memphis metro | ArcGIS Online (`services6.arcgis.com`) | DeSoto |

### 6a. Find the Parcel Layer

Search for `{county} mississippi GIS parcels` or check the county's website for a GIS viewer. Then find the ArcGIS REST endpoint.

### 6b. Check Field Names

```bash
curl -s "{gis_url}?f=json" | python -c "
import sys, json
data = json.load(sys.stdin)
for f in data.get('fields', []):
    print(f'{f[\"name\"]:25s} {f[\"type\"]}')" | grep -i 'deed\|book\|page\|owner\|addr\|acre\|value\|sub'
```

Key fields to look for:

| Need | Madison (CMPDD) | DeSoto (ArcGIS Online) |
|------|-----------------|----------------------|
| Deed book | `deed_book` | `DEED_BOOK1` |
| Deed page | `deed_page` | `DEED_PAGE1` |
| Owner | `name` | `OWNER_NAME` |
| Address | `street_number` + `street_name` | `FULL_ADDR` |
| Acreage | `arcacres` | `ACREAGE` |
| Value | `true_total_value` | `TOT_APVAL` |

If the GIS layer has `deed_book` and `deed_page`, cross-referencing works and you get situs addresses, acreage, values, and centroid lat/lon on matched records.

If it does NOT have deed references (Rankin, Hinds, Harrison), GIS enrichment is skipped — no join key.

### 6c. Add a Field Map (if new field layout)

If the field names don't match an existing map, add a new one in `gis_enrichment.py`:

```python
NEWCOUNTY_FIELDS = {
    'deed_book': '{book_field_name}',
    'deed_page': '{page_field_name}',
    'address': '{address_field}',        # or ['num_field', 'name_field']
    'acreage': '{acreage_field}',        # or ['primary', 'fallback']
    'value': '{value_field}',
}
```

Then reference it in `pull_records.py`'s `_GIS_FIELD_MAPS` dict and set `gis_fields` in configs.py.

---

## Step 7: Verify the Full Pipeline

```bash
# Pull records
python -m county_scrapers --county "CountyName MS" --begin 03/01/2026 --end 03/31/2026 --no-filter

# Check output
python -c "
import csv
with open('output/CountyName MS_03_2026.csv') as f:
    rows = list(csv.DictReader(f))
print(f'Records: {len(rows)}')
print(f'Columns: {list(rows[0].keys())}')
has_legal = sum(1 for r in rows if r.get('Legal','').strip())
has_addr = sum(1 for r in rows if r.get('Situs Address','').strip())
has_latlon = sum(1 for r in rows if r.get('Latitude','').strip())
print(f'With legal: {has_legal} ({100*has_legal//len(rows)}%)')
print(f'With address: {has_addr}')
print(f'With lat/lon: {has_latlon}')
"
```

Expected coverage by portal type:

| Metric | DuProcess | AcclaimWeb | GIndex |
|--------|-----------|------------|--------|
| Legal description | 95%+ | 100% | 0% |
| Subdivision | 50-95% | in legal text | 0% |
| Situs address | GIS-dependent | GIS-dependent | 0% |
| Lat/lon | GIS-dependent | GIS-dependent | 0% |

---

## MS-Specific Notes

- Mississippi is a **non-disclosure state**. No sale prices on deeds.
- Survey system is **PLSS** (St. Stephens Meridian). Legal descriptions use Section/Township/Range.
- Mississippi uses **Deed of Trust** instead of Mortgage. The trust book labels vary per county ("Deed Of Trust", "Deed of Trust", "Trust Book").
- The `DuProcessSession` auto-detects book type IDs via `/Lookup/BookTypeLookup` at connect time. No need to hardcode them.
- DuProcess portals also offer `/Lookup/SubdivisionLookup` for seeding reference data.
- The 82 counties in Mississippi are served by Chancery Clerks (not Circuit Clerks or Clerks of Court as in other states).

---

## Current MS County Status

| County | Portal | Status | Legal | Subdivision | GIS Cross-Ref | Lat/Lon |
|--------|--------|--------|-------|-------------|---------------|---------|
| Madison | DuProcess | live | 95% | 50% | yes (CMPDD) | yes |
| Rankin | DuProcess | live | 99% | 64% | no | no |
| Harrison | DuProcess | live | 94% | 94% | no | no |
| Hinds | GIndex | live | 0% | 0% | no | no |
| DeSoto | AcclaimWeb | live | 100% | in legal | yes (ArcGIS Online) | yes |

---

## Quick Reference: Files to Touch

| File | What to Add |
|------|------------|
| `county_scrapers/configs.py` | Entry in the appropriate `*_COUNTIES` dict |
| `counties.yaml` | Column mapping entry |
| `county-registry.yaml` | County block under Mississippi section |
| `reference_data/subdivisions.yaml` | Subdivision seed data (DuProcess only) |
| `county_scrapers/gis_enrichment.py` | New field map (only if GIS field names are novel) |
| `county_scrapers/pull_records.py` | New field map reference in `_GIS_FIELD_MAPS` (only if new GIS field map) |
| `county_scrapers/duprocess_client.py` | New book type label in `_resolve_book_type()` (only if novel label) |
