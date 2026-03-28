import unittest
from decimal import Decimal

from bay_price_extract import build_target_book_page, parse_bay_detail_html, parse_currency


class BayPriceExtractTests(unittest.TestCase):
    def test_build_target_book_page(self):
        locator = {'book': '4763', 'page': '0880'}
        self.assertEqual(build_target_book_page(locator), '4763/0880')

    def test_parse_currency_handles_dollar_text(self):
        self.assertEqual(parse_currency('$313,894.00'), Decimal('313894.00'))
        self.assertIsNone(parse_currency(''))
        self.assertIsNone(parse_currency(None))

    def test_parse_bay_detail_html_extracts_key_fields(self):
        html = """
        <table>
            <tr>
                <td class="boldTD"><label> Instrument #</label></td>
                <td>2024000975<br></td>
            </tr>
            <tr>
                <td class="boldTD"><label> Book/Page</label></td>
                <td>OR 4763 / 880<br></td>
            </tr>
            <tr>
                <td class="boldTD"><label> Record Date</label></td>
                <td>01/05/2024 03:28:08 PM<br></td>
            </tr>
            <tr>
                <td class="boldTD"><label> Book Type</label></td>
                <td>OR<br></td>
            </tr>
            <tr>
                <td class="boldTD"><label> Consideration</label></td>
                <td>$313,894.00<br></td>
            </tr>
        </table>
        """

        parsed = parse_bay_detail_html(html)

        self.assertEqual(parsed['instrument_number'], '2024000975')
        self.assertEqual(parsed['book_page'], 'OR 4763 / 880')
        self.assertEqual(parsed['record_date'], '01/05/2024 03:28:08 PM')
        self.assertEqual(parsed['book_type'], 'OR')
        self.assertEqual(parsed['consideration_raw'], '$313,894.00')


if __name__ == '__main__':
    unittest.main()
