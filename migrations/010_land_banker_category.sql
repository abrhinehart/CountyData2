-- 010: Add category column to land_bankers table.
-- Categories: 'land_banker', 'developer', 'btr' (build-to-rent).
-- After migration 013, land_bankers is merged into builders, so this is a no-op.

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables
               WHERE table_schema = 'public' AND table_name = 'land_bankers') THEN
        ALTER TABLE land_bankers ADD COLUMN IF NOT EXISTS category TEXT;
    END IF;
END $$;
