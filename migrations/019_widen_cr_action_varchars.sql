-- Widen varchar columns on cr_entitlement_actions that are too narrow for
-- real-world zoning/land-use descriptions extracted from meeting documents.
-- Example: "A-R Agricultural Residential District, A-C Agricultural District,
-- and C-2 General Commercial Districts" exceeds varchar(100).

ALTER TABLE cr_entitlement_actions ALTER COLUMN current_zoning TYPE varchar(500);
ALTER TABLE cr_entitlement_actions ALTER COLUMN proposed_zoning TYPE varchar(500);
ALTER TABLE cr_entitlement_actions ALTER COLUMN current_land_use TYPE varchar(500);
ALTER TABLE cr_entitlement_actions ALTER COLUMN proposed_land_use TYPE varchar(500);
ALTER TABLE cr_entitlement_actions ALTER COLUMN vote_detail TYPE varchar(2000);
ALTER TABLE cr_entitlement_actions ALTER COLUMN action_requested TYPE varchar(500);
ALTER TABLE cr_entitlement_actions ALTER COLUMN case_number TYPE varchar(255);
