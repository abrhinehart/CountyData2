-- 022: Add inspections_json to permits, structured_event_items to CR source documents
ALTER TABLE pt_permits ADD COLUMN IF NOT EXISTS inspections_json JSONB;
ALTER TABLE cr_source_documents ADD COLUMN IF NOT EXISTS structured_event_items JSONB;
