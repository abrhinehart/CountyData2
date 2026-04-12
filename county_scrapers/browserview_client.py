"""
browserview_client.py - Selenium-driven client for NewVision BrowserView portals.

Uses the hybrid captcha pattern: user opens the portal in a browser, does one
manual search to satisfy reCAPTCHA v3 (building trust score), then the script
takes over and drives subsequent searches through Angular's scope.

The BrowserView API enforces reCAPTCHA v3 server-side. Fresh Selenium instances
get a score of 0 (bot) regardless of headless/visible mode. After a human
performs one manual search, the reCAPTCHA trust persists and automated searches
succeed within the same session.

Used by Marion County FL.

Usage:
    from county_scrapers.browserview_client import BrowserViewSession

    session = BrowserViewSession("https://nvweb.marioncountyclerk.org/BrowserView")
    session.connect()  # Opens browser, user does one manual search
    rows = session.search_by_date_range("01/01/2026", "01/31/2026")
"""

import logging
import re
import time
from datetime import datetime

log = logging.getLogger(__name__)

_WHITESPACE_RE = re.compile(r'\s+')

# Deed doc type codes for BrowserView.
# Marion County: D = Deed, D2 = Deed, DD = Deed
DEFAULT_DEED_DOC_TYPES = 'D,D2,DD'


def _clean_text(value) -> str:
    """Normalize whitespace, strip None values."""
    if value is None:
        return ''
    text = str(value).strip()
    return _WHITESPACE_RE.sub(' ', text)


def _format_date(value) -> str:
    """Convert ISO 8601 date to MM/DD/YYYY."""
    if not value:
        return ''
    try:
        dt = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
        return dt.strftime('%m/%d/%Y')
    except (ValueError, TypeError):
        return str(value).strip()


def _format_money(value) -> str:
    """Format consideration amount, returning '' for zero/missing."""
    if value is None or value == '' or value == 0:
        return ''
    try:
        amt = float(value)
        return '' if amt == 0 else f'{amt:.0f}'
    except (ValueError, TypeError):
        return str(value)


# JavaScript helpers used in execute_script calls.
_JS_SET_CRITERIA = """
    var scope = angular.element(
        document.querySelector('[ng-controller="SearchController"]')
    ).scope();
    var svc = scope.documentService;
    svc.SearchCriteria.fromDate = new Date(arguments[0], arguments[1], arguments[2]);
    svc.SearchCriteria.toDate = new Date(arguments[3], arguments[4], arguments[5]);
    svc.SearchCriteria.searchDocType = arguments[6];
    svc.SearchCriteria.rowsPerPage = arguments[7];
    svc.SearchCriteria.startRow = arguments[8];
    svc.SearchCriteria.maxRows = 0;
    scope.$apply();
"""

_JS_RUN_SEARCH = """
    var scope = angular.element(
        document.querySelector('[ng-controller="SearchController"]')
    ).scope();
    scope.searchTabs = [false,true,false,false,false,false,false,
                        false,false,false,false,false,false];
    scope.mainTabs = [true, false, false];
    scope.runSearch(arguments[0]);
"""

_JS_CHECK_COUNT = """
    var svc = angular.element(
        document.querySelector('[ng-controller="SearchController"]')
    ).scope().documentService;
    var r = svc.SearchResults.results;
    return r ? r.length : 0;
"""

_JS_EXTRACT_RESULTS = """
    var svc = angular.element(
        document.querySelector('[ng-controller="SearchController"]')
    ).scope().documentService;
    var r = svc.SearchResults.results;
    if (!r || r.length === 0) {
        return {records:[], total_rows:0, max_rows:0, end_row:0, start_row:0};
    }
    var out = [];
    for (var i = 0; i < r.length; i++) {
        var row = {};
        for (var k in r[i]) {
            if (k !== '_headers') row[k] = r[i][k];
        }
        out.push(row);
    }
    return {
        records: out,
        total_rows: svc.SearchResults.totalRows || 0,
        max_rows: svc.SearchResults.maxRows || 0,
        end_row: svc.SearchResults.endRow || 0,
        start_row: svc.SearchResults.startRow || 0
    };
"""

_JS_ANGULAR_READY = """
    try {
        var scope = angular.element(
            document.querySelector('[ng-controller="SearchController"]')
        ).scope();
        if (!scope || !scope.documentService) return false;
        return typeof grecaptcha !== 'undefined'
            && typeof grecaptcha.execute === 'function';
    } catch(e) { return false; }
"""


class BrowserViewSession:
    """Selenium-driven client for a BrowserView portal (hybrid captcha pattern).

    On connect(), opens a visible Chrome browser and prompts the user to
    perform one manual search. This builds reCAPTCHA v3 trust so that
    subsequent automated searches succeed within the same session.
    """

    def __init__(self, base_url: str, doc_types: str = DEFAULT_DEED_DOC_TYPES,
                 page_size: int = 1000, request_delay: float = 2.0):
        self.base_url = base_url.rstrip('/')
        self.doc_types = doc_types
        self.page_size = page_size
        self.request_delay = request_delay
        self._driver = None
        self._connected = False

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def connect(self) -> None:
        """Launch browser, prompt user to do one manual search, then take over."""
        log.info('Connecting to %s', self.base_url)
        self._driver = self._build_driver()
        self._driver.get(self.base_url)
        self._wait_for_angular(timeout=30)

        # Hybrid captcha: user must do one manual search to build reCAPTCHA
        # trust. The script then takes over for all subsequent searches.
        print(
            '\n  Marion County BrowserView has opened in Chrome.\n'
            '  Please:\n'
            '    1. Click the "Document Type" tab\n'
            '    2. Set a date range (e.g., today\'s date in both fields)\n'
            '    3. Click "Search"\n'
            '    4. Wait for results to appear\n'
            '    5. Come back here and press Enter\n'
        )
        input('  Press Enter when done...')

        self._connected = True
        log.info('BrowserView session established (post-manual-search)')

    def close(self) -> None:
        if self._driver:
            try:
                self._driver.quit()
            except Exception:
                pass
            self._driver = None
        self._connected = False

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search_by_date_range(self, begin_date: str, end_date: str) -> list[dict]:
        """Search by recording date range (MM/DD/YYYY). Returns parsed records."""
        self._ensure_connected()

        start_dt = datetime.strptime(begin_date, '%m/%d/%Y')
        end_dt = datetime.strptime(end_date, '%m/%d/%Y')

        log.info('Searching records %s to %s (doc_types=%s)',
                 begin_date, end_date, self.doc_types)

        all_rows = []
        start_row = 0

        while True:
            result = self._execute_search(start_dt, end_dt, start_row)

            records = result.get('records', [])
            total_rows = result.get('total_rows', 0)
            max_rows = result.get('max_rows', 0)
            end_row = result.get('end_row', 0)
            effective_max = max_rows if max_rows > 0 else total_rows

            for raw in records:
                parsed = self._parse_row(raw)
                if parsed:
                    all_rows.append(parsed)

            log.info('  fetched %d records (rows %d-%d of %d)',
                     len(records), start_row + 1, end_row, total_rows)

            if not records or end_row >= effective_max or end_row >= total_rows:
                break

            start_row = end_row
            time.sleep(self.request_delay)

        log.info('Total records retrieved: %d', len(all_rows))
        return all_rows

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_driver(self):
        """Create a visible Chrome WebDriver with anti-detection settings."""
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager

        options = webdriver.ChromeOptions()
        # Visible browser required for reCAPTCHA v3 trust.
        options.add_argument('--window-size=1600,1200')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.execute_cdp_cmd(
            'Page.addScriptToEvaluateOnNewDocument',
            {'source': "Object.defineProperty(navigator, 'webdriver', "
                       "{get: () => undefined});"},
        )
        return driver

    def _wait_for_angular(self, timeout: int = 30) -> None:
        """Wait until Angular + reCAPTCHA v3 are bootstrapped."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            if self._driver.execute_script(_JS_ANGULAR_READY):
                log.info('Angular + reCAPTCHA ready')
                return
            time.sleep(1)
        raise RuntimeError('Angular/reCAPTCHA not ready after %ds' % timeout)

    def _execute_search(self, start_dt: datetime, end_dt: datetime,
                        start_row: int = 0) -> dict:
        """Run one search page through Angular's scope and wait for results."""

        # Clear previous results so we can detect fresh data
        self._driver.execute_script("""
            var svc = angular.element(
                document.querySelector('[ng-controller="SearchController"]')
            ).scope().documentService;
            svc.SearchResults.results = null;
            svc.SearchResults.totalRows = 0;
        """)

        # Set search criteria
        self._driver.execute_script(
            _JS_SET_CRITERIA,
            start_dt.year, start_dt.month - 1, start_dt.day,
            end_dt.year, end_dt.month - 1, end_dt.day,
            self.doc_types, self.page_size, start_row,
        )
        time.sleep(1)

        # Override tabs and trigger search
        self._driver.execute_script(_JS_RUN_SEARCH, start_row == 0)

        # Wait for results (reCAPTCHA token gen + server round-trip)
        deadline = time.time() + 60
        while time.time() < deadline:
            time.sleep(1)
            count = self._driver.execute_script(_JS_CHECK_COUNT)
            if count > 0:
                break

        # Extract results
        return self._driver.execute_script(_JS_EXTRACT_RESULTS)

    def _parse_row(self, raw: dict) -> dict | None:
        """Parse a single BrowserView record into a clean dict.

        In BrowserView's hitlist, party_name is the grantor (seller) and
        cross_party_name is the grantee (buyer).
        """
        grantor = _clean_text(raw.get('party_name', ''))
        grantee = _clean_text(raw.get('cross_party_name', ''))

        rec_date = raw.get('rec_date', '')
        if rec_date:
            rec_date = _format_date(rec_date)

        legal = _clean_text(raw.get('legal_1', ''))
        legal_2 = _clean_text(raw.get('legal_2', ''))
        legal_3 = _clean_text(raw.get('legal_3', ''))
        if legal_2:
            legal = f'{legal}; {legal_2}' if legal else legal_2
        if legal_3:
            legal = f'{legal}; {legal_3}' if legal else legal_3

        consideration = _format_money(raw.get('consid_1'))

        parsed = {
            'instrument': _clean_text(raw.get('file_num', '')),
            'grantor': grantor,
            'grantee': grantee,
            'doc_type': _clean_text(raw.get('doc_type', '')),
            'record_date': rec_date,
            'legal': legal,
            'book': _clean_text(raw.get('book', '')),
            'page': _clean_text(raw.get('page', '')),
            'book_type': 'O',
            'consideration': consideration,
        }
        return parsed if any(v for k, v in parsed.items()) else None

    def _ensure_connected(self) -> None:
        if not self._connected:
            self.connect()
