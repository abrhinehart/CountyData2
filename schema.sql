--CREATE EXTENSION IF NOT EXISTS postgis;

-- ───────────────────────────────────────────────────────────────
-- Reference tables (lookup-based matching)
-- ───────────────────────────────────────────────────────────────

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

-- ───────────────────────────────────────────────────────────────
-- Transactions
-- ───────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS transactions (
    id              SERIAL PRIMARY KEY,

    -- Display values (original case, trimmed at insert time)
    grantor         TEXT NOT NULL,
    grantee         TEXT,
    type            TEXT,
    instrument      TEXT,
    date            DATE,
    legal_desc      TEXT,
    legal_raw       TEXT,
    subdivision     TEXT,
    subdivision_id  INTEGER REFERENCES subdivisions(id),
    phase           TEXT,
    lots            INTEGER DEFAULT 1,
    price           NUMERIC(15, 2),
    price_per_lot   NUMERIC(15, 2),
    acres           NUMERIC(10, 4),
    price_per_acre  NUMERIC(15, 2),
    county          TEXT NOT NULL,
    notes           TEXT,
    builder_id      INTEGER REFERENCES builders(id),
    review_flag     BOOLEAN DEFAULT FALSE,

    -- Spatial: reserved for future parcel/geocode linkage
--    geom            GEOMETRY(Point, 4326),

    -- Normalized generated columns used for deduplication
    grantor_key     TEXT GENERATED ALWAYS AS (UPPER(TRIM(grantor))) STORED,
    grantee_key     TEXT GENERATED ALWAYS AS (UPPER(TRIM(COALESCE(grantee, '')))) STORED,
    instrument_key  TEXT GENERATED ALWAYS AS (UPPER(TRIM(COALESCE(instrument, '')))) STORED,
    county_key      TEXT GENERATED ALWAYS AS (UPPER(TRIM(county))) STORED,

    -- Audit
    source_file     TEXT,
    inserted_at     TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE (grantor_key, grantee_key, instrument_key, date, county_key)
);

CREATE INDEX IF NOT EXISTS idx_transactions_county         ON transactions (county);
CREATE INDEX IF NOT EXISTS idx_transactions_subdivision    ON transactions (subdivision);
CREATE INDEX IF NOT EXISTS idx_transactions_subdivision_id ON transactions (subdivision_id);
CREATE INDEX IF NOT EXISTS idx_transactions_builder_id     ON transactions (builder_id);
CREATE INDEX IF NOT EXISTS idx_transactions_date           ON transactions (date);
CREATE INDEX IF NOT EXISTS idx_transactions_review_flag    ON transactions (review_flag) WHERE review_flag = TRUE;
-- CREATE INDEX IF NOT EXISTS idx_transactions_geom        ON transactions USING GIST (geom);
