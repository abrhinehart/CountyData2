-- 017: Purge orphan builders created by legacy permit auto-insert.
--
-- These are 1,369 rows with source='permit_auto' and no corresponding
-- builder_aliases entry.  They are electricians, plumbers, AC techs,
-- owner-builders — not home builders.  Zero parcels reference them;
-- 743 permits do, which we null out first.

BEGIN;

-- 1. Unlink permits that reference orphan builders (set builder_id to NULL).
UPDATE pt_permits
SET    builder_id = NULL
WHERE  builder_id IN (
    SELECT b.id
    FROM   builders b
    WHERE  NOT EXISTS (
        SELECT 1 FROM builder_aliases ba WHERE ba.builder_id = b.id
    )
);

-- 2. Delete the orphan builder rows.
DELETE FROM builders
WHERE  id NOT IN (SELECT builder_id FROM builder_aliases);

COMMIT;
