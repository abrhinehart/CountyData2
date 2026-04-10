# Phase 3 Handoff: Permit Tracker Folded In

## What Was Done

Permit Tracker migrated from Flask+SQLite into the CountyData2 unified app as `modules/permits/`. All 18 endpoints now run under FastAPI against the shared PostgreSQL database.

### Schema Changes
**Migration 015** created 10 PT-specific tables, all prefixed with `pt_`:
- `pt_jurisdiction_config` — portal/adapter config per jurisdiction (adapter_slug, portal_type, portal_url, scrape_mode)
- `pt_permits` — core permit fact table (FK to shared jurisdictions, subdivisions, builders)
- `pt_scrape_runs` — audit log of scrape runs
- `pt_scrape_payload_archives` — raw payload JSON archive
- `pt_scrape_jobs` — durable job queue with lease-based concurrency + partial unique index on active scope
- `pt_scraper_artifacts` — HTTP request/response traces
- `pt_geocode_cache` — Census Bureau geocode results
- `pt_parcel_lookup_cache` — Bay County ArcGIS parcel results
- `pt_adapter_record_cache` — per-adapter persistent cache (used by Madison County adapter)
- `pt_adapter_state` — per-adapter key-value state

### Shared Tables Now Used By PT
- **jurisdictions**: 7 PT jurisdictions inserted (Bay County, Panama City, Panama City Beach, Polk, Okeechobee, Citrus, Madison County AL). The two-level model works — Bay County has 3 jurisdictions (county + 2 cities) all referencing the same Bay county_id.
- **subdivisions**: PT's watched flag + notes now live on the shared subdivisions table (added in migration 013). 5 subdivisions marked as watched from the PT watchlist.
- **builders**: PT builders now insert into the shared builders table with `type='builder'` and `scope='national'`. Canonicalization logic preserved.
- **counties**: 4 Alabama counties added in Phase 2 now back Madison County AL jurisdiction.

### Code Structure
```
modules/permits/
  __init__.py
  router.py                    # 391 lines — 17 FastAPI endpoints (dropped Flask index())
  services.py                  # 2327 lines — all business logic, SQLite→PostgreSQL
  normalization.py             # Builder name canonicalization, status normalization
  reference_data.py            # Loads jurisdiction_registry.json
  subdivision_geo.py           # PostGIS subdivision matching (now local, not cross-db)
  geocoding.py                 # Census Bureau batch/one-line geocoder
  parcels.py                   # Bay County ArcGIS parcel lookup
  data/
    jurisdiction_registry.json
    source_research.json
    demo_permits.json
  scrapers/
    base.py                    # JurisdictionAdapter ABC
    registry.py                # Dynamic adapter loading
    adapters/
      bay_county.py            # CityView PDF scraper
      panama_city.py           # Cloudpermit GeoJSON API
      panama_city_beach.py     # iWorq HTML portal
      polk_county.py           # Accela ASP.NET postbacks
      madison_county_al.py     # Authenticated CityView (uses pt_adapter_record_cache/pt_adapter_state)
      okeechobee.py            # Research-only stub
      citrus_county.py         # Research-only stub
```

### Key Conversions Applied
1. **Flask → FastAPI**: All 17 routes converted. `jsonify` → auto-serialize, `request.args` → `Query`, `request.get_json()` → Pydantic models, `render_template` dropped (React UI handles this).
2. **SQLite → PostgreSQL** throughout services.py (2327 lines):
   - `?` placeholders → `%s`
   - `cursor.lastrowid` → `RETURNING id`
   - `0`/`1` integer booleans → `True`/`False`
   - `INSERT OR REPLACE` → `ON CONFLICT DO UPDATE`
   - `sqlite3.IntegrityError` → `psycopg2.IntegrityError`
3. **Schema adaptations for shared tables**:
   - `builders.name` → `builders.canonical_name` (plus `type`, `scope` fields on insert)
   - `subdivisions.name` → `subdivisions.canonical_name`
   - `subdivisions.jurisdiction_id` → goes through `county_id` (joined via jurisdictions.county_id)
   - `jurisdictions.portal_type/portal_url/active` → moved to `pt_jurisdiction_config`
4. **subdivision_geo.py**: Used to open a separate psycopg2 connection to CountyData2's database. Now takes a local `conn` parameter since everything lives in the same database.

### Endpoint Namespacing
- Sales: `/api/*` (backward compat)
- Inventory: `/api/inventory/*`
- Permits: `/api/permits/*`

All 7 PT jurisdictions, 5 watched subdivisions, bootstrap + dashboard + scrape job queue endpoints return 200 OK.

### What Works
- All 18 platform routes across sales, inventory, permits
- Migration suite (15 files) runs idempotently
- pt_permits is empty (expected — no scrapes run yet against the shared DB)
- Bootstrap payload correctly reports 5 runnable + 2 research-only jurisdictions

### Structural Changes From Original PT
- **Subdivisions are county-scoped, not jurisdiction-scoped.** A subdivision in Bay County is visible to all three PT jurisdictions that operate in Bay County (Bay County, Panama City, Panama City Beach). This reflects geographic reality — a subdivision's physical location doesn't change based on which government issued a permit.
- **Subdivision listing in PT now filters to watched + permits-present** (vs. PT's original "all subdivisions in this jurisdiction"). The shared table has 43K subdivisions, so the old filter would return too many.
- **Cross-module visibility**: A subdivision created via PT's UI is now visible to the sales and inventory modules too. This is the core benefit of the shared spine.

### What Phase 4 (Commission Radar) Needs To Know
- **Flask modules can be ported.** PT was 2100+ lines of Flask+SQLite and ported cleanly to FastAPI+PostgreSQL with ~30 targeted schema fixes after the bulk agent-driven port.
- **Raw SQL with psycopg2 coexists with SQLAlchemy** (sales/permits use psycopg2 pool; inventory uses SQLAlchemy sessions). Both point at the same database.
- **Watch the shared table column differences.** PT's port needed fixes for `builders.name` → `canonical_name`, `subdivisions.name` → `canonical_name`, `jurisdictions.portal_type` → `pt_jurisdiction_config.portal_type`. CR will likely have similar mismatches.
- **Subdivisions can be inserted with both `county` (text) and `county_id` (FK)** — the shared table still has the legacy text column. Always set both.
- **Use LATERAL joins** when you need a "pick one representative jurisdiction for a subdivision" query, since counties can have multiple jurisdictions.

### Database State After Phase 3
- 24 tables total: 10 shared spine + 6 CD2 sales + 6 BI inventory + 10 PT permits (minus some overlaps)
- 7 jurisdictions, 5 watched subdivisions, 61 builders, 71 counties, 43,722 subdivisions, 18,109 sales transactions, 0 permits (no scrapes run yet), 0 parcels (no snapshots run yet)
- 41 lookup_categories, 48 GIS configs, 7 PT jurisdiction configs
