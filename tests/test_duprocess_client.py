import json
import unittest
from unittest.mock import MagicMock, patch

from county_scrapers.duprocess_client import (
    DuProcessSession,
    _build_criteria,
    _clean_party,
    _compose_legal,
    _convert_date,
    BOOK_TYPE_DEED,
    BOOK_TYPE_DEED_OF_TRUST,
)


class ConvertDateTests(unittest.TestCase):
    def test_duprocess_datetime(self):
        self.assertEqual(_convert_date('3/2/2026 7:46:19 AM'), '03/02/2026')

    def test_date_only(self):
        self.assertEqual(_convert_date('3/15/2026'), '03/15/2026')

    def test_empty(self):
        self.assertEqual(_convert_date(''), '')

    def test_already_padded(self):
        self.assertEqual(_convert_date('12/01/2025'), '12/01/2025')


class CleanPartyTests(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(_clean_party('SMITH JOHN'), 'SMITH JOHN')

    def test_extra_whitespace(self):
        self.assertEqual(_clean_party('SMITH   JOHN'), 'SMITH JOHN')

    def test_empty(self):
        self.assertEqual(_clean_party(''), '')


class BuildCriteriaTests(unittest.TestCase):
    def test_deed_criteria(self):
        result = json.loads(_build_criteria('03/01/2026', '03/31/2026',
                                            book_type_id='71'))
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['file_date_start'], '03/01/2026')
        self.assertEqual(result[0]['file_date_end'], '03/31/2026')
        self.assertEqual(result[0]['inst_book_type_id'], '71')

    def test_empty_book_type(self):
        result = json.loads(_build_criteria('01/01/2026', '01/31/2026'))
        self.assertEqual(result[0]['inst_book_type_id'], '')


class ComposeLegalTests(unittest.TestCase):
    def test_platted_lot(self):
        raw = {'subdivision_name': 'WALNUT RIDGE', 'lot_from': '3',
               'block': '', 'legal_section': '', 'legal_township': '',
               'legal_range': '', 'legal_remarks': ''}
        self.assertEqual(_compose_legal(raw), 'LOT 3 WALNUT RIDGE')

    def test_platted_lot_with_block(self):
        raw = {'subdivision_name': 'HILLCREST', 'lot_from': '81',
               'block': 'A', 'legal_section': '', 'legal_township': '',
               'legal_range': '', 'legal_remarks': ''}
        self.assertEqual(_compose_legal(raw), 'LOT 81 BLK A HILLCREST')

    def test_plss(self):
        raw = {'subdivision_name': '', 'lot_from': '', 'block': '',
               'legal_section': '22', 'legal_township': '9N',
               'legal_range': '4E', 'legal_remarks': ''}
        self.assertEqual(_compose_legal(raw), 'SEC 22 TWP 9N RNG 4E')

    def test_plss_with_remarks(self):
        raw = {'subdivision_name': '', 'lot_from': '', 'block': '',
               'legal_section': '9', 'legal_township': '9N',
               'legal_range': '4E', 'legal_remarks': 'NW/4 OF SE/4'}
        self.assertEqual(_compose_legal(raw), 'SEC 9 TWP 9N RNG 4E NW/4 OF SE/4')

    def test_empty(self):
        raw = {'subdivision_name': '', 'lot_from': '', 'block': '',
               'legal_section': '', 'legal_township': '', 'legal_range': '',
               'legal_remarks': ''}
        self.assertEqual(_compose_legal(raw), '')

    def test_remarks_only(self):
        raw = {'subdivision_name': '', 'lot_from': '', 'block': '',
               'legal_section': '', 'legal_township': '', 'legal_range': '',
               'legal_remarks': 'MISC LEGAL TEXT'}
        self.assertEqual(_compose_legal(raw), 'MISC LEGAL TEXT')

    def test_subdivision_only_no_lot(self):
        raw = {'subdivision_name': 'KNOX', 'lot_from': '', 'block': '',
               'legal_section': '', 'legal_township': '', 'legal_range': '',
               'legal_remarks': 'KNOX'}
        self.assertEqual(_compose_legal(raw), 'KNOX')


class DuProcessParseRowTests(unittest.TestCase):
    def test_parse_row_basic(self):
        session = DuProcessSession('http://example.com')
        raw = {
            'gin': '1747870',
            'from_party': 'SOUTHERN CUSTOM HOMES LLC',
            'to_party': 'HANSEN JEFFREY THOMAS ET AL',
            'instrument_type': 'DEED - [DEED 01W]',
            'file_date': '3/2/2026 7:46:19 AM',
            'legal_remarks': '',
            'book_reel': '4651',
            'page': '941',
            'book_description': 'DEED',
            'num_pages': '3',
            'inst_num': '1046626',
            'subdivision_name': 'WALNUT RIDGE',
            'lot_from': '3',
            'block': '',
        }
        result = session._parse_row(raw)

        self.assertEqual(result['instrument'], '1046626')
        self.assertEqual(result['grantor'], 'SOUTHERN CUSTOM HOMES LLC')
        self.assertEqual(result['grantee'], 'HANSEN JEFFREY THOMAS ET AL')
        self.assertEqual(result['doc_type'], 'DEED - [DEED 01W]')
        self.assertEqual(result['record_date'], '03/02/2026')
        self.assertEqual(result['legal'], 'LOT 3 WALNUT RIDGE')  # composed from structured fields
        self.assertEqual(result['book'], '4651')
        self.assertEqual(result['page'], '941')
        self.assertEqual(result['book_type'], 'DEED')
        self.assertEqual(result['page_count'], '3')
        self.assertEqual(result['subdivision'], 'WALNUT RIDGE')
        self.assertEqual(result['lot'], '3')
        self.assertEqual(result['gin'], '1747870')
        session.close()

    def test_parse_row_empty_returns_none(self):
        session = DuProcessSession('http://example.com')
        raw = {
            'gin': '', 'from_party': '', 'to_party': '',
            'instrument_type': '', 'file_date': '', 'legal_remarks': '',
            'book_reel': '', 'page': '', 'book_description': '',
            'num_pages': '', 'inst_num': '', 'subdivision_name': '',
            'lot_from': '', 'block': '',
        }
        result = session._parse_row(raw)
        self.assertIsNone(result)
        session.close()


class ResolveBookTypeTests(unittest.TestCase):
    def test_deed_fallback(self):
        """Without auto-detect, falls back to hardcoded constants."""
        session = DuProcessSession('http://example.com', search_type='deed')
        self.assertEqual(session._resolve_book_type(), BOOK_TYPE_DEED)
        session.close()

    def test_mortgage_fallback(self):
        session = DuProcessSession('http://example.com', search_type='mortgage')
        self.assertEqual(session._resolve_book_type(), BOOK_TYPE_DEED_OF_TRUST)
        session.close()

    def test_deed_of_trust_fallback(self):
        session = DuProcessSession('http://example.com', search_type='deed_of_trust')
        self.assertEqual(session._resolve_book_type(), BOOK_TYPE_DEED_OF_TRUST)
        session.close()

    def test_all(self):
        session = DuProcessSession('http://example.com', search_type='all')
        self.assertEqual(session._resolve_book_type(), '')
        session.close()

    def test_auto_detected_deed(self):
        """When book types are auto-detected, use county-specific IDs."""
        session = DuProcessSession('http://example.com', search_type='deed')
        session._book_types = {'deed': '1', 'deed of trust': '21'}
        self.assertEqual(session._resolve_book_type(), '1')
        session.close()

    def test_auto_detected_mortgage(self):
        session = DuProcessSession('http://example.com', search_type='mortgage')
        session._book_types = {'deed': '1', 'deed of trust': '21'}
        self.assertEqual(session._resolve_book_type(), '21')
        session.close()

    def test_auto_detected_deed_book_label(self):
        """Harrison uses 'Deed Book' instead of 'Deed'."""
        session = DuProcessSession('http://example.com', search_type='deed')
        session._book_types = {'deed book': '1', 'trust book': '2'}
        self.assertEqual(session._resolve_book_type(), '1')
        session.close()

    def test_auto_detected_trust_book_label(self):
        """Harrison uses 'Trust Book' instead of 'Deed of Trust'."""
        session = DuProcessSession('http://example.com', search_type='mortgage')
        session._book_types = {'deed book': '1', 'trust book': '2'}
        self.assertEqual(session._resolve_book_type(), '2')
        session.close()


class DuProcessConnectTests(unittest.TestCase):
    @patch('county_scrapers.duprocess_client.requests.Session')
    def test_connect_fetches_book_types(self, MockSessionClass):
        mock_session = MagicMock()
        MockSessionClass.return_value = mock_session

        home_resp = MagicMock()
        home_resp.raise_for_status = MagicMock()

        lookup_resp = MagicMock()
        lookup_resp.json.return_value = {'Deed': '1', 'Deed of Trust': '21'}
        lookup_resp.raise_for_status = MagicMock()

        mock_session.get.side_effect = [home_resp, lookup_resp]

        session = DuProcessSession('http://example.com')
        session._session = mock_session
        session.connect()

        self.assertTrue(session._connected)
        self.assertEqual(session._book_types, {'deed': '1', 'deed of trust': '21'})
        # Verify it called both home page and BookTypeLookup
        self.assertEqual(mock_session.get.call_count, 2)
        session.close()

    @patch('county_scrapers.duprocess_client.requests.Session')
    def test_connect_survives_lookup_failure(self, MockSessionClass):
        mock_session = MagicMock()
        MockSessionClass.return_value = mock_session

        home_resp = MagicMock()
        home_resp.raise_for_status = MagicMock()

        lookup_resp = MagicMock()
        lookup_resp.raise_for_status.side_effect = Exception('lookup failed')

        mock_session.get.side_effect = [home_resp, lookup_resp]

        session = DuProcessSession('http://example.com')
        session._session = mock_session
        session.connect()

        # Should still connect even if lookup fails
        self.assertTrue(session._connected)
        self.assertEqual(session._book_types, {})
        session.close()


class DuProcessSearchTests(unittest.TestCase):
    @patch('county_scrapers.duprocess_client.requests.Session')
    def test_search_returns_parsed_rows(self, MockSessionClass):
        mock_session = MagicMock()
        MockSessionClass.return_value = mock_session

        # Mock CriteriaSearchCount response (double-encoded JSON)
        count_resp = MagicMock()
        count_resp.json.return_value = '{"Count":2, "Max": 2000}'
        count_resp.raise_for_status = MagicMock()

        # Mock CriteriaSearch response (flat JSON array)
        search_data = [
            {
                'gin': '100', 'from_party': 'GRANTOR A', 'to_party': 'GRANTEE A',
                'instrument_type': 'DEED', 'file_date': '3/1/2026 8:00:00 AM',
                'legal_remarks': '', 'book_reel': '4650', 'page': '100',
                'book_description': 'DEED', 'num_pages': '2', 'inst_num': '1000',
                'subdivision_name': 'TEST SUB', 'lot_from': '1', 'block': '',
                'legal_section': '', 'legal_township': '', 'legal_range': '',
            },
            {
                'gin': '101', 'from_party': 'GRANTOR B', 'to_party': 'GRANTEE B',
                'instrument_type': 'DEED', 'file_date': '3/2/2026 9:00:00 AM',
                'legal_remarks': '', 'book_reel': '4650', 'page': '105',
                'book_description': 'DEED', 'num_pages': '1', 'inst_num': '1001',
                'subdivision_name': 'TEST SUB', 'lot_from': '2', 'block': 'A',
                'legal_section': '', 'legal_township': '', 'legal_range': '',
            },
        ]
        search_resp = MagicMock()
        search_resp.json.return_value = search_data
        search_resp.raise_for_status = MagicMock()

        mock_session.get.side_effect = [count_resp, search_resp]

        session = DuProcessSession(
            'http://example.com', request_delay=0)
        session._connected = True
        session._book_types = {'deed': '71'}
        session._session = mock_session

        rows = session.search_by_date_range('03/01/2026', '03/31/2026')
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]['grantor'], 'GRANTOR A')
        self.assertEqual(rows[0]['record_date'], '03/01/2026')
        self.assertEqual(rows[0]['subdivision'], 'TEST SUB')
        self.assertEqual(rows[1]['page'], '105')
        self.assertEqual(rows[1]['block'], 'A')
        session.close()

    @patch('county_scrapers.duprocess_client.requests.Session')
    def test_search_zero_count_returns_empty(self, MockSessionClass):
        mock_session = MagicMock()
        MockSessionClass.return_value = mock_session

        count_resp = MagicMock()
        count_resp.json.return_value = '{"Count":0, "Max": 2000}'
        count_resp.raise_for_status = MagicMock()

        mock_session.get.side_effect = [count_resp]

        session = DuProcessSession(
            'http://example.com', request_delay=0)
        session._connected = True
        session._book_types = {'deed': '71'}
        session._session = mock_session

        rows = session.search_by_date_range('03/01/2026', '03/31/2026')
        self.assertEqual(rows, [])
        session.close()


if __name__ == '__main__':
    unittest.main()
