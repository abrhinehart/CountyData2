import unittest

import psycopg2.extras

from processors.loader import _UPSERT_SQL, _prepare_db_row, _prepare_segment_rows


class LoaderTests(unittest.TestCase):
    def test_upsert_sql_includes_acres(self):
        self.assertIn('export_legal_desc, export_legal_raw, deed_locator, deed_legal_desc, deed_legal_parsed', _UPSERT_SQL)
        self.assertIn('lots, acres, acres_source, price', _UPSERT_SQL)
        self.assertIn('acres                   = EXCLUDED.acres', _UPSERT_SQL)
        self.assertIn('acres_source            = EXCLUDED.acres_source', _UPSERT_SQL)

    def test_prepare_db_row_wraps_parsed_data_for_json_storage(self):
        row = {
            'grantor': 'Seller Name',
            'deed_locator': {
                'book_type': 'OR',
                'book': '4643',
                'page': '317',
            },
            'parsed_data': {
                'grantor_parties': ['Seller Name'],
                'county_parse': {'lot_values': ['11,12']},
            },
            'deed_legal_parsed': {
                'legal_type': 'metes_bounds',
            },
        }

        prepared = _prepare_db_row(row)

        self.assertIsInstance(prepared['parsed_data'], psycopg2.extras.Json)
        self.assertIsInstance(prepared['deed_locator'], psycopg2.extras.Json)
        self.assertIsInstance(prepared['deed_legal_parsed'], psycopg2.extras.Json)
        self.assertEqual(prepared['parsed_data'].adapted, row['parsed_data'])
        self.assertEqual(prepared['deed_locator'].adapted, row['deed_locator'])
        self.assertEqual(prepared['deed_legal_parsed'].adapted, row['deed_legal_parsed'])
        self.assertEqual(row['parsed_data']['county_parse']['lot_values'], ['11,12'])

    def test_prepare_segment_rows_wraps_segment_data_for_json_storage(self):
        row = {
            'county': 'Hernando',
            'transaction_segments': [
                {
                    'segment_index': 0,
                    'county': 'Hernando',
                    'subdivision_lookup_text': 'ROYAL HIGHLANDS',
                    'raw_subdivision': 'ROYAL HIGHLANDS',
                    'subdivision': 'ROYAL HIGHLANDS',
                    'subdivision_id': 89,
                    'phase_raw': '2A',
                    'phase': '2A',
                    'inventory_category': 'scattered_legacy_lots',
                    'phase_confirmed': True,
                    'review_reasons': [],
                    'segment_data': {'details': {'line_index': 1}},
                },
            ],
        }

        segment_rows = _prepare_segment_rows(55, row)

        self.assertEqual(len(segment_rows), 1)
        segment_row = segment_rows[0]
        self.assertEqual(segment_row[0], 55)
        self.assertEqual(segment_row[1], 0)
        self.assertEqual(segment_row[2], 'Hernando')
        self.assertEqual(segment_row[6], 89)
        self.assertEqual(segment_row[9], 'scattered_legacy_lots')
        self.assertEqual(segment_row[10], True)
        self.assertEqual(segment_row[11], [])
        self.assertIsInstance(segment_row[12], psycopg2.extras.Json)
        self.assertEqual(segment_row[12].adapted, {'details': {'line_index': 1}})


if __name__ == '__main__':
    unittest.main()
