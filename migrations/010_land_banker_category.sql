-- 010: Add category column to land_bankers table.
-- Categories: 'land_banker', 'developer', 'btr' (build-to-rent).
-- This distinguishes circular lot-pipeline entities from one-way developers
-- and institutional bulk buyers of finished homes.

ALTER TABLE land_bankers
    ADD COLUMN IF NOT EXISTS category TEXT;
