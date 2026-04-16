"""
tyler_selfservice_client.py - HTTP client for Tyler Technologies Self-Service
(Clerk Official Records) portals.

Handles anonymous disclaimer-gated session setup, a per-search POST that sets
server-side search state, and paginated HTML result retrieval. Used by Okaloosa
County FL (migrated from LandmarkWeb on 2026-04-14).

GOTCHA -- REGRESSION RISK:
    The search POST endpoint (`/web/searchPost/{search_id}`) REQUIRES the
    `ajaxRequest: true` header. Without it the server returns an HTML error
    page instead of the JSON shell (with `validationMessages` / `totalPages`).
    If this client ever starts returning HTML where JSON is expected, check
    this header first.

Usage:
    from county_scrapers.tyler_selfservice_client import TylerSelfServiceSession

    with TylerSelfServiceSession(
        "https://okaloosacountyfl-web.tylerhost.net/web",
        search_id="DOCSEARCH138S1",
    ) as session:
        session.connect()
        rows = session.search_by_date_range("4/1/2026", "4/1/2026")
"""

import html
import logging
import re
import time
from datetime import datetime
from urllib.parse import urlsplit

import requests

logger = logging.getLogger("county_scrapers.tyler_selfservice")


_H1_SEP_RE = re.compile(r'&#149;|\u2022|\xb7', re.IGNORECASE)
_HTML_TAG_RE = re.compile(r'<[^>]+>')
_WHITESPACE_RE = re.compile(r'\s+')
_ROW_SPLIT_RE = re.compile(r'<li class="ss-search-row"', re.IGNORECASE)
_DOCID_RE = re.compile(r'data-documentid="([^"]+)"', re.IGNORECASE)
_H1_RE = re.compile(r'<h1[^>]*>(.*?)</h1>', re.IGNORECASE | re.DOTALL)
_COLUMN_RE = re.compile(
    r'<div class="searchResultFourColumn">(.*?)</div>',
    re.IGNORECASE | re.DOTALL,
)
_B_RE = re.compile(r'<b>(.*?)</b>', re.IGNORECASE | re.DOTALL)
_TIME_SUFFIX_RE = re.compile(
    r'\s+\d{1,2}:\d{2}\s*(?:am|pm)\s*$', re.IGNORECASE)


def _strip_html(text: str) -> str:
    """Strip HTML tags and collapse whitespace, preserving HTML-entity decoding."""
    if not text:
        return ''
    unescaped = html.unescape(text)
    no_tags = _HTML_TAG_RE.sub(' ', unescaped)
    return _WHITESPACE_RE.sub(' ', no_tags).strip()


def _normalize_date(raw: str) -> str:
    """
    Strip an optional trailing `HH:MM AM|PM` time-of-day from a date string.

    '04/02/2026 04:52 PM' -> '04/02/2026'
    '04/02/2026'          -> '04/02/2026'
    ''                    -> ''
    """
    if not raw:
        return ''
    value = raw.strip()
    value = _TIME_SUFFIX_RE.sub('', value).strip()
    return value


def _extract_h1(h1_text: str) -> tuple[str, str]:
    """
    Pull (instrument_number, doc_type) out of the raw inner text of an <h1>.

    Tyler renders these separated by a bullet entity (`&nbsp;&#149;&nbsp;` or
    similar). Returns ('', '') on malformed input.
    """
    if not h1_text:
        return ('', '')
    decoded = html.unescape(h1_text)
    decoded = _HTML_TAG_RE.sub(' ', decoded)
    parts = _H1_SEP_RE.split(decoded)
    if len(parts) < 2:
        return ('', '')
    instrument = _WHITESPACE_RE.sub(' ', parts[0]).strip()
    doc_type = _WHITESPACE_RE.sub(' ', parts[1]).strip()
    if not instrument or not doc_type:
        return ('', '')
    return (instrument, doc_type)


def _extract_column_values(column_html: str) -> list[str]:
    """Return all <b>...</b> text values from a result-column block, in order."""
    if not column_html:
        return []
    values = []
    for m in _B_RE.finditer(column_html):
        cleaned = _strip_html(m.group(1))
        if cleaned:
            values.append(cleaned)
    return values


def _normalize_legal(values: list[str]) -> str:
    """Join legal-column <b> values with newlines. Empty list -> ''."""
    if not values:
        return ''
    if len(values) == 1:
        return values[0]
    return '\n'.join(values)


def _extract_parcel(legal_values: list[str]) -> str:
    """Find a 'Parcel: ...' line and return the trailing value; else ''."""
    for v in legal_values:
        if v.lower().startswith('parcel:'):
            return v.split(':', 1)[1].strip()
    return ''


class TylerSelfServiceSession:
    """Stateful HTTP client for a single Tyler Self-Service Clerk portal.

    The Tyler Self-Service search flow is:

        1. GET /web                         -> sets JSESSIONID
        2. POST /web/user/disclaimer        -> sets disclaimerAccepted=true
        3. GET /web/search/{search_id}      -> renders search form HTML
        4. POST /web/searchPost/{search_id} -> JSON {totalPages, validationMessages, ...}
                                               *** requires ajaxRequest: true header ***
        5. GET /web/searchResults/{search_id}?page=N  -> HTML page of rows

    Consideration/sale-price is not exposed by the search-results HTML; the
    detail pages carry it only as PDF imagery. This client does not attempt
    to decode those.
    """

    _USER_AGENT = (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    )

    def __init__(self, base_url: str, search_id: str = 'DOCSEARCH138S1',
                 doc_types: str = '', page_size: int = 100,
                 request_delay: float = 1.0):
        self.base_url = base_url.rstrip('/')
        self.search_id = search_id
        self.doc_types = doc_types
        self.page_size = page_size
        self.request_delay = request_delay

        self._session = requests.Session()
        self._session.headers.update({'User-Agent': self._USER_AGENT})
        self._connected = False

    # ------- public API --------------------------------------------------

    def connect(self) -> None:
        """Establish JSESSIONID, accept disclaimer, load search form."""
        logger.info('Connecting to %s', self.base_url)

        resp = self._session.get(self.base_url, timeout=30)
        resp.raise_for_status()
        time.sleep(self.request_delay)

        disclaimer_url = f'{self.base_url}/user/disclaimer'
        resp = self._session.post(disclaimer_url, timeout=30)
        resp.raise_for_status()
        time.sleep(self.request_delay)

        form_url = f'{self.base_url}/search/{self.search_id}'
        resp = self._session.get(form_url, timeout=30)
        resp.raise_for_status()

        logger.info('Session established for search %s', self.search_id)
        self._connected = True

    def search_by_date_range(self, begin_date: str,
                             end_date: str) -> list[dict]:
        """
        Search recordings by date range and return a list of parsed row dicts.

        Args:
            begin_date: MM/DD/YYYY or M/D/YYYY -- zero-padding is stripped.
            end_date:   same.
        """
        if not self._connected:
            raise RuntimeError(
                'TylerSelfServiceSession.connect() must be called before '
                'search_by_date_range()')

        begin_fmt = _format_date(begin_date)
        end_fmt = _format_date(end_date)

        logger.info('Tyler search: %s to %s (search_id=%s)',
                    begin_fmt, end_fmt, self.search_id)

        shell = self._post_search(begin_fmt, end_fmt)
        total_pages = int(shell.get('totalPages', 0) or 0)
        if total_pages <= 0:
            logger.info('Tyler search returned totalPages=0')
            return []

        all_rows: list[dict] = []
        for page in range(1, total_pages + 1):
            time.sleep(self.request_delay)
            html_text = self._fetch_page(page)
            page_rows = self._parse_results_page(html_text)
            logger.info('  page %d/%d: %d rows', page, total_pages,
                        len(page_rows))
            all_rows.extend(page_rows)

        logger.info('Total records retrieved: %d', len(all_rows))
        return all_rows

    @classmethod
    def from_cookies(cls, base_url: str, cookies, **kwargs):
        """
        Build an already-authenticated session from a captured cookie jar.

        This is a plumbing stub intended for a future captcha_hybrid path
        (Chrome captures JSESSIONID + disclaimerAccepted, we hand them to the
        HTTP session). It does NOT re-run connect() -- it marks the session
        as connected and expects the caller to have done the disclaimer flow.
        """
        instance = cls(base_url, **kwargs)
        if hasattr(cookies, 'items'):
            for k, v in cookies.items():
                instance._session.cookies.set(k, v)
        else:
            for cookie in cookies:
                instance._session.cookies.set_cookie(cookie)
        instance._connected = True
        return instance

    def close(self) -> None:
        self._session.close()
        self._connected = False

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    # ------- internals ---------------------------------------------------

    def _post_search(self, begin: str, end: str) -> dict:
        """POST the search form and return the JSON shell."""
        url = f'{self.base_url}/searchPost/{self.search_id}'
        split = urlsplit(self.base_url)
        origin = f'{split.scheme}://{split.netloc}'
        referer = f'{self.base_url}/search/{self.search_id}'

        headers = {
            'User-Agent': self._USER_AGENT,
            'ajaxRequest': 'true',              # REGRESSION RISK -- see module docstring
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': referer,
            'Origin': origin,
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        }

        payload = {
            'field_RecordingDateID_DOT_StartDate': begin,
            'field_RecordingDateID_DOT_EndDate': end,
            'field_BothNamesID': '',
            'field_GrantorID': '',
            'field_GranteeID': '',
            'field_DocumentNumberID': '',
            'field_BookPageID_DOT_Book': '',
            'field_BookPageID_DOT_Volume': '',
            'field_BookPageID_DOT_Page': '',
            'field_PlattedLegalID_DOT_Subdivision': '',
            'field_PlattedLegalID_DOT_Lot': '',
            'field_PlattedLegalID_DOT_Block': '',
            'field_PlattedLegalID_DOT_Tract': '',
            'field_PlattedLegalID_DOT_Unit': '',
            'field_PLSSLegalID_DOT_SixteenthSection': '',
            'field_PLSSLegalID_DOT_QuarterSection': '',
            'field_PLSSLegalID_DOT_Section': '',
            'field_PLSSLegalID_DOT_Township': '',
            'field_PLSSLegalID_DOT_Range': '',
            'field_selfservice_documentTypes': self.doc_types,
            'field_UseAdvancedSearch': '',
        }

        resp = self._session.post(url, data=payload, headers=headers,
                                  timeout=60)
        resp.raise_for_status()

        try:
            data = resp.json()
        except ValueError as exc:
            raise RuntimeError(
                'Tyler searchPost returned non-JSON response -- check that '
                'the ajaxRequest header is set correctly'
            ) from exc

        validation = data.get('validationMessages') or {}
        if validation:
            raise RuntimeError(
                f'Tyler search validation failed: {validation}')
        return data

    def _fetch_page(self, page_num: int) -> str:
        """GET a results page and return raw HTML."""
        url = f'{self.base_url}/searchResults/{self.search_id}'
        headers = {
            'User-Agent': self._USER_AGENT,
            'Referer': f'{self.base_url}/search/{self.search_id}',
        }
        resp = self._session.get(url, params={'page': str(page_num)},
                                 headers=headers, timeout=60)
        resp.raise_for_status()
        return resp.text

    def _parse_results_page(self, html_text: str) -> list[dict]:
        """Split on <li class="ss-search-row"> boundaries and parse each row."""
        if not html_text:
            return []
        parts = _ROW_SPLIT_RE.split(html_text)
        rows: list[dict] = []
        # parts[0] is everything before the first row -- skip it.
        for chunk in parts[1:]:
            # Re-prefix so each chunk is a valid fragment starting with the
            # opening tag we just split on.
            fragment = '<li class="ss-search-row"' + chunk
            parsed = self._parse_row(fragment)
            if parsed:
                rows.append(parsed)
        return rows

    def _parse_row(self, li_html: str) -> dict | None:
        """Parse one <li class="ss-search-row"> fragment into a record dict."""
        if not li_html:
            return None

        doc_m = _DOCID_RE.search(li_html)
        document_id = doc_m.group(1) if doc_m else ''

        h1_m = _H1_RE.search(li_html)
        h1_inner = h1_m.group(1) if h1_m else ''
        instrument, doc_type = _extract_h1(h1_inner)

        columns = _COLUMN_RE.findall(li_html)
        # columns order: [RecordingDate, Grantor, Grantee, Legal]
        record_date = ''
        grantor = ''
        grantee = ''
        legal = ''
        parcel = ''

        if len(columns) >= 1:
            date_values = _extract_column_values(columns[0])
            record_date = _normalize_date(date_values[0]) if date_values else ''
        if len(columns) >= 2:
            grantor_values = _extract_column_values(columns[1])
            grantor = '; '.join(grantor_values)
        if len(columns) >= 3:
            grantee_values = _extract_column_values(columns[2])
            grantee = '; '.join(grantee_values)
        if len(columns) >= 4:
            legal_values = _extract_column_values(columns[3])
            legal = _normalize_legal(legal_values)
            parcel = _extract_parcel(legal_values)

        # Reject truly empty rows (all identity fields blank).
        if not (document_id or instrument or grantor or grantee or legal):
            return None

        return {
            'instrument': instrument,
            'doc_type': doc_type,
            'record_date': record_date,
            'grantor': grantor,
            'grantee': grantee,
            'legal': legal,
            'document_id': document_id,
            'book': '',
            'page': '',
            'book_type': '',
            'consideration': '',
            'parcel': parcel,
        }


def _format_date(raw: str) -> str:
    """
    Normalize a date string to Tyler's expected `M/D/YYYY` shape.

    Accepts 'MM/DD/YYYY', 'M/D/YYYY', or already-formatted input. Returns the
    input unchanged if it can't be parsed (caller is responsible for
    surfacing the error downstream).
    """
    if not raw:
        return raw
    candidate = raw.strip()
    for fmt in ('%m/%d/%Y', '%m/%d/%y', '%Y-%m-%d'):
        try:
            dt = datetime.strptime(candidate, fmt)
        except ValueError:
            continue
        return f'{dt.month}/{dt.day}/{dt.year}'
    return candidate
