"""
apply_benchmark_results.py - Write raw-land benchmark extraction results back to the transactions table.

Reads the best available benchmark CSV (default: results_anthropic_hybrid.csv)
and updates deed_legal_desc and deed_legal_parsed for each transaction.

Only writes rows with status='ok' and a non-empty candidate_legal_desc.

Usage:
    python tools/apply_benchmark_results.py
    python tools/apply_benchmark_results.py --results output/raw_land_legal_benchmark/results_anthropic_text.csv
    python tools/apply_benchmark_results.py --dry-run
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import psycopg2
import psycopg2.extras

from config import DATABASE_URL

DEFAULT_RESULTS = ROOT_DIR / 'output' / 'raw_land_legal_benchmark' / 'results_anthropic_hybrid.csv'


def _build_parsed(row: dict) -> dict:
    """Build a deed_legal_parsed JSONB payload from benchmark validation columns."""
    parsed = {}

    parsed['extraction_method'] = row.get('method', '')
    parsed['extraction_model'] = row.get('model', '')
    parsed['selected_mode'] = row.get('selected_mode', '')
    parsed['target_hint'] = row.get('target_hint', '')

    chars = row.get('candidate_chars', '')
    if chars:
        parsed['candidate_chars'] = int(chars)

    # Validation metadata from the selected mode
    prefix = row.get('selected_mode', 'text')  # 'text' or 'vision'
    similarity = row.get(f'{prefix}_validation_similarity_ratio', '')
    if similarity:
        parsed['similarity_ratio'] = float(similarity)

    target_parcel = row.get(f'{prefix}_validation_target_parcel', '')
    if target_parcel:
        parsed['target_parcel'] = target_parcel

    for key in ('candidate_parcels', 'candidate_bearings', 'candidate_distances'):
        val = row.get(f'{prefix}_validation_{key}', '')
        if val:
            try:
                parsed[key] = int(val)
            except ValueError:
                parsed[key] = val

    passed = row.get(f'{prefix}_validation_passed', '')
    if passed:
        parsed['validation_passed'] = passed.lower() == 'true'

    # Cost tracking
    cost = row.get('estimated_cost_usd', '')
    if cost:
        parsed['estimated_cost_usd'] = float(cost)

    return parsed


def apply_results(results_path: Path, dry_run: bool = False) -> int:
    if not results_path.exists():
        print(f'Results file not found: {results_path}')
        return 0

    with open(results_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    candidates = []
    for row in rows:
        if row.get('status') != 'ok':
            continue
        legal_desc = (row.get('candidate_legal_desc') or '').strip()
        if not legal_desc:
            continue
        txn_id = int(row['transaction_id'])
        parsed = _build_parsed(row)
        candidates.append((txn_id, legal_desc, parsed))

    if not candidates:
        print('No valid results to apply.')
        return 0

    print(f'Found {len(candidates)} results to write back.')

    if dry_run:
        for txn_id, legal_desc, parsed in candidates:
            print(f'  [DRY RUN] txn={txn_id}  chars={len(legal_desc)}  parsed_keys={list(parsed.keys())}')
            print(f'            legal: {legal_desc[:80]}...')
        return len(candidates)

    conn = psycopg2.connect(DATABASE_URL)
    updated = 0
    try:
        with conn.cursor() as cur:
            for txn_id, legal_desc, parsed in candidates:
                cur.execute("""
                    UPDATE transactions
                    SET deed_legal_desc = %s,
                        deed_legal_parsed = %s,
                        updated_at = NOW()
                    WHERE id = %s
                """, (legal_desc, psycopg2.extras.Json(parsed), txn_id))
                if cur.rowcount:
                    updated += 1
                    print(f'  Updated txn={txn_id}  chars={len(legal_desc)}')
                else:
                    print(f'  Skipped txn={txn_id} (not found)')
        conn.commit()
    finally:
        conn.close()

    print(f'Done. Updated {updated} / {len(candidates)} transactions.')
    return updated


def main():
    parser = argparse.ArgumentParser(description='Write benchmark results back to transactions')
    parser.add_argument('--results', type=Path, default=DEFAULT_RESULTS,
                        help='Path to benchmark results CSV')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be written without modifying the database')
    args = parser.parse_args()

    apply_results(args.results, dry_run=args.dry_run)


if __name__ == '__main__':
    main()
