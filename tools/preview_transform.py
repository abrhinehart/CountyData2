"""
Preview parser output directly from the workspace raw files.

Usage:
    python tools/preview_transform.py --county Hernando
    python tools/preview_transform.py --county Hernando --file hernando_focus --limit 3
    python tools/preview_transform.py --county Hernando --contains "ROYAL HIGHLANDS"
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_DIR = ROOT / 'raw data'

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from processors.reader import read_county_files
from processors.transformer import transform_row


def load_counties() -> dict:
    with open(ROOT / 'counties.yaml', encoding='utf-8') as f:
        data = yaml.safe_load(f) or {}
    return data.get('counties', {})


def build_preview_config(county: str, counties: dict) -> dict:
    config = dict(counties[county])
    config['input_folder'] = str(RAW_DATA_DIR / county)
    return config


def make_jsonable(value):
    try:
        import pandas as pd  # local import to avoid unnecessary import at module load
    except Exception:  # pragma: no cover
        pd = None

    if pd is not None and pd.isna(value):
        return None
    if hasattr(value, 'isoformat'):
        try:
            return value.isoformat()
        except Exception:
            pass
    return value


def row_matches(row, contains: str | None) -> bool:
    if not contains:
        return True
    needle = contains.lower()
    return any(needle in str(value).lower() for value in row.to_dict().values())


def main():
    parser = argparse.ArgumentParser(description='Preview transformed rows from raw county data')
    parser.add_argument('--county', required=True, help='County name, e.g. Hernando or "Santa Rosa"')
    parser.add_argument('--file', help='Optional filename substring filter')
    parser.add_argument('--contains', help='Optional raw-row text filter')
    parser.add_argument('--limit', type=int, default=5, help='Max transformed rows to print')
    args = parser.parse_args()

    counties = load_counties()
    county_map = {name.lower(): name for name in counties}
    county_key = county_map.get(args.county.lower())
    if county_key is None:
        raise SystemExit(f'Unknown county: {args.county}. Available: {", ".join(counties)}')

    config = build_preview_config(county_key, counties)
    file_frames = read_county_files(county_key, config)
    if args.file:
        file_frames = [(path, df) for path, df in file_frames if args.file.lower() in path.name.lower()]

    printed = 0
    for path, df in file_frames:
        for row_index, row in df.iterrows():
            if not row_matches(row, args.contains):
                continue

            transformed = transform_row(row, county_key, config)
            if not transformed:
                continue

            preview = {
                'file': path.name,
                'row_index': int(row_index),
                'raw': {key: make_jsonable(value) for key, value in row.to_dict().items()},
                'transformed': {key: make_jsonable(value) for key, value in transformed.items()},
            }
            print(json.dumps(preview, indent=2, default=str))
            print()

            printed += 1
            if printed >= args.limit:
                return

    if printed == 0:
        print('No transformed rows matched the filters.')


if __name__ == '__main__':
    main()
