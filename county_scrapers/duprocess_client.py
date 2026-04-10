"""
duprocess_client.py - HTTP client for DuProcess Web Inquiry portals (Catalis/Hyland).

Handles session management, searching by date range via the CriteriaSearch
JSON API, and parsing Infragistics igGrid results. No authentication required.
No Selenium.

DuProcess is used by many Mississippi counties (Madison, Rankin, Harrison,
Forrest, Pearl River, etc.).

Usage:
    from county_scrapers.duprocess_client import DuProcessSession

    session = DuProcessSession("http://records.madison-co.com/DuProcessWebInquiry")
    session.connect()
    rows = session.search_by_date_range("01/01/2025", "01/31/2025")
"""

import json
import logging
import re
import time
from datetime import datetime, timedelta

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

log = logging.getLogger(__name__)

# Book type IDs observed across DuProcess portals.
# These are used to filter the search by record type.
BOOK_TYPE_DEED = '71'
BOOK_TYPE_DEED_OF_TRUST = '70'  # Mississippi equivalent of mortgage

_WHITESPACE_RE = re.compile(r'\s+')


def _clean_party(value: str) -> str:
    """Normalize whitespace in party name."""
    if not value:
        return ''
    return _WHITESPACE_RE.sub(' ', value).strip()


def _compose_legal(raw: dict) -> str:
    """Build a legal description string from DuProcess structured fields.

    Platted lots produce: "LOT 3 BLK A WALNUT RIDGE"
    PLSS parcels produce: "SEC 22 TWP 9N RNG 4E NE:+SW section"
    Falls back to legal_remarks if no structured data.
    """
    subdivision = str(raw.get('subdivision_name', '')).strip()
    lot = str(raw.get('lot_from', '')).strip()
    block = str(raw.get('block', '')).strip()
    section = str(raw.get('legal_section', '')).strip()
    township = str(raw.get('legal_township', '')).strip()
    range_ = str(raw.get('legal_range', '')).strip()
    remarks = str(raw.get('legal_remarks', '')).strip()

    parts = []
    if subdivision:
        if lot:
            parts.append(f'LOT {lot}')
        if block:
            parts.append(f'BLK {block}')
        parts.append(subdivision)
    elif section or township or range_:
        if section:
            parts.append(f'SEC {section}')
        if township:
            parts.append(f'TWP {township}')
        if range_:
            parts.append(f'RNG {range_}')

    legal = ' '.join(parts)

    if remarks and remarks.upper() != subdivision.upper():
        legal = f'{legal} {remarks}'.strip() if legal else remarks

    return legal


def _convert_date(duprocess_date: str) -> str:
    """Convert DuProcess date (M/D/YYYY H:MM:SS AM) to MM/DD/YYYY."""
    if not duprocess_date:
        return ''
    # Take just the date portion (before the space)
    date_part = duprocess_date.split(' ')[0] if ' ' in duprocess_date else duprocess_date
    parts = date_part.split('/')
    if len(parts) == 3:
        return f'{int(parts[0]):02d}/{int(parts[1]):02d}/{parts[2]}'
    return duprocess_date


def _build_criteria(begin_date: str, end_date: str,
                    book_type_id: str = '') -> str:
    """Build the JSON criteria_array parameter for CriteriaSearch."""
    criteria = {
        'direction': '',
        'name_direction': False,
        'full_name': '',
        'file_date_start': begin_date,
        'file_date_end': end_date,
        'inst_type': '',
        'inst_book_type_id': book_type_id,
        'location_id': '',
        'book_reel': '',
        'page_image': '',
        'greater_than_page': False,
        'inst_num': '',
        'description': '',
        'consideration_value_min': '',
        'consideration_value_max': '',
        'parcel_id': '',
        'legal_section': '',
        'legal_township': '',
        'legal_range': '',
        'legal_square': '',
        'subdivision_code': '',
        'block': '',
        'lot_from': '',
        'q_ne': False,
        'q_nw': False,
        'q_se': False,
        'q_sw': False,
        'q_q_ne': False,
        'q_q_nw': False,
        'q_q_se': False,
        'q_q_sw': False,
        'q_q_search_type': False,
        'address_street': '',
        'address_number': '',
        'address_parcel': '',
        'address_ppin': '',
        'patent_number': '',
    }
    return json.dumps([criteria])


class DuProcessSession:
    """Stateful HTTP client for a single DuProcess Web Inquiry portal."""

    def __init__(self, base_url: str, search_type: str = 'deed',
                 request_delay: float = 1.0):
        self.base_url = base_url.rstrip('/')
        self.search_type = search_type
        self.request_delay = request_delay

        self._session = requests.Session()
        retry = Retry(total=3, backoff_factor=1.5,
                      status_forcelist=[500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retry)
        self._session.mount('https://', adapter)
        self._session.mount('http://', adapter)
        self._session.headers.update({
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/124.0.0.0 Safari/537.36'
            ),
        })
        self._connected = False
        self._book_types: dict[str, str] = {}  # lowercase name → id

    def connect(self) -> None:
        """GET the portal home page and fetch book type mappings."""
        log.info('Connecting to %s', self.base_url)
        resp = self._session.get(f'{self.base_url}/', timeout=30)
        resp.raise_for_status()

        # Fetch book type IDs (vary per county)
        try:
            resp = self._session.get(
                f'{self.base_url}/Lookup/BookTypeLookup', timeout=15)
            resp.raise_for_status()
            raw = resp.json()
            self._book_types = {k.lower(): str(v) for k, v in raw.items()}
            log.info('Book types: %s', raw)
        except Exception as exc:
            log.warning('Could not fetch book types, using defaults: %s', exc)

        log.info('Session established')
        self._connected = True

    def search_by_date_range(self, begin_date: str, end_date: str) -> list[dict]:
        """
        Search by recording date range.

        Args:
            begin_date: MM/DD/YYYY
            end_date: MM/DD/YYYY

        Returns list of parsed record dicts.
        """
        self._ensure_connected()

        book_type_id = self._resolve_book_type()
        log.info('Searching records %s to %s (search_type=%s, book_type_id=%s)',
                 begin_date, end_date, self.search_type, book_type_id or 'ALL')

        # Check count first — if it exceeds the 2000 cap, auto-chunk by week
        criteria_json = _build_criteria(begin_date, end_date,
                                        book_type_id=book_type_id)
        resp = self._session.get(
            f'{self.base_url}/Home/CriteriaSearchCount',
            params={'criteria_array': criteria_json, 'user_id': ''},
            timeout=30,
        )
        resp.raise_for_status()
        count_data = json.loads(resp.json())  # double-encoded JSON string
        total_count = count_data.get('Count', 0)
        max_count = count_data.get('Max', 2000)
        log.info('Count: %d (max: %d)', total_count, max_count)

        if total_count == 0:
            return []

        if total_count > max_count:
            log.info('Exceeds cap — splitting into weekly chunks')
            return self._search_chunked(begin_date, end_date, book_type_id)

        return self._fetch_results(criteria_json)

    def _search_chunked(self, begin_date: str, end_date: str,
                        book_type_id: str) -> list[dict]:
        """Split a date range into weekly chunks and collect all results."""
        start = datetime.strptime(begin_date, '%m/%d/%Y').date()
        end = datetime.strptime(end_date, '%m/%d/%Y').date()
        all_rows = []
        chunk_num = 0

        while start <= end:
            chunk_end = min(start + timedelta(days=6), end)
            chunk_begin_str = start.strftime('%m/%d/%Y')
            chunk_end_str = chunk_end.strftime('%m/%d/%Y')
            chunk_num += 1

            criteria_json = _build_criteria(chunk_begin_str, chunk_end_str,
                                            book_type_id=book_type_id)
            log.info('  chunk %d: %s to %s', chunk_num,
                     chunk_begin_str, chunk_end_str)

            time.sleep(self.request_delay)
            chunk_rows = self._fetch_results(criteria_json)
            all_rows.extend(chunk_rows)

            start = chunk_end + timedelta(days=1)

        log.info('Total records across all chunks: %d', len(all_rows))
        return all_rows

    def _fetch_results(self, criteria_json: str) -> list[dict]:
        """Fetch search results for a single criteria query."""
        time.sleep(self.request_delay)
        resp = self._session.get(
            f'{self.base_url}/Home/CriteriaSearch',
            params={'criteria_array': criteria_json, 'user_id': ''},
            timeout=120,
        )
        resp.raise_for_status()

        data = resp.json()
        if not isinstance(data, list):
            log.warning('Unexpected response type: %s', type(data))
            return []

        rows = []
        for raw in data:
            parsed = self._parse_row(raw)
            if parsed:
                rows.append(parsed)

        log.info('  fetched %d records', len(rows))
        return rows

    def fetch_subdivisions(self) -> dict[str, str]:
        """Fetch the subdivision lookup (name → code) from the portal."""
        self._ensure_connected()
        resp = self._session.get(
            f'{self.base_url}/Lookup/SubdivisionLookup',
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        log.info('Fetched %d subdivisions', len(data))
        return data

    def _resolve_book_type(self) -> str:
        """Map search_type to DuProcess book type ID (auto-detected per county).

        Book type labels vary across counties:
          Madison:  "Deed" / "Deed Of Trust"
          Rankin:   "Deed" / "Deed of Trust"
          Harrison: "Deed Book" / "Trust Book"
        """
        if self.search_type == 'deed':
            return (self._book_types.get('deed')
                    or self._book_types.get('deed book')
                    or BOOK_TYPE_DEED)
        if self.search_type in ('mortgage', 'deed_of_trust'):
            return (self._book_types.get('deed of trust')
                    or self._book_types.get('trust book')
                    or BOOK_TYPE_DEED_OF_TRUST)
        return ''  # all types

    def _parse_row(self, raw: dict) -> dict | None:
        """Parse a single CriteriaSearch result into a clean record."""
        parsed = {
            'instrument': str(raw.get('inst_num', '')),
            'grantor': _clean_party(str(raw.get('from_party', ''))),
            'grantee': _clean_party(str(raw.get('to_party', ''))),
            'doc_type': str(raw.get('instrument_type', '')),
            'record_date': _convert_date(str(raw.get('file_date', ''))),
            'legal': _compose_legal(raw),
            'book': str(raw.get('book_reel', '')),
            'page': str(raw.get('page', '')).strip(),
            'book_type': str(raw.get('book_description', '')),
            'page_count': str(raw.get('num_pages', '')),
            'subdivision': str(raw.get('subdivision_name', '')),
            'lot': str(raw.get('lot_from', '')),
            'block': str(raw.get('block', '')),
            'gin': str(raw.get('gin', '')),
        }
        return parsed if any(v for k, v in parsed.items()) else None

    def _ensure_connected(self) -> None:
        if not self._connected:
            self.connect()

    def close(self) -> None:
        self._session.close()
        self._connected = False

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
