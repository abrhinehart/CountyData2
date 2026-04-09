import unittest
from unittest.mock import MagicMock, patch, PropertyMock

from county_scrapers.countygov_client import (
    AuthenticationError,
    CountyGovSession,
    _clean_name,
    _convert_date,
)


class CountyGovParseRowTests(unittest.TestCase):
    def test_parse_row_basic(self):
        session = CountyGovSession(
            'https://example.com', email='a@b.com', password='x')
        raw = {
            'iID': 12345,
            'Name1': 'SMITH, JOHN',
            'Name2': 'DOE, JANE',
            'itNAME': 'WARRANTY DEED',
            'iRECORDED': '2025-03-15T00:00:00',
            'iDESC': 'LOT 5 BLK 2',
            'bkNAME': 'OR',
            'iNUMBER': '100',
            'bktNAME': 'Official Records',
            'iPAGES': '3',
            'itID': 7,
        }
        result = session._parse_row(raw)

        self.assertEqual(result['instrument'], '12345')
        self.assertEqual(result['grantor'], 'SMITH, JOHN')
        self.assertEqual(result['grantee'], 'DOE, JANE')
        self.assertEqual(result['doc_type'], 'WARRANTY DEED')
        self.assertEqual(result['record_date'], '03/15/2025')
        self.assertEqual(result['legal'], 'LOT 5 BLK 2')
        self.assertEqual(result['book'], 'OR')
        self.assertEqual(result['page'], '100')
        self.assertEqual(result['book_type'], 'Official Records')
        self.assertEqual(result['page_count'], '3')
        self.assertEqual(result['instrument_type_id'], '7')
        session.close()

    def test_parse_row_br_replacement(self):
        session = CountyGovSession(
            'https://example.com', email='a@b.com', password='x')
        raw = {
            'iID': 1,
            'Name1': 'SMITH, JOHN<br/>DOE, JANE<br>JONES, BOB',
            'Name2': 'BUYER ONE<BR/>BUYER TWO',
            'itNAME': 'DEED',
            'iRECORDED': '2025-01-01',
            'iDESC': '',
            'bkNAME': '',
            'iNUMBER': '',
            'bktNAME': '',
            'iPAGES': '',
            'itID': '',
        }
        result = session._parse_row(raw)

        self.assertEqual(result['grantor'], 'SMITH, JOHN; DOE, JANE; JONES, BOB')
        self.assertEqual(result['grantee'], 'BUYER ONE; BUYER TWO')
        session.close()


class CleanNameTests(unittest.TestCase):
    def test_clean_name_basic(self):
        self.assertEqual(_clean_name('SMITH, JOHN'), 'SMITH, JOHN')

    def test_clean_name_br_tags(self):
        self.assertEqual(
            _clean_name('AAA<br/>BBB<br>CCC'),
            'AAA; BBB; CCC',
        )

    def test_clean_name_empty(self):
        self.assertEqual(_clean_name(''), '')

    def test_clean_name_html_tags_stripped(self):
        self.assertEqual(
            _clean_name('<b>SMITH</b>, JOHN'),
            'SMITH, JOHN',
        )

    def test_clean_name_whitespace_normalized(self):
        self.assertEqual(
            _clean_name('SMITH,   JOHN'),
            'SMITH, JOHN',
        )


class SearchPaginationTests(unittest.TestCase):
    @patch('county_scrapers.countygov_client.requests.Session')
    def test_search_pagination(self, MockSessionClass):
        mock_session = MagicMock()
        MockSessionClass.return_value = mock_session

        # Build 500 rows for page 1, 100 rows for page 2
        page1_data = [
            {'iID': i, 'Name1': f'GRANTOR {i}', 'Name2': f'GRANTEE {i}',
             'itNAME': 'DEED', 'iRECORDED': '2025-01-01', 'iDESC': '',
             'bkNAME': '', 'iNUMBER': '', 'bktNAME': '', 'iPAGES': '', 'itID': ''}
            for i in range(500)
        ]
        page2_data = [
            {'iID': i, 'Name1': f'GRANTOR {i}', 'Name2': f'GRANTEE {i}',
             'itNAME': 'DEED', 'iRECORDED': '2025-01-01', 'iDESC': '',
             'bkNAME': '', 'iNUMBER': '', 'bktNAME': '', 'iPAGES': '', 'itID': ''}
            for i in range(500, 600)
        ]

        # Mock the search type page (GET /Search/SearchType)
        search_type_resp = MagicMock()
        search_type_resp.text = '<div data-searchqueryid="abc123"></div>'
        search_type_resp.raise_for_status = MagicMock()

        # Mock the search results page (GET /Search/SearchResults)
        search_results_resp = MagicMock()
        search_results_resp.text = '''
            <script>query: "somequery", qid: "abc123"</script>
        '''
        search_results_resp.raise_for_status = MagicMock()

        # Mock the grid POST responses
        grid_resp_1 = MagicMock()
        grid_resp_1.json.return_value = {'Data': page1_data, 'Total': 600}
        grid_resp_1.raise_for_status = MagicMock()

        grid_resp_2 = MagicMock()
        grid_resp_2.json.return_value = {'Data': page2_data, 'Total': 600}
        grid_resp_2.raise_for_status = MagicMock()

        # Set up the GET/POST call sequences
        mock_session.get.side_effect = [search_type_resp, search_results_resp]
        mock_session.post.side_effect = [grid_resp_1, grid_resp_2]

        session = CountyGovSession(
            'https://example.com', email='a@b.com', password='x',
            page_size=500, request_delay=0)
        session._connected = True
        session._session = mock_session

        rows = session.search_by_date_range('01/01/2025', '01/31/2025')
        self.assertEqual(len(rows), 600)
        session.close()


class SearchSinglePageTests(unittest.TestCase):
    @patch('county_scrapers.countygov_client.requests.Session')
    def test_search_single_page(self, MockSessionClass):
        mock_session = MagicMock()
        MockSessionClass.return_value = mock_session

        page_data = [
            {'iID': 1, 'Name1': 'GRANTOR A', 'Name2': 'GRANTEE A',
             'itNAME': 'DEED', 'iRECORDED': '2025-02-10', 'iDESC': 'LOT 1',
             'bkNAME': 'OR', 'iNUMBER': '50', 'bktNAME': 'Official Records',
             'iPAGES': '2', 'itID': '5'},
            {'iID': 2, 'Name1': 'GRANTOR B', 'Name2': 'GRANTEE B',
             'itNAME': 'DEED', 'iRECORDED': '2025-02-11', 'iDESC': 'LOT 2',
             'bkNAME': 'OR', 'iNUMBER': '51', 'bktNAME': 'Official Records',
             'iPAGES': '1', 'itID': '5'},
        ]

        # Mock GET responses: SearchType, SearchResults
        search_type_resp = MagicMock()
        search_type_resp.text = '<input name="SearchQueryId" value="q1" />'
        search_type_resp.raise_for_status = MagicMock()

        search_results_resp = MagicMock()
        search_results_resp.text = '<script>query: "myquery", qid: "q1"</script>'
        search_results_resp.raise_for_status = MagicMock()

        # Mock POST response: SearchResultsGrid (single page)
        grid_resp = MagicMock()
        grid_resp.json.return_value = {'Data': page_data, 'Total': 2}
        grid_resp.raise_for_status = MagicMock()

        mock_session.get.side_effect = [search_type_resp, search_results_resp]
        mock_session.post.side_effect = [grid_resp]

        session = CountyGovSession(
            'https://example.com', email='a@b.com', password='x',
            request_delay=0)
        session._connected = True
        session._session = mock_session

        rows = session.search_by_date_range('02/01/2025', '02/28/2025')
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]['grantor'], 'GRANTOR A')
        self.assertEqual(rows[0]['record_date'], '02/10/2025')
        self.assertEqual(rows[1]['page'], '51')
        session.close()


class AuthErrorTests(unittest.TestCase):
    @patch('county_scrapers.countygov_client.requests.Session')
    def test_auth_error_on_missing_csrf(self, MockSessionClass):
        mock_session = MagicMock()
        MockSessionClass.return_value = mock_session

        # Step 1: redirect from base URL
        redirect_resp = MagicMock()
        redirect_resp.status_code = 302
        redirect_resp.headers = {
            'Location': (
                'https://tenant.b2clogin.com/tenant/B2C_1_signin'
                '/oauth2/v2.0/authorize?client_id=abc&redirect_uri='
                'https://example.com/signin-oidc&p=B2C_1_signin'
            ),
        }

        # Step 2: B2C page WITHOUT csrf
        b2c_resp = MagicMock()
        b2c_resp.text = '<html><body>No settings here</body></html>'
        b2c_resp.raise_for_status = MagicMock()

        mock_session.get.side_effect = [redirect_resp, b2c_resp]

        session = CountyGovSession(
            'https://example.com', email='a@b.com', password='x',
            request_delay=0)
        session._session = mock_session

        with self.assertRaises(AuthenticationError) as ctx:
            session.connect()
        self.assertIn('csrf', str(ctx.exception).lower())
        session.close()


class ConvertDateTests(unittest.TestCase):
    def test_convert_iso_date(self):
        self.assertEqual(_convert_date('2025-03-15'), '03/15/2025')

    def test_convert_iso_datetime(self):
        self.assertEqual(_convert_date('2025-03-15T00:00:00'), '03/15/2025')

    def test_convert_empty(self):
        self.assertEqual(_convert_date(''), '')


if __name__ == '__main__':
    unittest.main()
