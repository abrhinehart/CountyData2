-- 023: Add raw owner fields to pt_permits (ACCELA-03).
-- Extracted from Accela CapDetail Owner section for Polk / Citrus / Lake Alfred / Winter Haven.
ALTER TABLE pt_permits ADD COLUMN IF NOT EXISTS raw_owner_name TEXT;
ALTER TABLE pt_permits ADD COLUMN IF NOT EXISTS raw_owner_address TEXT;
