-- 013_shared_foundation.sql
-- Establish the shared foundation tables for the unified platform.
-- Extends counties, subdivisions, builders. Creates jurisdictions, phases,
-- builder_counties, lookup_categories. Merges land_bankers into builders.
--
-- Fully idempotent: safe to re-run.

--------------------------------------------------------------------
-- 1. Extend counties: add state, FIPS, DOR number
--------------------------------------------------------------------

ALTER TABLE counties ADD COLUMN IF NOT EXISTS state VARCHAR(2) NOT NULL DEFAULT 'FL';
ALTER TABLE counties ADD COLUMN IF NOT EXISTS dor_county_no INTEGER;
ALTER TABLE counties ADD COLUMN IF NOT EXISTS county_fips VARCHAR(10);
ALTER TABLE counties ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT true;
ALTER TABLE counties ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();

-- Change unique constraint from name-only to (name, state)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'counties_name_key') THEN
        ALTER TABLE counties DROP CONSTRAINT counties_name_key;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'counties_name_state_key') THEN
        ALTER TABLE counties ADD CONSTRAINT counties_name_state_key UNIQUE(name, state);
    END IF;
END $$;

--------------------------------------------------------------------
-- 2. Jurisdictions (counties-as-governments + municipalities)
--------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS jurisdictions (
    id                  SERIAL PRIMARY KEY,
    slug                VARCHAR(100) UNIQUE,
    name                TEXT NOT NULL,
    county_id           INTEGER NOT NULL REFERENCES counties(id),
    municipality        VARCHAR(100),
    jurisdiction_type   VARCHAR(50),   -- county / city / town / village
    is_active           BOOLEAN DEFAULT true,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(name, county_id)
);

--------------------------------------------------------------------
-- 3. Extend subdivisions with entitlement + shared fields
--------------------------------------------------------------------

ALTER TABLE subdivisions ADD COLUMN IF NOT EXISTS entitlement_status  VARCHAR(50) DEFAULT 'not_started';
ALTER TABLE subdivisions ADD COLUMN IF NOT EXISTS lifecycle_stage     VARCHAR(50);
ALTER TABLE subdivisions ADD COLUMN IF NOT EXISTS last_action_date    DATE;
ALTER TABLE subdivisions ADD COLUMN IF NOT EXISTS next_expected_action VARCHAR(100);
ALTER TABLE subdivisions ADD COLUMN IF NOT EXISTS location_description TEXT;
ALTER TABLE subdivisions ADD COLUMN IF NOT EXISTS proposed_land_use   VARCHAR(100);
ALTER TABLE subdivisions ADD COLUMN IF NOT EXISTS proposed_zoning     VARCHAR(100);
ALTER TABLE subdivisions ADD COLUMN IF NOT EXISTS watched             BOOLEAN DEFAULT false;
ALTER TABLE subdivisions ADD COLUMN IF NOT EXISTS notes               TEXT;
ALTER TABLE subdivisions ADD COLUMN IF NOT EXISTS is_active           BOOLEAN DEFAULT true;

-- Add source column to subdivision_aliases
ALTER TABLE subdivision_aliases ADD COLUMN IF NOT EXISTS source     VARCHAR(20) DEFAULT 'manual';
ALTER TABLE subdivision_aliases ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW();

--------------------------------------------------------------------
-- 4. Phases table (replaces subdivisions.phases TEXT[])
--------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS phases (
    id                  SERIAL PRIMARY KEY,
    subdivision_id      INTEGER NOT NULL REFERENCES subdivisions(id) ON DELETE CASCADE,
    name                TEXT NOT NULL,
    acreage             DOUBLE PRECISION,
    lot_count           INTEGER,
    proposed_land_use   VARCHAR(100),
    proposed_zoning     VARCHAR(100),
    entitlement_status  VARCHAR(50) DEFAULT 'not_started',
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(subdivision_id, name)
);

-- Migrate existing phase data from subdivisions.phases array into rows
INSERT INTO phases (subdivision_id, name)
SELECT s.id, unnest(s.phases)
FROM subdivisions s
WHERE array_length(s.phases, 1) > 0
ON CONFLICT (subdivision_id, name) DO NOTHING;

--------------------------------------------------------------------
-- 5. Extend builders with type, scope, active flag
--------------------------------------------------------------------

ALTER TABLE builders ADD COLUMN IF NOT EXISTS type      VARCHAR(20) NOT NULL DEFAULT 'builder';
ALTER TABLE builders ADD COLUMN IF NOT EXISTS scope     VARCHAR(20) NOT NULL DEFAULT 'national';
ALTER TABLE builders ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT true;
ALTER TABLE builders ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();

--------------------------------------------------------------------
-- 6. Builder-county junction (for regional scope filtering)
--------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS builder_counties (
    id          SERIAL PRIMARY KEY,
    builder_id  INTEGER NOT NULL REFERENCES builders(id) ON DELETE CASCADE,
    county_id   INTEGER NOT NULL REFERENCES counties(id) ON DELETE CASCADE,
    UNIQUE(builder_id, county_id)
);

--------------------------------------------------------------------
-- 7. Shared lookup table for categorical variables
--------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS lookup_categories (
    id          SERIAL PRIMARY KEY,
    domain      VARCHAR(50) NOT NULL,
    code        VARCHAR(50) NOT NULL,
    label       TEXT NOT NULL,
    description TEXT,
    sort_order  INTEGER DEFAULT 0,
    is_active   BOOLEAN DEFAULT true,
    UNIQUE(domain, code)
);

-- Seed initial categories
INSERT INTO lookup_categories (domain, code, label, description, sort_order) VALUES
    -- Transaction types (CD2)
    ('transaction_type', 'house_sale',           'House Sale',            'Builder sells to non-builder, non-land-banker buyer', 1),
    ('transaction_type', 'builder_purchase',     'Builder Purchase',      'Non-builder sells to a builder', 2),
    ('transaction_type', 'builder_to_builder',   'Builder to Builder',    'Builder on both sides of the transaction', 3),
    ('transaction_type', 'land_banker_purchase',  'Land Banker Purchase', 'Someone sells to a land banker or developer', 4),
    ('transaction_type', 'btr_purchase',          'Build-to-Rent Purchase','Someone sells to a BTR entity', 5),
    ('transaction_type', 'raw_land_purchase',     'Raw Land Purchase',    'Builder or land banker buys unplatted acreage', 6),
    ('transaction_type', 'cdd_transfer',          'CDD Transfer',         'Grantee is a Community Development District', 7),
    ('transaction_type', 'association_transfer',  'Association Transfer',  'Grantee is an HOA/POA/condo association', 8),
    ('transaction_type', 'correction_quit_claim', 'Correction / Quit Claim', 'Quit claim deed or corrective instrument', 9),
    -- Parcel classifications (BI)
    ('parcel_class', 'lot',         'Lot',         'Individual buildable lot', 1),
    ('parcel_class', 'common_area', 'Common Area', 'Retention ponds, buffers, ROW, amenities', 2),
    ('parcel_class', 'tract',       'Tract',       'Unplatted large acreage', 3),
    ('parcel_class', 'other',       'Other',       'Commercial, institutional, or unclassified', 4),
    -- Builder entity types
    ('builder_type', 'builder',      'Builder',      'Production homebuilder', 1),
    ('builder_type', 'developer',    'Developer',    'Land developer — develops and sells lots', 2),
    ('builder_type', 'land_banker',  'Land Banker',  'Holds lots in circular pipeline with builder', 3),
    ('builder_type', 'btr',          'BTR',          'Build-to-rent fund', 4),
    -- Entitlement approval types (CR)
    ('approval_type', 'annexation',          'Annexation',          'Municipal boundary annexation', 1),
    ('approval_type', 'land_use',            'Land Use',            'Comprehensive plan / FLUM amendment', 2),
    ('approval_type', 'zoning',              'Zoning',              'Rezoning or PUD approval', 3),
    ('approval_type', 'development_review',  'Development Review',  'Site plan or major development review', 4),
    ('approval_type', 'subdivision',         'Subdivision',         'Plat approval', 5),
    ('approval_type', 'developer_agreement', 'Developer Agreement', 'Developer agreement approval', 6),
    ('approval_type', 'conditional_use',     'Conditional Use',     'Conditional or special use permit', 7),
    ('approval_type', 'text_amendment',      'Text Amendment',      'Code or ordinance text amendment', 8),
    -- Entitlement outcomes (CR)
    ('entitlement_outcome', 'recommended_approval', 'Recommended Approval', NULL, 1),
    ('entitlement_outcome', 'recommended_denial',   'Recommended Denial',   NULL, 2),
    ('entitlement_outcome', 'approved',              'Approved',             NULL, 3),
    ('entitlement_outcome', 'denied',                'Denied',               NULL, 4),
    ('entitlement_outcome', 'tabled',                'Tabled',               NULL, 5),
    ('entitlement_outcome', 'deferred',              'Deferred',             NULL, 6),
    ('entitlement_outcome', 'withdrawn',             'Withdrawn',            NULL, 7),
    ('entitlement_outcome', 'modified',              'Modified',             NULL, 8),
    ('entitlement_outcome', 'remanded',              'Remanded',             NULL, 9),
    -- Lifecycle stages (shared)
    ('lifecycle_stage', 'not_started',     'Not Started',     'No entitlement actions yet', 1),
    ('lifecycle_stage', 'planning_board',  'Planning Board',  'In front of planning board', 2),
    ('lifecycle_stage', 'first_reading',   'First Reading',   'Commission first reading', 3),
    ('lifecycle_stage', 'second_reading',  'Second Reading',  'Commission second/final reading', 4),
    ('lifecycle_stage', 'subdivision',     'Subdivision',     'Plat approved, not yet built', 5),
    ('lifecycle_stage', 'complete',        'Complete',        'Fully entitled and platted', 6),
    -- Inventory categories (CD2)
    ('inventory_category', 'scattered_legacy_lots', 'Scattered Legacy Lots', 'Infill lots in older subdivisions', 1)
ON CONFLICT (domain, code) DO NOTHING;

--------------------------------------------------------------------
-- 8. Merge land_bankers into builders
--------------------------------------------------------------------

DO $$
BEGIN
    -- Only run if land_bankers table still exists
    IF EXISTS (SELECT 1 FROM information_schema.tables
               WHERE table_schema = 'public' AND table_name = 'land_bankers') THEN

        -- 8a: Insert land_bankers as builders with correct type
        INSERT INTO builders (canonical_name, type, scope, is_active)
        SELECT
            lb.canonical_name,
            COALESCE(lb.category, 'land_banker'),
            'national',
            true
        FROM land_bankers lb
        ON CONFLICT (canonical_name) DO UPDATE SET type = EXCLUDED.type;

        -- 8b: Move land_banker_aliases to builder_aliases
        INSERT INTO builder_aliases (builder_id, alias)
        SELECT b.id, la.alias
        FROM land_banker_aliases la
        JOIN land_bankers lb ON la.land_banker_id = lb.id
        JOIN builders b ON b.canonical_name = lb.canonical_name
        ON CONFLICT (alias) DO NOTHING;

        -- 8c: Drop FK constraints on transaction land_banker columns
        IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'transactions_grantor_land_banker_id_fkey') THEN
            ALTER TABLE transactions DROP CONSTRAINT transactions_grantor_land_banker_id_fkey;
        END IF;
        IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'transactions_grantee_land_banker_id_fkey') THEN
            ALTER TABLE transactions DROP CONSTRAINT transactions_grantee_land_banker_id_fkey;
        END IF;

        -- 8d: Remap FK values from land_banker IDs to builder IDs
        UPDATE transactions t
        SET grantor_land_banker_id = b.id
        FROM land_bankers lb
        JOIN builders b ON b.canonical_name = lb.canonical_name
        WHERE t.grantor_land_banker_id = lb.id;

        UPDATE transactions t
        SET grantee_land_banker_id = b.id
        FROM land_bankers lb
        JOIN builders b ON b.canonical_name = lb.canonical_name
        WHERE t.grantee_land_banker_id = lb.id;

        -- 8e: Re-add FK constraints pointing to builders
        ALTER TABLE transactions ADD CONSTRAINT transactions_grantor_land_banker_id_fkey
            FOREIGN KEY (grantor_land_banker_id) REFERENCES builders(id);
        ALTER TABLE transactions ADD CONSTRAINT transactions_grantee_land_banker_id_fkey
            FOREIGN KEY (grantee_land_banker_id) REFERENCES builders(id);

        -- 8f: Drop old tables
        DROP TABLE IF EXISTS land_banker_aliases;
        DROP TABLE IF EXISTS land_bankers;

        RAISE NOTICE 'Land bankers merged into builders table.';
    END IF;
END $$;
