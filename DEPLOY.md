# Deployment / Bootstrap

## Prerequisites
- Docker Desktop installed
- `.env` created from `.env.example`
- Python dependencies installed with `pip install -r requirements.txt`

## Recommended workflow

### 1. Start PostgreSQL
```bash
docker compose up -d
```

`schema.sql` is mounted into Docker's init directory, so it applies automatically only when the `pgdata` volume is created for the first time.

### 2. Apply all additive SQL migrations
```bash
python apply_migrations.py
```

This is safe to re-run and is the easiest way to keep older databases aligned with the current codebase. It currently applies:
- `001_reference_tables.sql`
- `002_alter_transactions.sql`
- `004_party_entities.sql`
- `005_parsed_data.sql`
- `006_transaction_segments.sql`
- `007_deed_locator.sql`
- `008_inventory_category.sql`
- `009_canonical_transaction_shape.sql`
- `010_land_banker_category.sql`

### 3. Seed reference data
```bash
python seed_reference_data.py
```

Edit these YAML files before or after seeding as needed:
- `reference_data/subdivisions.yaml`
- `reference_data/builders.yaml`
- `reference_data/land_bankers.yaml`

### 4. Optional: backfill existing transaction rows
```bash
python migrations/003_backfill.py
```

Use this only when you already have transaction rows in the database and want to enrich them with newer lookup-backed fields.

### 5. Run ETL
```bash
python etl.py
python etl.py --county Bay
python etl.py --input-root "raw data"
```

`counties.yaml` points to shared-drive source folders by default. Use `--input-root "raw data"` if you want to process the repo-local county folders in this workspace.

### 6. Verify with tests
```bash
python -m pytest -q
```

## Notes
- Legacy workbook import is not part of the active workflow in this repo; there is no `etl_migrate.py`.
- The current missing-price workflow is `deed_queue_export.py`, with Bay automation available in `bay_price_extract.py`.
- Raw-land deed legal extraction is a manual benchmark workflow in `tools/raw_land_legal_benchmark.py`. After running a benchmark, use `python tools/apply_benchmark_results.py` to write results back to `deed_legal_desc` and `deed_legal_parsed`.
- Model-backed raw-land benchmark runs cache prior results and only spend tokens again when explicitly re-run with `--force`.
- The `land_bankers` table uses a `category` column to distinguish entity types: `land_banker` (circular lot pipeline), `developer` (one-way lot seller), and `btr` (build-to-rent institutional buyer). The `btr` category triggers the "Build-to-Rent Purchase" transaction type.
