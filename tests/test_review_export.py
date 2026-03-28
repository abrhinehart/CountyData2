import unittest

import pandas as pd

from review_export import build_query, build_summary_frames, flatten_review_row


class ReviewExportTests(unittest.TestCase):
    def test_build_query_includes_reason_filters_and_limit(self):
        sql, params = build_query('Marion', ['subdivision_unmatched', 'phase_not_confirmed_by_lookup'], 25)

        self.assertIn('review_flag = TRUE', sql)
        self.assertIn("REPLACE(UPPER(county), ' ', '') = REPLACE(UPPER(%s), ' ', '')", sql)
        self.assertEqual(sql.count("(parsed_data->'review_reasons') ? %s"), 2)
        self.assertTrue(sql.strip().endswith('LIMIT %s'))
        self.assertEqual(params, ['Marion', 'subdivision_unmatched', 'phase_not_confirmed_by_lookup', 25])

    def test_flatten_review_row_extracts_review_context(self):
        row = {
            'id': 101,
            'county': 'Hernando',
            'date': pd.Timestamp('2024-01-11'),
            'grantor': 'Seller Name',
            'grantee': 'Buyer Name',
            'type': 'House Sale',
            'instrument': 'WD',
            'price': 450000,
            'lots': 2,
            'subdivision': 'SPRING HILL',
            'subdivision_id': 620,
            'phase': '2',
            'legal_desc': 'L13 Blk280 Un6 SubSPRING BILL',
            'legal_raw': 'L13 Blk280 Un6 SubSPRING BILL',
            'source_file': 'raw data/Hernando/hernando_adams.xlsx',
            'parsed_data': {
                'review_reasons': ['phase_not_confirmed_by_lookup', 'subdivision_unmatched'],
                'phase_candidate_values': ['2'],
                'subdivision_lookup_text': 'SPRING HILL',
                'preparsed_subdivision': 'SPRING HILL',
                'ignored_subdivision_reason': None,
                'county_parse': {
                    'normalized_subdivision_candidates': [
                        {
                            'subdivision': 'SPRING HILL',
                            'phase': '2',
                            'details': {'alias_source': 'SPRING BILL'},
                        }
                    ],
                    'lot_values': ['13'],
                    'block_values': ['280'],
                    'unit_values': ['6'],
                    'parcel_references': ['R123'],
                    'subdivision_flags': ['replat'],
                },
            },
        }

        flattened = flatten_review_row(row)

        self.assertEqual(flattened['ID'], 101)
        self.assertEqual(flattened['Review Reasons'], 'phase_not_confirmed_by_lookup | subdivision_unmatched')
        self.assertEqual(flattened['Phase Candidates'], '2')
        self.assertEqual(flattened['Normalized Candidates'], 'SPRING HILL (phase=2, alias=SPRING BILL)')
        self.assertEqual(flattened['Lot Values'], '13')
        self.assertEqual(flattened['Block Values'], '280')
        self.assertEqual(flattened['Unit Values'], '6')
        self.assertEqual(flattened['Parcel References'], 'R123')
        self.assertEqual(flattened['Subdivision Flags'], 'replat')

    def test_build_summary_frames_counts_exploded_reasons(self):
        detail_df = pd.DataFrame([
            {'ID': 1, 'County': 'Bay', 'Review Reasons': 'subdivision_unmatched | multiple_subdivision_candidates'},
            {'ID': 2, 'County': 'Bay', 'Review Reasons': 'subdivision_unmatched'},
            {'ID': 3, 'County': 'Walton', 'Review Reasons': 'phase_not_confirmed_by_lookup'},
        ])

        overview, reason_counts, county_counts = build_summary_frames(detail_df)

        self.assertEqual(int(overview.loc[overview['Metric'] == 'Flagged Rows', 'Value'].iloc[0]), 3)
        self.assertEqual(
            reason_counts.set_index('Reason').loc['subdivision_unmatched', 'Rows'],
            2,
        )
        self.assertEqual(
            reason_counts.set_index('Reason').loc['multiple_subdivision_candidates', 'Rows'],
            1,
        )
        self.assertEqual(
            county_counts.set_index('County').loc['Bay', 'Rows'],
            2,
        )


if __name__ == '__main__':
    unittest.main()
