-- 012: Add mortgage enrichment fields to transactions table.
-- mortgage_amount: loan amount from matched mortgage record (proxy for sale price in non-disclosure states)
-- mortgage_originator: lender name from matched mortgage record

ALTER TABLE transactions
    ADD COLUMN IF NOT EXISTS mortgage_amount NUMERIC(15, 2);

ALTER TABLE transactions
    ADD COLUMN IF NOT EXISTS mortgage_originator TEXT;
