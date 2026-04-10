# Florida County Onboarding Guide

How to add a new Florida county to CountyData2. All FL deed counties use LandmarkWeb portals, but the bypass method, column layout, and ETL processing vary per county.

Florida is a **full-disclosure state** — sale prices appear on deeds. This makes FL the highest-value state for transaction data.

---

## Step 1: Find the Portal

Florida Clerks of Court use LandmarkWeb (Pioneer Technology Group) for official records. The URL usually ends in `/LandmarkWeb` or `/LandmarkWebLive`.

Search for `{county} florida clerk official records` or `{county} florida clerk of court land records`. The portal is typically hosted on the clerk's domain.

### Common URL patterns

```
https://{clerk-domain}/LandmarkWeb
https://{clerk-domain}/LandmarkWebLive
https://{clerk-domain}/Recording          # Bay County variant
```

---

## Step 2: Determine the Bypass Mode

LandmarkWeb portals have three access patterns. Test in order:

### 2a. Try plain requests first

```bash
curl -s "https://{portal_url}/Home/Index" -o /dev/null -w "%{http_code}"
```

- **200** → No bypass needed. Fully automated. (Hernando, Okeechobee)
- **403** or connection reset → Cloudflare protected, go to 2b.

### 2b. Try curl_cffi TLS impersonation

```python
from curl_cffi import requests as cf_requests
session = cf_requests.Session(impersonate='chrome')
resp = session.get('https://{portal_url}/Home/Index')
print(resp.status_code)  # 200 = cloudflare bypass works
```

If this returns 200, set `status: 'cloudflare'` and `use_cffi: True`. (Citrus, Escambia, Walton)

### 2c. Captcha hybrid (last resort)

If the portal has a visible CAPTCHA that curl_cffi can't bypass, use the captcha_hybrid flow:
1. Selenium opens a real Chrome browser
2. Human solves the CAPTCHA and does one search
3. Script captures the session cookies
4. `LandmarkSession.from_cookies()` uses the stolen cookies for automated searching

Set `status: 'captcha_hybrid'`. (Bay County)

This requires a visible Chrome session — it cannot run headless.

---

## Step 3: Map the Column Layout

LandmarkWeb returns records as DataTables JSON. Column indices vary between portal versions. You need to determine which column index holds each field.

### 3a. Connect and inspect

```python
from county_scrapers.landmark_client import LandmarkSession

session = LandmarkSession('https://{portal_url}', use_cffi=True)  # if cloudflare
session.connect()
rows = session.search_by_date_range('03/01/2026', '03/07/2026')
print(rows[0])  # inspect which fields populated correctly
session.close()
```

### 3b. Check against known column maps

| Portal Version | Legal Column | Subdivision Column | Notes |
|---------------|:---:|:---:|-------|
| Default | 13 | — | Most counties |
| v1.5.87 (Hernando) | 14 | 19 | Extended legal fields in columns 14-25 |
| v1.5.93 (Okeechobee) | 14 | — | Column 13 is secondary instrument number |

If the default column map works (legal descriptions look correct in the output), use `column_map: None` in config — the client uses `DEFAULT_COLUMN_MAP` automatically.

If legal or other fields are in the wrong columns, create a custom column map:

```python
_NEWCOUNTY_COLUMN_MAP = {
    'grantor': '5',
    'grantee': '6',
    'record_date': '7',
    'doc_type': '8',
    'book_type': '9',
    'book': '10',
    'page': '11',
    'instrument': '12',
    'legal': '13',        # adjust if different
    # 'subdivision': '19', # add if portal has dedicated subdivision column
}
```

---

## Step 4: Check Doc Type IDs

Some counties filter by document type ID to pull only deeds. Do a test search with `doc_types=''` (all types) first, then narrow if needed.

Citrus uses `doc_types: '17'` (DEED only). Most others use empty string (all types).

To find the doc type ID for deeds, inspect the portal's document type dropdown or search for a known deed and note the doc type field value.

---

## Step 5: Add County-Specific ETL Processing

Florida counties often need custom text cleaning in the ETL pipeline. Each county has a dedicated parser function in `processors/county_parsers.py`.

### Known processing quirks

| County | Quirk | Code Location |
|--------|-------|--------------|
| Bay | Strip leading `L\d+` and `LOTS?\d+` from legal | `cleanup_patterns` in `counties.yaml` |
| Citrus | Remove unit references (e.g., `83/C`) from subdivision | `parse_citrus_row` |
| Escambia | Strip LOT/BLK/SUB patterns; grantor/grantee labeled 'Direct Name'/'Reverse Name' | `parse_escambia_row` |
| Hernando | Dedicated subdivision column from portal; legal cleaned | `parse_hernando_row` |
| Marion | Grantor/grantee swapped when Star field is not `*`; has Consideration (price) | `parse_marion_row` |
| Okaloosa | `skiprows=1`; text after "Parcel" and "Section" removed | `parse_okaloosa_row` |
| Okeechobee | `before_first_newline` on grantor/grantee (multi-line parcel IDs) | `parse_okeechobee_row` |
| Santa Rosa | Party swap on "to" in Party Type; "unrec" removed; unit refs cleaned | `parse_santarosa_row` |
| Walton | "Legal " prefix stripped from legal description | `parse_walton_row` |

### Adding a new parser

1. Create `parse_newcounty_row()` in `processors/county_parsers.py`
2. Import and add dispatch in `processors/transformer.py`
3. Test with: `python etl.py --county NewCounty --input-root "raw data"`

If the county needs no special handling (rare), the default processing path works without a custom parser.

---

## Step 6: Add Configuration

### `county_scrapers/configs.py` — add to `LANDMARK_COUNTIES`:

```python
'NewCounty': {
    'base_url': 'https://{portal_url}',
    'doc_types': '',                    # or specific ID like '17'
    'column_map': None,                 # None = DEFAULT_COLUMN_MAP, or custom dict
    'status': 'working',               # or 'cloudflare' or 'captcha_hybrid'
    'portal': 'landmark',
},
```

### `counties.yaml`:

```yaml
  NewCounty:
    input_folder: "Z:/Shared/_Office_Shared/Adam/Code/Format/County Data/NewCounty"
    column_mapping:
      grantor: Grantor               # varies: 'Direct Name' for Escambia/Hernando
      grantee: Grantee               # varies: 'Reverse Name' for Escambia/Hernando
      date: Record Date              # varies: 'Record Date Search' for Bay
      instrument: Doc Type
      legal: Legal
      # price: Consideration         # add if county has price column (Marion, Santa Rosa)
      # sub: Subdivision             # add if portal has dedicated subdivision column (Hernando)
    phase_keywords:
      - Phase
      - Ph.?
      - PH
      - Unit
    lot_block_cutoffs:
      - Lot
      - Lots
      - Unit
      - Units
      - Blk
      - Block
      - BLK
    skiprows: 0                       # 1 for Okaloosa
    delimiters:
      - ","
      - Parcel
```

### `county-registry.yaml` — add under the Florida section:

```yaml
  newcounty-fl:
    name: New County
    state: FL
    fips: "12XXX"
    projects:
      cd2:
        portal: landmark
        url: https://{portal_url}
        bypass: none | cloudflare | captcha_hybrid
        status: live
        notes: ""
```

---

## Step 7: Verify

### Pull records via scraper

```bash
python -m county_scrapers --county NewCounty --begin 03/01/2026 --end 03/31/2026 --no-filter
```

### Load into database via ETL

```bash
python etl.py --county NewCounty --input-root "raw data"
# or after scraper output:
python etl.py --county NewCounty
```

### Check output

```bash
python -c "
import csv
with open('output/NewCounty_03_2026.csv') as f:
    rows = list(csv.DictReader(f))
print(f'Records: {len(rows)}')
has_legal = sum(1 for r in rows if r.get('Legal','').strip())
print(f'With legal: {has_legal} ({100*has_legal//len(rows)}%)')
"
```

---

## Troubleshooting

### Scraper Issues

| Error | Cause | Fix |
|-------|-------|-----|
| `ConnectionResetError` or `403 Forbidden` | Cloudflare TLS rejection | Set `status: 'cloudflare'` and use `use_cffi=True` in LandmarkSession |
| Records come back with empty legal descriptions | Wrong column_map — legal is at a different index | Run a test search, inspect raw DataTables JSON, adjust column indices |
| `RecordDateSearch` returns 0 results | Portal has CAPTCHA enforcement (`ShowCaptcha=True`) | Use `captcha_hybrid` flow with Selenium cookie capture |
| `requests.exceptions.SSLError` | Certificate verification issue | Try `use_cffi=True` or check if the portal URL is HTTP vs HTTPS |
| Scraper works but CSV has garbled characters | Source file encoding mismatch | Add the encoding to `SUPPORTED_ENCODINGS` in `config.py` |

### ETL Issues

| Error | Cause | Fix |
|-------|-------|-----|
| `UnicodeDecodeError` on CSV import | Source file has unusual encoding | Add encoding to `SUPPORTED_ENCODINGS` in `config.py` |
| Column mismatch / `KeyError` | Source file headers don't match `column_mapping` | Check actual headers in the source file; update `counties.yaml` |
| Grantor and grantee are swapped | Missing or wrong swap condition | Add swap logic in `processors/county_parsers.py` |
| Phase shows as Roman numerals (I, II, III) | Missing variant in phase normalizer | Add the variant to `fix_phase_typos()` in `utils/text_cleaning.py` |
| `psycopg2.OperationalError: connection refused` | Docker container not running | Run `docker compose up -d` |
| `UndefinedColumn` or `UndefinedTable` | Database schema out of date | Run `python apply_migrations.py` |
| Subdivision not matching reference data | Alias missing from `subdivisions.yaml` | Add the new spelling/variant as an alias, run `python seed_reference_data.py` |
| Duplicate records after re-run | Expected — dedup key (grantor+grantee+instrument+date+county) handles this | Re-runs produce 0 inserts/0 updates for unchanged data |

### Bay County CAPTCHA Flow

Bay County requires a human-in-the-loop CAPTCHA session:

1. Run `python -m county_scrapers --county Bay`
2. Chrome opens to the Bay County Official Records portal
3. Accept the disclaimer
4. Switch to "Record Date" search
5. Do one search (any date range) — this satisfies the CAPTCHA
6. Return to the terminal and press Enter
7. The script captures cookies and proceeds with automated searching

If the CAPTCHA flow fails, the cookies may have expired. Re-run from step 1.

---

## Gotchas and Lessons Learned

**Column maps are fragile.** When a county updates their LandmarkWeb version, column indices can shift. If a working county suddenly returns empty legal descriptions, check if the portal version changed and re-map the columns.

**Santa Rosa's URL is misconfigured.** `configs.py` currently points to Walton's clerk domain. This must be fixed before Santa Rosa automation can work. The correct URL needs to be discovered from the Santa Rosa Clerk of Court website.

**Okaloosa is untested.** The config entry exists but has `status: 'untested'`. The multi-delimiter issue (commas, Parcel, Section all used as delimiters in legal text) needs resolution before it can go live.

**Marion has no scraper.** It's CSV-only — data comes from manual export. A BrowserView portal with JSON API exists (`selfservice.marioncountyclerk.org/BrowserView/api/search`) and has been confirmed to have a `considAmount` field for prices, but the scraper hasn't been built. The portal uses reCAPTCHA v3.

**Cloudflare counties need weekly chunking.** The `curl_cffi` bypass works but portals may rate-limit large result sets. The scraper auto-chunks into weekly date ranges for cloudflare counties.

**FL has sale prices — use them.** Unlike MS and AL, Florida deeds include the Consideration amount. Counties with a `price` column in their `column_mapping` (Marion, Santa Rosa) flow prices through the ETL. For scraper-based counties, the price is not in the LandmarkWeb search results — it's only on the deed document itself. `bay_price_extract.py` demonstrates extracting prices from the document detail view.

**`input_folder` paths matter.** Default paths point to a shared drive (`Z:/Shared/...`). For local testing, use `--input-root "raw data"` to read from the repo-local county folders instead.

---

## Current FL County Status

| County | Bypass | Status | Price | Special Handling |
|--------|--------|--------|:---:|-----------------|
| Bay | captcha_hybrid | live | via `bay_price_extract.py` | cleanup_patterns |
| Citrus | cloudflare | live | no | Unit ref removal |
| Escambia | cloudflare | live | no | LOT/BLK/SUB removal |
| Hernando | none | live | no | Subdivision column; extended legal |
| Marion | — | csv-only | yes (Consideration) | Grantor/grantee swap |
| Okaloosa | untested | untested | no | skiprows=1; multi-delimiter issue |
| Okeechobee | none | live | no | Multi-line party names |
| Santa Rosa | — | misconfigured | yes (Consideration) | Party swap; URL bug |
| Walton | cloudflare | live | no | "Legal " prefix strip |

---

## FL-Specific Notes

- Florida is a **full-disclosure state**. Sale prices (Consideration) appear on deeds.
- Survey system is **PLSS** (Tallahassee Meridian).
- 67 counties, all using LandmarkWeb for clerk records. Most have ArcGIS for parcels.
- Transaction types are classified automatically: Builder Purchase, Land Banker Purchase, Build-to-Rent, Association Transfer, CDD Transfer, Raw Land Purchase, House Sale, etc.
- Builder and land banker reference data (`builders.yaml`, `land_bankers.yaml`) drive entity matching across all counties.

---

## Quick Reference: Files to Touch

| File | What to Add |
|------|------------|
| `county_scrapers/configs.py` | Entry in `LANDMARK_COUNTIES` with base_url, doc_types, column_map, status |
| `counties.yaml` | Column mapping, phase keywords, delimiters, skiprows |
| `county-registry.yaml` | County block under Florida section |
| `processors/county_parsers.py` | New `parse_{county}_row()` function (if special handling needed) |
| `processors/transformer.py` | Import and dispatch to new parser |
| `utils/text_cleaning.py` | New cleaning functions (if novel patterns in legal text) |
| `reference_data/subdivisions.yaml` | Subdivision aliases for the new county |
