-- 002_alter_transactions.sql
-- Adds lookup columns and legal_raw to the transactions table.

ALTER TABLE transactions
    ADD COLUMN IF NOT EXISTS legal_raw       TEXT,
    ADD COLUMN IF NOT EXISTS subdivision_id  INTEGER REFERENCES subdivisions(id),
    ADD COLUMN IF NOT EXISTS builder_id      INTEGER REFERENCES builders(id),
    ADD COLUMN IF NOT EXISTS review_flag     BOOLEAN DEFAULT FALSE;

CREATE INDEX IF NOT EXISTS idx_transactions_review_flag
    ON transactions (review_flag) WHERE review_flag = TRUE;

CREATE INDEX IF NOT EXISTS idx_transactions_subdivision_id
    ON transactions (subdivision_id);

CREATE INDEX IF NOT EXISTS idx_transactions_builder_id
    ON transactions (builder_id);
