-- 014_builder_inventory_tables.sql
-- Create Builder Inventory module-specific tables in the shared database.
-- GIS config moves to bi_county_config (separate from shared counties table).
-- Parcels, snapshots, and schedule are BI-owned.

CREATE EXTENSION IF NOT EXISTS postgis;

--------------------------------------------------------------------
-- 1. GIS config per county (BI module-owned)
--------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS bi_county_config (
    id                          SERIAL PRIMARY KEY,
    county_id                   INTEGER NOT NULL REFERENCES counties(id) UNIQUE,
    gis_endpoint                TEXT,
    gis_owner_field             TEXT,
    gis_parcel_field            TEXT,
    gis_address_field           TEXT,
    gis_use_field               TEXT,
    gis_acreage_field           TEXT,
    gis_subdivision_field       TEXT,
    gis_building_value_field    TEXT,
    gis_appraised_value_field   TEXT,
    gis_deed_date_field         TEXT,
    gis_previous_owner_field    TEXT,
    gis_max_records             INTEGER DEFAULT 1000,
    created_at                  TIMESTAMPTZ DEFAULT NOW(),
    updated_at                  TIMESTAMPTZ DEFAULT NOW()
);

--------------------------------------------------------------------
-- 2. Parcels (core BI inventory table)
--------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS parcels (
    id              SERIAL PRIMARY KEY,
    parcel_number   TEXT NOT NULL,
    county_id       INTEGER NOT NULL REFERENCES counties(id),
    builder_id      INTEGER REFERENCES builders(id),
    subdivision_id  INTEGER REFERENCES subdivisions(id),
    owner_name      TEXT,
    site_address    TEXT,
    use_type        TEXT,
    acreage         NUMERIC(10, 4),
    centroid        GEOMETRY(Point, 4326),
    geom            GEOMETRY(MultiPolygon, 4326),
    parcel_class    TEXT,
    lot_width_ft    NUMERIC(10, 1),
    lot_depth_ft    NUMERIC(10, 1),
    lot_area_sqft   NUMERIC(12, 1),
    building_value  NUMERIC(14, 2),
    appraised_value NUMERIC(14, 2),
    deed_date       TIMESTAMPTZ,
    previous_owner  TEXT,
    is_active       BOOLEAN DEFAULT true,
    first_seen      TIMESTAMPTZ DEFAULT NOW(),
    last_seen       TIMESTAMPTZ DEFAULT NOW(),
    last_changed    TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(parcel_number, county_id)
);

CREATE INDEX IF NOT EXISTS idx_parcels_county_id      ON parcels (county_id);
CREATE INDEX IF NOT EXISTS idx_parcels_builder_id     ON parcels (builder_id);
CREATE INDEX IF NOT EXISTS idx_parcels_subdivision_id ON parcels (subdivision_id);
CREATE INDEX IF NOT EXISTS idx_parcels_parcel_class   ON parcels (parcel_class);
CREATE INDEX IF NOT EXISTS idx_parcels_centroid       ON parcels USING GIST (centroid);
CREATE INDEX IF NOT EXISTS idx_parcels_geom           ON parcels USING GIST (geom);

--------------------------------------------------------------------
-- 3. Snapshots (BI scrape audit log)
--------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS bi_snapshots (
    id                      SERIAL PRIMARY KEY,
    county_id               INTEGER NOT NULL REFERENCES counties(id),
    started_at              TIMESTAMPTZ DEFAULT NOW(),
    completed_at            TIMESTAMPTZ,
    status                  TEXT DEFAULT 'running',
    total_parcels_queried   INTEGER DEFAULT 0,
    new_count               INTEGER DEFAULT 0,
    removed_count           INTEGER DEFAULT 0,
    changed_count           INTEGER DEFAULT 0,
    unchanged_count         INTEGER DEFAULT 0,
    error_message           TEXT,
    summary_text            TEXT
);

CREATE INDEX IF NOT EXISTS idx_bi_snapshots_county_id ON bi_snapshots (county_id);

--------------------------------------------------------------------
-- 4. Parcel snapshots (per-parcel change records)
--------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS bi_parcel_snapshots (
    id              SERIAL PRIMARY KEY,
    parcel_id       INTEGER NOT NULL REFERENCES parcels(id),
    snapshot_id     INTEGER NOT NULL REFERENCES bi_snapshots(id),
    change_type     TEXT NOT NULL,
    old_values      JSONB,
    new_values      JSONB,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_bi_parcel_snapshots_parcel_id   ON bi_parcel_snapshots (parcel_id);
CREATE INDEX IF NOT EXISTS idx_bi_parcel_snapshots_snapshot_id ON bi_parcel_snapshots (snapshot_id);

--------------------------------------------------------------------
-- 5. Schedule config (singleton for APScheduler)
--------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS bi_schedule_config (
    id                  INTEGER PRIMARY KEY DEFAULT 1,
    interval_minutes    INTEGER DEFAULT 10080,
    is_enabled          BOOLEAN DEFAULT true,
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

INSERT INTO bi_schedule_config (id, interval_minutes, is_enabled)
VALUES (1, 10080, true)
ON CONFLICT (id) DO NOTHING;
