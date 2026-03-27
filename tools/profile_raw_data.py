"""
Profile the raw county source files used to redesign parsing rules.

Usage:
    python tools/profile_raw_data.py
    python tools/profile_raw_data.py --county Bay
"""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_DIR = ROOT / 'raw data'
CONFIG_PATH = ROOT / 'counties.yaml'
HELPER_COLUMNS = [
    'Lot',
    'Building',
    'Block',
    'Unit',
    'Subdivision',
    'Section',
    'Township',
    'Range',
    'Land Lot',
    'District',
    'Property Section',
]


def load_counties() -> dict:
    with open(CONFIG_PATH, encoding='utf-8') as f:
        return yaml.safe_load(f)['counties']


def normalize_helper_value(value: str) -> str:
    text = str(value).strip()
    if not text:
        return ''
    if text.lower().startswith('legalfield_'):
        return text[len('legalfield_'):].strip()
    return text


def read_file(path: Path, skiprows: int) -> pd.DataFrame:
    if path.suffix.lower() == '.csv':
        for encoding in ('utf-8', 'cp1252', 'latin1', 'iso-8859-1', 'utf-16', 'cp1250'):
            try:
                return pd.read_csv(path, dtype=str, skiprows=skiprows, encoding=encoding)
            except UnicodeDecodeError:
                continue
        raise ValueError(f'Could not decode CSV: {path}')
    return pd.read_excel(path, dtype=str, skiprows=skiprows)


def summarize_field(df: pd.DataFrame, source_column: str) -> str:
    if source_column not in df.columns:
        return f'{source_column}: missing'

    series = df[source_column].fillna('').astype(str)
    non_empty = series[series.str.strip() != '']
    newline_count = int(non_empty.str.contains(r'\n', regex=True).sum())
    sample = non_empty.head(2).tolist()
    return (
        f'{source_column}: non-empty={len(non_empty)} '
        f'newlines={newline_count} sample={sample}'
    )


def summarize_helper_columns(df: pd.DataFrame) -> list[str]:
    lines = []
    for column in HELPER_COLUMNS:
        if column not in df.columns:
            continue
        series = df[column].fillna('').astype(str)
        non_empty = series[series.str.strip() != '']
        normalized = non_empty.map(normalize_helper_value)
        useful = normalized[normalized != '']
        if len(non_empty) == 0:
            continue
        sample = useful.head(3).tolist()
        lines.append(
            f'{column}: non-empty={len(non_empty)} useful={len(useful)} sample={sample}'
        )
    return lines


def summarize_legal_prefixes(df: pd.DataFrame, legal_column: str) -> str:
    if legal_column not in df.columns:
        return 'legal prefixes: unavailable'

    legal = df[legal_column].fillna('').astype(str)
    prefixes = Counter(
        value.split('\n', 1)[0][:24]
        for value in legal
        if value.strip()
    )
    return f'legal prefixes: {prefixes.most_common(8)}'


def profile_county(county: str, county_config: dict):
    folder = RAW_DATA_DIR / county
    if not folder.exists():
        print(f'=== {county} ===')
        print('Missing raw data folder.')
        print()
        return

    files = sorted([path for path in folder.iterdir() if path.is_file() and not path.name.startswith('~$')])
    if not files:
        print(f'=== {county} ===')
        print('No files found.')
        print()
        return

    path = files[0]
    skiprows = county_config.get('skiprows', 0)
    df = read_file(path, skiprows)
    column_mapping = county_config.get('column_mapping', {})

    print(f'=== {county} :: {path.name} ===')
    print(f'Rows={len(df)} Columns={len(df.columns)}')
    print(f'Configured columns={column_mapping}')
    missing = [source for source in column_mapping.values() if source not in df.columns]
    print(f'Missing configured columns={missing}')

    for logical_name in ('grantor', 'grantee', 'legal', 'sub', 'date', 'instrument', 'price'):
        source_column = column_mapping.get(logical_name)
        if not source_column:
            continue
        print('  ' + summarize_field(df, source_column))

    helper_lines = summarize_helper_columns(df)
    if helper_lines:
        print('  helper columns:')
        for line in helper_lines:
            print('   - ' + line)

    legal_column = column_mapping.get('legal')
    if legal_column:
        print('  ' + summarize_legal_prefixes(df, legal_column))
    print()


def main():
    parser = argparse.ArgumentParser(description='Profile raw county source files')
    parser.add_argument('--county', nargs='*', help='Optional county names to profile')
    args = parser.parse_args()

    counties = load_counties()
    if args.county:
        requested = {name.lower(): name for name in args.county}
        selected = {
            county: config
            for county, config in counties.items()
            if county.lower() in requested
        }
    else:
        selected = counties

    for county, config in selected.items():
        profile_county(county, config)


if __name__ == '__main__':
    main()
