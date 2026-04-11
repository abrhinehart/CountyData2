"""
pull_records.py - Pull county official records from LandmarkWeb portals.

Searches by date range, filters for builder/land banker transactions,
and writes CSV files compatible with the existing ETL pipeline.

Usage:
    python -m county_scrapers.pull_records --county Hernando
    python -m county_scrapers.pull_records --county Hernando --begin 01/01/2025 --end 01/31/2025
    python -m county_scrapers.pull_records --county Okeechobee --no-filter
    python -m county_scrapers.pull_records --county Hernando --all-doc-types
"""

import argparse
import csv
import logging
import os
import sys
from calendar import monthrange
from datetime import date, timedelta

from dotenv import load_dotenv
from pathlib import Path

# Load env vars from the project .env. override=True so the .env file wins
# over a stale or empty shell export (e.g. a pre-set MADISON_PORTAL_EMAIL=""
# from a previous session) — .env is the source of truth for secrets in
# development.
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(_PROJECT_ROOT / ".env", override=True)

import yaml

from county_scrapers.acclaimweb_client import AcclaimWebSession
from county_scrapers.configs import (
    get_acclaimweb_config, get_countygov_config, get_duprocess_config,
    get_gindex_config, get_gis_parcel_config, get_landmark_config,
)
from county_scrapers.configs import (
    ACCLAIMWEB_COUNTIES, COUNTYGOV_COUNTIES, DUPROCESS_COUNTIES,
    GIS_PARCEL_COUNTIES, GINDEX_COUNTIES, LANDMARK_COUNTIES,
)
from county_scrapers.countygov_client import CountyGovSession
from county_scrapers.duprocess_client import DuProcessSession
from county_scrapers.entity_filter import build_entity_set, filter_rows
from county_scrapers.gindex_client import GIndexSession
from county_scrapers.gis_parcel_client import GISParcelSession, JACKSON_FIELDS
from county_scrapers.gis_enrichment import (
    enrich_from_gis, MADISON_FIELDS, DESOTO_FIELDS, DEFAULT_FIELDS,
)

_GIS_FIELD_MAPS = {
    'madison': MADISON_FIELDS,
    'desoto': DESOTO_FIELDS,
}

_GIS_PARCEL_FIELD_MAPS = {
    'jackson': JACKSON_FIELDS,
}
from county_scrapers.landmark_client import LandmarkSession

log = logging.getLogger(__name__)

_CONFIG_PATH = Path(__file__).resolve().parent.parent / 'counties.yaml'

# Map from parsed record fields to counties.yaml column_mapping keys.
_FIELD_TO_MAPPING_KEY = {
    'grantor': 'grantor',
    'grantee': 'grantee',
    'record_date': 'date',
    'doc_type': 'instrument',
    'legal': 'legal',
}

# Extra fields always included in output (not in column_mapping but useful).
_EXTRA_COLUMNS = ['Book Type', 'Book', 'Page', 'Instrument Number', 'Mortgage Amount', 'Mortgage Originator',
                   'Situs Address', 'GIS Acreage', 'GIS Value', 'Sale Amount', 'Latitude', 'Longitude']
_EXTRA_FIELD_MAP = {
    'Book Type': 'book_type',
    'Book': 'book',
    'Page': 'page',
    'Instrument Number': 'instrument',
    'Mortgage Amount': 'mortgage_amount',
    'Mortgage Originator': 'mortgage_originator',
    'Situs Address': 'situs_address',
    'GIS Acreage': 'gis_acreage',
    'GIS Value': 'gis_value',
    'Sale Amount': 'sale_amount',
    'Latitude': 'latitude',
    'Longitude': 'longitude',
}


def _load_county_column_mapping(county: str) -> dict[str, str]:
    """Load the column_mapping for a county from counties.yaml."""
    with open(_CONFIG_PATH, encoding='utf-8') as f:
        config = yaml.safe_load(f)
    county_cfg = config.get('counties', {}).get(county, {})
    return county_cfg.get('column_mapping', {})


def _weekly_chunks(begin_date: str, end_date: str) -> list[tuple[str, str]]:
    """Split a MM/DD/YYYY date range into weekly chunks."""
    from datetime import datetime
    start = datetime.strptime(begin_date, '%m/%d/%Y').date()
    end = datetime.strptime(end_date, '%m/%d/%Y').date()
    chunks = []
    while start <= end:
        chunk_end = min(start + timedelta(days=6), end)
        chunks.append((start.strftime('%m/%d/%Y'), chunk_end.strftime('%m/%d/%Y')))
        start = chunk_end + timedelta(days=1)
    return chunks


def _default_date_range() -> tuple[str, str]:
    """Return the first and last day of the previous calendar month as MM/DD/YYYY."""
    today = date.today()
    first_of_this_month = today.replace(day=1)
    last_of_prev = first_of_this_month - timedelta(days=1)
    first_of_prev = last_of_prev.replace(day=1)
    return first_of_prev.strftime('%m/%d/%Y'), last_of_prev.strftime('%m/%d/%Y')


def _build_csv_header(column_mapping: dict[str, str]) -> list[str]:
    """Build the CSV header row from the county's column_mapping + extras."""
    headers = []
    for field, mapping_key in _FIELD_TO_MAPPING_KEY.items():
        col_name = column_mapping.get(mapping_key)
        if col_name:
            headers.append(col_name)
    # Price column if county has it
    if 'price' in column_mapping:
        headers.append(column_mapping['price'])
    # Subdivision column if county has it (e.g., Hernando)
    if 'sub' in column_mapping:
        headers.append(column_mapping['sub'])
    headers.extend(_EXTRA_COLUMNS)
    return headers


def _row_to_csv(record: dict, column_mapping: dict[str, str],
                header: list[str]) -> dict[str, str]:
    """Map a parsed record dict to a CSV row dict matching the header."""
    row = {}
    for field, mapping_key in _FIELD_TO_MAPPING_KEY.items():
        col_name = column_mapping.get(mapping_key)
        if col_name:
            row[col_name] = record.get(field, '')
    if 'price' in column_mapping:
        row[column_mapping['price']] = ''  # not available from search results
    if 'sub' in column_mapping:
        row[column_mapping['sub']] = record.get('subdivision', '')
    for csv_col, field in _EXTRA_FIELD_MAP.items():
        row[csv_col] = record.get(field, '')
    return row


def _extract_last_names(name_str: str) -> set[str]:
    """Extract last names from semicolon-separated party string."""
    names = set()
    for party in name_str.split(';'):
        party = party.strip()
        if not party:
            continue
        words = party.split()
        for word in words:
            candidate = word.upper()
            if len(candidate) > 1:
                names.add(candidate)
                break
    return names


def _match_mortgages(deed_rows: list[dict], mortgage_rows: list[dict]) -> None:
    """Match mortgage records to deed records and enrich deeds in-place."""
    mort_by_date: dict[str, list[dict]] = {}
    for m in mortgage_rows:
        d = m.get('record_date', '')
        mort_by_date.setdefault(d, []).append(m)

    for deed in deed_rows:
        date = deed.get('record_date', '')
        candidates = mort_by_date.get(date, [])
        if not candidates:
            continue

        buyer_names = _extract_last_names(deed.get('grantee', ''))
        if not buyer_names:
            continue

        best = None
        for mort in candidates:
            mort_names = _extract_last_names(mort.get('grantor', ''))
            if buyer_names & mort_names:
                best = mort
                break

        if best:
            deed['mortgage_amount'] = best.get('mortgage_value', '')
            deed['mortgage_originator'] = best.get('grantee', '')


def pull(county: str, begin_date: str, end_date: str, *,
         no_filter: bool = False, all_doc_types: bool = False,
         output_dir: Path | None = None) -> Path:
    """
    Pull records for a county and write a CSV.

    Returns the path to the output CSV file.
    """
    countygov_cfg = get_countygov_config(county)
    landmark_cfg = get_landmark_config(county)
    duprocess_cfg = get_duprocess_config(county)
    gindex_cfg = get_gindex_config(county)
    acclaimweb_cfg = get_acclaimweb_config(county)
    gis_parcel_cfg = get_gis_parcel_config(county)

    all_counties = (
        list(LANDMARK_COUNTIES.keys())
        + list(COUNTYGOV_COUNTIES.keys())
        + list(DUPROCESS_COUNTIES.keys())
        + list(GINDEX_COUNTIES.keys())
        + list(ACCLAIMWEB_COUNTIES.keys())
        + list(GIS_PARCEL_COUNTIES.keys()))

    active_cfg = countygov_cfg or landmark_cfg or duprocess_cfg or gindex_cfg or acclaimweb_cfg or gis_parcel_cfg
    if active_cfg is None:
        raise ValueError(f'{county} is not a configured county. Available: {", ".join(all_counties)}')

    if countygov_cfg is not None:
        status = countygov_cfg.get('status', 'unknown')
        portal_type = 'countygov'
    elif duprocess_cfg is not None:
        status = duprocess_cfg.get('status', 'unknown')
        portal_type = 'duprocess'
    elif gindex_cfg is not None:
        status = gindex_cfg.get('status', 'unknown')
        portal_type = 'gindex'
    elif acclaimweb_cfg is not None:
        status = acclaimweb_cfg.get('status', 'unknown')
        portal_type = 'acclaimweb'
    elif gis_parcel_cfg is not None:
        status = gis_parcel_cfg.get('status', 'unknown')
        portal_type = 'gis_parcel'
    else:
        status = landmark_cfg.get('status', 'unknown')
        portal_type = 'landmark'

    if status not in ('working', 'captcha_hybrid', 'cloudflare'):
        log.warning('County %s has status "%s" — results may be empty or blocked',
                     county, status)

    column_mapping = _load_county_column_mapping(county)
    if not column_mapping:
        raise ValueError(f'No column_mapping found for {county} in counties.yaml')

    doc_types = '' if all_doc_types else (active_cfg or {}).get('doc_types', '')
    header = _build_csv_header(column_mapping)

    # Determine output path
    if output_dir is None:
        output_dir = Path(__file__).resolve().parent.parent / 'output'
    output_dir.mkdir(parents=True, exist_ok=True)

    # Parse dates for filename
    month_label = begin_date.split('/')[0] + '_' + begin_date.split('/')[2]
    out_path = output_dir / f'{county}_{month_label}.csv'

    log.info('County: %s | Date range: %s to %s | Doc types: %s',
             county, begin_date, end_date, doc_types or 'ALL')

    # Connect and search
    if portal_type == 'gis_parcel':
        fm_name = gis_parcel_cfg.get('gis_fields', '')
        fm = _GIS_PARCEL_FIELD_MAPS.get(fm_name, JACKSON_FIELDS)
        with GISParcelSession(
            layer_url=gis_parcel_cfg['layer_url'],
            field_map=fm,
        ) as session:
            session.connect()
            rows = session.search_by_date_range(begin_date, end_date)
    elif portal_type == 'acclaimweb':
        with AcclaimWebSession(
            base_url=acclaimweb_cfg['base_url'],
            doc_types=acclaimweb_cfg.get('doc_types', ''),
        ) as session:
            session.connect()
            rows = session.search_by_date_range(begin_date, end_date)
        # GIS enrichment
        gis_url = acclaimweb_cfg.get('gis_url')
        if gis_url:
            fm = _GIS_FIELD_MAPS.get(acclaimweb_cfg.get('gis_fields', ''))
            enrich_from_gis(rows, gis_url, field_map=fm)
    elif portal_type == 'gindex':
        use_cffi = gindex_cfg.get('status') == 'cloudflare'
        with GIndexSession(
            base_url=gindex_cfg['base_url'],
            book_type=gindex_cfg.get('book_type', '2'),
            use_cffi=use_cffi,
        ) as session:
            session.connect()
            rows = session.search_by_date_range(begin_date, end_date)
    elif portal_type == 'duprocess':
        with DuProcessSession(
            base_url=duprocess_cfg['base_url'],
            search_type=duprocess_cfg.get('search_type', 'deed'),
        ) as session:
            session.connect()
            rows = session.search_by_date_range(begin_date, end_date)
        # Enrich with GIS parcel data (address, acreage, value, lat/lon)
        gis_url = duprocess_cfg.get('gis_url')
        if gis_url:
            fm = _GIS_FIELD_MAPS.get(duprocess_cfg.get('gis_fields', ''))
            enrich_from_gis(rows, gis_url, field_map=fm)
    elif portal_type == 'countygov':
        email = os.environ.get('MADISON_PORTAL_EMAIL', '')
        password = os.environ.get('MADISON_PORTAL_PASSWORD', '')
        if not email or not password:
            raise ValueError(
                f'Missing MADISON_PORTAL_EMAIL/PASSWORD env vars for {county}')
        with CountyGovSession(
            base_url=countygov_cfg['base_url'],
            email=email,
            password=password,
            search_type=countygov_cfg.get('search_type', 'deed'),
        ) as session:
            session.connect()
            rows = session.search_by_date_range(begin_date, end_date)
        # Pull mortgages for cross-referencing
        log.info('Pulling mortgage records for cross-reference...')
        with CountyGovSession(
            base_url=countygov_cfg['base_url'],
            email=email,
            password=password,
            search_type='mortgage',
        ) as mort_session:
            mort_session.connect()
            mort_rows = mort_session.search_by_date_range(begin_date, end_date)
        log.info('Mortgage records: %d', len(mort_rows))
        _match_mortgages(rows, mort_rows)
        log.info('Mortgage matches: %d',
                 sum(1 for r in rows if r.get('mortgage_amount')))
    else:
        if landmark_cfg.get('status') == 'captcha_hybrid':
            from county_scrapers.cookie_session import capture_cookies
            cookies = capture_cookies(
                landmark_cfg['base_url'] + '/Home/Index',
                prompt=(
                    f'\n  {county} Official Records has opened in Chrome.\n'
                    f'  Please:\n'
                    f'    1. Accept the disclaimer\n'
                    f'    2. Switch to "Record Date" search\n'
                    f'    3. Do one search (any date range)\n'
                    f'    4. Come back here and press Enter\n'
                ),
            )
            with LandmarkSession.from_cookies(
                landmark_cfg['base_url'],
                cookies,
                column_map=landmark_cfg['column_map'],
            ) as session:
                rows = session.search_by_date_range(
                    begin_date, end_date, doc_types=doc_types)
        elif landmark_cfg.get('status') == 'cloudflare':
            chunks = _weekly_chunks(begin_date, end_date)
            rows = []
            with LandmarkSession(
                landmark_cfg['base_url'],
                column_map=landmark_cfg['column_map'],
                use_cffi=True,
            ) as session:
                session.connect()
                for i, (chunk_begin, chunk_end) in enumerate(chunks, 1):
                    log.info('  chunk %d/%d: %s to %s',
                             i, len(chunks), chunk_begin, chunk_end)
                    chunk_rows = session.search_by_date_range(
                        chunk_begin, chunk_end, doc_types=doc_types)
                    rows.extend(chunk_rows)
        else:
            with LandmarkSession(landmark_cfg['base_url'],
                                 column_map=landmark_cfg['column_map']) as session:
                session.connect()
                rows = session.search_by_date_range(
                    begin_date, end_date, doc_types=doc_types)

    log.info('Raw results: %d records', len(rows))

    # Filter for builder/land banker entities
    if not no_filter:
        entity_set = build_entity_set()
        filtered = filter_rows(rows, entity_set)
        log.info('After entity filter: %d records (removed %d)',
                 len(filtered), len(rows) - len(filtered))
        rows = filtered

    # Write CSV
    with open(out_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=header, extrasaction='ignore')
        writer.writeheader()
        for record in rows:
            csv_row = _row_to_csv(record, column_mapping, header)
            writer.writerow(csv_row)

    log.info('Wrote %d records to %s', len(rows), out_path)
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Pull county official records from LandmarkWeb portals')
    parser.add_argument('--county', required=True,
                        help='County name (must match counties.yaml)')
    parser.add_argument('--begin', dest='begin_date',
                        help='Begin date MM/DD/YYYY (default: first of last month)')
    parser.add_argument('--end', dest='end_date',
                        help='End date MM/DD/YYYY (default: last of last month)')
    parser.add_argument('--no-filter', action='store_true',
                        help='Skip entity filtering, pull all records')
    parser.add_argument('--all-doc-types', action='store_true',
                        help='Pull all doc types, not just deeds')
    parser.add_argument('--output-dir',
                        help='Output directory (default: ./output)')
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%H:%M:%S',
    )

    begin, end = args.begin_date, args.end_date
    if not begin or not end:
        default_begin, default_end = _default_date_range()
        begin = begin or default_begin
        end = end or default_end

    output_dir = Path(args.output_dir) if args.output_dir else None

    try:
        out_path = pull(args.county, begin, end,
                        no_filter=args.no_filter,
                        all_doc_types=args.all_doc_types,
                        output_dir=output_dir)
        print(f'Done. Output: {out_path}')
    except Exception as exc:
        log.error('Failed: %s', exc, exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
