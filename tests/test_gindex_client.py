import unittest
from unittest.mock import MagicMock, patch

from county_scrapers.gindex_client import GIndexSession, _clean_text, _parse_date


class CleanTextTests(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(_clean_text('SMITH JOHN'), 'SMITH JOHN')

    def test_html_tags(self):
        self.assertEqual(
            _clean_text('<a class="link">SMITH JOHN</a>'),
            'SMITH JOHN',
        )

    def test_nbsp(self):
        self.assertEqual(
            _clean_text('A&nbsp;B&nbsp;C'),
            'A B C',
        )

    def test_empty(self):
        self.assertEqual(_clean_text(''), '')


class ParseDateTests(unittest.TestCase):
    def test_normal(self):
        self.assertEqual(_parse_date('03-15-2026'), '03/15/2026')

    def test_empty(self):
        self.assertEqual(_parse_date(''), '')


class GIndexParseRowTests(unittest.TestCase):
    def test_parse_row_basic(self):
        session = GIndexSession('https://example.com')
        row_html = (
            '<TD class="normaltxtleft">'
            '<a href="GINDEX_query.asp?sn0=SMITH%20JOHN">SMITH JOHN                    </a>\n'
            '&nbsp;&nbsp;&nbsp;&nbsp;DOE JANE'
            '</TD>\n'
            '<TD class="normaltxtleft">WD        \n\n7302-7543</TD>\n'
            '<TD class="normaltxtleft">04-04-2024\n\n\t\n&nbsp;</TD>'
        )
        result = session._parse_row(row_html)

        self.assertEqual(result['grantor'], 'SMITH JOHN')
        self.assertEqual(result['grantee'], 'DOE JANE')
        self.assertEqual(result['doc_type'], 'WD')
        self.assertEqual(result['book'], '7302')
        self.assertEqual(result['page'], '7543')
        self.assertEqual(result['book_page'], '7302-7543')
        self.assertEqual(result['record_date'], '04/04/2024')
        self.assertFalse(result['has_remark'])
        session.close()

    def test_parse_row_with_remark(self):
        session = GIndexSession('https://example.com')
        row_html = (
            '<TD class="normaltxtleft">'
            'BETHANY GERALD W ET AL        \n'
            '&nbsp;&nbsp;&nbsp;&nbsp;BETHANY GERALD W ET AL'
            '</TD>\n'
            '<TD class="normaltxtleft">TR AGREE  \n\n0809-0495</TD>\n'
            '<TD class="normaltxtleft">03-02-2026\n\n\t\n\nRemark</TD>'
        )
        result = session._parse_row(row_html)

        self.assertEqual(result['grantor'], 'BETHANY GERALD W ET AL')
        self.assertEqual(result['grantee'], 'BETHANY GERALD W ET AL')
        self.assertEqual(result['doc_type'], 'TR AGREE')
        self.assertTrue(result['has_remark'])
        session.close()

    def test_parse_row_leading_zero_book(self):
        session = GIndexSession('https://example.com')
        row_html = (
            '<TD>SELLER\n&nbsp;&nbsp;&nbsp;&nbsp;BUYER</TD>\n'
            '<TD>DEED\n\n0809-0424</TD>\n'
            '<TD>01-15-2026</TD>'
        )
        result = session._parse_row(row_html)
        self.assertEqual(result['book'], '809')
        self.assertEqual(result['page'], '424')
        session.close()

    def test_parse_row_empty_returns_none(self):
        session = GIndexSession('https://example.com')
        row_html = '<TD></TD><TD></TD><TD></TD>'
        result = session._parse_row(row_html)
        self.assertIsNone(result)
        session.close()


class GIndexConnectTests(unittest.TestCase):
    @patch('county_scrapers.gindex_client.requests.Session')
    def test_connect_gets_search_form(self, MockSessionClass):
        mock_session = MagicMock()
        MockSessionClass.return_value = mock_session

        resp = MagicMock()
        resp.raise_for_status = MagicMock()
        mock_session.get.return_value = resp

        session = GIndexSession('https://example.com')
        session._session = mock_session
        session.connect()

        mock_session.get.assert_called_once_with(
            'https://example.com/gindex_query.asp', timeout=30)
        self.assertTrue(session._connected)
        session.close()


class GIndexDeduplicationTests(unittest.TestCase):
    @patch('county_scrapers.gindex_client.requests.Session')
    def test_deduplicates_results(self, MockSessionClass):
        mock_session = MagicMock()
        MockSessionClass.return_value = mock_session

        # Simulate page 1 with duplicate rows
        page_html = '''
        <h3>Page 1 of 1</h3>
        <TR VALIGN=TOP>
        <TD>SMITH JOHN\n&nbsp;&nbsp;&nbsp;&nbsp;DOE JANE</TD>
        <TD>WD\n\n1000-0100</TD>
        <TD>01-01-2026</TD>
        </TR>
        <TR VALIGN=TOP>
        <TD>SMITH JOHN\n&nbsp;&nbsp;&nbsp;&nbsp;DOE JANE</TD>
        <TD>WD\n\n1000-0100</TD>
        <TD>01-01-2026</TD>
        </TR>
        <TR VALIGN=TOP>
        <TD>OTHER PERSON\n&nbsp;&nbsp;&nbsp;&nbsp;BUYER TWO</TD>
        <TD>QCD\n\n1000-0200</TD>
        <TD>01-01-2026</TD>
        </TR>
        '''
        resp = MagicMock()
        resp.text = page_html
        resp.raise_for_status = MagicMock()
        mock_session.get.return_value = resp

        session = GIndexSession('https://example.com', request_delay=0)
        session._connected = True
        session._session = mock_session

        rows = session.search_by_date_range('01/01/2026', '01/01/2026')
        self.assertEqual(len(rows), 2)  # deduped from 3 to 2
        session.close()


if __name__ == '__main__':
    unittest.main()
