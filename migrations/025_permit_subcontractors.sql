-- 025: Add subcontractor list to pt_permits (ACCELA-04a).
-- Captures the "View Additional Licensed Professionals>>" enumerated list from
-- the Accela CapDetail flat text.  Serialized as
-- "NAME|LICENSE_NUMBER|LICENSE_TYPE" per LP, joined by "; " between LPs.
-- See docs/api-maps/polk-county-accela.md §4 (Additional Licensed Professionals
-- subsection) and the adapter docstring for live-recon evidence (Polk
-- BR-2026-2659 observed with 4 subcontractors: roofing, plumbing, general,
-- electrical).
ALTER TABLE pt_permits ADD COLUMN IF NOT EXISTS raw_additional_licensed_professionals TEXT;
