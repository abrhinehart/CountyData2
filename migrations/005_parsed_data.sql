-- 005_parsed_data.sql
-- Stores parser output so extracted categories are preserved end-to-end.

ALTER TABLE transactions
    ADD COLUMN IF NOT EXISTS parsed_data JSONB DEFAULT '{}'::jsonb;
