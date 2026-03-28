ALTER TABLE transactions
ADD COLUMN IF NOT EXISTS deed_locator JSONB DEFAULT '{}'::jsonb;
