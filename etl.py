"""
etl.py - Real estate transaction ETL pipeline.

Reads county source files (Excel/CSV), transforms each row, and upserts
into the PostgreSQL transactions table.

Usage:
    python etl.py                          # Process all counties
    python etl.py --county Bay             # Single county
    python etl.py --county Bay Citrus      # Multiple counties
"""

import argparse
from pathlib import Path

import psycopg2
import yaml

from config import DATABASE_URL
from processors.loader import upsert_rows
from processors.reader import read_county_files
from processors.transformer import transform_row
from utils.county_utils import normalize_county_key
from utils.lookup import BuilderMatcher, LandBankerMatcher, SubdivisionMatcher


CONFIG_DIR = Path(__file__).parent


def load_config() -> dict:
    with open(CONFIG_DIR / 'counties.yaml', encoding='utf-8') as f:
        full = yaml.safe_load(f)
    global_indicators = full.get('company_indicators', [])
    counties = full.get('counties', {})
    for cfg in counties.values():
        cfg.setdefault('company_indicators', global_indicators)
    return counties


def resolve_county_names(requested: list[str], counties_config: dict) -> tuple[dict, list[str]]:
    by_key = {normalize_county_key(name): name for name in counties_config}
    resolved = {}
    unknown = []

    for requested_name in requested:
        match = by_key.get(normalize_county_key(requested_name))
        if match is None:
            unknown.append(requested_name)
            continue
        resolved[match] = counties_config[match]

    return resolved, unknown


def process_county(county: str, config: dict, conn,
                   sub_matcher: SubdivisionMatcher,
                   builder_matcher: BuilderMatcher,
                   land_banker_matcher: LandBankerMatcher) -> dict:
    summary = {'files': 0, 'inserted': 0, 'updated': 0, 'errors': 0}

    file_frames = read_county_files(county, config)
    if not file_frames:
        return summary

    for file_path, df in file_frames:
        rows = []
        for _, row in df.iterrows():
            try:
                result = transform_row(
                    row,
                    county,
                    config,
                    sub_matcher,
                    builder_matcher,
                    land_banker_matcher,
                )
                if result:
                    rows.append(result)
            except Exception as e:
                print(f"  [{county}] Row error in {file_path.name}: {e}")
                summary['errors'] += 1

        if not rows:
            continue

        ins, upd, err = upsert_rows(rows, file_path, conn)
        summary['files'] += 1
        summary['inserted'] += ins
        summary['updated'] += upd
        summary['errors'] += err

    return summary


def main():
    counties_config = load_config()

    parser = argparse.ArgumentParser(description='ETL: county files -> PostgreSQL')
    parser.add_argument(
        '--county', nargs='+', metavar='COUNTY',
        help=f'County/counties to process (default: all; quote names with spaces). Available: {", ".join(counties_config)}'
    )
    args = parser.parse_args()

    if args.county:
        to_run, unknown = resolve_county_names(args.county, counties_config)
        if unknown:
            print(f"Unknown: {', '.join(unknown)}")
            print(f"Available: {', '.join(counties_config)}")
            return
    else:
        to_run = counties_config

    conn = psycopg2.connect(DATABASE_URL)
    try:
        sub_matcher = SubdivisionMatcher(conn)
        builder_matcher = BuilderMatcher(conn)
        land_banker_matcher = LandBankerMatcher(conn)

        results = {}
        for county, cfg in to_run.items():
            results[county] = process_county(
                county,
                cfg,
                conn,
                sub_matcher,
                builder_matcher,
                land_banker_matcher,
            )
    finally:
        conn.close()

    print()
    print(f"{'County':<15} {'Files':>6} {'Inserted':>9} {'Updated':>8} {'Errors':>7}")
    print('-' * 50)
    totals = {'files': 0, 'inserted': 0, 'updated': 0, 'errors': 0}
    for county, s in results.items():
        note = '  (no input)' if s['files'] == 0 and s['errors'] == 0 else ''
        print(f"{county:<15} {s['files']:>6} {s['inserted']:>9} {s['updated']:>8} {s['errors']:>7}{note}")
        for k in totals:
            totals[k] += s[k]
    print('-' * 50)
    print(f"{'TOTAL':<15} {totals['files']:>6} {totals['inserted']:>9} {totals['updated']:>8} {totals['errors']:>7}")


if __name__ == '__main__':
    main()
