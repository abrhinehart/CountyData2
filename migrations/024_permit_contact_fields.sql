-- 024: Add raw applicant/contractor contact fields to pt_permits (ACCELA-04).
-- Structured Contacts DOM Parse — extracts applicant company/phone/email and
-- contractor license type/number from the Accela CapDetail Applicant /
-- Licensed Professional sections.  See docs/api-maps/polk-county-accela.md
-- §4 and the adapter docstring for live-recon evidence (Polk BR-2026-2894).
ALTER TABLE pt_permits ADD COLUMN IF NOT EXISTS raw_applicant_company TEXT;
ALTER TABLE pt_permits ADD COLUMN IF NOT EXISTS raw_applicant_address TEXT;
ALTER TABLE pt_permits ADD COLUMN IF NOT EXISTS raw_applicant_phone TEXT;
ALTER TABLE pt_permits ADD COLUMN IF NOT EXISTS raw_applicant_email TEXT;
ALTER TABLE pt_permits ADD COLUMN IF NOT EXISTS raw_contractor_license_number TEXT;
ALTER TABLE pt_permits ADD COLUMN IF NOT EXISTS raw_contractor_license_type TEXT;
