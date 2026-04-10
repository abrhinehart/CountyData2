# Phase 2 Handoff: Builder Inventory Folded In

## What Was Done

Builder Inventory is now a module (`modules/inventory/`) within the unified CountyData2 app. It shares the same PostgreSQL database, the same FastAPI app, and the same foundation tables.

### Schema Changes
- **Migration 014**: Created BI-specific tables in the shared database:
  - `bi_county_config` — GIS endpoint URLs and field mappings per county (48 rows seeded)
  - `parcels` — core inventory table (builder-owned lots/parcels from ArcGIS)
  - `bi_snapshots` — scrape audit log for GIS snapshot runs
  - `bi_parcel_snapshots` — per-parcel change records
  - `bi_schedule_config` — APScheduler interval config (singleton)
- GIS config columns moved off the shared `counties` table into `bi_county_config`
- 4 Alabama counties added to the shared `counties` table (Madison, Jefferson, Baldwin, Montgomery)

### App Structure
```
modules/
  sales/           # CD2 sales data (Phase 1)
    router.py      # 14 endpoints at /api/*
  inventory/       # Builder Inventory (Phase 2)
    router.py      # Aggregated router at /api/inventory/*
    models.py      # BI-specific SQLAlchemy models
    routers/       # 8 sub-routers (builders, counties, parcels, etc.)
    schemas/       # 7 Pydantic schema files
    services/      # 8 service files (GIS query, snapshot runner, etc.)
    scheduler.py   # APScheduler for periodic snapshots
shared/
  database.py      # psycopg2 pool (sales module)
  sa_database.py   # SQLAlchemy engine + SessionLocal (inventory + future modules)
  models.py        # Shared foundation models (County, Subdivision, Builder, etc.)
```

### Shared Tables Now In Use
| Table | Used By |
|---|---|
| counties | Sales (text ref), Inventory (FK) |
| subdivisions | Sales (FK), Inventory (FK) |
| builders | Sales (FK), Inventory (FK) |
| builder_aliases | Sales (lookup), Inventory (lookup + CRUD) |
| builder_counties | Inventory (scope filtering) |
| phases | Sales (reference) |
| lookup_categories | Reference data |

### What Works
- All 14 sales endpoints at `/api/*` — unchanged behavior
- All inventory endpoints at `/api/inventory/*` — 200 OK
- 61 builders visible to both modules (27 builder + 19 developer + 7 land_banker + 8 btr)
- 71 counties (67 FL + 4 AL), 48 with GIS endpoints
- 43,722 subdivisions visible to inventory module
- Parcels/snapshots are 0 — no data migrated from BI's separate database yet (this is expected; once a snapshot run happens, parcels will populate)
- Full migration suite (014 files) runs idempotently

### What The Next Module Needs To Know
- **SQLAlchemy and psycopg2 coexist.** Sales uses the psycopg2 pool (`shared/database.py`). Inventory uses SQLAlchemy sessions (`shared/sa_database.py`). Both point at the same PostgreSQL database. Future modules can use either.
- **Shared models are in `shared/models.py`.** Import `County`, `Subdivision`, `Builder`, etc. from there. Don't redefine them.
- **`Subdivision.name` is a hybrid_property** aliasing `canonical_name`. Works in both Python and SQL expressions.
- **Module-specific tables should be prefixed** (e.g., `bi_snapshots`, `bi_schedule_config`) to avoid name collisions.
- **Router namespacing**: Sales uses `/api/*` (backward compat). New modules get `/api/{module}/*`.
- **GIS config pattern**: Module-specific config goes in its own table (e.g., `bi_county_config`), not on shared tables.

### Database State
- PostgreSQL 16 + PostGIS 3.4 on port 1100
- 14 tables total: 8 shared + 6 BI-specific
- 18,109 transactions, 61 builders, 71 counties, 43,722 subdivisions, 275 phases, 48 GIS configs, 41 lookup categories
