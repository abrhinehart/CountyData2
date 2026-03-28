import unittest

import pandas as pd

from deed_queue_export import (
    build_query,
    build_search_query,
    build_summary_frames,
    flatten_deed_row,
    recommend_search,
)


class DeedQueueExportTests(unittest.TestCase):
    def test_build_query_includes_filters_and_limit(self):
        sql, params = build_query('Hernando', 'Builder Purchase', 50)

        self.assertIn('price IS NULL', sql)
        self.assertIn('type = %s', sql)
        self.assertIn("REPLACE(UPPER(county), ' ', '') = REPLACE(UPPER(%s), ' ', '')", sql)
        self.assertTrue(sql.strip().endswith('LIMIT %s'))
        self.assertEqual(params, ['Builder Purchase', 'Hernando', 50])

    def test_recommend_search_prefers_instrument_before_book_page(self):
        locator = {
            'book_type': 'OR',
            'book': '4643',
            'page': '0317',
            'instrument_number': '2025083923',
        }

        self.assertEqual(recommend_search(locator), 'Instrument Number')
        self.assertEqual(build_search_query(locator), 'Instrument 2025083923')

    def test_flatten_deed_row_extracts_locator_fields(self):
        row = {
            'id': 5467,
            'county': 'Hernando',
            'date': pd.Timestamp('2025-04-11'),
            'grantor': 'Seller LLC',
            'grantee': 'Builder Homes LLC',
            'type': 'Builder Purchase',
            'instrument': 'WD',
            'subdivision': 'WATERFORD',
            'phase': '38',
            'lots': 1,
            'price': None,
            'source_file': 'raw data/Hernando/hernando_horton.xlsx',
            'deed_locator': {
                'book_type': 'OR',
                'book': '4643',
                'page': '0317',
                'instrument_number': '2025083923',
                'raw_fields': {
                    'Book Type': 'OR',
                    'Book': '4643',
                    'Page': '0317',
                    'Instrument #': '2025083923',
                },
            },
        }

        flattened = flatten_deed_row(row)

        self.assertEqual(flattened['ID'], 5467)
        self.assertEqual(flattened['Recommended Search'], 'Instrument Number')
        self.assertEqual(flattened['Search Query'], 'Instrument 2025083923')
        self.assertEqual(flattened['Book/Page'], '4643/0317')
        self.assertEqual(flattened['Instrument Number'], '2025083923')
        self.assertEqual(flattened['Doc Link Text'], '')

    def test_flatten_deed_row_keeps_non_url_doc_link_text(self):
        row = {
            'id': 14464,
            'county': 'Santa Rosa',
            'date': pd.Timestamp('2025-11-03'),
            'grantor': 'Seller LLC',
            'grantee': 'Builder LLC',
            'type': 'Builder Purchase',
            'instrument': 'WD',
            'subdivision': 'WOODLANDS',
            'phase': '1-C',
            'lots': 1,
            'price': None,
            'source_file': 'raw data/Santa Rosa/santarosa_adams.xlsx',
            'deed_locator': {
                'book_type': 'OR',
                'book_page': '4612/160',
                'book': '4612',
                'page': '160',
                'instrument_number': '202519873',
                'doc_link': 'OR 4612/159 (202519872)',
                'doc_links': ['OR 4612/159 (202519872)'],
            },
        }

        flattened = flatten_deed_row(row)

        self.assertEqual(flattened['Recommended Search'], 'Instrument Number')
        self.assertEqual(flattened['Doc Link Text'], 'OR 4612/159 (202519872)')
        self.assertEqual(flattened['Search Portal'], 'https://santarosaclerk.com/courts/search-public-records/')

    def test_build_summary_frames_counts_strategies(self):
        detail_df = pd.DataFrame([
            {'County': 'Bay', 'Recommended Search': 'Book/Page', 'Search Portal': 'https://example.com'},
            {'County': 'Bay', 'Recommended Search': 'Instrument Number', 'Search Portal': 'https://example.com'},
            {'County': 'Okaloosa', 'Recommended Search': 'Missing Locator', 'Search Portal': ''},
        ])

        overview, county_counts, strategy_counts = build_summary_frames(detail_df)

        self.assertEqual(int(overview.loc[overview['Metric'] == 'Queue Rows', 'Value'].iloc[0]), 3)
        self.assertEqual(int(overview.loc[overview['Metric'] == 'Rows With Locator', 'Value'].iloc[0]), 2)
        self.assertEqual(county_counts.set_index('County').loc['Bay', 'Rows'], 2)
        self.assertEqual(strategy_counts.set_index('Strategy').loc['Missing Locator', 'Rows'], 1)


if __name__ == '__main__':
    unittest.main()
