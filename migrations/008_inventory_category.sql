ALTER TABLE transactions
ADD COLUMN IF NOT EXISTS inventory_category TEXT;

CREATE INDEX IF NOT EXISTS idx_transactions_inventory_category
    ON transactions (inventory_category)
    WHERE inventory_category IS NOT NULL;
