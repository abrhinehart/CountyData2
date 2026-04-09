# County Onboarding Checklist

Use this when adding a new county (or city jurisdiction) to **any** project. Update `county-registry.yaml` as you go — the registry is the shared memory across projects.

---

## Step 1: Registry Check

Before writing any code, check `county-registry.yaml`:

- [ ] Does the county already have an entry? If yes, read its quirks and notes.
- [ ] Does the **state** already have an entry? If yes, read disclosure status, survey system, alias quirks.
- [ ] If this is a **new state**, add the state block first (see template below).

If the county is brand new, create its entry in the registry with what you know so far. Fill in project-specific details as you work through the steps below.

---

## Step 2: State-Level Intel (first county in a new state only)

These apply to every project. Research once, document in the state block.

| Question | Where It Matters | How to Find |
|----------|-----------------|-------------|
| Disclosure status? (full / non-disclosure) | CD2 (sale price availability), BI (deed_date/prev_owner utility) | Web search: "[state] real estate disclosure law" |
| PLSS or metes-and-bounds? | Plat Reviewer (legal description parsing), BI (parcel geometry) | Check if the state has a principal meridian. FL/AL = PLSS. GA/SC/NC/TN = metes-and-bounds. |
| Comp plan mandatory? | CR (what appears on commission agendas) | See `multi-state-land-dev-regulations.md` in the wiki |
| Alias quirks? | All projects (entity matching) | Run a test query and inspect owner name formatting. AL uses `L L C` spacing. |

---

## Step 3: County-Level Discovery (per county, all projects)

These facts apply across projects. Research once.

| Question | How to Find |
|----------|-------------|
| FIPS code | Census.gov or `counties` table in Builder Inventory DB |
| Deed portal type? | Visit the clerk of court website. Look for LandmarkWeb, CountyGovServices, Tyler, or other portal software. |
| Parcel/GIS portal? | Search for "[county] GIS" or "[county] property appraiser map." Look for ArcGIS REST endpoints. |
| Permit portal? | Search for "[county] building permits." Look for CityView, Accela, iWorQ, Cloudpermit, or custom portals. |
| Commission agenda portal? | Search for "[county] commission agendas." Look for Legistar, CivicPlus, CivicClerk, NovusAgenda. |
| Bot protection? | Try a simple GET request. Cloudflare → curl_cffi needed. CAPTCHA → Selenium cookie steal. B2C login → auth flow adapter. |

---

## Step 4: Project-Specific Setup

### CountyData2 (deeds/transactions)

- [ ] Identify the clerk portal and its type (LandmarkWeb / CountyGovServices / BrowserView / other)
- [ ] Test access: plain HTTP → CAPTCHA → Cloudflare? Set bypass method accordingly.
- [ ] Add entry to `county_scrapers/configs.py` with URL, status, column map
- [ ] If non-disclosure state: plan mortgage cross-reference (separate search type for mortgages)
- [ ] Add county to `counties.yaml` with column mappings and cleanup patterns
- [ ] Test with `pull_records.py --county [name] --dry-run` if available
- [ ] Update `county-registry.yaml` with portal type, bypass method, status

### Builder Inventory (parcels via ArcGIS)

- [ ] Find the ArcGIS REST endpoint (FeatureServer or MapServer with owner data)
- [ ] Identify field names: owner, parcel ID, address, use type, acreage
- [ ] Check for extended fields: subdivision, deed date, previous owner, building value
- [ ] If no acreage field: check for square footage (÷43560) or Shape.STArea() (geometry area with cos²(lat) correction)
- [ ] Add county to `backend/seed/seed_counties.py`
- [ ] Run seed: `python -m backend.seed.seed_counties`
- [ ] Test query: `python -m backend.app.services.gis_query --county "[name]" --test`
- [ ] Add entity aliases for builders active in this county (check if `L L C` spacing needed)
- [ ] Update `county-registry.yaml` with endpoint, field mapping, status

### Permit Tracker (building permits)

- [ ] Identify the permit portal type (CityView, Accela, iWorQ, Cloudpermit, Tyler EPL, other)
- [ ] Document portal in `data/source_research.json` (always research before code)
- [ ] Write adapter class in `app/scrapers/` implementing `JurisdictionAdapter`
- [ ] Register in `app/scrapers/registry.py` and `data/jurisdiction_registry.json`
- [ ] Add builder normalization patterns to `app/normalization.py` if new builders appear
- [ ] Test scrape and verify dedup works
- [ ] Update `county-registry.yaml` with portal type, URL, status

### Commission Radar (agendas/meetings)

- [ ] Identify the agenda platform (Legistar, CivicPlus, CivicClerk, NovusAgenda, manual)
- [ ] Create jurisdiction YAML in `config/jurisdictions/[STATE]/`
- [ ] If new state: create `config/states/[STATE].yaml` and `config/jurisdictions/[STATE]/_[state]-defaults.yaml`
- [ ] Set `scraping.platform`, `base_url`, and platform-specific fields
- [ ] Run bootstrap: `python bootstrap_commission.py [slug]`
- [ ] Check leaderboard status (usable_seed / partial / zero_listing)
- [ ] Update `county-registry.yaml` with platform, slug, bootstrap status

---

## Step 5: Cross-Project Entity Sync

After adding a county, check for shared entities:

- [ ] Are there new builders in this county not yet in `reference_data/builders.yaml`? Add them.
- [ ] Do existing builders use different name variants here? Add aliases.
- [ ] If Builder Inventory is active: run `sync_reference_data.py` to propagate new entities.
- [ ] If this county has a `gis_subdivision_field`: subdivision auto-creation is handled. If not: check if subdivision polygons are available for import.

---

## Templates

### New State Block (for `county-registry.yaml`)

```yaml
  XX:
    disclosure: full | non-disclosure
    survey_system: plss | metes-and-bounds
    comp_plan: mandatory | optional | advisory | de-facto-mandatory
    plat_approval: varies
    alias_quirks: []
    notes: ""
```

### New County Block (for `county-registry.yaml`)

```yaml
  [slug]:
    name: [Full County Name]
    state: XX
    fips: "[FIPS code]"
    projects:
      cd2:
        portal: landmark | countygov-b2c | browserview | none
        url: https://...
        bypass: none | cloudflare | captcha_hybrid | b2c-auth
        status: live | untested | planned | csv-only
        notes: ""
      bi:
        portal: arcgis
        endpoint: ...
        status: active | inactive
        fields: { owner: X, parcel: X, address: X, use: X, acreage: X }
        notes: ""
      pt:
        portal: cityview | accela | iworq | cloudpermit | tyler-epl
        url: https://...
        status: live | research-only | not-started
        notes: ""
      cr:
        platform: legistar | civicplus | civicclerk | novusagenda | manual
        slug: [jurisdiction-slug]
        status: usable_seed | partial_or_outlier | zero_listing | not-started
    quirks:
      - "Any county-specific notes that apply across projects"
```
