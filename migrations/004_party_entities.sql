-- 004_party_entities.sql
-- Adds land banker reference tables and side-specific builder/land banker columns.

CREATE TABLE IF NOT EXISTS land_bankers (
    id              SERIAL PRIMARY KEY,
    canonical_name  TEXT NOT NULL UNIQUE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS land_banker_aliases (
    id              SERIAL PRIMARY KEY,
    land_banker_id  INTEGER NOT NULL REFERENCES land_bankers(id) ON DELETE CASCADE,
    alias           TEXT NOT NULL UNIQUE
);
CREATE INDEX IF NOT EXISTS idx_land_banker_aliases_alias
    ON land_banker_aliases (UPPER(alias));

ALTER TABLE transactions
    ADD COLUMN IF NOT EXISTS grantor_builder_id      INTEGER REFERENCES builders(id),
    ADD COLUMN IF NOT EXISTS grantee_builder_id      INTEGER REFERENCES builders(id),
    ADD COLUMN IF NOT EXISTS grantor_land_banker_id  INTEGER REFERENCES land_bankers(id),
    ADD COLUMN IF NOT EXISTS grantee_land_banker_id  INTEGER REFERENCES land_bankers(id);

CREATE INDEX IF NOT EXISTS idx_transactions_grantor_builder_id
    ON transactions (grantor_builder_id);

CREATE INDEX IF NOT EXISTS idx_transactions_grantee_builder_id
    ON transactions (grantee_builder_id);

CREATE INDEX IF NOT EXISTS idx_transactions_grantor_land_banker_id
    ON transactions (grantor_land_banker_id);

CREATE INDEX IF NOT EXISTS idx_transactions_grantee_land_banker_id
    ON transactions (grantee_land_banker_id);
