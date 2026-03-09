-- 001_reference_tables.sql
-- Creates subdivision and builder reference tables for lookup-based matching.

CREATE TABLE IF NOT EXISTS subdivisions (
    id              SERIAL PRIMARY KEY,
    canonical_name  TEXT NOT NULL,
    county          TEXT NOT NULL,
    phases          TEXT[] DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (canonical_name, county)
);

CREATE TABLE IF NOT EXISTS subdivision_aliases (
    id              SERIAL PRIMARY KEY,
    subdivision_id  INTEGER NOT NULL REFERENCES subdivisions(id) ON DELETE CASCADE,
    alias           TEXT NOT NULL,
    UNIQUE (alias, subdivision_id)
);
CREATE INDEX IF NOT EXISTS idx_subdivision_aliases_alias
    ON subdivision_aliases (UPPER(alias));

CREATE TABLE IF NOT EXISTS builders (
    id              SERIAL PRIMARY KEY,
    canonical_name  TEXT NOT NULL UNIQUE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS builder_aliases (
    id              SERIAL PRIMARY KEY,
    builder_id      INTEGER NOT NULL REFERENCES builders(id) ON DELETE CASCADE,
    alias           TEXT NOT NULL UNIQUE
);
CREATE INDEX IF NOT EXISTS idx_builder_aliases_alias
    ON builder_aliases (UPPER(alias));
