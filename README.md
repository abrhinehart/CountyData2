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
  etl.py                       # Entry point — load county files into the database
  export.py                    # Export to styled Excel on demand
  config.py                    # DB connection + global constants
  counties.yaml                # County-specific configuration
  schema.sql                   # PostgreSQL table definition
  docker-compose.yml           # Local Postgres + PostGIS setup
  .env.example                 # DB credentials template
  processors/
    reader.py                  # File reading (CSV/XLS/XLSX)
    transformer.py             # Row normalization
    loader.py                  # PostgreSQL upsert
  utils/
    text_cleaning.py           # Text extraction and cleaning
    date_utils.py              # Date parsing → Python date objects
    transaction_utils.py       # Transaction type classification
```

---

## Setup

### 1. Install Docker

Download and install Docker Desktop: https://docs.docker.com/get-docker/

### 2. Configure credentials

```bash
cp .env.example .env
# Edit .env — set POSTGRES_PASSWORD and update DATABASE_URL to match
```

### 3. Start the database

```bash
docker compose up -d
```

The `schema.sql` file is automatically applied on first start. PostGIS is enabled.

### 4. Install Python dependencies

```bash
pip install pandas openpyxl pyyaml xlrd psycopg2-binary python-dotenv
```

---

## Usage

### Load county data

```bash
# Process all counties
python etl.py

# Process a single county
python etl.py --county Bay

# Process multiple counties
python etl.py --county Bay Citrus Escambia
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
    legal_desc      TEXT,
    subdivision     TEXT,
    phase           TEXT,
    lots            INTEGER,
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
- **House Sale** — all other transactions

Builders and land bankers are tracked through reference-data alias lists.

---

## Migrating Existing Repository Data

If you have an existing `updated_repository.xlsx` to preserve, load it with a one-time command:

```bash
python etl_migrate.py --file "Z:/path/to/updated_repository.xlsx"
```

> `etl_migrate.py` reads the old Excel columns and maps them into the DB schema via the same upsert path, so no duplicates will be created even if you re-run county files afterward.

*(Create this script when ready to migrate.)*

---

## Troubleshooting

| Issue | Fix |
|---|---|
| `UnicodeDecodeError` on CSV | Add the encoding to `SUPPORTED_ENCODINGS` in `config.py` |
| Column mismatch | Check headers in the source file; update `column_mapping` in `counties.yaml` |
| Missing county | Verify the YAML entry and that source files exist at `input_folder` |
| Grantor/Grantee swapped | Check the swap condition in `processors/transformer.py` |
| Phase showing Roman numerals | Add the variant to `fix_phase_typos()` in `utils/text_cleaning.py` |
| `psycopg2.OperationalError` | Confirm Docker container is running: `docker compose ps` |


I commented out 3 lines in the scheme.SQL AFTER it was loaded. When geometry functions are added I'll need to remove the comments or reload schema.SQL.
