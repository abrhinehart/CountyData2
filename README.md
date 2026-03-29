# Format All App

A Python ETL pipeline that reads Florida county real estate transaction files (Excel/CSV) and loads them into a PostgreSQL + PostGIS database.

Supported counties: Bay, Citrus, Escambia, Hernando, Marion, Okaloosa, Okeechobee, Santa Rosa, Walton

---

## Architecture

```
County Excel/CSV files
        │
        ▼
   python etl.py          ← single command, replaces the old 3-script pipeline
        │
   processors/
     reader.py            ← reads Excel/CSV with encoding fallback
     transformer.py       ← normalizes each row (parties, date, subdivision, phase, type)
     loader.py            ← upserts into PostgreSQL (ON CONFLICT → deduplication)
        │
        ▼
  PostgreSQL + PostGIS    ← real database: indexing, SQL queries, spatial-ready
        │
        ▼
   python export.py       ← query the DB and export a styled Excel file on demand
```

---

## Project Structure

```
Format_All_App/
  apply_migrations.py          # Apply additive SQL migrations in order
  etl.py                       # Entry point — load county files into the database
  export.py                    # Export to styled Excel on demand
  review_export.py             # Export flagged rows for review triage
  deed_queue_export.py         # Export missing-price deed lookup queue
  bay_price_extract.py         # Bay-specific price extraction helper
  seed_reference_data.py       # Load YAML reference data into PostgreSQL
  config.py                    # DB connection + global constants
  counties.yaml                # County-specific configuration
  schema.sql                   # PostgreSQL table definition
  docker-compose.yml           # Local Postgres + PostGIS setup
  .env.example                 # DB credentials template
  migrations/                  # Additive schema changes for existing databases
  reference_data/              # Subdivision / builder / land banker aliases
  processors/
    reader.py                  # File reading (CSV/XLS/XLSX)
    transformer.py             # Row normalization
    loader.py                  # PostgreSQL upsert
  tools/
    raw_land_legal_benchmark.py  # Manual raw-land deed legal benchmark harness
  utils/
    text_cleaning.py           # Text extraction and cleaning
    date_utils.py              # Date parsing → Python date objects
    transaction_utils.py       # Transaction type classification
    raw_land_benchmark.py      # OCR cleanup, validation, and legal extraction helpers
```

---

## Setup

### 1. Install Docker

Download and install Docker Desktop: https://docs.docker.com/get-docker/

### 2. Configure credentials and output path

```bash
cp .env.example .env
# Edit .env if you want a different password, host, OUTPUT_DIR, or optional benchmark API keys
```

### 3. Start the database

```bash
docker compose up -d
```

The `schema.sql` file is automatically applied only when Docker initializes a new `pgdata` volume. PostGIS is enabled.

### 4. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 5. Apply additive migrations

```bash
python apply_migrations.py
```

This is safe on a fresh database and on an existing database. It keeps older volumes aligned with the current codebase (`parsed_data`, `transaction_segments`, `deed_locator`, and related indexes).

### 6. Seed reference data

```bash
python seed_reference_data.py
```

### 7. Optional: verify the install

```bash
python -m pytest -q
```

---

## Usage

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

`deed_queue_export.py` writes a workbook of missing-price transactions with deed locator fields, a recommended search key, and county portal URLs where configured. This is meant to support manual deed review now and later automation of price extraction.

### Extract Bay prices

```bash
# Dry run Bay builder-purchase price extraction
python bay_price_extract.py --limit 5

# Apply matched Bay prices back to the DB
python bay_price_extract.py --apply
```

`bay_price_extract.py` uses a visible Chrome session to search Bay County Official Records by clerk file number, open the matched document detail view, extract `Consideration`, and optionally write the price back to the database. Bay currently requires a real browser session; headless mode is not reliable against the county site's captcha flow.

### Benchmark raw-land deed legal extraction

This workflow is only for a small subset of transactions: rows already classified as `Raw Land Purchase`. It is not part of ETL, it does not run automatically, and it should be treated as a manual benchmark / review tool until the extraction path is productionized.

```bash
# Build a benchmark set (Bay only right now)
python tools/raw_land_legal_benchmark.py prepare --county Bay --limit 4

# Fetch deed PDFs, OCR them, and build a baseline extraction
python tools/raw_land_legal_benchmark.py run

# Run Claude Opus against OCR text first, with automatic vision fallback only when validation fails
python tools/raw_land_legal_benchmark.py run-anthropic --mode hybrid --model claude-opus-4-6

# Re-run a model path only when you explicitly want to refresh cached results
python tools/raw_land_legal_benchmark.py run-anthropic --mode hybrid --model claude-opus-4-6 --force

# Compare extracted candidates to hand-transcribed gold text
python tools/raw_land_legal_benchmark.py compare --results output/raw_land_legal_benchmark/results_anthropic_hybrid.csv
```

Artifacts are written under `output/raw_land_legal_benchmark/`, including:
- `manifest.csv` — sampled raw-land transactions and stored deed locators
- `gold_transcriptions.csv` — hand-transcribed legal text for comparison
- `results.csv` — OCR + heuristic baseline
- `results_anthropic_*.csv` — model-backed benchmark runs
- `comparison.csv` and `comparison_summary.json` — benchmark scoring output
- `artifacts/<transaction_id>/source_document.pdf` and `ocr/page_*.txt` — fetched deed PDFs and per-page OCR text

Important guardrails:
- Nothing in this workflow runs automatically during ETL or export.
- `run-anthropic` only spends tokens when you explicitly invoke it.
- Model-backed result files act as a local run ledger. Re-running the same command with the same model and target hint reuses existing results instead of calling the model again.
- Use `--force` only when you intentionally want to refresh an existing model result.

### Query directly with SQL

```bash
# Connect via psql
psql postgresql://etl_user:changeme@localhost:5432/County-Data

# Examples
SELECT COUNT(*), county FROM transactions GROUP BY county ORDER BY county;
SELECT grantor, grantee, price, date FROM transactions WHERE subdivision = 'PALMETTO COVE' ORDER BY date DESC;
SELECT subdivision, COUNT(*), AVG(price) FROM transactions WHERE county = 'Bay' GROUP BY subdivision;
```

---

## Database Schema

```sql
transactions (
    id              SERIAL PRIMARY KEY,
    grantor         TEXT NOT NULL,
    grantee         TEXT,
    type            TEXT,           -- 'Builder Purchase', 'Land Banker Purchase', 'Builder to Builder', or 'House Sale'
    instrument      TEXT,
    date            DATE,
    export_legal_desc TEXT,
    export_legal_raw  TEXT,
    deed_legal_desc   TEXT,
    deed_legal_parsed JSONB,
    subdivision     TEXT,
    phase           TEXT,
    inventory_category TEXT,
    lots            INTEGER,
    acres_source    TEXT,
    price           NUMERIC(15,2),
    price_per_lot   NUMERIC(15,2),
    acres           NUMERIC(10,4),
    price_per_acre  NUMERIC(15,2),
    county          TEXT NOT NULL,
    notes           TEXT,
    geom            GEOMETRY(Point, 4326),  -- spatial: reserved for future use
    source_file     TEXT,
    inserted_at     TIMESTAMPTZ,
    updated_at      TIMESTAMPTZ
)
```

**Deduplication key:** Grantor + Grantee + Instrument + Date + County (normalized: uppercased, trimmed). Handled by a PostgreSQL UNIQUE constraint on generated columns — no manual dedup step required.

**Spatial:** PostGIS is installed and the `geom` column is ready. Geometry will be NULL until parcel shapefiles or geocoding data are linked.

---

## County Configuration

All county-specific rules live in `counties.yaml`. Structure is unchanged from the previous version.

| Field | Description |
|---|---|
| `input_folder` | Path to raw source files |
| `column_mapping` | Maps source column names to standard fields |
| `phase_keywords` | Keywords used to extract phase from legal descriptions |
| `delimiters` | Characters to split grantor/grantee names on |
| `skiprows` | Header rows to skip when reading source files |

### Adding a New County

1. Add an entry under `counties:` in `counties.yaml`
2. If special handling is needed (party swaps, legal cleaning), add a branch in `processors/transformer.py`
3. Test: `python etl.py --county NewCounty`

---

## County-Specific Processing

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

---

## Transaction Type Classification

- **Builder to Builder** — both grantor and grantee match known builders
- **Builder Purchase** — grantee matches a known builder
- **Land Banker Purchase** — grantee matches a known land banker
- **Association Transfer** — grantee is an HOA / POA / condominium / community association
- **CDD Transfer** — grantee is a community development district
- **Correction / Quit Claim** — corrective or quit-claim style deed used to fix title / record issues
- **Raw Land Purchase** — builder / land-banker style acquisition with raw-land legal indicators instead of platted lot inventory
- **House Sale** — all other transactions

Builders and land bankers are tracked through reference-data alias lists.

---

## Legacy Workbook Data

Legacy workbook import is not part of the active workflow right now, and `etl_migrate.py` is not implemented in this repo.

The current path for recovering missing sales data is the deed queue plus county-specific deed lookup, starting with `python deed_queue_export.py` and, for Bay, `python bay_price_extract.py --apply`.

---

## Troubleshooting

| Issue | Fix |
|---|---|
| `UnicodeDecodeError` on CSV | Add the encoding to `SUPPORTED_ENCODINGS` in `config.py` |
| Column mismatch | Check headers in the source file; update `column_mapping` in `counties.yaml` |
| Missing county or no input files found | Verify the YAML entry and that source files exist at `input_folder`, or run with `--input-root "raw data"` for the repo-local county folders |
| Grantor/Grantee swapped | Check the swap condition in `processors/transformer.py` |
| Phase showing Roman numerals | Add the variant to `fix_phase_typos()` in `utils/text_cleaning.py` |
| `psycopg2.OperationalError` | Confirm Docker container is running: `docker compose ps` |
| `UndefinedColumn`, `UndefinedTable`, or missing JSON/segment fields | Run `python apply_migrations.py` to bring the database schema up to date |
| `run-anthropic` fails before sending any request | Confirm `ANTHROPIC_API_KEY` is set in your environment or `.env` |
| Re-running the benchmark does not refresh a model result | This is expected; `run-anthropic` reuses cached results unless you pass `--force` |
