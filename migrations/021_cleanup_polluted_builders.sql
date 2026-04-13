-- 021: Clean up builder table pollution (round 2).
--
-- Migration 017 purged ~1,369 orphan builders, but the table has been
-- re-polluted with auto-inserted contractor names that are not home
-- builders.  This migration:
--   1. NULLs out FK references to polluted builders in pt_permits,
--      transactions, and parcels.
--   2. DELETEs builders with source='permit_auto' and no builder_aliases.
--   3. As a safety net, DELETEs any remaining builders that have no
--      builder_aliases, are not source='seed', and are not referenced
--      by any remaining FK.

BEGIN;

-- Identify polluted builder IDs: source='permit_auto' with no aliases.
-- Also catch rows that defaulted to source='manual' but were clearly
-- auto-inserted (no aliases, not seeded).

-- Step 1: NULL out builder_id on pt_permits referencing polluted builders.
UPDATE pt_permits
SET    builder_id = NULL
WHERE  builder_id IN (
    SELECT b.id
    FROM   builders b
    WHERE  b.source = 'permit_auto'
      AND  NOT EXISTS (
          SELECT 1 FROM builder_aliases ba WHERE ba.builder_id = b.id
      )
);

-- Step 2: NULL out builder_id / grantor_builder_id / grantee_builder_id
-- on transactions referencing polluted builders.
UPDATE transactions
SET    builder_id = NULL
WHERE  builder_id IS NOT NULL
  AND  builder_id IN (
    SELECT b.id
    FROM   builders b
    WHERE  b.source = 'permit_auto'
      AND  NOT EXISTS (
          SELECT 1 FROM builder_aliases ba WHERE ba.builder_id = b.id
      )
);

UPDATE transactions
SET    grantor_builder_id = NULL
WHERE  grantor_builder_id IS NOT NULL
  AND  grantor_builder_id IN (
    SELECT b.id
    FROM   builders b
    WHERE  b.source = 'permit_auto'
      AND  NOT EXISTS (
          SELECT 1 FROM builder_aliases ba WHERE ba.builder_id = b.id
      )
);

UPDATE transactions
SET    grantee_builder_id = NULL
WHERE  grantee_builder_id IS NOT NULL
  AND  grantee_builder_id IN (
    SELECT b.id
    FROM   builders b
    WHERE  b.source = 'permit_auto'
      AND  NOT EXISTS (
          SELECT 1 FROM builder_aliases ba WHERE ba.builder_id = b.id
      )
);

-- Step 3: NULL out builder_id on parcels referencing polluted builders (defensive).
UPDATE parcels
SET    builder_id = NULL
WHERE  builder_id IS NOT NULL
  AND  builder_id IN (
    SELECT b.id
    FROM   builders b
    WHERE  b.source = 'permit_auto'
      AND  NOT EXISTS (
          SELECT 1 FROM builder_aliases ba WHERE ba.builder_id = b.id
      )
);

-- Step 4: DELETE polluted builders (source='permit_auto', no aliases).
WITH polluted AS (
    SELECT b.id
    FROM   builders b
    WHERE  b.source = 'permit_auto'
      AND  NOT EXISTS (
          SELECT 1 FROM builder_aliases ba WHERE ba.builder_id = b.id
      )
)
DELETE FROM builders WHERE id IN (SELECT id FROM polluted);

-- Step 5: Safety-net pass — delete any remaining builders that:
--   * have no builder_aliases
--   * are not source='seed'
--   * are not referenced by any remaining FK in pt_permits, parcels, or transactions
WITH unreferenced AS (
    SELECT b.id
    FROM   builders b
    WHERE  b.source != 'seed'
      AND  NOT EXISTS (
          SELECT 1 FROM builder_aliases ba WHERE ba.builder_id = b.id
      )
      AND  NOT EXISTS (
          SELECT 1 FROM pt_permits pp WHERE pp.builder_id = b.id
      )
      AND  NOT EXISTS (
          SELECT 1 FROM parcels p WHERE p.builder_id = b.id
      )
      AND  NOT EXISTS (
          SELECT 1 FROM transactions t
          WHERE t.builder_id = b.id
             OR t.grantor_builder_id = b.id
             OR t.grantee_builder_id = b.id
      )
)
DELETE FROM builders WHERE id IN (SELECT id FROM unreferenced);

COMMIT;
