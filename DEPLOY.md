# Deployment — Lookup-Based Matching Refactor

## Prerequisites
- PostgreSQL running (Docker: `docker-compose up -d`)
- `.env` configured with `DATABASE_URL`
- Python deps installed (`psycopg2`, `pyyaml`, `pandas`, `openpyxl`)

## Steps

### 1. Run schema migrations
```bash
psql "$DATABASE_URL" -f migrations/001_reference_tables.sql
psql "$DATABASE_URL" -f migrations/002_alter_transactions.sql
```
These are additive — safe to run on an existing database with data.

### 2. Curate reference data
Edit the YAML files with your known subdivisions and builders:
- `reference_data/subdivisions.yaml` — add entries per county
- `reference_data/builders.yaml` — add builder canonical names + aliases

### 3. Seed reference tables
```bash
python seed_reference_data.py
```
Idempotent — safe to re-run after adding new entries.

### 4. Run ETL
```bash
python etl.py                    # all counties
python etl.py --county Bay       # single county
```
Pipeline now uses lookup matching first, falls back to regex for unmatched rows. Unmatched rows get `review_flag=TRUE`.

### 5. Backfill existing data (one-time)
```bash
python migrations/003_backfill.py
```
Populates `legal_raw`, `subdivision_id`, and `builder_id` on rows already in the database.

### 6. Review unmatched rows
```bash
python export.py --unmatched-only --out unmatched_review.xlsx
```
Use this to find missing subdivisions/builders, add them to the YAML files, re-seed, and re-run ETL.

## New CLI flags (export.py)
- `--include-raw` — adds the full `legal_raw` column to the export
- `--unmatched-only` — filters to only rows where lookup matching failed

## What changed
- **transformer.py** — multi-party splitting, builder promotion, `legal_raw` (no truncation), lookup-first subdivision/phase matching
- **loader.py** — upserts 4 new columns (legal_raw, subdivision_id, builder_id, review_flag)
- **etl.py** — loads matchers once at startup, passes them through the pipeline
- **New: utils/lookup.py** — SubdivisionMatcher (longest-match substring) + BuilderMatcher (normalized exact match)
