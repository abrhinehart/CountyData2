# Real Estate Intelligence Platform (CountyData2)

A unified Python + FastAPI + React platform that consolidates four formerly-separate real estate intelligence projects — **Sales** (deed transactions), **Builder Inventory** (GIS parcel snapshots), **Permit Tracker** (permit scraping), and **Commission Radar** (entitlement / commission agenda mining) — into a single application backed by one PostgreSQL + PostGIS database. The four modules share one spine of `counties`, `jurisdictions`, `subdivisions`, `builders`, and `phases`, so a click on a subdivision can pull its sales history, permit activity, parcel inventory, and entitlement timeline from a handful of joins.

(Older internal name: "Format All App". The Sales module is the original repo; the other three were merged in over Phases 2–4 of the unification project.)

---

## Status

See [STATUS.md](STATUS.md) (regenerated via `python scripts/status.py --write`) for current HEAD, counts, and pytest baseline. See [TODO.md](TODO.md) for the open-work backlog.

---

## Architecture

```
+----------------------------------------------------------------+
|                          UI (port 1560)                        |
|              React 19 + Vite + TanStack Query/Table            |
|              dev proxy: /api -> http://localhost:1460          |
+----------------------------------------------------------------+
                                 |
                                 v
+----------------------------------------------------------------+
|                       FastAPI (port 1460)                      |
|        api.py — app factory, CORS, /api/platform/health        |
|                                                                |
|   /api/*               sales      modules/sales/router.py      |
|   /api/inventory/*     inventory  modules/inventory/router.py  |
|   /api/permits/*       permits    modules/permits/router.py    |
|   /api/commission/*    commission modules/commission/router.py |
+----------------------------------------------------------------+
                                 |
                                 v
+----------------------------------------------------------------+
|        PostgreSQL 16 + PostGIS  (host port ${POSTGRES_PORT     |
|        :-5432} -> container 5432, see docker-compose.yml)      |
|                                                                |
|   Shared spine:  counties · jurisdictions · subdivisions       |
|                  builders · phases · transactions              |
|                                                                |
|   Module tables: bi_*  (snapshots, parcels, county_config)     |
|                  pt_*  (permits, jurisdiction_config,          |
|                         scrape_jobs, scraper_artifacts)        |
|                  cr_*  (jurisdiction_config, source_documents, |
|                         entitlement_actions, commissioners)    |
+----------------------------------------------------------------+
```

Architectural decisions worth knowing before you read code:

- **Two-level geography.** `counties` is the geographic anchor; `jurisdictions` is the institutional layer (cities, planning boards, commissions) that FK back to a county. Permits and Commission Radar both attach to jurisdictions; Sales and Inventory attach directly to counties.
- **Subdivisions are the cross-module join key.** Commission Radar's old `projects` table was merged directly into the shared `subdivisions` table during Phase 4. `Project` is now a Python alias for `Subdivision` inside `modules/commission/`. The 48,667+ subdivisions are visible to every module.
- **Unified builders + land bankers with a `category` column** instead of parallel tables (`category` ∈ {`builder`, `land_banker`, `developer`, `btr`}).
- **Module-specific config tables** (`bi_county_config`, `pt_jurisdiction_config`, `cr_jurisdiction_config`) hold per-module portal URLs, GIS endpoints, agenda platforms, and other settings — keeping the shared spine clean of module-specific clutter.
- **Prefix convention** for module-private tables: `bi_*`, `pt_*`, `cr_*`. The shared spine has no prefix.
- **SQLAlchemy and psycopg2 coexist on the same connection pool.** Inventory and Commission use SQLAlchemy ORM models; Sales and Permits use raw psycopg2 for performance and historical reasons. Both go through `shared/database.py` (psycopg2 pool) and `shared/sa_database.py` (SQLAlchemy session factory).

---

## Modules

### Sales — `modules/sales/`

The original CountyData2 ETL pipeline. Reads county clerk deed exports (Excel/CSV), normalizes parties / dates / legal descriptions / phases, classifies into 9 transaction types, and upserts into `transactions` with a deduplication key. Currently covers 9 Florida counties (Bay, Citrus, Escambia, Hernando, Marion, Okaloosa, Okeechobee, Santa Rosa, Walton) plus AL and MS counties added during the unification push, for **18,109 transactions** to date. Mature CLI surface (`etl.py`, `export.py`, `review_export.py`, `deed_queue_export.py`, `bay_price_extract.py`) plus a deed-legal benchmark harness under `tools/`.

**Entry points:** `etl.py`, `export.py`, `review_export.py`, `deed_queue_export.py`, `bay_price_extract.py`, FastAPI under `/api/*`.

### Builder Inventory — `modules/inventory/`

GIS parcel snapshotting. Reads parcel polygons from county ArcGIS REST endpoints, snapshots them into `parcels` (current state) + `bi_snapshots` (snapshot run metadata) + `bi_parcel_snapshots` (point-in-time history), discovers new subdivisions from parcel attributes, and tracks builder lot inventory over time. 48 county GIS configs are seeded; **Madison AL was the live-validated reference county** (4042 parcels, 166 new subdivisions, 61.7s end-to-end). A scheduler at `modules/inventory/scheduler.py` drives recurring runs.

**Entry points:** `seed_bi_county_config.py`, `/api/inventory/*`, `modules/inventory/scheduler.py`. There is **no BI CLI equivalent to Sales' `etl.py`** — runs are driven through the API or scheduler.

### Permit Tracker — `modules/permits/`

Scrapes building / development permits from county and city portals via per-portal adapter classes (iWorq, Accela ASP.NET ViewState, PRSF PDF, Cloudpermit JSON API). 7 jurisdiction configs are seeded; **3 are actively scraped and validated** — Bay County (PRSF PDF), Panama City Beach (iWorq, 46 permits + 114 trace artifacts), Polk County (Accela, 85 permits + 97 trace artifacts). Total **213 permits** captured. Scrape runs are tracked in `pt_scrape_jobs` and a `record_trace` mechanism captures every HTTP transaction in `pt_scraper_artifacts` for cold-path audit.

**Entry points:** `seed_pt_jurisdiction_config.py`, `/api/permits/*`. There is **no PT CLI beyond the seed script** — scrapes are triggered via the API.

### Commission Radar — `modules/commission/`

Mines city / county commission and planning board agendas + minutes for entitlement actions (rezones, comp plan amendments, plat approvals). Implemented as an **8-step Server-Sent Events pipeline**: convert PDFs/HTML/DOCX → keyword filter → Claude extract → threshold filter → packet enrichment → record insert → match to subdivisions → lifecycle refresh. Scrapes CivicPlus, CivicClerk, and Legistar portals. **98 FL jurisdiction configs** are seeded; 3 are live-validated (Panama City Commission, Pasco County PZ, Panama City Planning Board). The CR module is where `Project` is aliased to the shared `Subdivision` model.

**Entry points:** `seed_cr_jurisdiction_config.py`, `/api/commission/*`. Document processing is driven via the SSE endpoint, not a standalone CLI.

---

## Project structure

```
CountyData2/
  api.py                              # FastAPI app factory, CORS, /api/platform/*
  config.py                           # DB URL builder, env loading, constants
  apply_migrations.py                 # Idempotent SQL migration runner
  docker-compose.yml                  # PostgreSQL 16 + PostGIS service
  schema.sql                          # Initial-volume bootstrap schema
  counties.yaml                       # Sales module per-county ETL config
  county-registry.yaml                # Cross-project shared county knowledge
  requirements.txt
  .env.example
  README.md
  ONBOARDING-CHECKLIST.md             # Cross-project new-county workflow
  FL-ONBOARDING.md                    # FL-specific onboarding notes
  AL-ONBOARDING.md                    # AL-specific onboarding notes
  MS-ONBOARDING.md                    # MS-specific onboarding notes

  seed_reference_data.py              # Load YAML reference data (subdivisions, builders, etc.)
  seed_bi_county_config.py            # Seed bi_county_config from YAML
  seed_pt_jurisdiction_config.py      # Seed pt_jurisdiction_config from YAML
  seed_cr_jurisdiction_config.py      # Seed cr_jurisdiction_config from 98 FL YAML files

  migrations/                         # 16 additive SQL migrations, applied in order
    001_reference_tables.sql ... 012_mortgage_fields.sql
    013_shared_foundation.sql         # The unification spine: counties/jurisdictions/subdivisions/builders/phases
    014_builder_inventory_tables.sql  # bi_* tables
    015_permit_tracker_tables.sql     # pt_* tables
    016_commission_radar_tables.sql   # cr_* tables

  shared/
    database.py                       # psycopg2 connection pool
    sa_database.py                    # SQLAlchemy session factory + get_db dependency
    models.py                         # SQLAlchemy models for the shared spine

  modules/
    sales/
      router.py                       # /api/* endpoints (mounted with no submodule prefix)
    inventory/
      router.py                       # /api/inventory/* aggregator
      routers/                        # builders, counties, inventory, parcels, raw_land, schedule, snapshots, subdivisions
      services/                       # snapshot_runner, etc.
      scheduler.py                    # Recurring snapshot scheduler
    permits/
      router.py                       # /api/permits/*
      services.py                     # Scrape orchestration, dashboard, payload builders
      adapters/                       # iWorq, Accela, PRSF PDF, Cloudpermit
    commission/
      router.py                       # /api/commission/* aggregator
      routers/                        # dashboard, process, review, roster, scrape
      models.py                       # Cr* models + Project = Subdivision alias
      config/jurisdictions/FL/        # 98 jurisdiction YAML configs
      converters/                     # PDF/HTML/DOCX text extraction
      scrapers/                       # CivicPlus, CivicClerk, Legistar adapters

  processors/                         # Sales ETL: reader, transformer, loader
  utils/                              # Sales utilities: text_cleaning, lookup, transaction_utils, ...
  reference_data/                     # YAML reference lists (subdivisions, builders, land bankers, BTR aliases)
  county_scrapers/                    # Cross-module scraper helpers
  tools/                              # raw_land_legal_benchmark.py, apply_benchmark_results.py
  tests/                              # pytest suite (snapshot_runner geometry, packet_fetcher, etc.)

  ui/                                 # React 19 + Vite + Tailwind frontend
    package.json
    vite.config.ts
    src/
      App.tsx                         # Routes: /, /transactions, /review, /pipeline, /subdivisions, /subdivisions/:id
      components/Layout.tsx
      pages/                          # DashboardPage, TransactionsPage, ReviewPage, PipelinePage, SubdivisionsPage, SubdivisionDetailPage

  docs/
    unification/
      schema-reconciliation.md        # Authoritative unified schema design
      phase2-handoff.md               # Builder Inventory port notes
      phase3-handoff.md               # Permit Tracker port notes
      phase4-handoff.md               # Commission Radar port notes
      post-merge-quirks.md            # ARCHIVED lessons-learned reference (11 fixed/cleared entries)
```

---

## Setup

### 1. Install Docker

Download and install Docker Desktop: https://docs.docker.com/get-docker/

### 2. Configure credentials

```bash
cp .env.example .env
# Edit .env: POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB
# Optional: OUTPUT_DIR (Sales export destination)
# Optional: ANTHROPIC_API_KEY — required for Commission Radar's Claude-backed extractor
#                               and for the Sales raw-land legal benchmark harness
```

### 3. Start PostgreSQL + PostGIS

```bash
docker compose up -d
```

`schema.sql` is bound to the container's init directory and is applied **only when Docker initializes a fresh `pgdata` volume**. On an existing volume the migration runner takes over.

### 4. Install Python dependencies

```bash
pip install -r requirements.txt           # prod/runtime
pip install -r requirements-dev.txt       # adds pytest for local verification
```

### 5. Apply schema migrations

```bash
python apply_migrations.py
```

This walks `migrations/` in order and applies all 16 files idempotently. Safe on a fresh database, safe on an existing database.

### 6. Seed reference data and module configs

Run all four in this order — each is idempotent:

```bash
python seed_reference_data.py            # Subdivisions, builders, land bankers, BTR aliases
python seed_bi_county_config.py          # 48 BI county GIS configs
python seed_pt_jurisdiction_config.py    # 7 PT permit jurisdiction configs
python seed_cr_jurisdiction_config.py    # 98 CR commission jurisdiction configs
```

### 7. Install the UI

```bash
cd ui && npm install && cd ..
```

### 8. Optional: run the test suite

```bash
python -m pytest -q
```

---

## Ports

| Service       | Port                       | Source                                      |
|---------------|----------------------------|---------------------------------------------|
| PostgreSQL    | `${POSTGRES_PORT:-5432}`   | `docker-compose.yml` → host:container 5432  |
| FastAPI       | `1460`                     | `api.py` docstring + uvicorn invocation     |
| Vite (UI dev) | `1560`                     | `ui/vite.config.ts`                         |

The Vite dev server proxies `/api/*` to `http://localhost:1460` (see `ui/vite.config.ts`), so the UI never has to know about CORS in development. In production / dev with a non-default origin, FastAPI's CORS middleware is configured in `api.py` from the `CORS_ORIGINS` env var (default: `http://localhost:1560,http://localhost:1460`).

---

## Running the platform

Start the API (in one terminal):

```bash
uvicorn api:app --reload --host 0.0.0.0 --port 1460
```

Health check:

```bash
curl http://localhost:1460/api/platform/health
# {"status":"ok","modules":{"sales":"active","inventory":"active","permits":"active","commission":"active"}}
```

Start the UI (in a second terminal):

```bash
cd ui && npm run dev
```

UI pages (from `ui/src/App.tsx`):

- `/` — dashboard
- `/transactions` — sales transaction explorer
- `/review` — review queue for flagged sales rows
- `/pipeline` — ETL / scrape pipeline status
- `/subdivisions` *(new, not yet tagged)*
- `/subdivisions/:id` *(new, not yet tagged)*

---

## Sales usage

The Sales module retains its full standalone CLI surface from before the unification merge. Everything below targets `modules/sales/` but is invoked from the repo root.

### Load county data

```bash
# Process all counties
python etl.py

# Process all counties using the repo-local raw data folders
python etl.py --input-root "raw data"

# Process a single county
python etl.py --county Bay

# Process multiple counties
python etl.py --county Bay Citrus Escambia

# Single county using repo-local raw data
python etl.py --county Bay --input-root "raw data"
```

**Output:**

```
County          Files  Inserted  Updated  Errors
--------------------------------------------------
Bay                 3       412        0       0
Citrus              2       289        5       0
...
--------------------------------------------------
TOTAL              18      3201       12       0
```

- **Inserted** = new records added
- **Updated** = existing records updated (same dedup key, file re-processed with corrections)
- Re-running the same files produces 0 inserts and 0 updates — safe to re-run at any time
- `counties.yaml` points to shared-drive source folders by default; use `--input-root "raw data"` to run against the repo-local county folders in this workspace

### Export to Excel

```bash
# All records
python export.py

# Filter by county
python export.py --county Bay

# Filter by subdivision
python export.py --subdivision "PALMETTO COVE"

# Date range
python export.py --from 2023-01-01 --to 2024-01-01

# Custom output path
python export.py --county Bay --out "Z:/Reports/bay_export.xlsx"
```

Output is a styled Excel file (frozen header, bold headers, column widths, date/number formats).

### Export the review queue

```bash
# All flagged rows
python review_export.py

# Only Marion review rows
python review_export.py --county Marion

# Only specific review reasons
python review_export.py --reason subdivision_unmatched
python review_export.py --reason subdivision_unmatched --reason phase_not_confirmed_by_lookup
```

`review_export.py` writes a workbook with a summary sheet and a detailed review sheet, including review reasons, lookup text, normalized subdivision candidates, and structured parsed-data context for triage.

### Export the deed / price queue

```bash
# Missing-price builder purchases
python deed_queue_export.py

# Single county
python deed_queue_export.py --county Hernando

# Different transaction type
python deed_queue_export.py --type "House Sale"
```

`deed_queue_export.py` writes a workbook of missing-price transactions with deed locator fields, a recommended search key, and county portal URLs where configured.

### Extract Bay prices

```bash
# Dry run Bay builder-purchase price extraction
python bay_price_extract.py --limit 5

# Apply matched Bay prices back to the DB
python bay_price_extract.py --apply
```

`bay_price_extract.py` uses a visible Chrome session to search Bay County Official Records by clerk file number, open the matched document detail view, extract `Consideration`, and optionally write the price back to the database. Bay currently requires a real browser session; headless mode is not reliable against the county site's captcha flow.

### County-specific processing

| County | Special Handling |
|---|---|
| **Bay** | Standard processing |
| **Citrus** | Unit references (e.g., `83/C`) removed from subdivision |
| **Escambia** | LOT/BLK/SUB pattern removal in legal |
| **Hernando** | Separate subdivision column used for extraction; legal cleaned |
| **Marion** | Grantor/Grantee swapped when Star field is not `*` |
| **Okaloosa** | `skiprows=1`; text after "Parcel" and "Section" removed from legal |
| **Okeechobee** | `before_first_newline` applied to grantor/grantee |
| **Santa Rosa** | Party swap when Party Type contains "to"; "unrec" removed; unit refs cleaned |
| **Walton** | "Legal " prefix removed from legal description |

### Transaction type classification (9 types)

- **Builder to Builder** — both grantor and grantee match known builders
- **Builder Purchase** — grantee matches a known builder
- **Land Banker Purchase** — grantee matches a known land banker or developer
- **Build-to-Rent Purchase** — grantee matches a known build-to-rent entity (institutional bulk buyer)
- **Association Transfer** — grantee is an HOA / POA / condominium / community association
- **CDD Transfer** — grantee is a community development district
- **Correction / Quit Claim** — corrective or quit-claim deed used to fix title / record issues
- **Raw Land Purchase** — builder / land-banker acquisition with raw-land legal indicators
- **House Sale** — all other transactions

### Raw-land legal benchmark (manual / experimental)

A small benchmark + Claude-backed extraction harness for `Raw Land Purchase` transactions lives under `tools/raw_land_legal_benchmark.py` and `tools/apply_benchmark_results.py`. It is **not part of ETL** — it does not run automatically and only spends Anthropic API tokens when you explicitly invoke `run-anthropic`. See `tools/raw_land_legal_benchmark.py --help` for the prepare / run / run-anthropic / compare workflow and `tools/apply_benchmark_results.py --help` for writing approved extractions back to `deed_legal_desc` / `deed_legal_parsed`.

---

## Database schema

Migrations 013–016 lay down the unified spine and the three module-specific table groups; migrations 001–012 belong to the original Sales pipeline. Run `python apply_migrations.py` against any database (fresh or existing) to bring it current.

**Shared spine:**

- `counties` — geographic anchor (FIPS, state, DOR county number)
- `jurisdictions` — institutional layer (cities, planning boards, commissions; FK → counties)
- `subdivisions` — cross-module canonical names + entitlement lifecycle columns (CR-driven). Includes the legacy CR `projects` rows.
- `builders` / `land_bankers` — entity reference lists with a `category` discriminator
- `phases` — phase tracking, FK → subdivisions
- `transactions` — Sales deed records with the dedup key and PostGIS `geom` column

**Module tables:**

- **Sales:** `transactions`, `parsed_data`, `transaction_segments`, `deed_locator`
- **Builder Inventory:** `bi_county_config`, `bi_snapshots`, `parcels`, `bi_parcel_snapshots`
- **Permit Tracker:** `pt_jurisdiction_config`, `pt_permits`, `pt_scrape_jobs`, `pt_scraper_artifacts`
- **Commission Radar:** `cr_jurisdiction_config`, `cr_source_documents`, `cr_entitlement_actions`, `cr_commissioners`, `cr_commissioner_votes`

**Sales dedup key:** Grantor + Grantee + Instrument + Date + County (normalized: uppercased, trimmed). Enforced by a PostgreSQL UNIQUE constraint on generated columns — no manual dedup step required.

PostGIS is enabled on the database and `transactions.geom`, `parcels.geom`, `subdivisions.geom` are all spatial columns (some still NULL pending backfill).

For the full design rationale and the column-by-column reconciliation between the four legacy schemas see `docs/unification/schema-reconciliation.md`.

---

## Adding a new county

The cross-project workflow for onboarding a new county lives in `ONBOARDING-CHECKLIST.md`. Per-state intel — disclosure rules, survey system, alias quirks — lives in `FL-ONBOARDING.md`, `AL-ONBOARDING.md`, and `MS-ONBOARDING.md`. The shared knowledge base used by all four modules is `county-registry.yaml`. Update the registry as you go.

---

## Reference documentation

| Doc | Purpose |
|---|---|
| `docs/unification/schema-reconciliation.md` | Authoritative design-of-record for the unified schema |
| `docs/unification/phase2-handoff.md` | Builder Inventory port notes |
| `docs/unification/phase3-handoff.md` | Permit Tracker port notes |
| `docs/unification/phase4-handoff.md` | Commission Radar port notes |
| `docs/unification/post-merge-quirks.md` | **Archived** lessons-learned reference (11 fixed/cleared entries). Do not append. |
| `ONBOARDING-CHECKLIST.md` | Cross-project new-county workflow |
| `FL-ONBOARDING.md` / `AL-ONBOARDING.md` / `MS-ONBOARDING.md` | Per-state onboarding guides |
| `county-registry.yaml` | Shared cross-project county knowledge base |
| `counties.yaml` | Sales module ETL county config |

---

## Troubleshooting

| Issue | Fix |
|---|---|
| `psycopg2.OperationalError` on startup | Confirm Docker is running and the DB container is up: `docker compose ps` |
| `UndefinedColumn` / `UndefinedTable` / missing JSON or segment fields | Run `python apply_migrations.py` to bring the schema current |
| FastAPI returns 502 / connection refused from the UI | Confirm `uvicorn api:app --port 1460` is running and `/api/platform/health` returns `ok` |
| Vite dev server cannot reach `/api/*` | Verify `ui/vite.config.ts` proxy target is `http://localhost:1460` and the API is up |
| `subdivisions.county` `NotNullViolation` when writing from a module | Pass `county` (legacy NOT NULL column) alongside `county_id`; see archived `post-merge-quirks.md` Entry 1 for the model-drift backstory |
| `UnicodeDecodeError` on a Sales CSV | Add the encoding to `SUPPORTED_ENCODINGS` in `config.py` |
| Sales column mismatch from a county file | Check headers in the source file; update `column_mapping` in `counties.yaml` |
| Sales grantor / grantee swapped | Check the swap condition in `processors/transformer.py` for that county |
| Sales phase showing Roman numerals | Add the variant to `fix_phase_typos()` in `utils/text_cleaning.py` |
| CR `run-anthropic` fails before sending any request | Confirm `ANTHROPIC_API_KEY` is set in your environment or `.env` |
| CR `run-anthropic` reuses a stale model result | This is expected — model-backed runs cache by target hint. Pass `--force` to refresh. |
