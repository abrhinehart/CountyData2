-- Add classification column to subdivisions to distinguish active developments
-- from scattered lots (builder purchases in decades-old neighborhoods).
-- Default is 'scattered'; curated-list promotion happens via seed_reference_data.py.

ALTER TABLE subdivisions ADD COLUMN IF NOT EXISTS classification VARCHAR(30) DEFAULT 'scattered';

-- Promote subdivisions that have Commission Radar entitlement actions
UPDATE subdivisions SET classification = 'active_development'
WHERE classification = 'scattered'
  AND id IN (
    SELECT DISTINCT subdivision_id
    FROM cr_entitlement_actions
    WHERE subdivision_id IS NOT NULL
  );

-- Promote subdivisions with 3+ builder-owned active parcels
UPDATE subdivisions SET classification = 'active_development'
WHERE classification = 'scattered'
  AND id IN (
    SELECT subdivision_id
    FROM parcels
    WHERE subdivision_id IS NOT NULL
      AND builder_id IS NOT NULL
      AND is_active = true
    GROUP BY subdivision_id
    HAVING COUNT(*) >= 3
  );
