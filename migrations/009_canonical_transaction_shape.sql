DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'transactions'
          AND column_name = 'legal_desc'
    ) AND NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'transactions'
          AND column_name = 'export_legal_desc'
    ) THEN
        ALTER TABLE transactions RENAME COLUMN legal_desc TO export_legal_desc;
    END IF;
END $$;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'transactions'
          AND column_name = 'legal_raw'
    ) AND NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'transactions'
          AND column_name = 'export_legal_raw'
    ) THEN
        ALTER TABLE transactions RENAME COLUMN legal_raw TO export_legal_raw;
    END IF;
END $$;

ALTER TABLE transactions
    ADD COLUMN IF NOT EXISTS deed_legal_desc TEXT,
    ADD COLUMN IF NOT EXISTS deed_legal_parsed JSONB DEFAULT '{}'::jsonb,
    ADD COLUMN IF NOT EXISTS acres_source TEXT;

ALTER TABLE transaction_segments
    ADD COLUMN IF NOT EXISTS inventory_category TEXT;

CREATE INDEX IF NOT EXISTS idx_transaction_segments_inventory_category
    ON transaction_segments (inventory_category)
    WHERE inventory_category IS NOT NULL;

UPDATE transactions
SET acres_source = NULLIF(parsed_data->>'acres_source', '')
WHERE acres_source IS NULL
  AND parsed_data ? 'acres_source';

UPDATE transaction_segments
SET inventory_category = NULLIF(segment_data->>'inventory_category', '')
WHERE inventory_category IS NULL
  AND segment_data ? 'inventory_category';
