import unittest
from unittest.mock import MagicMock, patch

from county_scrapers.acclaimweb_client import (
    AcclaimWebSession,
    _clean_name,
    _convert_date,
    _parse_book_page,
)


class CleanNameTests(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(_clean_name('SMITH,JOHN'), 'SMITH,JOHN')

    def test_br_tags(self):
        self.assertEqual(
            _clean_name('SMITH,JOHN<br>DOE,JANE<br/>JONES,BOB'),
            'SMITH,JOHN; DOE,JANE; JONES,BOB',
        )

    def test_empty(self):
        self.assertEqual(_clean_name(''), '')


class ConvertDateTests(unittest.TestCase):
    def test_dotnet_date(self):
        # /Date(1772460395000)/ = 3/1/2026
        result = _convert_date('/Date(1772460395000)/')
        self.assertTrue(result.startswith('0'))  # month starts with 0

    def test_empty(self):
        self.assertEqual(_convert_date(''), '')

    def test_no_match(self):
        self.assertEqual(_convert_date('not a date'), 'not a date')


class ParseBookPageTests(unittest.TestCase):
    def test_normal(self):
        self.assertEqual(_parse_book_page('1026  /  3364'), ('1026', '3364'))

    def test_tight(self):
        self.assertEqual(_parse_book_page('100/200'), ('100', '200'))

    def test_empty(self):
        self.assertEqual(_parse_book_page(''), ('', ''))


class AcclaimWebParseRowTests(unittest.TestCase):
    def test_parse_row_basic(self):
        session = AcclaimWebSession('https://example.com')
        raw = {
            'TransactionItemId': 1967796,
            'RecordDate': '/Date(1772460395000)/',
            'DocType': 'WAR',
            'BookType': 'W',
            'BookPage': '1026  /  3364',
            'NumericPage': 3364.0,
            'DirectName': 'SMITH,JOHN',
            'IndirectName': 'DOE,JANE',
            'DocLegalDescription': 'SOUTHAVEN WEST Sec O Lot 3068, Plat Book 5 Page 12',
            'TransactionId': 282651,
        }
        result = session._parse_row(raw)

        self.assertEqual(result['instrument'], '1967796')
        self.assertEqual(result['grantor'], 'SMITH,JOHN')
        self.assertEqual(result['grantee'], 'DOE,JANE')
        self.assertEqual(result['doc_type'], 'WAR')
        self.assertEqual(result['book'], '1026')
        self.assertEqual(result['page'], '3364')
        self.assertEqual(result['book_type'], 'W')
        self.assertIn('SOUTHAVEN WEST', result['legal'])
        session.close()

    def test_parse_row_multi_party(self):
        session = AcclaimWebSession('https://example.com')
        raw = {
            'TransactionItemId': 100,
            'RecordDate': '/Date(1772460395000)/',
            'DocType': 'WAR',
            'BookType': 'W',
            'BookPage': '1026  /  100',
            'DirectName': 'SELLER,A<br>SELLER,B',
            'IndirectName': 'BUYER,X',
            'DocLegalDescription': 'LOT 1',
            'TransactionId': 1,
        }
        result = session._parse_row(raw)
        self.assertEqual(result['grantor'], 'SELLER,A; SELLER,B')
        session.close()

    def test_parse_row_empty_returns_none(self):
        session = AcclaimWebSession('https://example.com')
        raw = {
            'TransactionItemId': '',
            'RecordDate': '',
            'DocType': '',
            'BookType': '',
            'BookPage': '',
            'DirectName': '',
            'IndirectName': '',
            'DocLegalDescription': '',
            'TransactionId': '',
        }
        result = session._parse_row(raw)
        self.assertIsNone(result)
        session.close()


class AcclaimWebSearchTests(unittest.TestCase):
    @patch('county_scrapers.acclaimweb_client.cf_requests.Session')
    def test_search_returns_parsed_rows(self, MockSessionClass):
        mock_session = MagicMock()
        MockSessionClass.return_value = mock_session

        # Mock search POST (just needs to succeed)
        search_resp = MagicMock()
        search_resp.raise_for_status = MagicMock()

        # Mock GridResults POST
        grid_data = {
            'data': [
                {
                    'TransactionItemId': 1, 'RecordDate': '/Date(1772460395000)/',
                    'DocType': 'WAR', 'BookType': 'W', 'BookPage': '100 / 200',
                    'DirectName': 'SELLER', 'IndirectName': 'BUYER',
                    'DocLegalDescription': 'LOT 1 TEST SUB', 'TransactionId': 1,
                },
                {
                    'TransactionItemId': 2, 'RecordDate': '/Date(1772460395000)/',
                    'DocType': 'QCL', 'BookType': 'W', 'BookPage': '100 / 201',
                    'DirectName': 'SELLER B', 'IndirectName': 'BUYER B',
                    'DocLegalDescription': 'LOT 2 TEST SUB', 'TransactionId': 2,
                },
            ],
            'total': 2,
        }
        grid_resp = MagicMock()
        grid_resp.json.return_value = grid_data
        grid_resp.raise_for_status = MagicMock()

        mock_session.post.side_effect = [search_resp, grid_resp]

        session = AcclaimWebSession('https://example.com', request_delay=0)
        session._connected = True
        session._session = mock_session

        rows = session.search_by_date_range('03/01/2026', '03/31/2026')
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]['grantor'], 'SELLER')
        self.assertEqual(rows[1]['doc_type'], 'QCL')
        session.close()


if __name__ == '__main__':
    unittest.main()
