-- 016_commission_radar_tables.sql
-- Create Commission Radar module-specific tables in the shared database.
-- CR "projects" merge into shared subdivisions (per reconciliation decision).
-- CR phases merge into shared phases (already migrated in 013).
-- CR project_aliases merge into shared subdivision_aliases.
-- Commission-specific jurisdiction fields move to cr_jurisdiction_config.
-- CR source_documents, entitlement_actions, commissioners, commissioner_votes
-- are module-owned with cr_ prefix.

--------------------------------------------------------------------
-- 1. Commission-specific jurisdiction config
--------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS cr_jurisdiction_config (
    id                      SERIAL PRIMARY KEY,
    jurisdiction_id         INTEGER NOT NULL REFERENCES jurisdictions(id) UNIQUE,
    commission_type         VARCHAR(50) NOT NULL,   -- city_commission, bcc, planning_board, planning_commission, boa, lpa
    agenda_source_url       VARCHAR(500),
    agenda_platform         VARCHAR(100),            -- civicplus, civicclerk, legistar, manual
    has_duplicate_page_bug  BOOLEAN DEFAULT false,
    pinned                  BOOLEAN DEFAULT false,
    config_json             TEXT,                    -- keywords, extraction_notes, detection_patterns, scraping params
    created_at              TIMESTAMPTZ DEFAULT NOW(),
    updated_at              TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_cr_jurisdiction_config_commission_type
    ON cr_jurisdiction_config (commission_type);

--------------------------------------------------------------------
-- 2. Source documents (agendas + minutes)
--------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS cr_source_documents (
    id                          SERIAL PRIMARY KEY,
    jurisdiction_id             INTEGER NOT NULL REFERENCES jurisdictions(id),
    filename                    VARCHAR(255) NOT NULL,
    file_hash                   VARCHAR(64),
    source_url                  VARCHAR(1000),
    external_document_id        VARCHAR(255),
    file_format                 VARCHAR(10),   -- pdf, html, docx
    document_type               VARCHAR(50) NOT NULL,  -- agenda, minutes
    meeting_date                DATE,
    page_count                  INTEGER,
    extracted_text_length       INTEGER,
    keyword_filter_passed       BOOLEAN,
    extraction_attempted        BOOLEAN DEFAULT false,
    extraction_successful       BOOLEAN,
    items_extracted             INTEGER,
    items_after_filtering       INTEGER,
    processing_status           VARCHAR(50) NOT NULL DEFAULT 'detected',
    failure_stage               VARCHAR(50),
    failure_reason              TEXT,
    processing_notes            TEXT,
    created_at                  TIMESTAMPTZ DEFAULT NOW(),
    updated_at                  TIMESTAMPTZ DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS ix_cr_source_documents_juris_hash
    ON cr_source_documents (jurisdiction_id, file_hash) WHERE file_hash IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS ix_cr_source_documents_juris_ext_id
    ON cr_source_documents (jurisdiction_id, external_document_id) WHERE external_document_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS ix_cr_source_documents_juris_source_url
    ON cr_source_documents (jurisdiction_id, source_url);
CREATE INDEX IF NOT EXISTS ix_cr_source_documents_juris_filename
    ON cr_source_documents (jurisdiction_id, filename);

--------------------------------------------------------------------
-- 3. Entitlement actions (core CR fact table)
--    FK points at shared subdivisions (formerly projects) and shared phases
--------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS cr_entitlement_actions (
    id                              SERIAL PRIMARY KEY,
    source_document_id              INTEGER REFERENCES cr_source_documents(id),
    subdivision_id                  INTEGER REFERENCES subdivisions(id),
    phase_id                        INTEGER REFERENCES phases(id),
    linked_action_id                INTEGER REFERENCES cr_entitlement_actions(id),

    -- Identifiers
    case_number                     VARCHAR(100),
    ordinance_number                VARCHAR(100),
    parcel_ids                      TEXT,   -- JSON array
    address                         VARCHAR(500),

    -- Action
    approval_type                   VARCHAR(50) NOT NULL,
    outcome                         VARCHAR(50),
    vote_detail                     VARCHAR(100),
    conditions                      TEXT,
    reading_number                  VARCHAR(20),
    scheduled_first_reading_date    DATE,
    scheduled_final_reading_date    DATE,

    -- Extracted content
    action_summary                  TEXT,
    applicant_name                  VARCHAR(255),
    current_land_use                VARCHAR(100),
    proposed_land_use               VARCHAR(100),
    current_zoning                  VARCHAR(100),
    proposed_zoning                 VARCHAR(100),
    acreage                         FLOAT,
    lot_count                       INTEGER,
    project_name                    VARCHAR(255),   -- raw extracted name (before subdivision matching)
    phase_name                      VARCHAR(100),   -- raw extracted name
    land_use_scale                  VARCHAR(20),    -- small_scale, large_scale
    action_requested                VARCHAR(100),

    -- Metadata
    meeting_date                    DATE,
    agenda_section                  VARCHAR(255),
    multi_project_flag              BOOLEAN DEFAULT false,
    backup_doc_filename             VARCHAR(255),
    needs_review                    BOOLEAN DEFAULT false,
    review_notes                    TEXT,

    created_at                      TIMESTAMPTZ DEFAULT NOW(),
    updated_at                      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_cr_actions_subdivision_id ON cr_entitlement_actions (subdivision_id);
CREATE INDEX IF NOT EXISTS idx_cr_actions_phase_id       ON cr_entitlement_actions (phase_id);
CREATE INDEX IF NOT EXISTS idx_cr_actions_source_doc_id  ON cr_entitlement_actions (source_document_id);
CREATE INDEX IF NOT EXISTS idx_cr_actions_meeting_date   ON cr_entitlement_actions (meeting_date);
CREATE INDEX IF NOT EXISTS idx_cr_actions_approval_type  ON cr_entitlement_actions (approval_type);

--------------------------------------------------------------------
-- 4. Commissioners
--------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS cr_commissioners (
    id              SERIAL PRIMARY KEY,
    jurisdiction_id INTEGER NOT NULL REFERENCES jurisdictions(id),
    name            VARCHAR(255) NOT NULL,
    title           VARCHAR(100),   -- Commissioner, Mayor, Chair, Vice Chair
    active          BOOLEAN DEFAULT true,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT uq_cr_commissioner_juris_name UNIQUE (jurisdiction_id, name)
);

CREATE INDEX IF NOT EXISTS idx_cr_commissioners_jurisdiction_id
    ON cr_commissioners (jurisdiction_id);

--------------------------------------------------------------------
-- 5. Commissioner votes
--------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS cr_commissioner_votes (
    id                      SERIAL PRIMARY KEY,
    entitlement_action_id   INTEGER NOT NULL REFERENCES cr_entitlement_actions(id) ON DELETE CASCADE,
    commissioner_id         INTEGER NOT NULL REFERENCES cr_commissioners(id) ON DELETE CASCADE,
    vote                    VARCHAR(20) NOT NULL,   -- yea, nay, abstain, absent
    made_motion             BOOLEAN DEFAULT false,
    seconded_motion         BOOLEAN DEFAULT false,
    created_at              TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_cr_votes_action_id       ON cr_commissioner_votes (entitlement_action_id);
CREATE INDEX IF NOT EXISTS idx_cr_votes_commissioner_id ON cr_commissioner_votes (commissioner_id);
