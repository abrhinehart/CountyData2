"""
acclaimweb_client.py - HTTP client for AcclaimWeb portals (Harris Recording Solutions).

Handles session management, searching by date range via Telerik grid
JSON API, and parsing record results. No authentication required.

Used by DeSoto County MS.

Usage:
    from county_scrapers.acclaimweb_client import AcclaimWebSession

    session = AcclaimWebSession("https://landrecords.desotocountyms.gov/AcclaimWeb")
    session.connect()
    rows = session.search_by_date_range("01/01/2025", "01/31/2025")
"""

import json
import logging
import re
import time
from datetime import datetime, timedelta

from curl_cffi import requests as cf_requests

log = logging.getLogger(__name__)

_BR_RE = re.compile(r'<br\s*/?>', re.IGNORECASE)
_HTML_TAG_RE = re.compile(r'<[^>]+>')
_WHITESPACE_RE = re.compile(r'\s+')

# Default doc type IDs for common deed types (DeSoto County values).
# Can be overridden per county via configs.
DEFAULT_DEED_DOC_TYPES = '1509,1342,1080'  # WAR + QCL + DEE


def _clean_name(value: str) -> str:
    """Replace <br> with '; ', strip HTML tags, normalize whitespace."""
    if not value:
        return ''
    text = _BR_RE.sub('; ', value)
    text = _HTML_TAG_RE.sub('', text)
    text = _WHITESPACE_RE.sub(' ', text).strip()
    text = text.strip('; ').strip()
    return text


def _convert_date(dotnet_date: str) -> str:
    """Convert .NET JSON date (/Date(epoch_ms)/) to MM/DD/YYYY."""
    if not dotnet_date:
        return ''
    match = re.search(r'/Date\((\d+)\)/', dotnet_date)
    if match:
        epoch_ms = int(match.group(1))
        dt = datetime.fromtimestamp(epoch_ms / 1000)
        return dt.strftime('%m/%d/%Y')
    return dotnet_date


def _parse_book_page(book_page: str) -> tuple[str, str]:
    """Parse 'BOOK  /  PAGE' format into (book, page)."""
    if not book_page or '/' not in book_page:
        return ('', '')
    parts = book_page.split('/', 1)
    return (parts[0].strip(), parts[1].strip())


class AcclaimWebSession:
    """Stateful HTTP client for a single AcclaimWeb portal."""

    def __init__(self, base_url: str, doc_types: str = DEFAULT_DEED_DOC_TYPES,
                 page_size: int = 500, request_delay: float = 1.0):
        self.base_url = base_url.rstrip('/')
        self.doc_types = doc_types
        self.page_size = page_size
        self.request_delay = request_delay

        self._session = cf_requests.Session(impersonate='chrome')
        self._connected = False

    def connect(self) -> None:
        """GET the search form to establish a session cookie."""
        log.info('Connecting to %s', self.base_url)
        resp = self._session.get(
            f'{self.base_url}/search/SearchTypeDocType', timeout=30)
        resp.raise_for_status()
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
        log.info('Searching records %s to %s (doc_types=%s)',
                 begin_date, end_date, self.doc_types)

        # Step 1: POST the search form to set server-side search state
        resp = self._session.post(
            f'{self.base_url}/search/SearchTypeDocType?Length=6',
            data={
                'DocTypes': self.doc_types,
                'RecordDateFrom': begin_date,
                'RecordDateTo': end_date,
                'ShowAllNames': 'true',
                'ShowAllLegals': 'true',
            },
            timeout=60,
        )
        resp.raise_for_status()

        time.sleep(self.request_delay)

        # Step 2: Paginate through GridResults
        all_rows = []
        page = 1

        while True:
            resp = self._session.post(
                f'{self.base_url}/Search/GridResults?Length=6',
                data={
                    'page': str(page),
                    'size': str(self.page_size),
                    'orderBy': '~',
                    'groupBy': '~',
                    'filter': '~',
                },
                headers={'X-Requested-With': 'XMLHttpRequest'},
                timeout=60,
            )
            resp.raise_for_status()

            data = resp.json()
            total = int(data.get('total', 0))
            page_data = data.get('data', [])

            if not page_data:
                break

            for raw in page_data:
                parsed = self._parse_row(raw)
                if parsed:
                    all_rows.append(parsed)

            log.info('  fetched %d/%d records', len(all_rows), total)

            if len(all_rows) >= total:
                break

            page += 1
            time.sleep(self.request_delay)

        log.info('Total records retrieved: %d', len(all_rows))
        return all_rows

    def _parse_row(self, raw: dict) -> dict | None:
        """Parse a single GridResults row into a clean record."""
        book, page = _parse_book_page(str(raw.get('BookPage', '')))

        # doc_type: DeSoto uses DocType (abbreviation), Santa Rosa uses DocTypeDescription
        doc_type = str(raw.get('DocType', '')) or str(raw.get('DocTypeDescription', ''))
        # legal: DeSoto uses DocLegalDescription, Santa Rosa uses Comments
        legal = str(raw.get('DocLegalDescription', '')) or str(raw.get('Comments', ''))
        # consideration: Santa Rosa has sale prices (FL full-disclosure)
        consideration = raw.get('Consideration')
        consideration_str = f'{consideration:.0f}' if consideration else ''

        parsed = {
            'instrument': str(raw.get('TransactionItemId', '')),
            'grantor': _clean_name(str(raw.get('DirectName', ''))),
            'grantee': _clean_name(str(raw.get('IndirectName', ''))),
            'doc_type': doc_type,
            'record_date': _convert_date(str(raw.get('RecordDate', ''))),
            'legal': legal,
            'book': book,
            'page': page,
            'book_type': str(raw.get('BookType', '')),
            'transaction_id': str(raw.get('TransactionId', '')),
            'consideration': consideration_str,
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
