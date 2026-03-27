import unittest

import pandas as pd

from processors.transformer import transform_row


class FakeMatcher:
    def __init__(self, matches):
        self.matches = matches

    def match(self, name):
        if name is None:
            return (None, None)
        return self.matches.get(name, (None, None))


class TransformerTypeTests(unittest.TestCase):
    def setUp(self):
        self.config = {
            'column_mapping': {
                'grantor': 'Grantor',
                'grantee': 'Grantee',
                'date': 'Date',
                'instrument': 'Instrument',
                'legal': 'Legal',
            },
            'company_indicators': ['INC', 'LLC', 'HOMES'],
            'phase_keywords': [],
            'delimiters': [','],
        }

    def test_generic_company_falls_back_to_house_sale(self):
        row = pd.Series({
            'Grantor': 'Seller Name',
            'Grantee': 'Beach Resort Holding LLC',
            'Date': '2024-01-01',
            'Instrument': 'WD',
            'Legal': 'Lot 1 Example Subdivision',
        })

        result = transform_row(
            row,
            'Bay',
            self.config,
            sub_matcher=None,
            builder_matcher=FakeMatcher({}),
            land_banker_matcher=FakeMatcher({}),
        )

        self.assertEqual(result['type'], 'House Sale')
        self.assertIsNone(result['builder_id'])
        self.assertIsNone(result['grantee_land_banker_id'])

    def test_transformer_preserves_first_party_text_when_builder_found_later(self):
        row = pd.Series({
            'Grantor': 'Seller Name',
            'Grantee': 'Some Trustee, D R Horton Inc',
            'Date': '2024-01-01',
            'Instrument': 'WD',
            'Legal': 'Lot 1 Example Subdivision',
        })

        result = transform_row(
            row,
            'Bay',
            self.config,
            sub_matcher=None,
            builder_matcher=FakeMatcher({'D R Horton Inc': (1, 'DR Horton')}),
            land_banker_matcher=FakeMatcher({}),
        )

        self.assertEqual(result['grantee'], 'Some Trustee')
        self.assertEqual(result['builder_id'], 1)
        self.assertEqual(result['grantee_builder_id'], 1)
        self.assertEqual(result['type'], 'Builder Purchase')

    def test_transformer_captures_land_banker_purchase(self):
        row = pd.Series({
            'Grantor': 'Seller Name',
            'Grantee': 'Land Bank LLC',
            'Date': '2024-01-01',
            'Instrument': 'WD',
            'Legal': 'Lot 1 Example Subdivision',
        })

        result = transform_row(
            row,
            'Bay',
            self.config,
            sub_matcher=None,
            builder_matcher=FakeMatcher({}),
            land_banker_matcher=FakeMatcher({'Land Bank LLC': (7, 'Land Bank LLC')}),
        )

        self.assertEqual(result['type'], 'Land Banker Purchase')
        self.assertEqual(result['grantee_land_banker_id'], 7)


if __name__ == '__main__':
    unittest.main()
