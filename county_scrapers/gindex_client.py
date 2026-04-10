"""
gindex_client.py - HTML scraper for Hinds County MS General Index portal.

Handles session management, date-range searching, pagination, and HTML
table parsing for the ASP Classic portal at co.hinds.ms.us.

No authentication required. No API — results are server-rendered HTML tables.
500-record cap per search; auto-chunks into daily ranges to stay under the cap.

Usage:
    from county_scrapers.gindex_client import GIndexSession

    session = GIndexSession("https://www.co.hinds.ms.us/pgs/apps")
    session.connect()
    rows = session.search_by_date_range("01/01/2025", "01/31/2025")
"""

import logging
import re
import time
from datetime import datetime, timedelta

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

log = logging.getLogger(__name__)

_HTML_TAG_RE = re.compile(r'<[^>]+>')
_NBSP_INDENT_RE = re.compile(r'&nbsp;&nbsp;&nbsp;&nbsp;\s*')
_WHITESPACE_RE = re.compile(r'\s+')
_PAGE_RE = re.compile(r'Page\s+(\d+)\s+of\s+(\d+)')
_ROW_RE = re.compile(r'<TR VALIGN=TOP>(.*?)</TR>', re.DOTALL | re.IGNORECASE)
_CELL_RE = re.compile(r'<TD[^>]*>(.*?)</TD>', re.DOTALL | re.IGNORECASE)

# sn2 values for the General Index search form
BOOK_DEED = '2'          # Deed Book only
BOOK_DEED_OF_TRUST = '1' # Deed of Trust only
BOOK_BOTH = '3'          # Both


def _clean_text(html_text: str) -> str:
    """Strip HTML tags and normalize whitespace."""
    text = _HTML_TAG_RE.sub(' ', html_text)
    text = text.replace('&nbsp;', ' ')
    text = _WHITESPACE_RE.sub(' ', text).strip()
    return text


def _parse_date(date_str: str) -> str:
    """Convert MM-DD-YYYY to MM/DD/YYYY."""
    if not date_str:
        return ''
    return date_str.replace('-', '/')


class GIndexSession:
    """Stateful HTTP client for the Hinds County General Index portal."""

    def __init__(self, base_url: str, book_type: str = BOOK_DEED,
                 request_delay: float = 1.0, use_cffi: bool = False):
        self.base_url = base_url.rstrip('/')
        self.book_type = book_type
        self.request_delay = request_delay

        if use_cffi:
            from curl_cffi import requests as cf_requests
            self._session = cf_requests.Session(impersonate='chrome')
        else:
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
        """GET the search form to establish a session cookie."""
        log.info('Connecting to %s', self.base_url)
        resp = self._session.get(
            f'{self.base_url}/gindex_query.asp', timeout=30)
        resp.raise_for_status()
        log.info('Session established')
        self._connected = True

    def search_by_date_range(self, begin_date: str, end_date: str) -> list[dict]:
        """
        Search by recording date range, auto-chunking into daily ranges.

        Args:
            begin_date: MM/DD/YYYY
            end_date: MM/DD/YYYY

        Returns list of parsed record dicts.
        """
        self._ensure_connected()
        log.info('Searching records %s to %s (book_type=%s)',
                 begin_date, end_date, self.book_type)

        start = datetime.strptime(begin_date, '%m/%d/%Y').date()
        end = datetime.strptime(end_date, '%m/%d/%Y').date()

        all_rows = []
        current = start

        while current <= end:
            chunk_end = min(current + timedelta(days=2), end)
            chunk_rows = self._search_single_range(current, chunk_end)
            all_rows.extend(chunk_rows)
            current = chunk_end + timedelta(days=1)
            if current <= end:
                time.sleep(self.request_delay)

        # Deduplicate by (grantor, grantee, book_page, date)
        seen = set()
        unique = []
        for row in all_rows:
            key = (row.get('grantor', ''), row.get('grantee', ''),
                   row.get('book_page', ''), row.get('record_date', ''))
            if key not in seen:
                seen.add(key)
                unique.append(row)

        log.info('Total unique records: %d (from %d raw)',
                 len(unique), len(all_rows))
        return unique

    def _search_single_range(self, start_date, end_date) -> list[dict]:
        """Search a single short date range and paginate through all results."""
        params = {
            'sn0': '',
            'sn1': '3',       # Both grantor and grantee
            'sn2': self.book_type,
            'Start_Date_m': f'{start_date.month:02d}',
            'Start_Date_d': f'{start_date.day:02d}',
            'Start_Date_y': str(start_date.year),
            'End_Date_m': f'{end_date.month:02d}',
            'End_Date_d': f'{end_date.day:02d}',
            'End_Date_y': str(end_date.year),
        }

        # Page 1
        resp = self._session.get(
            f'{self.base_url}/gindex_list.asp',
            params=params,
            timeout=30,
        )
        resp.raise_for_status()

        all_rows = []
        page_rows = self._parse_page(resp.text)
        all_rows.extend(page_rows)

        # Check total pages
        page_match = _PAGE_RE.search(resp.text)
        if not page_match:
            return all_rows

        total_pages = int(page_match.group(2))
        log.info('  %s to %s: page 1/%d (%d rows)',
                 start_date.strftime('%m/%d'), end_date.strftime('%m/%d'),
                 total_pages, len(page_rows))

        # Paginate through remaining pages
        for page_num in range(2, total_pages + 1):
            time.sleep(self.request_delay)
            resp = self._session.get(
                f'{self.base_url}/gindex_list.asp',
                params={'ScrollAction': f'Page {page_num}', 'SS1': '1'},
                timeout=30,
            )
            resp.raise_for_status()

            page_rows = self._parse_page(resp.text)
            all_rows.extend(page_rows)

        return all_rows

    def _parse_page(self, html: str) -> list[dict]:
        """Parse all data rows from a results page HTML."""
        rows = []
        for match in _ROW_RE.finditer(html):
            row_html = match.group(1)
            parsed = self._parse_row(row_html)
            if parsed:
                rows.append(parsed)
        return rows

    def _parse_row(self, row_html: str) -> dict | None:
        """Parse a single HTML table row into a record dict."""
        cells = _CELL_RE.findall(row_html)
        if len(cells) < 3:
            return None

        # Cell 0: Grantor / Grantee (separated by &nbsp; indent)
        name_html = cells[0]
        name_text = _HTML_TAG_RE.sub('', name_html)
        name_parts = _NBSP_INDENT_RE.split(name_text, maxsplit=1)
        grantor = _WHITESPACE_RE.sub(' ', name_parts[0]).strip()
        grantee = _WHITESPACE_RE.sub(' ', name_parts[1]).strip() if len(name_parts) > 1 else ''

        # Cell 1: Instrument type + book-page (separated by newline)
        inst_text = _HTML_TAG_RE.sub('', cells[1]).strip()
        inst_lines = [l.strip() for l in inst_text.split('\n') if l.strip()]
        doc_type = inst_lines[0] if inst_lines else ''
        book_page = inst_lines[-1] if len(inst_lines) > 1 else ''

        # Split book-page (format: "7302-7543" or "0809-0424")
        book = ''
        page = ''
        if '-' in book_page:
            bp_parts = book_page.split('-', 1)
            book = bp_parts[0].strip().lstrip('0') or '0'
            page = bp_parts[1].strip().lstrip('0') or '0'

        # Cell 2: Date + optional Remark
        date_text = _HTML_TAG_RE.sub('', cells[2]).strip()
        date_lines = [l.strip() for l in date_text.split('\n') if l.strip()]
        record_date = _parse_date(date_lines[0]) if date_lines else ''
        has_remark = 'Remark' in cells[2]

        if not grantor and not grantee:
            return None

        return {
            'grantor': grantor,
            'grantee': grantee,
            'doc_type': doc_type,
            'book': book,
            'page': page,
            'book_page': book_page,
            'record_date': record_date,
            'instrument': book_page,
            'has_remark': has_remark,
        }

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
