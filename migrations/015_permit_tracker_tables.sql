-- 015_permit_tracker_tables.sql
-- Create Permit Tracker module-specific tables in the shared database.
-- PT jurisdictions map to the shared jurisdictions table.
-- PT subdivisions map to the shared subdivisions table (watched flag already there).
-- PT builders map to the shared builders table.
-- All permit-specific tables are prefixed with pt_.

--------------------------------------------------------------------
-- 1. Permit jurisdiction config (portal details per jurisdiction)
--------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS pt_jurisdiction_config (
    id                  SERIAL PRIMARY KEY,
    jurisdiction_id     INTEGER NOT NULL REFERENCES jurisdictions(id) UNIQUE,
    adapter_slug        TEXT NOT NULL,
    adapter_class       TEXT NOT NULL,
    portal_type         TEXT NOT NULL,
    portal_url          TEXT NOT NULL,
    scrape_mode         TEXT DEFAULT 'live',  -- live / research-only
    fragile_note        TEXT,
    config_json         JSONB DEFAULT '{}',
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

--------------------------------------------------------------------
-- 2. Permits (core fact table)
--------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS pt_permits (
    id                              SERIAL PRIMARY KEY,
    permit_number                   TEXT NOT NULL,
    jurisdiction_id                 INTEGER NOT NULL REFERENCES jurisdictions(id),
    subdivision_id                  INTEGER REFERENCES subdivisions(id),
    builder_id                      INTEGER REFERENCES builders(id),
    address                         TEXT NOT NULL,
    parcel_id                       TEXT,
    issue_date                      DATE NOT NULL,
    status                          TEXT NOT NULL,
    permit_type                     TEXT NOT NULL,
    valuation                       NUMERIC(14, 2),
    raw_subdivision_name            TEXT,
    raw_contractor_name             TEXT,
    raw_applicant_name              TEXT,
    raw_licensed_professional_name  TEXT,
    latitude                        DOUBLE PRECISION,
    longitude                       DOUBLE PRECISION,
    first_seen_at                   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_updated_at                 TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen_at                    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(jurisdiction_id, permit_number)
);

CREATE INDEX IF NOT EXISTS idx_pt_permits_jurisdiction_id ON pt_permits (jurisdiction_id);
CREATE INDEX IF NOT EXISTS idx_pt_permits_subdivision_id  ON pt_permits (subdivision_id);
CREATE INDEX IF NOT EXISTS idx_pt_permits_builder_id      ON pt_permits (builder_id);
CREATE INDEX IF NOT EXISTS idx_pt_permits_issue_date      ON pt_permits (issue_date);

--------------------------------------------------------------------
-- 3. Scrape runs (audit log)
--------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS pt_scrape_runs (
    id                  SERIAL PRIMARY KEY,
    jurisdiction_id     INTEGER NOT NULL REFERENCES jurisdictions(id),
    run_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    status              TEXT NOT NULL,
    permits_found       INTEGER NOT NULL DEFAULT 0,
    permits_new         INTEGER NOT NULL DEFAULT 0,
    permits_updated     INTEGER NOT NULL DEFAULT 0,
    error_log           TEXT
);

--------------------------------------------------------------------
-- 4. Scrape payload archives
--------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS pt_scrape_payload_archives (
    id                  SERIAL PRIMARY KEY,
    jurisdiction_id     INTEGER NOT NULL REFERENCES jurisdictions(id),
    run_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    status              TEXT NOT NULL,
    permits_count       INTEGER NOT NULL DEFAULT 0,
    source_start_date   DATE,
    source_end_date     DATE,
    payload_json        JSONB NOT NULL
);

--------------------------------------------------------------------
-- 5. Scrape jobs (durable queue with lease-based concurrency)
--------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS pt_scrape_jobs (
    id                      SERIAL PRIMARY KEY,
    jurisdiction_name       TEXT,  -- NULL = scrape all
    status                  TEXT NOT NULL DEFAULT 'pending',
    trigger_type            TEXT NOT NULL,
    request_payload_json    JSONB NOT NULL DEFAULT '{}',
    attempt_count           INTEGER NOT NULL DEFAULT 0,
    max_attempts            INTEGER NOT NULL DEFAULT 1,
    retry_of_job_id         INTEGER REFERENCES pt_scrape_jobs(id),
    queued_at               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at              TIMESTAMPTZ,
    lease_expires_at        TIMESTAMPTZ,
    finished_at             TIMESTAMPTZ,
    last_error              TEXT,
    result_summary_json     JSONB,
    scrape_run_id           INTEGER REFERENCES pt_scrape_runs(id)
);

CREATE INDEX IF NOT EXISTS idx_pt_scrape_jobs_status_queued
    ON pt_scrape_jobs (status, queued_at);
CREATE INDEX IF NOT EXISTS idx_pt_scrape_jobs_jurisdiction_status
    ON pt_scrape_jobs (jurisdiction_name, status);
CREATE INDEX IF NOT EXISTS idx_pt_scrape_jobs_lease
    ON pt_scrape_jobs (lease_expires_at);

-- Prevent duplicate active jobs for the same scope
CREATE UNIQUE INDEX IF NOT EXISTS idx_pt_scrape_jobs_active_scope
    ON pt_scrape_jobs (COALESCE(jurisdiction_name, '__all__'))
    WHERE status IN ('pending', 'running');

--------------------------------------------------------------------
-- 6. Scraper artifacts (HTTP traces for debugging)
--------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS pt_scraper_artifacts (
    id                  SERIAL PRIMARY KEY,
    jurisdiction_id     INTEGER REFERENCES jurisdictions(id),
    adapter_slug        TEXT NOT NULL,
    scrape_job_id       INTEGER REFERENCES pt_scrape_jobs(id),
    scrape_run_id       INTEGER REFERENCES pt_scrape_runs(id),
    artifact_type       TEXT NOT NULL,
    method              TEXT,
    url                 TEXT,
    status_code         INTEGER,
    content_type        TEXT,
    excerpt_text        TEXT,
    metadata_json       JSONB NOT NULL DEFAULT '{}',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_pt_artifacts_created
    ON pt_scraper_artifacts (created_at DESC, id DESC);
CREATE INDEX IF NOT EXISTS idx_pt_artifacts_adapter
    ON pt_scraper_artifacts (adapter_slug, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_pt_artifacts_job
    ON pt_scraper_artifacts (scrape_job_id);

--------------------------------------------------------------------
-- 7. Geocode cache (Census Bureau results)
--------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS pt_geocode_cache (
    address             TEXT PRIMARY KEY,
    latitude            DOUBLE PRECISION,
    longitude           DOUBLE PRECISION,
    matched_address     TEXT,
    match_type          TEXT,
    match_status        TEXT NOT NULL,
    geocoded_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

--------------------------------------------------------------------
-- 8. Parcel lookup cache (Bay County ArcGIS)
--------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS pt_parcel_lookup_cache (
    address             TEXT PRIMARY KEY,
    parcel_id           TEXT,
    matched_address     TEXT,
    site_address        TEXT,
    owner_name          TEXT,
    match_type          TEXT,
    match_status        TEXT NOT NULL,
    looked_up_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

--------------------------------------------------------------------
-- 9. Adapter record cache (per-adapter persistent cache)
--------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS pt_adapter_record_cache (
    adapter_slug    TEXT NOT NULL,
    record_key      TEXT NOT NULL,
    payload_json    JSONB NOT NULL,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (adapter_slug, record_key)
);

--------------------------------------------------------------------
-- 10. Adapter state (per-adapter key-value state)
--------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS pt_adapter_state (
    adapter_slug    TEXT NOT NULL,
    state_key       TEXT NOT NULL,
    state_value     TEXT NOT NULL,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (adapter_slug, state_key)
);
