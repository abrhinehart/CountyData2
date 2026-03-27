import unittest

import psycopg2.extras

from processors.loader import _prepare_db_row


class LoaderTests(unittest.TestCase):
    def test_prepare_db_row_wraps_parsed_data_for_json_storage(self):
        row = {
            'grantor': 'Seller Name',
            'parsed_data': {
                'grantor_parties': ['Seller Name'],
                'county_parse': {'lot_values': ['11,12']},
            },
        }

        prepared = _prepare_db_row(row)

        self.assertIsInstance(prepared['parsed_data'], psycopg2.extras.Json)
        self.assertEqual(prepared['parsed_data'].adapted, row['parsed_data'])
        self.assertEqual(row['parsed_data']['county_parse']['lot_values'], ['11,12'])


if __name__ == '__main__':
    unittest.main()
