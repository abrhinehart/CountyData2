"""
landmark_client.py - HTTP client for Pioneer Technology Group LandmarkWeb portals.

Handles session management, disclaimer acceptance, searching by date range
or document type, and parsing DataTables JSON responses. No Selenium.

Usage:
    from county_scrapers.landmark_client import LandmarkSession

    session = LandmarkSession("https://or.hernandoclerk.com/LandmarkWeb")
    session.connect()
    rows = session.search_by_date_range("01/01/2025", "01/31/2025")
"""

import html
import logging
import re
import time

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

log = logging.getLogger(__name__)

_HTML_TAG_RE = re.compile(r'<[^>]+>')
_WHITESPACE_RE = re.compile(r'\s+')
_VALUE_PREFIX_RE = re.compile(r'^(?:nobreak_|hidden_(?:legalfield_)?|unclickable_)')
_NAME_SEP_RE = re.compile(r'<div\s+class=[\'"]nameSeperator[\'"]>\s*</div>', re.IGNORECASE)

# Default DataTables column indices for RecordDateSearch results.
# These can be overridden per county via configs.py.
# Column counts and indices vary between LandmarkWeb versions.
DEFAULT_COLUMN_MAP = {
    'grantor': '5',
    'grantee': '6',
    'record_date': '7',
    'doc_type': '8',
    'book_type': '9',
    'book': '10',
    'page': '11',
    'instrument': '12',
    'legal': '13',
}

_AJAX_HEADERS = {
    'X-Requested-With': 'XMLHttpRequest',
}


def _clean_value(value: str) -> str:
    """Strip LandmarkWeb prefixes, HTML tags, and normalize whitespace."""
    if not value:
        return ''
    # Strip nobreak_, hidden_, unclickable_ prefixes
    text = _VALUE_PREFIX_RE.sub('', value)
    # Replace name separator divs with semicolons
    text = _NAME_SEP_RE.sub('; ', text)
    # Strip remaining HTML tags
    text = _HTML_TAG_RE.sub(' ', text)
    text = html.unescape(text)
    text = _WHITESPACE_RE.sub(' ', text).strip()
    return text


class LandmarkSession:
    """Stateful HTTP client for a single LandmarkWeb portal."""

    def __init__(self, base_url: str, column_map: dict | None = None,
                 page_size: int = 500, request_delay: float = 1.0):
        self.base_url = base_url.rstrip('/')
        self.column_map = column_map or dict(DEFAULT_COLUMN_MAP)
        self.page_size = page_size
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

    def connect(self) -> None:
        """GET the home page (obtains session cookie) then accept the disclaimer."""
        log.info('Connecting to %s', self.base_url)
        resp = self._session.get(f'{self.base_url}/Home/Index', timeout=30)
        resp.raise_for_status()
        log.debug('Home page loaded, status %s', resp.status_code)

        resp = self._session.post(
            f'{self.base_url}/Search/SetDisclaimer',
            headers=_AJAX_HEADERS,
            timeout=15,
        )
        resp.raise_for_status()
        log.info('Disclaimer accepted')
        self._connected = True

    def search_by_date_range(self, begin_date: str, end_date: str,
                             doc_types: str = '') -> list[dict]:
        """
        Search by recording date range.

        Args:
            begin_date: MM/DD/YYYY
            end_date: MM/DD/YYYY
            doc_types: Comma-separated doc type IDs to filter (e.g. "17" for DEED).
                       Empty string means all types.

        Returns list of parsed record dicts.
        """
        self._ensure_connected()
        log.info('Searching records %s to %s (doc_types=%s)',
                 begin_date, end_date, doc_types or 'ALL')

        payload = {
            'beginDate': begin_date,
            'endDate': end_date,
            'doctype': doc_types,
            'recordCount': '50000',
            'exclude': 'false',
            'ReturnIndexGroups': 'false',
            'townName': '',
            'mobileHomesOnly': 'false',
        }
        resp = self._session.post(
            f'{self.base_url}/Search/RecordDateSearch',
            data=payload,
            headers=_AJAX_HEADERS,
            timeout=30,
        )
        resp.raise_for_status()
        log.debug('RecordDateSearch posted, status %s', resp.status_code)

        time.sleep(self.request_delay)
        return self._fetch_all_results()

    def search_by_doc_type(self, doc_type_ids: str,
                           begin_date: str = '', end_date: str = '') -> list[dict]:
        """
        Search by document type with optional date range.

        Args:
            doc_type_ids: Comma-separated doc type IDs (required).
            begin_date: MM/DD/YYYY (optional).
            end_date: MM/DD/YYYY (optional).
        """
        self._ensure_connected()
        log.info('Searching by doc type %s (%s to %s)',
                 doc_type_ids, begin_date or '*', end_date or '*')

        payload = {
            'doctype': doc_type_ids,
            'beginDate': begin_date,
            'endDate': end_date,
            'recordCount': '50000',
            'exclude': 'false',
            'ReturnIndexGroups': 'false',
            'townName': '',
            'mobileHomesOnly': 'false',
        }
        resp = self._session.post(
            f'{self.base_url}/Search/DocumentTypeSearch',
            data=payload,
            headers=_AJAX_HEADERS,
            timeout=30,
        )
        resp.raise_for_status()
        log.debug('DocumentTypeSearch posted, status %s', resp.status_code)

        time.sleep(self.request_delay)
        return self._fetch_all_results()

    def _ensure_connected(self) -> None:
        if not self._connected:
            self.connect()

    def _fetch_all_results(self) -> list[dict]:
        """Page through GetSearchResults until all rows are collected."""
        all_rows = []
        draw = 1
        start = 0

        while True:
            payload = {
                'draw': str(draw),
                'start': str(start),
                'length': str(self.page_size),
            }
            resp = self._session.post(
                f'{self.base_url}/Search/GetSearchResults',
                data=payload,
                headers=_AJAX_HEADERS,
                timeout=30,
            )
            resp.raise_for_status()

            data = resp.json()
            records_total = int(data.get('recordsTotal', 0))
            page_rows = data.get('data', [])

            if not page_rows:
                break

            for raw in page_rows:
                parsed = self._parse_row(raw)
                if parsed:
                    all_rows.append(parsed)

            log.info('  fetched %d/%d records', len(all_rows), records_total)

            start += len(page_rows)
            draw += 1

            if start >= records_total:
                break

            time.sleep(self.request_delay)

        log.info('Total records retrieved: %d', len(all_rows))
        return all_rows

    def _parse_row(self, raw: dict) -> dict | None:
        """Parse a single DataTables row dict into a clean record."""
        row_id = raw.get('DT_RowId', '')
        doc_id = None
        if row_id:
            parts = row_id.split('_')
            if len(parts) >= 2:
                doc_id = parts[1]

        parsed = {}
        for field, col_key in self.column_map.items():
            value = raw.get(col_key, '')
            parsed[field] = _clean_value(str(value)) if value else ''

        # Always use document_id from the DT_RowId (most reliable)
        if doc_id:
            parsed['document_id'] = doc_id

        return parsed if any(v for k, v in parsed.items() if k != 'document_id') else None

    def close(self) -> None:
        self._session.close()
        self._connected = False

    @classmethod
    def from_cookies(cls, base_url: str, cookies: dict[str, str],
                     column_map: dict | None = None,
                     page_size: int = 500,
                     request_delay: float = 1.0) -> 'LandmarkSession':
        """Create a LandmarkSession pre-loaded with cookies (captcha_hybrid flow)."""
        from county_scrapers.cookie_session import apply_cookies_to_session
        instance = cls(base_url, column_map=column_map,
                       page_size=page_size, request_delay=request_delay)
        apply_cookies_to_session(instance._session, cookies)
        instance._connected = True
        return instance

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
