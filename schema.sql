--CREATE EXTENSION IF NOT EXISTS postgis;

-- Reference tables (lookup-based matching)

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

CREATE TABLE IF NOT EXISTS land_bankers (
    id              SERIAL PRIMARY KEY,
    canonical_name  TEXT NOT NULL UNIQUE,
    category        TEXT,           -- 'land_banker', 'developer', or 'btr'
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS land_banker_aliases (
    id              SERIAL PRIMARY KEY,
    land_banker_id  INTEGER NOT NULL REFERENCES land_bankers(id) ON DELETE CASCADE,
    alias           TEXT NOT NULL UNIQUE
);
CREATE INDEX IF NOT EXISTS idx_land_banker_aliases_alias
    ON land_banker_aliases (UPPER(alias));

-- Transactions

CREATE TABLE IF NOT EXISTS transactions (
    id                      SERIAL PRIMARY KEY,

    -- Display values (original case, trimmed at insert time)
    grantor                 TEXT NOT NULL,
    grantee                 TEXT,
    type                    TEXT,
    instrument              TEXT,
    date                    DATE,
    export_legal_desc       TEXT,
    export_legal_raw        TEXT,
    deed_locator            JSONB DEFAULT '{}'::jsonb,
    deed_legal_desc         TEXT,
    deed_legal_parsed       JSONB DEFAULT '{}'::jsonb,
    subdivision             TEXT,
    subdivision_id          INTEGER REFERENCES subdivisions(id),
    phase                   TEXT,
    inventory_category      TEXT,
    lots                    INTEGER DEFAULT 1,
    price                   NUMERIC(15, 2),
    price_per_lot           NUMERIC(15, 2),
    acres                   NUMERIC(10, 4),
    acres_source            TEXT,
    price_per_acre          NUMERIC(15, 2),
    parsed_data             JSONB DEFAULT '{}'::jsonb,
    county                  TEXT NOT NULL,
    notes                   TEXT,

    -- Legacy compatibility field: prefer buyer-side builder when present
    builder_id              INTEGER REFERENCES builders(id),

    -- Side-specific tracked entities
    grantor_builder_id      INTEGER REFERENCES builders(id),
    grantee_builder_id      INTEGER REFERENCES builders(id),
    grantor_land_banker_id  INTEGER REFERENCES land_bankers(id),
    grantee_land_banker_id  INTEGER REFERENCES land_bankers(id),

    review_flag             BOOLEAN DEFAULT FALSE,

    -- Spatial: reserved for future parcel/geocode linkage
--    geom                    GEOMETRY(Point, 4326),

    -- Normalized generated columns used for deduplication
    grantor_key             TEXT GENERATED ALWAYS AS (UPPER(TRIM(grantor))) STORED,
    grantee_key             TEXT GENERATED ALWAYS AS (UPPER(TRIM(COALESCE(grantee, '')))) STORED,
    instrument_key          TEXT GENERATED ALWAYS AS (UPPER(TRIM(COALESCE(instrument, '')))) STORED,
    county_key              TEXT GENERATED ALWAYS AS (UPPER(TRIM(county))) STORED,

    -- Audit
    source_file             TEXT,
    inserted_at             TIMESTAMPTZ DEFAULT NOW(),
    updated_at              TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE (grantor_key, grantee_key, instrument_key, date, county_key)
);

CREATE INDEX IF NOT EXISTS idx_transactions_county                  ON transactions (county);
CREATE INDEX IF NOT EXISTS idx_transactions_subdivision             ON transactions (subdivision);
CREATE INDEX IF NOT EXISTS idx_transactions_subdivision_id          ON transactions (subdivision_id);
CREATE INDEX IF NOT EXISTS idx_transactions_inventory_category      ON transactions (inventory_category) WHERE inventory_category IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_transactions_builder_id              ON transactions (builder_id);
CREATE INDEX IF NOT EXISTS idx_transactions_grantor_builder_id      ON transactions (grantor_builder_id);
CREATE INDEX IF NOT EXISTS idx_transactions_grantee_builder_id      ON transactions (grantee_builder_id);
CREATE INDEX IF NOT EXISTS idx_transactions_grantor_land_banker_id  ON transactions (grantor_land_banker_id);
CREATE INDEX IF NOT EXISTS idx_transactions_grantee_land_banker_id  ON transactions (grantee_land_banker_id);
CREATE INDEX IF NOT EXISTS idx_transactions_date                    ON transactions (date);
CREATE INDEX IF NOT EXISTS idx_transactions_review_flag             ON transactions (review_flag) WHERE review_flag = TRUE;
-- CREATE INDEX IF NOT EXISTS idx_transactions_geom                 ON transactions USING GIST (geom);

CREATE TABLE IF NOT EXISTS transaction_segments (
    id                      SERIAL PRIMARY KEY,
    transaction_id          INTEGER NOT NULL REFERENCES transactions(id) ON DELETE CASCADE,
    segment_index           INTEGER NOT NULL,
    county                  TEXT NOT NULL,
    subdivision_lookup_text TEXT,
    raw_subdivision         TEXT,
    subdivision             TEXT,
    subdivision_id          INTEGER REFERENCES subdivisions(id),
    phase_raw               TEXT,
    phase                   TEXT,
    inventory_category      TEXT,
    phase_confirmed         BOOLEAN,
    segment_review_reasons  TEXT[] DEFAULT '{}',
    segment_data            JSONB DEFAULT '{}'::jsonb,
    created_at              TIMESTAMPTZ DEFAULT NOW(),
    updated_at              TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE (transaction_id, segment_index)
);

CREATE INDEX IF NOT EXISTS idx_transaction_segments_transaction_id ON transaction_segments (transaction_id);
CREATE INDEX IF NOT EXISTS idx_transaction_segments_subdivision_id ON transaction_segments (subdivision_id);
CREATE INDEX IF NOT EXISTS idx_transaction_segments_county         ON transaction_segments (county);
CREATE INDEX IF NOT EXISTS idx_transaction_segments_inventory_category
    ON transaction_segments (inventory_category) WHERE inventory_category IS NOT NULL;
