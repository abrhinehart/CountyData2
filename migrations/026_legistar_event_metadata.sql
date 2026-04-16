-- 026: Add Legistar per-event metadata to cr_source_documents (LEGISTAR-04).
-- Fields captured from the /events list payload; no additional API calls.
-- See docs/api-maps/polk-county-legistar.md §3 and the LEGISTAR-04 ticket.
ALTER TABLE cr_source_documents ADD COLUMN IF NOT EXISTS event_portal_url TEXT;
ALTER TABLE cr_source_documents ADD COLUMN IF NOT EXISTS event_location TEXT;
ALTER TABLE cr_source_documents ADD COLUMN IF NOT EXISTS event_time TEXT;
ALTER TABLE cr_source_documents ADD COLUMN IF NOT EXISTS event_comment TEXT;
ALTER TABLE cr_source_documents ADD COLUMN IF NOT EXISTS agenda_status_name VARCHAR(50);
ALTER TABLE cr_source_documents ADD COLUMN IF NOT EXISTS agenda_last_published_utc TIMESTAMP WITH TIME ZONE;
ALTER TABLE cr_source_documents ADD COLUMN IF NOT EXISTS minutes_status_name VARCHAR(50);
ALTER TABLE cr_source_documents ADD COLUMN IF NOT EXISTS minutes_last_published_utc TIMESTAMP WITH TIME ZONE;
