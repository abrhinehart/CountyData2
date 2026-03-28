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
    phase_confirmed         BOOLEAN,
    segment_review_reasons  TEXT[] DEFAULT '{}',
    segment_data            JSONB DEFAULT '{}'::jsonb,
    created_at              TIMESTAMPTZ DEFAULT NOW(),
    updated_at              TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE (transaction_id, segment_index)
);

CREATE INDEX IF NOT EXISTS idx_transaction_segments_transaction_id
    ON transaction_segments (transaction_id);

CREATE INDEX IF NOT EXISTS idx_transaction_segments_subdivision_id
    ON transaction_segments (subdivision_id);

CREATE INDEX IF NOT EXISTS idx_transaction_segments_county
    ON transaction_segments (county);
