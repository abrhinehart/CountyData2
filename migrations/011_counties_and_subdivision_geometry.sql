-- 011_counties_and_subdivision_geometry.sql
-- Create counties reference table and add geometry + metadata columns to subdivisions.
-- Supports GIS polygon imports and future plat-derived boundaries.

-- Enable PostGIS (idempotent)
CREATE EXTENSION IF NOT EXISTS postgis;

-- Counties reference table (shared across CountyData2, Builder Inventory, etc.)
CREATE TABLE IF NOT EXISTS counties (
    id              SERIAL PRIMARY KEY,
    name            TEXT NOT NULL UNIQUE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Seed all 67 Florida counties (uses NOT EXISTS to work before and after 013 constraint change)
INSERT INTO counties (name)
SELECT name FROM (VALUES
    ('Alachua'), ('Baker'), ('Bay'), ('Bradford'), ('Brevard'),
    ('Broward'), ('Calhoun'), ('Charlotte'), ('Citrus'), ('Clay'),
    ('Collier'), ('Columbia'), ('DeSoto'), ('Dixie'), ('Duval'),
    ('Escambia'), ('Flagler'), ('Franklin'), ('Gadsden'), ('Gilchrist'),
    ('Glades'), ('Gulf'), ('Hamilton'), ('Hardee'), ('Hendry'),
    ('Hernando'), ('Highlands'), ('Hillsborough'), ('Holmes'), ('Indian River'),
    ('Jackson'), ('Jefferson'), ('Lafayette'), ('Lake'), ('Lee'),
    ('Leon'), ('Levy'), ('Liberty'), ('Madison'), ('Manatee'),
    ('Marion'), ('Martin'), ('Miami-Dade'), ('Monroe'), ('Nassau'),
    ('Okaloosa'), ('Okeechobee'), ('Orange'), ('Osceola'), ('Palm Beach'),
    ('Pasco'), ('Pinellas'), ('Polk'), ('Putnam'), ('Santa Rosa'),
    ('Sarasota'), ('Seminole'), ('St. Johns'), ('St. Lucie'), ('Sumter'),
    ('Suwannee'), ('Taylor'), ('Union'), ('Volusia'), ('Wakulla'),
    ('Walton'), ('Washington')
) AS v(name)
WHERE NOT EXISTS (SELECT 1 FROM counties c WHERE c.name = v.name);

-- Add geometry and metadata columns to subdivisions
ALTER TABLE subdivisions ADD COLUMN IF NOT EXISTS county_id       INTEGER REFERENCES counties(id);
ALTER TABLE subdivisions ADD COLUMN IF NOT EXISTS geom            GEOMETRY(MultiPolygon, 4326);
ALTER TABLE subdivisions ADD COLUMN IF NOT EXISTS source          TEXT;
ALTER TABLE subdivisions ADD COLUMN IF NOT EXISTS plat_book       TEXT;
ALTER TABLE subdivisions ADD COLUMN IF NOT EXISTS plat_page       TEXT;
ALTER TABLE subdivisions ADD COLUMN IF NOT EXISTS developer_name  TEXT;
ALTER TABLE subdivisions ADD COLUMN IF NOT EXISTS recorded_date   DATE;
ALTER TABLE subdivisions ADD COLUMN IF NOT EXISTS platted_acreage DOUBLE PRECISION;
ALTER TABLE subdivisions ADD COLUMN IF NOT EXISTS updated_at      TIMESTAMPTZ DEFAULT NOW();

-- Backfill county_id for existing subdivision rows
UPDATE subdivisions s
SET county_id = c.id
FROM counties c
WHERE UPPER(s.county) = UPPER(c.name)
  AND s.county_id IS NULL;

-- Indexes
CREATE INDEX IF NOT EXISTS idx_subdivisions_geom      ON subdivisions USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_subdivisions_county_id  ON subdivisions (county_id);
CREATE INDEX IF NOT EXISTS idx_subdivisions_source     ON subdivisions (source);
