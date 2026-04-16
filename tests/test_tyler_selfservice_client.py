"""Tests for county_scrapers.tyler_selfservice_client."""

import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from county_scrapers.tyler_selfservice_client import (
    TylerSelfServiceSession,
    _extract_column_values,
    _extract_h1,
    _extract_parcel,
    _format_date,
    _normalize_date,
    _normalize_legal,
)


_FIXTURE_PATH = (
    Path(__file__).resolve().parent
    / 'fixtures' / 'tyler_selfservice_results_sample.html'
)


def _load_fixture() -> str:
    return _FIXTURE_PATH.read_text(encoding='utf-8')


class FactoryIntegrity(unittest.TestCase):
    def test_constructor_defaults(self):
        session = TylerSelfServiceSession(
            'https://okaloosacountyfl-web.tylerhost.net/web')
        self.assertEqual(
            session.base_url,
            'https://okaloosacountyfl-web.tylerhost.net/web')
        self.assertEqual(session.search_id, 'DOCSEARCH138S1')
        self.assertEqual(session.doc_types, '')
        self.assertEqual(session.page_size, 100)
        self.assertEqual(session.request_delay, 1.0)
        self.assertFalse(session._connected)
        session.close()

    def test_constructor_trims_trailing_slash(self):
        session = TylerSelfServiceSession('https://example.com/web/')
        self.assertEqual(session.base_url, 'https://example.com/web')
        session.close()

    def test_constructor_override_args(self):
        session = TylerSelfServiceSession(
            'https://example.com/web',
            search_id='DOCSEARCH999S1',
            doc_types='DEED',
            page_size=50,
            request_delay=0,
        )
        self.assertEqual(session.search_id, 'DOCSEARCH999S1')
        self.assertEqual(session.doc_types, 'DEED')
        self.assertEqual(session.page_size, 50)
        self.assertEqual(session.request_delay, 0)
        session.close()


class NormalizationTests(unittest.TestCase):
    def test_normalize_date_strips_time(self):
        self.assertEqual(
            _normalize_date('04/02/2026 04:52 PM'), '04/02/2026')

    def test_normalize_date_no_time(self):
        self.assertEqual(_normalize_date('04/02/2026'), '04/02/2026')

    def test_normalize_date_am_suffix(self):
        self.assertEqual(
            _normalize_date('04/02/2026 11:15 AM'), '04/02/2026')

    def test_normalize_date_empty(self):
        self.assertEqual(_normalize_date(''), '')

    def test_extract_h1_standard(self):
        raw = '\n\n3808515\n\n  &nbsp;&#149;&nbsp;\n  MORTGAGE\n'
        self.assertEqual(_extract_h1(raw), ('3808515', 'MORTGAGE'))

    def test_extract_h1_empty(self):
        self.assertEqual(_extract_h1(''), ('', ''))

    def test_extract_h1_malformed(self):
        # No separator -> treated as unparseable
        self.assertEqual(_extract_h1('just some text'), ('', ''))

    def test_extract_column_values_multi(self):
        html = (
            '<ul>'
            '<li>Grantor/Party 1 (2)</li>'
            '<li class="x"><b>DR HORTON INC</b></li>'
            '<li class="y"><b>D R HORTON INC</b></li>'
            '</ul>'
        )
        self.assertEqual(
            _extract_column_values(html),
            ['DR HORTON INC', 'D R HORTON INC'])

    def test_normalize_legal_single(self):
        self.assertEqual(
            _normalize_legal(['GARDEN VILLA Lot: 10']),
            'GARDEN VILLA Lot: 10')

    def test_normalize_legal_multi(self):
        self.assertEqual(
            _normalize_legal(['Lot 10', 'Parcel: 12345']),
            'Lot 10\nParcel: 12345')

    def test_normalize_legal_empty(self):
        self.assertEqual(_normalize_legal([]), '')

    def test_extract_parcel_found(self):
        values = ['GARDEN VILLA Lot: 10 Block: A',
                  'Parcel: 05-3N-23-1650-000A-0100']
        self.assertEqual(
            _extract_parcel(values), '05-3N-23-1650-000A-0100')

    def test_extract_parcel_absent(self):
        self.assertEqual(_extract_parcel(['Lot 10 Block A']), '')

    def test_format_date_zero_padded(self):
        self.assertEqual(_format_date('04/01/2026'), '4/1/2026')

    def test_format_date_unpadded(self):
        self.assertEqual(_format_date('4/1/2026'), '4/1/2026')


class ParseRowTests(unittest.TestCase):
    def setUp(self):
        self.session = TylerSelfServiceSession(
            'https://example.com/web', request_delay=0)
        self.fixture = _load_fixture()
        self.rows = self.session._parse_results_page(self.fixture)

    def tearDown(self):
        self.session.close()

    def test_parses_all_three_rows(self):
        self.assertEqual(len(self.rows), 3)

    def test_basic_single_party_row(self):
        # Row 0 is a mortgage with single grantor
        row = self.rows[0]
        self.assertEqual(row['document_id'], 'DOC549S1614')
        self.assertEqual(row['instrument'], '3808515')
        self.assertEqual(row['doc_type'], 'MORTGAGE')
        self.assertEqual(row['record_date'], '04/02/2026')
        self.assertEqual(row['grantor'], 'LUCIO ERIANA UNIQUE')
        # multi-party grantee joined with '; '
        self.assertEqual(
            row['grantee'],
            'DHI MORTGAGE COMPANY LTD; '
            'MORTGAGE ELECTRONIC REGISTRATION SYSTEMS INC')
        self.assertIn('GARDEN VILLA TOWNHOMES', row['legal'])
        self.assertIn('Parcel:', row['legal'])
        self.assertEqual(row['book'], '')
        self.assertEqual(row['consideration'], '')

    def test_multi_party_grantor(self):
        # Row 1 is the DEED with two grantors joined by '; '
        row = self.rows[1]
        self.assertEqual(row['doc_type'], 'DEED')
        self.assertEqual(row['grantor'], 'DR HORTON INC; D R HORTON INC')
        self.assertEqual(row['grantee'], 'LUCIO ERIANA UNIQUE')

    def test_parcel_extraction(self):
        # Row 1 legal carries a Parcel sub-line
        row = self.rows[1]
        self.assertEqual(
            row['parcel'], '05-3N-23-1650-000A-0100')

    def test_unparseable_returns_none(self):
        session = TylerSelfServiceSession(
            'https://example.com/web', request_delay=0)
        self.assertIsNone(session._parse_row(''))
        self.assertIsNone(session._parse_row('<div>junk</div>'))
        session.close()


class SearchFlowTests(unittest.TestCase):
    @patch('county_scrapers.tyler_selfservice_client.requests.Session')
    def test_full_flow_mocked(self, MockSessionClass):
        mock_session = MagicMock()
        mock_session.headers = {}
        MockSessionClass.return_value = mock_session

        # connect() -> GET /web
        get_root = MagicMock()
        get_root.raise_for_status = MagicMock()

        # POST /web/user/disclaimer
        disc_resp = MagicMock()
        disc_resp.raise_for_status = MagicMock()

        # GET /web/search/DOCSEARCH138S1
        form_resp = MagicMock()
        form_resp.raise_for_status = MagicMock()

        # POST /web/searchPost/DOCSEARCH138S1  -> JSON shell
        search_resp = MagicMock()
        search_resp.raise_for_status = MagicMock()
        search_resp.json.return_value = {
            'validationMessages': {},
            'totalPages': 2,
            'currentPage': 1,
        }

        # GET /web/searchResults -> fixture HTML, then 1-row-trimmed fixture
        full_fixture = _load_fixture()
        # Trimmed fixture: only first row
        trimmed = full_fixture.split('</li>', 1)[0] + '</li>'

        page1_resp = MagicMock()
        page1_resp.raise_for_status = MagicMock()
        page1_resp.text = full_fixture

        page2_resp = MagicMock()
        page2_resp.raise_for_status = MagicMock()
        page2_resp.text = trimmed

        # requests.Session.get gets called several times in order:
        # 1: connect root, 2: connect form, 3: page1, 4: page2
        mock_session.get.side_effect = [
            get_root, form_resp, page1_resp, page2_resp]
        mock_session.post.side_effect = [disc_resp, search_resp]

        session = TylerSelfServiceSession(
            'https://okaloosacountyfl-web.tylerhost.net/web',
            request_delay=0,
        )
        session.connect()
        rows = session.search_by_date_range('4/1/2026', '4/1/2026')

        # 3 rows on page 1 + 1 row on page 2 = 4 total
        self.assertEqual(len(rows), 4)
        self.assertEqual(rows[0]['instrument'], '3808515')
        self.assertEqual(rows[1]['doc_type'], 'DEED')
        self.assertEqual(rows[3]['document_id'], 'DOC549S1614')
        session.close()

    @patch('county_scrapers.tyler_selfservice_client.requests.Session')
    def test_search_without_connect_raises(self, MockSessionClass):
        mock_session = MagicMock()
        mock_session.headers = {}
        MockSessionClass.return_value = mock_session

        session = TylerSelfServiceSession(
            'https://example.com/web', request_delay=0)
        with self.assertRaises(RuntimeError):
            session.search_by_date_range('4/1/2026', '4/1/2026')
        session.close()


class AjaxHeaderRegressionTest(unittest.TestCase):
    """Guards the #1 gotcha: ajaxRequest: true MUST be sent on searchPost."""

    @patch('county_scrapers.tyler_selfservice_client.requests.Session')
    def test_ajax_request_header_is_set(self, MockSessionClass):
        mock_session = MagicMock()
        mock_session.headers = {}
        MockSessionClass.return_value = mock_session

        search_resp = MagicMock()
        search_resp.raise_for_status = MagicMock()
        search_resp.json.return_value = {
            'validationMessages': {}, 'totalPages': 0}

        mock_session.post.return_value = search_resp

        session = TylerSelfServiceSession(
            'https://example.com/web', request_delay=0)
        session._connected = True

        session.search_by_date_range('4/1/2026', '4/1/2026')

        # Find the searchPost call and assert the header is present.
        found = False
        for call in mock_session.post.call_args_list:
            args, kwargs = call
            url = args[0] if args else kwargs.get('url', '')
            if 'searchPost' in url:
                headers = kwargs.get('headers', {})
                self.assertEqual(headers.get('ajaxRequest'), 'true')
                found = True
        self.assertTrue(
            found, 'searchPost call was not made -- cannot verify header')
        session.close()


class ValidationMessagesTest(unittest.TestCase):
    @patch('county_scrapers.tyler_selfservice_client.requests.Session')
    def test_validation_messages_raises(self, MockSessionClass):
        mock_session = MagicMock()
        mock_session.headers = {}
        MockSessionClass.return_value = mock_session

        bad_resp = MagicMock()
        bad_resp.raise_for_status = MagicMock()
        bad_resp.json.return_value = {
            'validationMessages': {'field_X': 'bad'},
            'totalPages': 0,
        }
        mock_session.post.return_value = bad_resp

        session = TylerSelfServiceSession(
            'https://example.com/web', request_delay=0)
        session._connected = True

        with self.assertRaises(RuntimeError) as ctx:
            session.search_by_date_range('4/1/2026', '4/1/2026')
        self.assertIn('validation', str(ctx.exception).lower())
        session.close()


class FromCookiesTest(unittest.TestCase):
    def test_from_cookies_marks_connected(self):
        cookies = {'JSESSIONID': 'abc', 'disclaimerAccepted': 'true'}
        session = TylerSelfServiceSession.from_cookies(
            'https://example.com/web', cookies, request_delay=0)
        self.assertTrue(session._connected)
        self.assertEqual(session._session.cookies.get('JSESSIONID'), 'abc')
        session.close()


if __name__ == '__main__':
    unittest.main()
