# Alabama County Onboarding Guide

How to add a new Alabama county to CountyData2. Alabama is a **non-disclosure state** — sale prices don't appear on deeds. Mortgage cross-referencing is the primary price proxy (~40% match rate).

Currently only Madison County AL is active in CD2. This guide documents the CountyGovServices portal pattern and prepares for future AL county expansion.

---

## Step 1: Investigate the GIS Layer First

Alabama is non-disclosure, so deed portals won't have prices. Check the GIS parcel layer before committing to a portal scraper — it may have assessed values, subdivision data, or even deed references that complement or replace portal data.

### 1a. Find the Parcel Layer

Search for `{county} alabama GIS parcels` or `{county} alabama property appraiser map`.

Known AL GIS endpoints:

| County | Host | Key Fields |
|--------|------|------------|
| Madison | `web3.kcsgis.com` | PropertyOwner, Subdivision, DeedDate, PreviousOwners, TotalBuildingValue |
| Jefferson | `jccgis.jccal.org` | OWNERNAME, SUBDIV_NAME, AssdValue |
| Baldwin | `utility.arcgis.com` | Owner, Subdivision, DeedRecorded, PreviousOwner, CImpValue |
| Montgomery | `gis.montgomeryal.gov` | OwnerName, SubDiv1, InstDate, TotalImpValue, TotalValue |

### 1b. Check for extended fields

AL GIS layers often have fields FL doesn't — subdivision names, deed dates, previous owners, and building values. These are valuable for Builder Inventory.

```bash
curl -s "{gis_url}?f=json" | python -c "
import sys, json
data = json.load(sys.stdin)
for f in data.get('fields', []):
    print(f'{f[\"name\"]:25s} {f[\"type\"]}')" | grep -iE 'owner|sub|deed|prev|value|build'
```

---

## Step 2: Identify the Deed Portal

Alabama counties use various portal types. The only one automated so far is CountyGovServices.

| Portal | How to Identify | Counties |
|--------|----------------|----------|
| **CountyGovServices** | Azure AD B2C login, Kendo Grid, `countygovservices.com` domain | Madison |
| **BrowserView** | `BrowserView/api/search` endpoint, ASP.NET + Angular | Marion FL planned (same vendor appears in some AL counties) |
| **Other** | Various — investigate individually | Unknown |

### Check for CountyGovServices

```bash
# Look for B2C redirect from the base URL
curl -s -o /dev/null -w "%{redirect_url}" "https://{portal_url}/"
# If it redirects to *.b2clogin.com, it's CountyGovServices with B2C auth
```

---

## Step 3: CountyGovServices Setup

### 3a. Get Credentials

CountyGovServices portals require Azure AD B2C authentication. You need:
- An email address registered with the portal
- A password

Set them in `.env`:

```
MADISON_PORTAL_EMAIL=your@email.com
MADISON_PORTAL_PASSWORD=yourpassword
```

For new AL counties, add new env var names (e.g., `JEFFERSON_PORTAL_EMAIL`). The env var names are currently hardcoded in `pull_records.py` — you'll need to add a new branch for each county's credentials.

### 3b. Understand the Auth Flow

The B2C authentication is a 7-step process (handled by `CountyGovSession.connect()`):

1. `GET /` → 302 redirect to B2C authorize URL
2. `GET` B2C authorize URL → extract `SETTINGS.csrf` and `SETTINGS.transId`
3. `POST /SelfAsserted` with email + password + CSRF token
4. `GET /CombinedSigninAndSignup/confirmed` → extract authorization code
5. `POST /signin-oidc` with code + state → sets session cookie
6. `GET /Home/Requirements` → extract `__RequestVerificationToken`
7. `POST /Home/Requirements` with `TermsAccepted=true`

If any step fails, `AuthenticationError` is raised with a descriptive message.

### 3c. Test the Connection

```python
from county_scrapers.countygov_client import CountyGovSession

session = CountyGovSession(
    'https://{portal_url}',
    email='your@email.com',
    password='yourpassword',
    search_type='deed',
)
session.connect()
rows = session.search_by_date_range('03/01/2026', '03/31/2026')
session.close()
print(f'{len(rows)} records')
```

### 3d. Mortgage Cross-Referencing

Alabama is non-disclosure, so mortgage cross-referencing is essential. The scraper:
1. Searches deeds for the date range
2. Creates a second session with `search_type='mortgage'`
3. Searches mortgages for the same date range
4. Matches by date + grantee/grantor last name overlap
5. Sets `mortgage_amount` and `mortgage_originator` on matched deeds

Madison AL gets ~40% mortgage match rate. The mortgage amount comes from the `idVALUE_MORT` field in the Kendo Grid JSON.

### 3e. Add Configuration

**`county_scrapers/configs.py`** — add to `COUNTYGOV_COUNTIES`:

```python
'NewCounty AL': {
    'base_url': 'https://{portal_url}',
    'search_type': 'deed',
    'doc_types': '',
    'status': 'working',
    'portal': 'countygov',
},
```

**`counties.yaml`**:

```yaml
  "NewCounty AL":
    input_folder: "output"
    column_mapping:
      grantor: Direct Name
      grantee: Reverse Name
      date: Record Date
      instrument: Doc Type
      legal: Legal
      mortgage_amount: Mortgage Amount
      mortgage_originator: Mortgage Originator
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

**`.env`**:

```
NEWCOUNTY_PORTAL_EMAIL=your@email.com
NEWCOUNTY_PORTAL_PASSWORD=yourpassword
```

**`county-registry.yaml`**:

```yaml
  newcounty-al:
    name: New County
    state: AL
    fips: "01XXX"
    projects:
      cd2:
        portal: countygov-b2c
        url: https://{portal_url}
        bypass: b2c-auth
        status: live
        notes: ""
    quirks:
      - "Non-disclosure state: no sale prices on deeds. Mortgage cross-ref needed."
      - "Assessor data uses 'L L C' spacing — aliases must include both LLC and L L C."
```

---

## Step 4: Entity Alias Quirks

### L L C Spacing

Alabama assessor data uses `L L C` (with spaces) instead of `LLC`. When adding builder or land banker aliases for an AL county, include both forms:

```yaml
# reference_data/builders.yaml
- canonical_name: "D.R. Horton"
  aliases:
    - "D R HORTON INC"
    - "D R HORTON INC - BIRMINGHAM"
    - "DR HORTON INC"
    - "D R HORTON I N C"          # L L C-style spacing variant
```

### Known Land Banker Relationships

| Entity | Parent Builder | Role |
|--------|---------------|------|
| Millrose Properties | Lennar | Land banker (1,044 parcels in Madison AL) |
| Forestar | DR Horton | Land banker / developer |

---

## Step 5: Verify

```bash
# Pull records (requires portal credentials in .env)
python -m county_scrapers --county "NewCounty AL" --begin 03/01/2026 --end 03/31/2026 --no-filter

# Check output
python -c "
import csv
with open('output/NewCounty AL_03_2026.csv') as f:
    rows = list(csv.DictReader(f))
print(f'Records: {len(rows)}')
has_mortgage = sum(1 for r in rows if r.get('Mortgage Amount','').strip())
has_originator = sum(1 for r in rows if r.get('Mortgage Originator','').strip())
print(f'With mortgage amount: {has_mortgage} ({100*has_mortgage//len(rows)}%)')
print(f'With mortgage originator: {has_originator} ({100*has_originator//len(rows)}%)')
"
```

Expected: ~40% mortgage match rate for active residential counties.

---

## Troubleshooting

### Authentication Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `AuthenticationError: Could not find SETTINGS.csrf in B2C page` | B2C login page HTML structure changed | Inspect the B2C page source; update the regex in `countygov_client.py` |
| `AuthenticationError: Could not find SETTINGS.transId` | Same — B2C page updated | Update the `transId` regex pattern |
| `AuthenticationError: B2C SelfAsserted returned status 400` | Wrong email or password | Check `.env` credentials. Try logging in manually to verify the account works. |
| `AuthenticationError: B2C SelfAsserted returned 404 for both /api/ and root paths` | B2C endpoint path changed | Check B2C tenant config; the code already tries both `/api/SelfAsserted` and `/SelfAsserted` |
| `AuthenticationError: Could not find code/state in B2C confirmed response` | Auth flow succeeded but response format changed | Inspect the confirmed page HTML for the hidden form fields |
| `Missing MADISON_PORTAL_EMAIL/PASSWORD env vars` | Credentials not set | Add to `.env` file |

### Search Issues

| Error | Cause | Fix |
|-------|-------|-----|
| Search returns 0 records for a date range that should have data | SearchQueryId extraction failed | Check if `data-searchqueryid` attribute format changed in the search type page |
| Kendo grid query/qid extraction returns empty | Grid config HTML format changed | Inspect the SearchResults page for the new Kendo config format |
| Mortgage match rate is 0% | Name matching logic issue | Check `_extract_last_names()` — it expects semicolon-separated names. Verify the name format from `_clean_name()` output. |
| Mortgage match rate is unexpectedly low | Mortgage search_type not returning results | Test mortgage search separately: `CountyGovSession(..., search_type='mortgage')` |

### ETL Issues

| Error | Cause | Fix |
|-------|-------|-----|
| `psycopg2.OperationalError: connection refused` | Docker not running | `docker compose up -d` |
| `UndefinedColumn` or `UndefinedTable` | Schema out of date | `python apply_migrations.py` |
| Builder not classified correctly | Missing alias in `builders.yaml` | Add the alias (include `L L C` variant for AL) and run `python seed_reference_data.py` |

---

## Gotchas and Lessons Learned

**Every AL county may have a different B2C tenant.** The B2C authentication parameters (tenant name, policy, client ID) are extracted dynamically from the redirect URL. A new CountyGovServices county should work without code changes — but the env var names for credentials are currently hardcoded per county in `pull_records.py`.

**Mortgage cross-ref only works on same-day matches.** The `_match_mortgages` function matches deeds to mortgages recorded on the same date where the deed grantee's last name appears in the mortgage grantor field. If a mortgage is recorded on a different day than the deed, it won't match. The 40% rate reflects this limitation.

**`L L C` is a real problem.** AL assessor records consistently space out LLC as `L L C`. Every builder and land banker alias list must include both `LLC` and `L L C` forms. Missing this causes failed entity matching.

**Millrose = Lennar's land bank.** If you see Millrose Properties acquiring lots in bulk, that's Lennar's lot pipeline. Similarly, Forestar = DR Horton's land bank. These relationships are documented in `land_bankers.yaml`.

**B2C sessions expire.** The portal session established during `connect()` has a limited lifetime. For long-running pulls (large date ranges), the session may expire mid-search. The client handles this with retries, but very large pulls may need to be split into smaller date ranges.

**Not all AL counties use CountyGovServices.** Jefferson, Baldwin, and Montgomery are in Builder Inventory only (ArcGIS parcel queries). Their deed portals haven't been investigated. They may use different portal software requiring a new client class.

---

## Current AL County Status

| County | Portal | Status | Mortgage Cross-Ref | Notes |
|--------|--------|--------|:---:|-------|
| Madison | CountyGovServices | live | 40% match rate | B2C auth, Kendo Grid |
| Jefferson | — | BI only | — | ArcGIS parcel queries, 369 DR Horton parcels |
| Baldwin | — | BI only | — | ArcGIS parcels, 793 DR Horton / 292 Lennar |
| Montgomery | — | BI only | — | ArcGIS parcels, 111 DR Horton |

---

## AL-Specific Notes

- Alabama is a **non-disclosure state**. No sale prices on deeds. Mortgage amounts from cross-referencing are the best price proxy.
- Survey system is **PLSS** (St. Stephens and Huntsville Meridians).
- Comp plans are **optional** (enabling legislation only, not mandated).
- Entity names use `L L C` spacing in assessor data. Always include both `LLC` and `L L C` alias forms.
- The Probate Judge (not Clerk of Court) handles deed recording in Alabama.

---

## Quick Reference: Files to Touch

| File | What to Add |
|------|------------|
| `county_scrapers/configs.py` | Entry in `COUNTYGOV_COUNTIES` |
| `counties.yaml` | Column mapping including `mortgage_amount` and `mortgage_originator` |
| `county-registry.yaml` | County block under Alabama section |
| `.env` | Portal email and password env vars |
| `county_scrapers/pull_records.py` | New env var branch for county credentials (if not using MADISON_PORTAL_*) |
| `reference_data/builders.yaml` | `L L C` alias variants for builders active in this county |
| `reference_data/land_bankers.yaml` | Land banker entities with `L L C` variants |
