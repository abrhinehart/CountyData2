# Schema Reconciliation — Cross-Project Analysis

## 1. Overlapping Entities

Four concepts appear in multiple projects and need a shared definition.

### Jurisdictions / Counties

| Project | Table | Key Columns | Scope |
|---|---|---|---|
| CD2 | `counties` | id, name | 67 FL counties, no state column |
| BI | `counties` | id, name, state, dor_county_no, county_fips, 12 gis_* fields | Multi-state, ArcGIS config per county |
| PT | `jurisdictions` | id, name, portal_type, portal_url | Counties and municipalities mixed |
| CR | `jurisdictions` | id, slug, name, state, county, municipality, commission_type, agenda_platform, config_json | Richest model — distinguishes county vs municipality, tracks commission bodies |

**Who has what:**
- Only BI and CR have a `state` column
- Only BI has FIPS codes and DOR county numbers
- Only CR distinguishes county from municipality
- PT and CR store portal/platform config; BI stores GIS endpoint config
- CD2's `counties` is the simplest — just a name

### Subdivisions

| Project | Table | Key Columns | Identity Key |
|---|---|---|---|
| CD2 | `subdivisions` + `subdivision_aliases` | canonical_name, county(text), county_id, phases[], geom, plat info, developer | (canonical_name, county) |
| BI | `subdivisions` | name, county_id, geom | (name, county_id) |
| PT | `subdivisions` | name, jurisdiction_id, watched, notes | (name, jurisdiction_id) |
| CR | `projects` + `project_aliases` | name, jurisdiction_id, acreage, lot_count, land_use, zoning, lifecycle_stage | (name, jurisdiction_id) — but these are pre-platting development projects |

**Who has what:**
- CD2 has the richest subdivision model (aliases, phases array, geometry, plat book/page, developer, acreage)
- BI also has geometry but is simpler (auto-created from GIS)
- PT has a watchlist flag and notes
- CR's "projects" are the entitlement-stage form of subdivisions — the name originates at commission and flows downstream to permits, inventory, and sales. Projects are entitled by phase; multiple phases can be entitled simultaneously. Commission is the source of truth for subdivision names.

### Builders

| Project | Table | Key Columns | Entity Types |
|---|---|---|---|
| CD2 | `builders` + `builder_aliases` | canonical_name | Builders only (25) |
| CD2 | `land_bankers` + `land_banker_aliases` | canonical_name, category | land_banker/developer/btr (32) |
| BI | `builders` + `builder_aliases` + `builder_counties` | canonical_name, type, scope, is_active | All types unified (builder/developer/land_banker/btr) |
| PT | `builders` | name | Auto-created, no aliases, no types |
| CR | (none) | applicant_name on entitlement_actions | Text field only |

**Who has what:**
- CD2 splits builders and land_bankers into two separate tables
- BI unifies all entity types in one table with a `type` column, adds `scope` (national/regional) and `builder_counties` junction
- PT auto-creates builders from raw names using a canonicalization function
- CR doesn't track builders as entities at all

### Phases

| Project | Table | Key Columns |
|---|---|---|
| CD2 | (column on `subdivisions`) | phases TEXT[] — just name strings like "1", "1A", "2" |
| BI | (none) | Phase sometimes baked into subdivision name ("KINGSTON PHASE 2") |
| PT | (none) | No phase concept |
| CR | `phases` | project_id, name, acreage, lot_count, land_use, zoning |

**Who has what:**
- CD2 stores phases as a simple string array on the subdivisions table
- CR has a proper phases table with metadata (acreage, lot_count, zoning)
- BI and PT don't model phases at all

---

## 2. Conflicts

### C1: County identity — name-only vs (name, state)

**CD2** uses `county TEXT` as a loose string on transactions ("Bay", "Jackson MS", "Madison AL") and has a `counties` table with just `name` unique. **BI** correctly uses (name, state) as the unique key. The CD2 approach will break when two states have the same county name (e.g., "Madison" exists in MS, AL, and FL).

**Resolution:** Adopt BI's (name, state) composite unique key. Backfill CD2's existing county text references to point to proper IDs. The text column can stay as a denormalized display field during migration.

### C2: Jurisdictions vs counties — different granularity

**CD2/BI** track counties only. **PT/CR** track jurisdictions (counties and municipalities). A permit from Panama City, FL needs to reference the "Panama City" jurisdiction but also belong to Bay County for subdivision/builder purposes.

**Resolution:** Create a two-level model:
- `counties` table: the 67 FL counties + out-of-state counties. Used by CD2, BI for geographic grouping.
- `jurisdictions` table: includes both counties and municipalities, with a `county_id` FK back to counties. Used by PT, CR for portal/platform tracking.

Subdivisions FK to `counties` (geographic). Permits and entitlement actions FK to `jurisdictions` (institutional). This matches reality — subdivisions are in a county, permits come from a jurisdiction.

### C3: Builder table split (CD2) vs unified (BI)

**CD2** has separate `builders` and `land_bankers` tables. **BI** merges them into one `builders` table with a `type` column.

**Resolution:** Adopt BI's unified approach. One `builders` table with columns: canonical_name, type (builder/developer/land_banker/btr), scope (national/regional), is_active. Merge CD2's land_bankers into it. Keep `builder_aliases` and `builder_counties` tables. The `type` column replaces the `category` column on land_bankers.

CD2's transaction columns (`builder_id`, `grantor_builder_id`, etc.) can stay as-is — they'll just all point to the unified builders table. The separate `land_banker_id` FKs become unnecessary since the type is on the builder record itself, but this can be handled during the CD2 migration refactor (not a schema blocker).

### C4: Subdivision aliases — different approaches

**CD2** has a proper `subdivision_aliases` table with UPPER() index for case-insensitive matching. **CR** has `project_aliases` with a `source` column (extracted/manual/inferred). **BI** and **PT** have no alias concept.

**Resolution:** Keep CD2's `subdivision_aliases` table as the shared standard. Add a `source` column (from CR's approach) to track provenance. CR's project_aliases will map to this once projects are linked to subdivisions.

### C5: Phases — array column vs proper table

**CD2** stores phases as `TEXT[]` on subdivisions. **CR** has a proper `phases` table with metadata.

**Resolution:** Create a proper `phases` table (like CR's) in the shared schema. Columns: id, subdivision_id, name, acreage, lot_count, proposed_land_use, proposed_zoning, entitlement_status. Migrate CD2's phases[] array into rows. CR's phase metadata enriches the records.

### C6: Database engine mismatch

**CD2** and **BI** use PostgreSQL/PostGIS. **PT** and **CR** use SQLite.

**Resolution:** Everything migrates to the shared PostgreSQL instance (CD2's database). PT and CR modules will switch from sqlite3/SQLAlchemy-SQLite to psycopg2 or SQLAlchemy-PostgreSQL. SQLite-specific syntax (INTEGER PRIMARY KEY AUTOINCREMENT, TEXT for dates) becomes PostgreSQL equivalents (SERIAL, proper DATE/TIMESTAMPTZ). PT's `scrape_jobs` partial unique index uses SQLite expression syntax that needs PostgreSQL translation.

### C7: Portal/scraper config — different storage approaches

**BI** stores GIS endpoint config as columns directly on the counties table (12 gis_* columns). **PT** stores portal config on jurisdictions (portal_type, portal_url). **CR** stores scraper config in YAML files synced to a `config_json` TEXT column.

**Resolution:** Module-specific scraper config stays module-specific. Don't try to unify GIS field mappings with permit portal URLs — they're different concerns. Each module has its own config table or config columns:
- BI: `bi_county_config` (or keep gis_* columns on a BI-specific extension of counties)
- PT: `pt_jurisdiction_config` (portal_type, portal_url, adapter_slug)
- CR: `cr_jurisdiction_config` (platform, agenda_source_url, config_json)

The shared `counties`/`jurisdictions` tables stay clean. Module config is module-owned.

### C8: Subdivision identity across PT/CR vs CD2/BI

**CD2/BI** identify subdivisions by (name, county). **PT/CR** identify subdivisions by (name, jurisdiction). A subdivision in "Panama City" (PT jurisdiction) and in "Bay County" (CD2 county) might be the same place.

**Resolution:** Subdivisions FK to `counties` (geographic). When PT or CR needs to filter by jurisdiction, join through the jurisdiction → county relationship. PT's `jurisdiction_id` on subdivisions becomes `county_id` (with jurisdiction available through the county link). This prevents duplicate subdivision records for the same physical place under different jurisdictions.

---

## 3. Proposed Shared Schema

### Shared Foundation Tables

```sql
-- Geographic hierarchy
CREATE TABLE counties (
    id              SERIAL PRIMARY KEY,
    name            TEXT NOT NULL,
    state           VARCHAR(2) NOT NULL DEFAULT 'FL',
    dor_county_no   INTEGER,
    county_fips     VARCHAR(10),
    is_active       BOOLEAN DEFAULT true,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(name, state)
);

-- Institutional bodies (includes both counties-as-governments and municipalities)
CREATE TABLE jurisdictions (
    id                  SERIAL PRIMARY KEY,
    slug                VARCHAR(100) UNIQUE,
    name                TEXT NOT NULL,
    county_id           INTEGER NOT NULL REFERENCES counties(id),
    municipality        VARCHAR(100),  -- NULL for county-level jurisdictions
    jurisdiction_type   VARCHAR(50),   -- county/city/town/village
    is_active           BOOLEAN DEFAULT true,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(name, county_id)
);

-- Central shared entity. Name originates at commission (CR) and flows downstream.
-- CR "projects" become subdivisions — no separate projects table needed.
CREATE TABLE subdivisions (
    id                  SERIAL PRIMARY KEY,
    canonical_name      TEXT NOT NULL,
    county_id           INTEGER NOT NULL REFERENCES counties(id),
    geom                GEOMETRY(MultiPolygon, 4326),
    source              TEXT,                   -- where geometry came from
    plat_book           TEXT,
    plat_page           TEXT,
    developer_name      TEXT,
    recorded_date       DATE,
    platted_acreage     DOUBLE PRECISION,
    entitlement_status  VARCHAR(50) DEFAULT 'not_started',
    lifecycle_stage     VARCHAR(50),    -- planning_board/first_reading/second_reading/subdivision/complete
    last_action_date    DATE,
    next_expected_action VARCHAR(100),
    location_description TEXT,
    proposed_land_use   VARCHAR(100),
    proposed_zoning     VARCHAR(100),
    watched             BOOLEAN DEFAULT false,  -- shared watchlist flag (universal across modules)
    notes               TEXT,
    is_active           BOOLEAN DEFAULT true,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(canonical_name, county_id)
);

CREATE TABLE subdivision_aliases (
    id              SERIAL PRIMARY KEY,
    subdivision_id  INTEGER NOT NULL REFERENCES subdivisions(id) ON DELETE CASCADE,
    alias           TEXT NOT NULL,
    source          VARCHAR(20) DEFAULT 'manual',  -- manual/extracted/inferred
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(alias, subdivision_id)
);
CREATE INDEX idx_subdivision_aliases_upper ON subdivision_aliases (UPPER(alias));

-- Proper phases table (replaces CD2's text[] and houses CR's phase metadata)
CREATE TABLE phases (
    id                  SERIAL PRIMARY KEY,
    subdivision_id      INTEGER NOT NULL REFERENCES subdivisions(id) ON DELETE CASCADE,
    name                TEXT NOT NULL,
    acreage             DOUBLE PRECISION,
    lot_count           INTEGER,
    proposed_land_use   VARCHAR(100),
    proposed_zoning     VARCHAR(100),
    entitlement_status  VARCHAR(50) DEFAULT 'not_started',
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(subdivision_id, name)
);

-- Unified builders (merges CD2 builders + land_bankers, adopts BI's type/scope model)
CREATE TABLE builders (
    id              SERIAL PRIMARY KEY,
    canonical_name  TEXT NOT NULL UNIQUE,
    type            VARCHAR(20) NOT NULL DEFAULT 'builder',  -- builder/developer/land_banker/btr
    scope           VARCHAR(20) NOT NULL DEFAULT 'national', -- national/regional
    is_active       BOOLEAN DEFAULT true,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE builder_aliases (
    id          SERIAL PRIMARY KEY,
    builder_id  INTEGER NOT NULL REFERENCES builders(id) ON DELETE CASCADE,
    alias       TEXT NOT NULL UNIQUE,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_builder_aliases_upper ON builder_aliases (UPPER(alias));

CREATE TABLE builder_counties (
    id          SERIAL PRIMARY KEY,
    builder_id  INTEGER NOT NULL REFERENCES builders(id) ON DELETE CASCADE,
    county_id   INTEGER NOT NULL REFERENCES counties(id) ON DELETE CASCADE,
    UNIQUE(builder_id, county_id)
);

-- Shared reference/lookup table for categorical variables across all modules.
-- parcel_class (lot/common_area/tract/other), transaction types, permit statuses, etc.
CREATE TABLE lookup_categories (
    id          SERIAL PRIMARY KEY,
    domain      VARCHAR(50) NOT NULL,   -- e.g. 'parcel_class', 'transaction_type', 'permit_status', 'inventory_category'
    code        VARCHAR(50) NOT NULL,   -- e.g. 'lot', 'common_area', 'house_sale'
    label       TEXT NOT NULL,          -- human-readable display name
    description TEXT,                   -- what this value means
    sort_order  INTEGER DEFAULT 0,
    is_active   BOOLEAN DEFAULT true,
    UNIQUE(domain, code)
);
```

### Module-Owned Tables (stay with each module)

**CountyData2:** transactions, transaction_segments + module config  
**Builder Inventory:** parcels, snapshots, parcel_snapshots, bi_county_config, schedule_config  
**Permit Tracker:** permits, scrape_runs, scrape_payload_archives, scrape_jobs, scraper_artifacts, geocode_cache, parcel_lookup_cache, adapter_record_cache, adapter_state, pt_jurisdiction_config  
**Commission Radar:** source_documents, entitlement_actions, commissioners, commissioner_votes, cr_jurisdiction_config

All module tables FK into the shared spine (counties, jurisdictions, subdivisions, builders, phases, lookup_categories) but do not cross-reference each other.

---

## 4. Migration Impact Per Module

### CountyData2 (host — least disruption)
- `counties`: Add `state`, `dor_county_no`, `county_fips` columns. Change unique from `name` to `(name, state)`.
- `subdivisions`: Change FK from `county` text to use `county_id` exclusively. Drop `phases` TEXT[] column after migrating to `phases` table. Drop `county` text column after all text references are resolved. Add entitlement columns (entitlement_status, lifecycle_stage, etc.) and `watched` boolean.
- `builders`: Add `type`, `scope`, `is_active` columns.
- `land_bankers` + `land_banker_aliases`: Merge into `builders` + `builder_aliases`. Migration script inserts land_bankers as builders with appropriate type. All 6 FK columns on transactions keep working — just repoint to unified builders table.
- New: `jurisdictions` table, `phases` table, `builder_counties` table, `lookup_categories` table.

### Builder Inventory
- `counties`: Its rich schema becomes the basis for the shared `counties` table. GIS-specific columns (`gis_endpoint`, `gis_*_field`) move to a `bi_county_config` table.
- `builders`, `builder_aliases`, `builder_counties`: Already match the proposed shared schema almost exactly. Minor column alignment.
- `subdivisions`: Already has (name, county_id) identity. Add `canonical_name` alias for `name` or rename.
- `parcels`, `snapshots`, `parcel_snapshots`: Stay as-is, just point at shared tables.

### Permit Tracker
- Migrates from SQLite to PostgreSQL.
- `jurisdictions` → FK to shared `jurisdictions` table (or create rows there).
- `subdivisions` → FK to shared `subdivisions` via county_id. Drop local subdivisions table.
- `builders` → FK to shared `builders` table. Auto-created builders get matched against shared aliases.
- `permits`: Keep as module-owned. Change FKs to reference shared tables.
- All TEXT date columns become proper DATE/TIMESTAMPTZ.
- Scraper config (portal_type, portal_url) moves to `pt_jurisdiction_config`.

### Commission Radar
- Migrates from SQLite to PostgreSQL.
- `jurisdictions` → Map to shared `jurisdictions` table. Commission-specific fields (commission_type, agenda_platform, config_json) move to `cr_jurisdiction_config`.
- `projects` → Merge into shared `subdivisions`. Commission is the source of truth for names — subdivisions are created when first seen at commission. CR's `entitlement_status`, `lifecycle_stage`, `last_action_date`, `next_expected_action`, `location_description`, `proposed_land_use`, `proposed_zoning` columns are now on the shared subdivisions table. Drop `projects` table entirely.
- `project_aliases` → Become rows in shared `subdivision_aliases` with source='extracted'.
- `phases` → Merge into shared `phases` table. CR's phase metadata (acreage, lot_count, land_use, zoning, entitlement_status) is already on the shared phases table.
- `entitlement_actions`: Stay as CR-owned. `project_id` FK becomes `subdivision_id` FK. `phase_id` FK points at shared phases.
- `source_documents`, `commissioners`, `commissioner_votes`: Stay as CR-owned.
- `applicant_name` on entitlement_actions can optionally FK to shared `builders` where the applicant is a known builder.

---

## 5. Resolved Decisions

1. **CR projects merge into subdivisions.** Commission is the source of truth for subdivision names. A subdivision is created when it first appears at commission, with entitlement_status and lifecycle_stage tracking on the shared subdivisions table. No separate projects table. Projects are entitled by phase — multiple phases can be entitled simultaneously. Names flow downstream: commission → permits → inventory → sales.

2. **Land banker FK migration: keep all columns, repoint FKs.** Keep all 6 FK columns on transactions (builder_id, grantor_builder_id, grantee_builder_id, grantor_land_banker_id, grantee_land_banker_id). After merging land_bankers into the unified builders table, all columns point at the same table. Minimal disruption.

3. **Watchlist is shared.** `watched` becomes a boolean column on the shared subdivisions table. UI will be redesigned and universalized across modules.

4. **Inventory categories stay CD2-specific for now.** Will tighten up as we go.

5. **Parcel class and other categorical variables use a shared `lookup_categories` table.** BI's parcel_class (lot/common_area/tract/other), CD2's transaction types, PT's permit statuses, and similar categorical fields all get centralized in one reference table keyed by (domain, code). Modules can add their own domains. This prevents hardcoded string constants scattered across modules.
