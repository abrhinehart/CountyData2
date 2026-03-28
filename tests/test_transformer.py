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


class FakeSubdivisionMatcher:
    def __init__(self):
        self.calls = []

    def match(self, text, county, phase_keywords=None):
        self.calls.append((text, county, phase_keywords))
        return (None, None, None)


class ConfiguredSubdivisionMatcher:
    def __init__(self, mapping):
        self.mapping = mapping
        self.calls = []

    def match(self, text, county, phase_keywords=None):
        self.calls.append((text, county, phase_keywords))
        return self.mapping.get((text, county), (None, None, None))


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

    def test_transformer_handles_missing_grantee_without_crashing(self):
        row = pd.Series({
            'Grantor': 'Seller Name',
            'Grantee': pd.NA,
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

        self.assertEqual(result['grantor'], 'Seller Name')
        self.assertIsNone(result['grantee'])
        self.assertEqual(result['parsed_data']['grantee_parties'], [])

    def test_transformer_captures_deed_locator_fields(self):
        row = pd.Series({
            'Grantor': 'Seller Name',
            'Grantee': 'Buyer Name',
            'Date': '2024-01-01',
            'Instrument': 'WD',
            'Legal': 'Lot 1 Example Subdivision',
            'Book Type': 'OR',
            'Book': '4643',
            'Page': '317',
            'Clerk File #': '2025083923',
            'DocLinks': 'https://county.example/doc/123',
            'DocLinks.1': 'https://county.example/doc/456',
        })

        result = transform_row(
            row,
            'Bay',
            self.config,
            sub_matcher=None,
            builder_matcher=FakeMatcher({}),
            land_banker_matcher=FakeMatcher({}),
        )

        locator = result['deed_locator']
        self.assertEqual(locator['book_type'], 'OR')
        self.assertEqual(locator['book'], '4643')
        self.assertEqual(locator['page'], '317')
        self.assertEqual(locator['clerk_file_number'], '2025083923')
        self.assertEqual(locator['doc_link'], 'https://county.example/doc/123')
        self.assertEqual(
            locator['doc_links'],
            ['https://county.example/doc/123', 'https://county.example/doc/456'],
        )
        self.assertIn('Book Type', locator['raw_fields'])

    def test_transformer_splits_santarosa_book_page_in_deed_locator(self):
        row = pd.Series({
            'Grantor': 'Seller Name',
            'Grantee': 'Buyer Name',
            'Date': '2024-01-01',
            'Instrument': 'WD',
            'Legal': 'Lot 1 Example Subdivision',
            'Instrument #': '2025012345',
            'Book Type': 'OR',
            'Book/Page': '7175/2080',
            'Doc Link': 'https://county.example/doc/789',
            'Case #': '2024-CA-55',
        })

        result = transform_row(
            row,
            'Santa Rosa',
            self.config,
            sub_matcher=None,
            builder_matcher=FakeMatcher({}),
            land_banker_matcher=FakeMatcher({}),
        )

        locator = result['deed_locator']
        self.assertEqual(locator['instrument_number'], '2025012345')
        self.assertEqual(locator['book_page'], '7175/2080')
        self.assertEqual(locator['book'], '7175')
        self.assertEqual(locator['page'], '2080')
        self.assertEqual(locator['case_number'], '2024-CA-55')
        self.assertEqual(locator['doc_link'], 'https://county.example/doc/789')

    def test_transformer_preserves_full_party_text_when_builder_found_later(self):
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

        self.assertEqual(result['grantee'], 'Some Trustee, D R Horton Inc')
        self.assertEqual(result['builder_id'], 1)
        self.assertEqual(result['grantee_builder_id'], 1)
        self.assertEqual(result['type'], 'Builder Purchase')
        self.assertEqual(result['parsed_data']['grantee_parties'], ['Some Trustee', 'D R Horton Inc'])
        self.assertFalse(result['parsed_data']['swap']['applied'])

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

    def test_lookup_known_phase_does_not_force_review(self):
        config = dict(self.config)
        config['phase_keywords'] = ['Phase', 'Ph.?', 'PH']

        row = pd.Series({
            'Grantor': 'Seller Name',
            'Grantee': 'Buyer Name',
            'Date': '2024-01-01',
            'Instrument': 'WD',
            'Legal': 'LOT 55 LIBERTY PH 3',
        })

        result = transform_row(
            row,
            'Bay',
            config,
            sub_matcher=ConfiguredSubdivisionMatcher({
                ('LIBERTY', 'Bay'): (7, 'Liberty', None, ['1', '2', '3']),
            }),
            builder_matcher=FakeMatcher({}),
            land_banker_matcher=FakeMatcher({}),
        )

        self.assertEqual(result['subdivision_id'], 7)
        self.assertEqual(result['subdivision'], 'Liberty')
        self.assertEqual(result['phase'], '3')
        self.assertFalse(result['review_flag'])
        self.assertNotIn('phase_not_confirmed_by_lookup', result['parsed_data']['review_reasons'])

    def test_lookup_unknown_phase_still_flags_review(self):
        config = dict(self.config)
        config['phase_keywords'] = ['Phase', 'Ph.?', 'PH']

        row = pd.Series({
            'Grantor': 'Seller Name',
            'Grantee': 'Buyer Name',
            'Date': '2024-01-01',
            'Instrument': 'WD',
            'Legal': 'LOT 55 LIBERTY PH 3',
        })

        result = transform_row(
            row,
            'Bay',
            config,
            sub_matcher=ConfiguredSubdivisionMatcher({
                ('LIBERTY', 'Bay'): (7, 'Liberty', None, ['1', '2']),
            }),
            builder_matcher=FakeMatcher({}),
            land_banker_matcher=FakeMatcher({}),
        )

        self.assertEqual(result['subdivision_id'], 7)
        self.assertEqual(result['phase'], '3')
        self.assertTrue(result['review_flag'])
        self.assertIn('phase_not_confirmed_by_lookup', result['parsed_data']['review_reasons'])

    def test_lookup_known_compound_phase_does_not_force_review(self):
        config = dict(self.config)
        config['phase_keywords'] = ['Phase', 'Ph.?', 'PH']

        row = pd.Series({
            'Grantor': 'Seller Name',
            'Grantee': 'Buyer Name',
            'Date': '2024-01-01',
            'Instrument': 'WD',
            'Legal': 'LOT 55 SUNDANCE PH 1-2',
        })

        result = transform_row(
            row,
            'Marion',
            config,
            sub_matcher=ConfiguredSubdivisionMatcher({
                ('SUNDANCE', 'Marion'): (7, 'SUNDANCE', None, ['1', '2', '1-2']),
            }),
            builder_matcher=FakeMatcher({}),
            land_banker_matcher=FakeMatcher({}),
        )

        self.assertEqual(result['subdivision_id'], 7)
        self.assertEqual(result['phase'], '1-2')
        self.assertFalse(result['review_flag'])
        self.assertNotIn('phase_not_confirmed_by_lookup', result['parsed_data']['review_reasons'])

    def test_lookup_known_letter_suffix_phase_does_not_force_review(self):
        config = dict(self.config)
        config['phase_keywords'] = ['Phase', 'Ph.?', 'PH']

        row = pd.Series({
            'Grantor': 'Seller Name',
            'Grantee': 'Buyer Name',
            'Date': '2024-01-01',
            'Instrument': 'WD',
            'Legal': 'LOT 55 OWLS HEAD FARMS PH 1-C',
        })

        result = transform_row(
            row,
            'Walton',
            config,
            sub_matcher=ConfiguredSubdivisionMatcher({
                ('OWLS HEAD FARMS', 'Walton'): (8, 'OWLS HEAD FARMS', None, ['1', '1A', '1B', '1-C']),
            }),
            builder_matcher=FakeMatcher({}),
            land_banker_matcher=FakeMatcher({}),
        )

        self.assertEqual(result['subdivision_id'], 8)
        self.assertEqual(result['phase'], '1-C')
        self.assertFalse(result['review_flag'])
        self.assertNotIn('phase_not_confirmed_by_lookup', result['parsed_data']['review_reasons'])

    def test_lookup_normalizes_marion_slash_o_phase_when_known(self):
        config = dict(self.config)
        config['phase_keywords'] = ['Phase', 'Ph.?', 'PH']

        row = pd.Series({
            'Grantor': 'Seller Name',
            'Grantee': 'Buyer Name',
            'Date': '2024-01-01',
            'Instrument': 'WD',
            'Legal': 'LT 1 AUTUMN GLEN PH 1/O',
        })

        result = transform_row(
            row,
            'Marion',
            config,
            sub_matcher=ConfiguredSubdivisionMatcher({
                ('AUTUMN GLEN', 'Marion'): (11, 'AUTUMN GLEN', None, ['1', '2']),
            }),
            builder_matcher=FakeMatcher({}),
            land_banker_matcher=FakeMatcher({}),
        )

        self.assertEqual(result['subdivision_id'], 11)
        self.assertEqual(result['phase'], '1')
        self.assertFalse(result['review_flag'])
        self.assertNotIn('phase_not_confirmed_by_lookup', result['parsed_data']['review_reasons'])
        self.assertEqual(result['parsed_data']['phase_candidate_values'], ['1 / O'])

    def test_bay_confidential_text_does_not_become_subdivision(self):
        row = pd.Series({
            'Grantor': 'Seller Name',
            'Grantee': 'Buyer Name',
            'Date': '2024-01-01',
            'Instrument': 'WD',
            'Legal': 'CONFIDENTIAL',
        })

        result = transform_row(
            row,
            'Bay',
            self.config,
            sub_matcher=ConfiguredSubdivisionMatcher({}),
            builder_matcher=FakeMatcher({}),
            land_banker_matcher=FakeMatcher({}),
        )

        self.assertIsNone(result['subdivision'])
        self.assertFalse(result['review_flag'])
        self.assertEqual(result['parsed_data']['county_parse']['normalized_subdivision_candidates'], [])
        self.assertEqual(result['parsed_data']['review_reasons'], [])

    def test_citrus_redaction_text_does_not_become_subdivision(self):
        row = pd.Series({
            'Grantor': 'Seller Name',
            'Grantee': 'Buyer Name',
            'Date': '2024-01-01',
            'Instrument': 'WD',
            'Legal': 'REDACTION APPLIED PURSUANT TO FLORIDA PUBLIC RECORDS LAWS',
        })

        result = transform_row(
            row,
            'Citrus',
            self.config,
            sub_matcher=ConfiguredSubdivisionMatcher({}),
            builder_matcher=FakeMatcher({}),
            land_banker_matcher=FakeMatcher({}),
        )

        self.assertIsNone(result['subdivision'])
        self.assertFalse(result['review_flag'])
        self.assertEqual(result['parsed_data']['county_parse']['normalized_subdivision_candidates'], [])
        self.assertEqual(result['parsed_data']['review_reasons'], [])

    def test_escambia_section_only_text_does_not_become_subdivision(self):
        row = pd.Series({
            'Grantor': 'Seller Name',
            'Grantee': 'Buyer Name',
            'Date': '2024-01-01',
            'Instrument': 'WD',
            'Legal': 'SEC:01 TWP:1S RGE:32W',
        })

        result = transform_row(
            row,
            'Escambia',
            self.config,
            sub_matcher=ConfiguredSubdivisionMatcher({}),
            builder_matcher=FakeMatcher({}),
            land_banker_matcher=FakeMatcher({}),
        )

        self.assertIsNone(result['subdivision'])
        self.assertFalse(result['review_flag'])
        self.assertEqual(result['parsed_data']['ignored_subdivision_reason'], 'section_reference')
        self.assertEqual(result['parsed_data']['review_reasons'], [])

    def test_citrus_str_only_text_does_not_become_subdivision(self):
        row = pd.Series({
            'Grantor': 'Seller Name',
            'Grantee': 'Buyer Name',
            'Date': '2024-01-01',
            'Instrument': 'WD',
            'Legal': 'S: 16 T: 19S R: 21E',
        })

        result = transform_row(
            row,
            'Citrus',
            self.config,
            sub_matcher=ConfiguredSubdivisionMatcher({}),
            builder_matcher=FakeMatcher({}),
            land_banker_matcher=FakeMatcher({}),
        )

        self.assertIsNone(result['subdivision'])
        self.assertFalse(result['review_flag'])
        self.assertEqual(result['parsed_data']['ignored_subdivision_reason'], 'section_reference')
        self.assertEqual(result['parsed_data']['review_reasons'], [])

    def test_okaloosa_city_name_does_not_become_subdivision(self):
        config = dict(self.config)
        config['phase_keywords'] = ['Phase', 'Ph.?', 'PH', 'Unit']
        row = pd.Series({
            'Grantor': 'Seller Name',
            'Grantee': 'Buyer Name',
            'Date': '2024-01-01',
            'Instrument': 'WD',
            'Legal': 'CRESTVIEW',
        })

        result = transform_row(
            row,
            'Okaloosa',
            config,
            sub_matcher=ConfiguredSubdivisionMatcher({}),
            builder_matcher=FakeMatcher({}),
            land_banker_matcher=FakeMatcher({}),
        )

        self.assertIsNone(result['subdivision'])
        self.assertFalse(result['review_flag'])
        self.assertEqual(result['parsed_data']['county_parse']['normalized_subdivision_candidates'], [])
        self.assertEqual(result['parsed_data']['review_reasons'], [])

    def test_walton_placeholder_text_does_not_become_subdivision(self):
        row = pd.Series({
            'Grantor': 'Seller Name',
            'Grantee': 'Buyer Name',
            'Date': '2024-01-01',
            'Instrument': 'WD',
            'Legal': 'TO CORRECT',
        })

        result = transform_row(
            row,
            'Walton',
            self.config,
            sub_matcher=ConfiguredSubdivisionMatcher({}),
            builder_matcher=FakeMatcher({}),
            land_banker_matcher=FakeMatcher({}),
        )

        self.assertIsNone(result['subdivision'])
        self.assertFalse(result['review_flag'])
        self.assertEqual(result['parsed_data']['ignored_subdivision_reason'], 'exact_ignore')
        self.assertEqual(result['parsed_data']['review_reasons'], [])

    def test_okeechobee_preserves_multiline_party_text_and_matches_later_names(self):
        row = pd.Series({
            'Grantor': 'Seller Name\nD R Horton Inc',
            'Grantee': 'Buyer Name\nLand Bank LLC',
            'Date': '2024-01-01',
            'Instrument': 'WD',
            'Legal': 'Lot 1 Example Subdivision',
        })

        result = transform_row(
            row,
            'Okeechobee',
            self.config,
            sub_matcher=None,
            builder_matcher=FakeMatcher({'D R Horton Inc': (1, 'DR Horton')}),
            land_banker_matcher=FakeMatcher({'Land Bank LLC': (7, 'Land Bank LLC')}),
        )

        self.assertEqual(result['grantor'], 'Seller Name\nD R Horton Inc')
        self.assertEqual(result['grantee'], 'Buyer Name\nLand Bank LLC')
        self.assertEqual(result['grantor_builder_id'], 1)
        self.assertEqual(result['grantee_land_banker_id'], 7)
        self.assertEqual(result['type'], 'Land Banker Purchase')

    def test_okaloosa_grantee_trims_parcel_tail_before_matching(self):
        config = dict(self.config)
        config['delimiters'] = [',', 'Parcel', 'Section']

        row = pd.Series({
            'Grantor': 'Seller Name',
            'Grantee': 'Some Trustee, D R Horton Inc Parcel 12345',
            'Date': '2024-01-01',
            'Instrument': 'WD',
            'Legal': 'Lot 1 Example Subdivision',
        })

        result = transform_row(
            row,
            'Okaloosa',
            config,
            sub_matcher=None,
            builder_matcher=FakeMatcher({'D R Horton Inc': (1, 'DR Horton')}),
            land_banker_matcher=FakeMatcher({'12345': (7, 'Fake Land Banker')}),
        )

        self.assertEqual(result['grantee'], 'Some Trustee, D R Horton Inc')
        self.assertEqual(result['grantee_builder_id'], 1)
        self.assertIsNone(result['grantee_land_banker_id'])
        self.assertEqual(result['type'], 'Builder Purchase')

    def test_marion_aliases_known_subdivision_abbreviations_and_captures_unit(self):
        config = dict(self.config)
        config['column_mapping'] = dict(self.config['column_mapping'])
        config['column_mapping']['star'] = 'Star'
        config['phase_keywords'] = ['Phase', 'Ph.?', 'PH']

        row = pd.Series({
            'Star': '*',
            'Grantor': 'Seller Name',
            'Grantee': 'Buyer Name',
            'Date': '2024-01-01',
            'Instrument': 'WD',
            'Legal': 'LT 1 BK 288 SSS U-17',
        })

        result = transform_row(
            row,
            'Marion',
            config,
            sub_matcher=ConfiguredSubdivisionMatcher({}),
            builder_matcher=FakeMatcher({}),
            land_banker_matcher=FakeMatcher({}),
        )

        self.assertEqual(result['subdivision'], 'SILVER SPRINGS SHORES')
        self.assertIsNone(result['phase'])
        self.assertEqual(result['parsed_data']['county_parse']['structured_block_values'], ['288'])
        self.assertEqual(result['parsed_data']['county_parse']['structured_unit_values'], ['17'])
        self.assertEqual(result['parsed_data']['county_parse']['lot_values'], ['1'])

    def test_marion_tracks_tract_and_common_area_details(self):
        config = dict(self.config)
        config['column_mapping'] = dict(self.config['column_mapping'])
        config['column_mapping']['star'] = 'Star'
        config['phase_keywords'] = ['Phase', 'Ph.?', 'PH']

        row = pd.Series({
            'Star': '*',
            'Grantor': 'Seller Name',
            'Grantee': 'Buyer Name',
            'Date': '2024-01-01',
            'Instrument': 'WD',
            'Legal': 'TRACTS A-F SCBDW SUNDANCE PH 3/O',
        })

        result = transform_row(
            row,
            'Marion',
            config,
            sub_matcher=ConfiguredSubdivisionMatcher({}),
            builder_matcher=FakeMatcher({}),
            land_banker_matcher=FakeMatcher({}),
        )

        self.assertEqual(result['subdivision'], 'SUNDANCE')
        self.assertEqual(result['phase'], '3 / O')
        self.assertEqual(result['parsed_data']['county_parse']['tract_values'], ['A-F'])
        self.assertEqual(result['parsed_data']['county_parse']['common_area_codes'], ['SCBDW'])

    def test_marion_marks_replat_subdivision_flag(self):
        config = dict(self.config)
        config['column_mapping'] = dict(self.config['column_mapping'])
        config['column_mapping']['star'] = 'Star'
        config['phase_keywords'] = ['Phase', 'Ph.?', 'PH']

        row = pd.Series({
            'Star': '*',
            'Grantor': 'Seller Name',
            'Grantee': 'Buyer Name',
            'Date': '2024-01-01',
            'Instrument': 'WD',
            'Legal': 'LT 243 JULIETTE FALLS 2ND REPLAT',
        })

        result = transform_row(
            row,
            'Marion',
            config,
            sub_matcher=ConfiguredSubdivisionMatcher({}),
            builder_matcher=FakeMatcher({}),
            land_banker_matcher=FakeMatcher({}),
        )

        self.assertEqual(result['subdivision'], 'JULLIETTE FALLS')
        self.assertEqual(result['parsed_data']['county_parse']['subdivision_flags'], ['replat'])

    def test_marion_aliases_marion_rch_and_preserves_lot_series_count(self):
        config = dict(self.config)
        config['column_mapping'] = dict(self.config['column_mapping'])
        config['column_mapping']['star'] = 'Star'
        config['phase_keywords'] = ['Phase', 'Ph.?', 'PH']

        row = pd.Series({
            'Star': '',
            'Grantor': 'Seller Name',
            'Grantee': 'Buyer Name',
            'Date': '2024-01-01',
            'Instrument': 'WD',
            'Legal': 'LS 13-16 MARION RCH PH 2/O',
        })

        result = transform_row(
            row,
            'Marion',
            config,
            sub_matcher=ConfiguredSubdivisionMatcher({}),
            builder_matcher=FakeMatcher({}),
            land_banker_matcher=FakeMatcher({}),
        )

        self.assertEqual(result['subdivision'], 'MARION RANCH')
        self.assertEqual(result['phase'], '2 / O')
        self.assertEqual(result['lots'], 4)

    def test_marion_aliases_oaks_at_oc_s_variant(self):
        config = dict(self.config)
        config['column_mapping'] = dict(self.config['column_mapping'])
        config['column_mapping']['star'] = 'Star'
        config['phase_keywords'] = ['Phase', 'Ph.?', 'PH']

        row = pd.Series({
            'Star': '*',
            'Grantor': 'Seller Name',
            'Grantee': 'Buyer Name',
            'Date': '2024-01-01',
            'Instrument': 'WD',
            'Legal': 'LT 20 BK D OAKS AT OC S PH 2',
        })

        result = transform_row(
            row,
            'Marion',
            config,
            sub_matcher=ConfiguredSubdivisionMatcher({}),
            builder_matcher=FakeMatcher({}),
            land_banker_matcher=FakeMatcher({}),
        )

        self.assertEqual(result['subdivision'], 'OAKS AT OCALA CROSSINGS SOUTH')
        self.assertEqual(result['phase'], '2')
        self.assertEqual(result['parsed_data']['county_parse']['structured_block_values'], ['D'])
        self.assertEqual(result['parsed_data']['county_parse']['subdivision_suffix_values'], [])

    def test_marion_uses_reference_list_for_calesa_abbreviation(self):
        config = dict(self.config)
        config['column_mapping'] = dict(self.config['column_mapping'])
        config['column_mapping']['star'] = 'Star'
        config['phase_keywords'] = ['Phase', 'Ph.?', 'PH']

        row = pd.Series({
            'Star': '*',
            'Grantor': 'Seller Name',
            'Grantee': 'Buyer Name',
            'Date': '2024-01-01',
            'Instrument': 'WD',
            'Legal': 'LT 162 CTPG',
        })

        result = transform_row(
            row,
            'Marion',
            config,
            sub_matcher=ConfiguredSubdivisionMatcher({}),
            builder_matcher=FakeMatcher({}),
            land_banker_matcher=FakeMatcher({}),
        )

        self.assertEqual(result['subdivision'], 'CALESA TOWNSHIP PERLINO GROVE')
        self.assertEqual(result['parsed_data']['county_parse']['subdivision_suffix_values'], [])

    def test_marion_reference_list_maps_grand_park_north(self):
        config = dict(self.config)
        config['column_mapping'] = dict(self.config['column_mapping'])
        config['column_mapping']['star'] = 'Star'
        config['phase_keywords'] = ['Phase', 'Ph.?', 'PH']

        row = pd.Series({
            'Star': '*',
            'Grantor': 'Seller Name',
            'Grantee': 'Buyer Name',
            'Date': '2024-01-01',
            'Instrument': 'WD',
            'Legal': 'LT 88 GRAND PK N',
        })

        result = transform_row(
            row,
            'Marion',
            config,
            sub_matcher=ConfiguredSubdivisionMatcher({}),
            builder_matcher=FakeMatcher({}),
            land_banker_matcher=FakeMatcher({}),
        )

        self.assertEqual(result['subdivision'], 'GRAND PARK NORTH')
        self.assertEqual(result['parsed_data']['county_parse']['subdivision_suffix_values'], [])

    def test_marion_reference_match_captures_prefix_tokens_for_common_area_variant(self):
        config = dict(self.config)
        config['column_mapping'] = dict(self.config['column_mapping'])
        config['column_mapping']['star'] = 'Star'
        config['phase_keywords'] = ['Phase', 'Ph.?', 'PH']

        row = pd.Series({
            'Star': '*',
            'Grantor': 'Seller Name',
            'Grantee': 'Buyer Name',
            'Date': '2024-01-01',
            'Instrument': 'WD',
            'Legal': 'LT 333 CH W ASHFORD & BALFOUR',
        })

        result = transform_row(
            row,
            'Marion',
            config,
            sub_matcher=ConfiguredSubdivisionMatcher({}),
            builder_matcher=FakeMatcher({}),
            land_banker_matcher=FakeMatcher({}),
        )

        self.assertEqual(result['subdivision'], 'ASHFORD & BALFOUR')
        self.assertEqual(result['parsed_data']['county_parse']['subdivision_prefix_values'], ['CH', 'W'])

    def test_marion_reference_list_maps_jb_ranch(self):
        config = dict(self.config)
        config['column_mapping'] = dict(self.config['column_mapping'])
        config['column_mapping']['star'] = 'Star'
        config['phase_keywords'] = ['Phase', 'Ph.?', 'PH']

        row = pd.Series({
            'Star': '',
            'Grantor': 'Seller Name',
            'Grantee': 'Buyer Name',
            'Date': '2024-01-01',
            'Instrument': 'WD',
            'Legal': 'LT 91 JB RCH SUB PH 2A',
        })

        result = transform_row(
            row,
            'Marion',
            config,
            sub_matcher=ConfiguredSubdivisionMatcher({}),
            builder_matcher=FakeMatcher({}),
            land_banker_matcher=FakeMatcher({}),
        )

        self.assertEqual(result['subdivision'], 'JB RANCH')
        self.assertEqual(result['phase'], '2A')

    def test_marion_partial_subdivision_rows_preserve_flag_while_normalizing_name(self):
        config = dict(self.config)
        config['column_mapping'] = dict(self.config['column_mapping'])
        config['column_mapping']['star'] = 'Star'
        config['phase_keywords'] = ['Phase', 'Ph.?', 'PH']

        row = pd.Series({
            'Star': '*',
            'Grantor': 'Seller Name',
            'Grantee': 'Buyer Name',
            'Date': '2024-01-01',
            'Instrument': 'WD',
            'Legal': 'PT W OAK PH 1',
        })

        result = transform_row(
            row,
            'Marion',
            config,
            sub_matcher=ConfiguredSubdivisionMatcher({}),
            builder_matcher=FakeMatcher({}),
            land_banker_matcher=FakeMatcher({}),
        )

        self.assertEqual(result['subdivision'], 'WEST OAK')
        self.assertEqual(result['phase'], '1')
        self.assertIn('partial_subdivision', result['parsed_data']['county_parse']['subdivision_flags'])

    def test_marion_maps_rh_to_rolling_hills_and_preserves_partial_lot(self):
        config = dict(self.config)
        config['column_mapping'] = dict(self.config['column_mapping'])
        config['column_mapping']['star'] = 'Star'
        config['phase_keywords'] = ['Phase', 'Ph.?', 'PH']

        row = pd.Series({
            'Star': '*',
            'Grantor': 'Seller Name',
            'Grantee': 'Buyer Name',
            'Date': '2024-01-01',
            'Instrument': 'WD',
            'Legal': 'PT LT 12 BK 4 RH U-1',
        })

        result = transform_row(
            row,
            'Marion',
            config,
            sub_matcher=ConfiguredSubdivisionMatcher({}),
            builder_matcher=FakeMatcher({}),
            land_banker_matcher=FakeMatcher({}),
        )

        self.assertEqual(result['subdivision'], 'ROLLING HILLS')
        self.assertEqual(result['parsed_data']['county_parse']['structured_unit_values'], ['1'])
        self.assertEqual(result['parsed_data']['county_parse']['structured_partial_lot_values'], ['12'])
        self.assertNotIn('partial_subdivision', result['parsed_data']['county_parse']['subdivision_flags'])

    def test_marion_replat_typo_still_captures_unit_and_canonical_subdivision(self):
        config = dict(self.config)
        config['column_mapping'] = dict(self.config['column_mapping'])
        config['column_mapping']['star'] = 'Star'
        config['phase_keywords'] = ['Phase', 'Ph.?', 'PH']

        row = pd.Series({
            'Star': '*',
            'Grantor': 'Seller Name',
            'Grantee': 'Buyer Name',
            'Date': '2024-01-01',
            'Instrument': 'WD',
            'Legal': 'LT 1 BK 1293 MO U-8 1SR REPLAT',
        })

        result = transform_row(
            row,
            'Marion',
            config,
            sub_matcher=ConfiguredSubdivisionMatcher({}),
            builder_matcher=FakeMatcher({}),
            land_banker_matcher=FakeMatcher({}),
        )

        self.assertEqual(result['subdivision'], 'MARION OAKS')
        self.assertEqual(result['parsed_data']['county_parse']['structured_unit_values'], ['8'])
        self.assertIn('replat', result['parsed_data']['county_parse']['subdivision_flags'])

    def test_okaloosa_normalizes_subdivision_suffix_and_parcel_capture(self):
        config = dict(self.config)
        config['phase_keywords'] = ['Phase', 'Ph.?', 'PH', 'Unit']

        row = pd.Series({
            'Grantor': 'Seller Name',
            'Grantee': 'Buyer Name',
            'Date': '2024-01-01',
            'Instrument': 'WD',
            'Legal': 'ASHTON VIEW SUBDIVISION Lot: 26 , Parcel: 25-4N-23-1050-0000-0260',
        })

        result = transform_row(
            row,
            'Okaloosa',
            config,
            sub_matcher=ConfiguredSubdivisionMatcher({}),
            builder_matcher=FakeMatcher({}),
            land_banker_matcher=FakeMatcher({}),
        )

        self.assertEqual(result['subdivision'], 'ASHTON VIEW')
        self.assertIsNone(result['phase'])
        self.assertEqual(result['lots'], 1)
        self.assertEqual(result['parsed_data']['county_parse']['structured_lot_values'], ['26'])
        self.assertEqual(
            result['parsed_data']['county_parse']['structured_parcel_references'],
            ['25-4N-23-1050-0000-0260'],
        )

    def test_okaloosa_keeps_unit_separate_from_phase(self):
        config = dict(self.config)
        config['phase_keywords'] = ['Phase', 'Ph.?', 'PH', 'Unit']

        row = pd.Series({
            'Grantor': 'Seller Name',
            'Grantee': 'Buyer Name',
            'Date': '2024-01-01',
            'Instrument': 'WD',
            'Legal': 'RIDGEWAY LANDING PHASE 2 Unit: 101 , Parcel: 05-3N-23-1500-0000-1010',
        })

        result = transform_row(
            row,
            'Okaloosa',
            config,
            sub_matcher=ConfiguredSubdivisionMatcher({}),
            builder_matcher=FakeMatcher({}),
            land_banker_matcher=FakeMatcher({}),
        )

        self.assertEqual(result['subdivision'], 'RIDGEWAY LANDING')
        self.assertEqual(result['phase'], '2')
        self.assertEqual(result['parsed_data']['county_parse']['structured_unit_values'], ['101'])
        self.assertEqual(
            result['parsed_data']['county_parse']['structured_parcel_references'],
            ['05-3N-23-1500-0000-1010'],
        )

    def test_okaloosa_keeps_subdivision_only_clause_with_duplicate_phase_keyword(self):
        config = dict(self.config)
        config['phase_keywords'] = ['Phase', 'Ph.?', 'PH', 'Unit']

        row = pd.Series({
            'Grantor': 'Seller Name',
            'Grantee': 'Buyer Name',
            'Date': '2024-01-01',
            'Instrument': 'WD',
            'Legal': 'PATRIOT RIDGE PHASE PHASE 6 , Parcel: 33-3N-23-2810-0000-2440',
        })

        result = transform_row(
            row,
            'Okaloosa',
            config,
            sub_matcher=ConfiguredSubdivisionMatcher({}),
            builder_matcher=FakeMatcher({}),
            land_banker_matcher=FakeMatcher({}),
        )

        self.assertEqual(result['subdivision'], 'PATRIOT RIDGE')
        self.assertEqual(result['phase'], '6')
        self.assertEqual(
            result['parsed_data']['county_parse']['structured_parcel_references'],
            ['33-3N-23-2810-0000-2440'],
        )

    def test_okaloosa_metes_bounds_rows_store_geo_without_fake_subdivision(self):
        config = dict(self.config)
        config['phase_keywords'] = ['Phase', 'Ph.?', 'PH', 'Unit']

        row = pd.Series({
            'Grantor': 'Seller Name',
            'Grantee': 'Buyer Name',
            'Date': '2024-01-01',
            'Instrument': 'WD',
            'Legal': 'Section: 29 Township: 4NRange: 22Legal Remarks: COMM AT SWC OF , Parcel: 29-4N-22-0000-0001-031A',
        })

        result = transform_row(
            row,
            'Okaloosa',
            config,
            sub_matcher=ConfiguredSubdivisionMatcher({}),
            builder_matcher=FakeMatcher({}),
            land_banker_matcher=FakeMatcher({}),
        )

        self.assertIsNone(result['subdivision'])
        self.assertIsNone(result['phase'])
        self.assertEqual(result['parsed_data']['county_parse']['structured_section_values'], ['29'])
        self.assertEqual(result['parsed_data']['county_parse']['structured_township_values'], ['4N'])
        self.assertEqual(result['parsed_data']['county_parse']['structured_range_values'], ['22'])
        self.assertEqual(result['parsed_data']['county_parse']['legal_remarks_values'], ['COMM AT SWC OF'])
        self.assertEqual(
            result['parsed_data']['county_parse']['structured_parcel_references'],
            ['29-4N-22-0000-0001-031A'],
        )

    def test_okaloosa_can_derive_subdivision_from_plat_style_legal_remarks(self):
        config = dict(self.config)
        config['phase_keywords'] = ['Phase', 'Ph.?', 'PH', 'Unit']

        row = pd.Series({
            'Grantor': 'Seller Name',
            'Grantee': 'Buyer Name',
            'Date': '2024-01-01',
            'Instrument': 'WD',
            'Legal': 'Parcel: 15-3N-23-0000-0012-0010 Legal Remarks: UNREC. OPPORTUNITY ADDITION TO SHOFFNER CITY LOTS 26-29 BLK 13',
        })

        result = transform_row(
            row,
            'Okaloosa',
            config,
            sub_matcher=ConfiguredSubdivisionMatcher({}),
            builder_matcher=FakeMatcher({}),
            land_banker_matcher=FakeMatcher({}),
        )

        self.assertEqual(result['subdivision'], 'OPPORTUNITY ADDITION TO SHOFFNER CITY')
        self.assertIsNone(result['phase'])
        self.assertEqual(
            result['parsed_data']['county_parse']['legal_remarks_values'],
            ['UNREC. OPPORTUNITY ADDITION TO SHOFFNER CITY LOTS 26-29 BLK 13'],
        )
        self.assertEqual(
            result['parsed_data']['county_parse']['structured_parcel_references'],
            ['15-3N-23-0000-0012-0010'],
        )

    def test_okeechobee_legal_strips_leading_parcel_id(self):
        config = dict(self.config)
        config['phase_keywords'] = ['Phase', 'PH']
        matcher = FakeSubdivisionMatcher()

        row = pd.Series({
            'Grantor': 'Seller Name',
            'Grantee': 'Buyer Name',
            'Date': '2024-01-01',
            'Instrument': 'WD',
            'Legal': '0-00-00-00-0000-00000-0000 BASSWOOD PHASE 2',
        })

        result = transform_row(
            row,
            'Okeechobee',
            config,
            sub_matcher=matcher,
            builder_matcher=FakeMatcher({}),
            land_banker_matcher=FakeMatcher({}),
        )

        self.assertEqual(result['legal_raw'], 'BASSWOOD PHASE 2')
        self.assertEqual(result['legal_desc'], 'BASSWOOD PHASE 2')
        self.assertEqual(result['subdivision'], 'BASSWOOD')
        self.assertEqual(result['phase'], '2')
        self.assertEqual(matcher.calls[0][0], 'BASSWOOD')

    def test_okeechobee_keeps_unit_as_structured_field_not_phase(self):
        config = dict(self.config)
        config['phase_keywords'] = ['Phase', 'Ph.?', 'PH', 'Unit']

        row = pd.Series({
            'Grantor': 'Seller Name',
            'Grantee': 'Buyer Name',
            'Date': '2024-01-01',
            'Instrument': 'WD',
            'Legal': '1-05-37-35-0020-00310-0130\nLOT 13 BLK 31 BASSWOOD INC UNIT 2',
        })

        result = transform_row(
            row,
            'Okeechobee',
            config,
            sub_matcher=ConfiguredSubdivisionMatcher({}),
            builder_matcher=FakeMatcher({}),
            land_banker_matcher=FakeMatcher({}),
        )

        self.assertEqual(result['legal_raw'], 'LOT 13 BLK 31 BASSWOOD INC UNIT 2')
        self.assertEqual(result['subdivision'], 'BASSWOOD')
        self.assertIsNone(result['phase'])
        self.assertEqual(result['lots'], 1)
        self.assertEqual(result['parsed_data']['county_parse']['structured_block_values'], ['31'])
        self.assertEqual(result['parsed_data']['county_parse']['structured_unit_values'], ['2'])
        self.assertEqual(
            result['parsed_data']['county_parse']['structured_parcel_references'],
            ['1-05-37-35-0020-00310-0130'],
        )
        self.assertEqual(
            result['parsed_data']['county_parse']['normalized_subdivision_candidates'][0]['details']['alias_source'],
            'BASSWOOD INC',
        )

    def test_okeechobee_str_tail_does_not_become_fake_subdivision(self):
        config = dict(self.config)
        config['phase_keywords'] = ['Phase', 'Ph.?', 'PH', 'Unit']

        row = pd.Series({
            'Grantor': 'Seller Name',
            'Grantee': 'Buyer Name',
            'Date': '2024-01-01',
            'Instrument': 'WD',
            'Legal': '1-06-37-35-0A00-00000-0090\nLOT 9 UNIT 7 6/37/35',
        })

        result = transform_row(
            row,
            'Okeechobee',
            config,
            sub_matcher=ConfiguredSubdivisionMatcher({}),
            builder_matcher=FakeMatcher({}),
            land_banker_matcher=FakeMatcher({}),
        )

        self.assertIsNone(result['subdivision'])
        self.assertIsNone(result['phase'])
        self.assertEqual(result['lots'], 1)
        self.assertEqual(result['parsed_data']['county_parse']['structured_unit_values'], ['7'])
        self.assertEqual(result['parsed_data']['county_parse']['structured_section_values'], ['6'])
        self.assertEqual(result['parsed_data']['county_parse']['structured_township_values'], ['37'])
        self.assertEqual(result['parsed_data']['county_parse']['structured_range_values'], ['35'])
        self.assertEqual(
            result['parsed_data']['county_parse']['structured_parcel_references'],
            ['1-06-37-35-0A00-00000-0090'],
        )

    def test_santarosa_slash_shorthand_captures_phase_and_lot_count(self):
        config = dict(self.config)
        config['phase_keywords'] = ['Phase', 'Ph.?', 'PH', 'Unit']

        row = pd.Series({
            'Grantor': 'Seller Name',
            'Grantee': 'Buyer Name',
            'Date': '2024-01-01',
            'Instrument': 'WD',
            'Legal': 'PARKLAND PLACE PH 1A 1-27/A, 1-21/B, 1-10/C',
        })

        result = transform_row(
            row,
            'Santa Rosa',
            config,
            sub_matcher=ConfiguredSubdivisionMatcher({}),
            builder_matcher=FakeMatcher({}),
            land_banker_matcher=FakeMatcher({}),
        )

        self.assertEqual(result['subdivision'], 'PARKLAND PLACE')
        self.assertEqual(result['phase'], '1A')
        self.assertEqual(result['lots'], 58)
        self.assertEqual(
            result['parsed_data']['county_parse']['structured_block_values'],
            ['A', 'B', 'C'],
        )

    def test_santarosa_unit_stays_structured_data_not_phase(self):
        config = dict(self.config)
        config['phase_keywords'] = ['Phase', 'Ph.?', 'PH', 'Unit']

        row = pd.Series({
            'Grantor': 'Seller Name',
            'Grantee': 'Buyer Name',
            'Date': '2024-01-01',
            'Instrument': 'WD',
            'Legal': 'TIGER POINT VILLAGE UNIT 7 4/C',
        })

        result = transform_row(
            row,
            'Santa Rosa',
            config,
            sub_matcher=ConfiguredSubdivisionMatcher({}),
            builder_matcher=FakeMatcher({}),
            land_banker_matcher=FakeMatcher({}),
        )

        self.assertEqual(result['subdivision'], 'TIGER POINT VILLAGE')
        self.assertIsNone(result['phase'])
        self.assertEqual(result['lots'], 1)
        self.assertEqual(result['parsed_data']['county_parse']['structured_unit_values'], ['7'])
        self.assertEqual(result['parsed_data']['county_parse']['structured_block_values'], ['C'])

    def test_santarosa_unrecorded_str_prefix_row_is_structured(self):
        config = dict(self.config)
        config['phase_keywords'] = ['Phase', 'Ph.?', 'PH', 'Unit']

        row = pd.Series({
            'Grantor': 'Seller Name',
            'Grantee': 'Buyer Name',
            'Date': '2024-01-01',
            'Instrument': 'WD',
            'Legal': '14-3N-29W; 15-3N-29W THREE HOLLOW EAST LOT 33 UNREC',
        })

        result = transform_row(
            row,
            'Santa Rosa',
            config,
            sub_matcher=ConfiguredSubdivisionMatcher({}),
            builder_matcher=FakeMatcher({}),
            land_banker_matcher=FakeMatcher({}),
        )

        self.assertEqual(result['subdivision'], 'THREE HOLLOW EAST')
        self.assertIsNone(result['phase'])
        self.assertEqual(result['lots'], 1)
        self.assertEqual(
            result['parsed_data']['county_parse']['structured_parcel_references'],
            ['14-3N-29W', '15-3N-29W'],
        )
        self.assertEqual(result['parsed_data']['county_parse']['structured_section_values'], ['14', '15'])
        self.assertIn('unrecorded', result['parsed_data']['county_parse']['subdivision_flags'])

    def test_santarosa_no_phase_rows_preserve_flag_without_fake_phase(self):
        config = dict(self.config)
        config['phase_keywords'] = ['Phase', 'Ph.?', 'PH', 'Unit']

        row = pd.Series({
            'Grantor': 'Seller Name',
            'Grantee': 'Buyer Name',
            'Date': '2024-01-01',
            'Instrument': 'WD',
            'Legal': 'CHASE FARMS NO PHASE 2 15/A',
        })

        result = transform_row(
            row,
            'Santa Rosa',
            config,
            sub_matcher=ConfiguredSubdivisionMatcher({}),
            builder_matcher=FakeMatcher({}),
            land_banker_matcher=FakeMatcher({}),
        )

        self.assertEqual(result['subdivision'], 'CHASE FARMS')
        self.assertIsNone(result['phase'])
        self.assertEqual(result['parsed_data']['county_parse']['no_phase_values'], ['2'])
        self.assertIn('no_phase', result['parsed_data']['county_parse']['subdivision_flags'])

    def test_santarosa_bare_subdivision_phase_line_is_not_left_unparsed(self):
        config = dict(self.config)
        config['phase_keywords'] = ['Phase', 'Ph.?', 'PH', 'Unit']

        row = pd.Series({
            'Grantor': 'Seller Name',
            'Grantee': 'Buyer Name',
            'Date': '2024-01-01',
            'Instrument': 'WD',
            'Legal': 'LAKES OF WOODBINE PH II',
        })

        result = transform_row(
            row,
            'Santa Rosa',
            config,
            sub_matcher=ConfiguredSubdivisionMatcher({}),
            builder_matcher=FakeMatcher({}),
            land_banker_matcher=FakeMatcher({}),
        )

        self.assertEqual(result['subdivision'], 'LAKES OF WOODBINE')
        self.assertEqual(result['phase'], '2')
        self.assertEqual(result['parsed_data']['county_parse']['unparsed_lines'], [])

    def test_santarosa_reference_aliases_hidden_pines_addition_variant(self):
        config = dict(self.config)
        config['phase_keywords'] = ['Phase', 'Ph.?', 'PH', 'Unit']

        row = pd.Series({
            'Grantor': 'Seller Name',
            'Grantee': 'Buyer Name',
            'Date': '2024-01-01',
            'Instrument': 'WD',
            'Legal': 'HIDDEN PINES ESTATES 1ST ADDITION 6/A',
        })

        result = transform_row(
            row,
            'Santa Rosa',
            config,
            sub_matcher=ConfiguredSubdivisionMatcher({}),
            builder_matcher=FakeMatcher({}),
            land_banker_matcher=FakeMatcher({}),
        )

        self.assertEqual(result['subdivision'], 'HIDDEN PINES ESTATES')
        self.assertEqual(
            result['parsed_data']['county_parse']['normalized_subdivision_candidates'][0]['details']['alias_source'],
            'HIDDEN PINES ESTATES 1ST ADDITION',
        )

    def test_santarosa_no_ph_abbreviation_does_not_leave_fake_suffix(self):
        config = dict(self.config)
        config['phase_keywords'] = ['Phase', 'Ph.?', 'PH', 'Unit']

        row = pd.Series({
            'Grantor': 'Seller Name',
            'Grantee': 'Buyer Name',
            'Date': '2024-01-01',
            'Instrument': 'WD',
            'Legal': 'CHASE FARMS NO PH 2 1/B',
        })

        result = transform_row(
            row,
            'Santa Rosa',
            config,
            sub_matcher=ConfiguredSubdivisionMatcher({}),
            builder_matcher=FakeMatcher({}),
            land_banker_matcher=FakeMatcher({}),
        )

        self.assertEqual(result['subdivision'], 'CHASE FARMS')
        self.assertIsNone(result['phase'])
        self.assertEqual(result['parsed_data']['county_parse']['no_phase_values'], ['2'])

    def test_santarosa_phase_suffix_letter_stays_with_phase_not_subdivision(self):
        config = dict(self.config)
        config['phase_keywords'] = ['Phase', 'Ph.?', 'PH', 'Unit']

        row = pd.Series({
            'Grantor': 'Seller Name',
            'Grantee': 'Buyer Name',
            'Date': '2024-01-01',
            'Instrument': 'WD',
            'Legal': 'BLACKWATER RESERVE PH I A 30/L',
        })

        result = transform_row(
            row,
            'Santa Rosa',
            config,
            sub_matcher=ConfiguredSubdivisionMatcher({}),
            builder_matcher=FakeMatcher({}),
            land_banker_matcher=FakeMatcher({}),
        )

        self.assertEqual(result['subdivision'], 'BLACKWATER RESERVE')
        self.assertEqual(result['phase'], '1A')

    def test_santarosa_spelled_out_phase_suffix_letter_stays_with_phase(self):
        config = dict(self.config)
        config['phase_keywords'] = ['Phase', 'Ph.?', 'PH', 'Unit']

        row = pd.Series({
            'Grantor': 'Seller Name',
            'Grantee': 'Buyer Name',
            'Date': '2024-01-01',
            'Instrument': 'WD',
            'Legal': 'BLACKWATER RESERVE PHASE ONE A 32/M',
        })

        result = transform_row(
            row,
            'Santa Rosa',
            config,
            sub_matcher=ConfiguredSubdivisionMatcher({}),
            builder_matcher=FakeMatcher({}),
            land_banker_matcher=FakeMatcher({}),
        )

        self.assertEqual(result['subdivision'], 'BLACKWATER RESERVE')
        self.assertEqual(result['phase'], '1A')

    def test_santarosa_reference_aliases_winsor_ridge(self):
        config = dict(self.config)
        config['phase_keywords'] = ['Phase', 'Ph.?', 'PH', 'Unit']

        row = pd.Series({
            'Grantor': 'Seller Name',
            'Grantee': 'Buyer Name',
            'Date': '2024-01-01',
            'Instrument': 'WD',
            'Legal': 'WINSOR RIDGE LOT 41',
        })

        result = transform_row(
            row,
            'Santa Rosa',
            config,
            sub_matcher=ConfiguredSubdivisionMatcher({}),
            builder_matcher=FakeMatcher({}),
            land_banker_matcher=FakeMatcher({}),
        )

        self.assertEqual(result['subdivision'], 'WINDSOR RIDGE')

    def test_legal_description_keeps_full_cleaned_text(self):
        legal = (
            'Lot 1 Example Subdivision with a much longer legal description that used to be cut off '
            'for spreadsheet viewing only'
        )
        row = pd.Series({
            'Grantor': 'Seller Name',
            'Grantee': 'Buyer Name',
            'Date': '2024-01-01',
            'Instrument': 'WD',
            'Legal': legal,
        })

        result = transform_row(
            row,
            'Bay',
            self.config,
            sub_matcher=None,
            builder_matcher=FakeMatcher({}),
            land_banker_matcher=FakeMatcher({}),
        )

        self.assertEqual(result['legal_desc'], legal)
        self.assertEqual(result['legal_raw'], legal)

    def test_subdivision_keeps_full_cleaned_text(self):
        legal = (
            'Example Subdivision With An Intentionally Long Name That Used To Be Clipped For Viewing '
            'But Should Now Stay Whole'
        )
        row = pd.Series({
            'Grantor': 'Seller Name',
            'Grantee': 'Buyer Name',
            'Date': '2024-01-01',
            'Instrument': 'WD',
            'Legal': legal,
        })

        result = transform_row(
            row,
            'Bay',
            self.config,
            sub_matcher=None,
            builder_matcher=FakeMatcher({}),
            land_banker_matcher=FakeMatcher({}),
        )

        self.assertEqual(result['subdivision'], legal)

    def test_hernando_uses_helper_subdivision_and_multi_lot_count(self):
        config = {
            'column_mapping': {
                'grantor': 'Direct Name',
                'grantee': 'Reverse Name',
                'date': 'Record Date',
                'instrument': 'Doc Type',
                'legal': 'Legal',
                'sub': 'Subdivision',
            },
            'phase_keywords': ['Phase', 'PH'],
            'delimiters': [','],
        }
        row = pd.Series({
            'Direct Name': 'Seller Name',
            'Reverse Name': 'Buyer Name',
            'Record Date': '01/02/2024',
            'Doc Type': 'DEED',
            'Legal': 'L Blk Un Sub S T R\nL11,12 Blk389 Un6 SubROYAL HIGHLANDS S T R\n',
            'Lot': 'legalfield_11,12',
            'Block': 'legalfield_389',
            'Unit': 'legalfield_6',
            'Subdivision': 'legalfield_ROYAL HIGHLANDS',
        })
        matcher = ConfiguredSubdivisionMatcher({
            ('ROYAL HIGHLANDS', 'Hernando'): (10, 'ROYAL HIGHLANDS', None),
        })

        result = transform_row(
            row,
            'Hernando',
            config,
            sub_matcher=matcher,
            builder_matcher=FakeMatcher({}),
            land_banker_matcher=FakeMatcher({}),
        )

        self.assertEqual(result['legal_desc'], 'L11,12 Blk389 Un6 SubROYAL HIGHLANDS')
        self.assertEqual(result['subdivision_id'], 10)
        self.assertEqual(result['subdivision'], 'ROYAL HIGHLANDS')
        self.assertEqual(result['lots'], 2)
        self.assertEqual(matcher.calls[0][0], 'ROYAL HIGHLANDS')
        segment = result['parsed_data']['county_parse']['legal_segments'][0]
        self.assertEqual(segment['kind'], 'legal_segment')
        self.assertEqual(segment['raw'], 'L11,12 Blk389 Un6 SubROYAL HIGHLANDS')
        self.assertEqual(segment['lot'], '11,12')
        self.assertEqual(segment['block'], '389')
        self.assertEqual(segment['unit'], '6')
        self.assertEqual(segment['subdivision'], 'ROYAL HIGHLANDS')
        self.assertEqual(segment['subdivision_raw'], 'ROYAL HIGHLANDS')
        self.assertEqual(segment['line_index'], 1)
        self.assertEqual(result['parsed_data']['county_parse']['lot_values'], ['11,12'])
        self.assertEqual(result['parsed_data']['county_parse']['lot_identifiers'], ['11', '12'])
        self.assertEqual(result['parsed_data']['review_reasons'], [])

    def test_hernando_multi_subdivision_rows_are_reviewed(self):
        config = {
            'column_mapping': {
                'grantor': 'Direct Name',
                'grantee': 'Reverse Name',
                'date': 'Record Date',
                'instrument': 'Doc Type',
                'legal': 'Legal',
                'sub': 'Subdivision',
            },
            'phase_keywords': ['Phase', 'PH'],
            'delimiters': [','],
        }
        row = pd.Series({
            'Direct Name': 'Seller Name',
            'Reverse Name': 'Buyer Name',
            'Record Date': '01/11/2024',
            'Doc Type': 'DEED',
            'Legal': 'L Blk Un Sub S T R\nL20 Blk640 Un8 SubROYAL HIGHLANDS S T R\nL3 Blk532 Un7 SubSPRING HILL S T R\n',
            'Lot': 'legalfield_20\n3',
            'Block': 'legalfield_640\n532',
            'Unit': 'legalfield_8\n7',
            'Subdivision': 'legalfield_ROYAL HIGHLANDS\nlegalfield_SPRING HILL',
        })
        matcher = ConfiguredSubdivisionMatcher({})

        result = transform_row(
            row,
            'Hernando',
            config,
            sub_matcher=matcher,
            builder_matcher=FakeMatcher({}),
            land_banker_matcher=FakeMatcher({}),
        )

        self.assertEqual(result['legal_desc'], 'L20 Blk640 Un8 SubROYAL HIGHLANDS; L3 Blk532 Un7 SubSPRING HILL')
        self.assertIsNone(result['subdivision'])
        self.assertTrue(result['review_flag'])
        self.assertEqual(result['lots'], 2)
        self.assertEqual(
            matcher.calls,
            [
                ('ROYAL HIGHLANDS', 'Hernando', ['Phase', 'PH']),
                ('SPRING HILL', 'Hernando', ['Phase', 'PH']),
            ],
        )
        self.assertIn('multiple_subdivision_candidates', result['parsed_data']['review_reasons'])
        self.assertNotIn('subdivision_unmatched', result['parsed_data']['review_reasons'])
        self.assertEqual(result['parsed_data']['preparsed_subdivision'], 'ROYAL HIGHLANDS / SPRING HILL')
        self.assertEqual(len(result['transaction_segments']), 2)
        self.assertEqual(
            [segment['subdivision'] for segment in result['transaction_segments']],
            ['ROYAL HIGHLANDS', 'SPRING HILL'],
        )
        self.assertEqual(
            [segment['review_reasons'] for segment in result['transaction_segments']],
            [['subdivision_unmatched'], ['subdivision_unmatched']],
        )
        self.assertEqual(
            result['parsed_data']['county_parse']['subdivision_values'],
            ['ROYAL HIGHLANDS', 'SPRING HILL'],
        )

    def test_hernando_alias_normalization_uses_canonical_lookup_text(self):
        config = {
            'column_mapping': {
                'grantor': 'Direct Name',
                'grantee': 'Reverse Name',
                'date': 'Record Date',
                'instrument': 'Doc Type',
                'legal': 'Legal',
                'sub': 'Subdivision',
            },
            'phase_keywords': ['Phase', 'PH'],
            'delimiters': [','],
        }
        row = pd.Series({
            'Direct Name': 'Seller Name',
            'Reverse Name': 'Buyer Name',
            'Record Date': '01/11/2024',
            'Doc Type': 'DEED',
            'Legal': 'L Blk Un Sub S T R\nL8 Blk410 Un6 SubROYAI HIGHLANDS S T R\n',
            'Lot': 'legalfield_8',
            'Block': 'legalfield_410',
            'Unit': 'legalfield_6',
            'Subdivision': 'legalfield_ROYAI HIGHLANDS',
        })
        matcher = ConfiguredSubdivisionMatcher({
            ('ROYAL HIGHLANDS', 'Hernando'): (89, 'ROYAL HIGHLANDS', None, []),
        })

        result = transform_row(
            row,
            'Hernando',
            config,
            sub_matcher=matcher,
            builder_matcher=FakeMatcher({}),
            land_banker_matcher=FakeMatcher({}),
        )

        self.assertEqual(result['subdivision_id'], 89)
        self.assertEqual(result['subdivision'], 'ROYAL HIGHLANDS')
        self.assertEqual(matcher.calls, [('ROYAL HIGHLANDS', 'Hernando', ['Phase', 'PH'])])
        self.assertEqual(result['parsed_data']['review_reasons'], [])
        self.assertEqual(len(result['transaction_segments']), 1)
        self.assertEqual(result['transaction_segments'][0]['subdivision_id'], 89)
        self.assertEqual(result['transaction_segments'][0]['review_reasons'], [])

    def test_hernando_same_subdivision_multiple_phases_collapses_base_name(self):
        config = {
            'column_mapping': {
                'grantor': 'Direct Name',
                'grantee': 'Reverse Name',
                'date': 'Record Date',
                'instrument': 'Doc Type',
                'legal': 'Legal',
                'sub': 'Subdivision',
            },
            'phase_keywords': ['Phase', 'Ph.?', 'PH'],
            'delimiters': [','],
        }
        row = pd.Series({
            'Direct Name': 'Seller Name',
            'Reverse Name': 'Buyer Name',
            'Record Date': '01/05/2024',
            'Doc Type': 'DEED',
            'Legal': 'L Blk Un Sub S T R\nL100 Blk Un SubSUNCOAST LANDING PH 2 S T R\nL19 Blk Un SubSUNCOAST LANDING PH 1 S T R\n',
            'Lot': 'legalfield_100\n19',
            'Block': 'legalfield_',
            'Unit': 'legalfield_',
            'Subdivision': 'legalfield_SUNCOAST LANDING PH 1\nSUNCOAST LANDING PH 2',
        })

        result = transform_row(
            row,
            'Hernando',
            config,
            sub_matcher=ConfiguredSubdivisionMatcher({
                ('SUNCOAST LANDING', 'Hernando'): (7, 'SUNCOAST LANDING', None, ['1', '2']),
            }),
            builder_matcher=FakeMatcher({}),
            land_banker_matcher=FakeMatcher({}),
        )

        self.assertEqual(result['subdivision_id'], 7)
        self.assertEqual(result['subdivision'], 'SUNCOAST LANDING')
        self.assertIsNone(result['phase'])
        self.assertEqual(result['lots'], 2)
        self.assertTrue(result['review_flag'])
        self.assertIn('multiple_phase_candidates', result['parsed_data']['review_reasons'])
        self.assertNotIn('multiple_subdivision_candidates', result['parsed_data']['review_reasons'])
        self.assertEqual(
            result['parsed_data']['phase_candidate_values'],
            ['1', '2'],
        )
        self.assertEqual(
            result['parsed_data']['county_parse']['normalized_subdivision_values'],
            ['SUNCOAST LANDING'],
        )
        self.assertEqual(len(result['transaction_segments']), 2)
        self.assertEqual(
            [segment['phase'] for segment in result['transaction_segments']],
            ['1', '2'],
        )
        self.assertEqual(
            [segment['phase_confirmed'] for segment in result['transaction_segments']],
            [True, True],
        )
        self.assertEqual(
            [segment['review_reasons'] for segment in result['transaction_segments']],
            [[], []],
        )

    def test_hernando_reconciles_same_row_subdivision_typos(self):
        config = {
            'column_mapping': {
                'grantor': 'Direct Name',
                'grantee': 'Reverse Name',
                'date': 'Record Date',
                'instrument': 'Doc Type',
                'legal': 'Legal',
                'sub': 'Subdivision',
            },
            'phase_keywords': ['Phase', 'Ph.?', 'PH'],
            'delimiters': [','],
        }
        row = pd.Series({
            'Direct Name': 'Seller Name',
            'Reverse Name': 'Buyer Name',
            'Record Date': '01/12/2024',
            'Doc Type': 'DEED',
            'Legal': 'L Blk Un Sub S T R\nL4 Blk430 Un8 SubSPRNG HILL S T R\nL4 Blk670 Un10 SubSPRING HILL S T R\n',
            'Lot': 'legalfield_4\n4',
            'Block': 'legalfield_430\n670',
            'Unit': 'legalfield_8\n10',
            'Subdivision': 'legalfield_SPRNG HILL\nSPRING HILL',
        })

        result = transform_row(
            row,
            'Hernando',
            config,
            sub_matcher=ConfiguredSubdivisionMatcher({}),
            builder_matcher=FakeMatcher({}),
            land_banker_matcher=FakeMatcher({}),
        )

        self.assertEqual(result['subdivision'], 'SPRING HILL')
        self.assertNotIn('multiple_subdivision_candidates', result['parsed_data']['review_reasons'])
        self.assertEqual(
            result['parsed_data']['county_parse']['normalized_subdivision_values'],
            ['SPRING HILL'],
        )
        self.assertEqual(
            result['parsed_data']['county_parse']['normalized_subdivision_candidates'][0]['details']['alias_source'],
            'SPRNG HILL',
        )

    def test_hernando_extracts_str_from_subdivision_tail(self):
        config = {
            'column_mapping': {
                'grantor': 'Direct Name',
                'grantee': 'Reverse Name',
                'date': 'Record Date',
                'instrument': 'Doc Type',
                'legal': 'Legal',
                'sub': 'Subdivision',
            },
            'phase_keywords': ['Phase', 'PH'],
            'delimiters': [','],
        }
        row = pd.Series({
            'Direct Name': 'Seller Name',
            'Reverse Name': 'Buyer Name',
            'Record Date': '02/02/2024',
            'Doc Type': 'DEED',
            'Legal': 'L Blk Un Sub S T R\nL17 BlkP Un SubHIGHLAND LAKES S25 T22 R17\n',
            'Lot': 'legalfield_17',
            'Block': 'legalfield_P',
            'Unit': 'legalfield_',
            'Subdivision': 'legalfield_HIGHLAND LAKES',
        })
        matcher = ConfiguredSubdivisionMatcher({})

        result = transform_row(
            row,
            'Hernando',
            config,
            sub_matcher=matcher,
            builder_matcher=FakeMatcher({}),
            land_banker_matcher=FakeMatcher({}),
        )

        self.assertEqual(result['subdivision'], 'HIGHLAND LAKES')
        self.assertEqual(result['parsed_data']['county_parse']['section_values'], ['25'])
        self.assertEqual(result['parsed_data']['county_parse']['township_values'], ['22'])
        self.assertEqual(result['parsed_data']['county_parse']['range_values'], ['17'])
        self.assertEqual(result['parsed_data']['county_parse']['effective_legal_segments'][0]['effective_block'], 'P')

    def test_hernando_captures_tract_and_unrecorded_details(self):
        config = {
            'column_mapping': {
                'grantor': 'Direct Name',
                'grantee': 'Reverse Name',
                'date': 'Record Date',
                'instrument': 'Doc Type',
                'legal': 'Legal',
                'sub': 'Subdivision',
            },
            'phase_keywords': ['Phase', 'Ph.?', 'PH'],
            'delimiters': [','],
        }
        row = pd.Series({
            'Direct Name': 'Seller Name',
            'Reverse Name': 'Buyer Name',
            'Record Date': '03/01/2024',
            'Doc Type': 'DEED',
            'Legal': 'L Blk Un Sub S T R\nL Blk Un SubWOODLAND RETREATS UNREC TR 16 S25 T23S R19E\n',
            'Lot': 'legalfield_',
            'Block': 'legalfield_',
            'Unit': 'legalfield_',
            'Subdivision': 'legalfield_WOODLAND RETREATS UNREC TR 16',
        })

        result = transform_row(
            row,
            'Hernando',
            config,
            sub_matcher=ConfiguredSubdivisionMatcher({}),
            builder_matcher=FakeMatcher({}),
            land_banker_matcher=FakeMatcher({}),
        )

        self.assertEqual(result['subdivision'], 'WOODLAND RETREATS')
        self.assertEqual(result['parsed_data']['county_parse']['tract_values'], ['16'])
        self.assertEqual(result['parsed_data']['county_parse']['subdivision_flags'], ['unrecorded'])
        self.assertEqual(result['parsed_data']['county_parse']['base_subdivision_candidates'], ['WOODLAND RETREATS'])
        self.assertEqual(result['parsed_data']['county_parse']['section_values'], ['25'])
        self.assertEqual(result['parsed_data']['county_parse']['township_values'], ['23S'])
        self.assertEqual(result['parsed_data']['county_parse']['range_values'], ['19E'])

    def test_hernando_extracts_unit_number_from_subdivision_text(self):
        config = {
            'column_mapping': {
                'grantor': 'Direct Name',
                'grantee': 'Reverse Name',
                'date': 'Record Date',
                'instrument': 'Doc Type',
                'legal': 'Legal',
                'sub': 'Subdivision',
            },
            'phase_keywords': ['Phase', 'Ph.?', 'PH'],
            'delimiters': [','],
        }
        row = pd.Series({
            'Direct Name': 'Seller Name',
            'Reverse Name': 'Buyer Name',
            'Record Date': '03/03/2024',
            'Doc Type': 'DEED',
            'Legal': 'L Blk Un Sub S T R\nL15 Blk466 Un SubROYAL HIGHLANDS IINIT NO 7\n',
            'Lot': 'legalfield_15',
            'Block': 'legalfield_466',
            'Unit': 'legalfield_',
            'Subdivision': 'legalfield_ROYAL HIGHLANDS IINIT NO 7',
        })

        result = transform_row(
            row,
            'Hernando',
            config,
            sub_matcher=ConfiguredSubdivisionMatcher({}),
            builder_matcher=FakeMatcher({}),
            land_banker_matcher=FakeMatcher({}),
        )

        self.assertEqual(result['subdivision'], 'ROYAL HIGHLANDS')
        self.assertEqual(result['parsed_data']['county_parse']['subdivision_unit_values'], ['7'])
        self.assertEqual(result['parsed_data']['county_parse']['base_subdivision_candidates'], ['ROYAL HIGHLANDS'])

    def test_hernando_captures_pod_details_without_swallowing_subdivision_name(self):
        config = {
            'column_mapping': {
                'grantor': 'Direct Name',
                'grantee': 'Reverse Name',
                'date': 'Record Date',
                'instrument': 'Doc Type',
                'legal': 'Legal',
                'sub': 'Subdivision',
            },
            'phase_keywords': ['Phase', 'Ph.?', 'PH'],
            'delimiters': [','],
        }
        row = pd.Series({
            'Direct Name': 'Seller Name',
            'Reverse Name': 'Buyer Name',
            'Record Date': '03/02/2024',
            'Doc Type': 'DEED',
            'Legal': 'L Blk Un Sub S T R\nL Blk Un SubPOD A LAKE HIDEAWAY PODS A&B\n',
            'Lot': 'legalfield_',
            'Block': 'legalfield_',
            'Unit': 'legalfield_',
            'Subdivision': 'legalfield_POD A LAKE HIDEAWAY PODS A&B',
        })

        result = transform_row(
            row,
            'Hernando',
            config,
            sub_matcher=ConfiguredSubdivisionMatcher({}),
            builder_matcher=FakeMatcher({}),
            land_banker_matcher=FakeMatcher({}),
        )

        self.assertEqual(result['subdivision'], 'POD A LAKE HIDEAWAY PODS A&B')
        self.assertEqual(result['parsed_data']['county_parse']['pod_values'], ['A', 'A & B'])
        self.assertEqual(result['parsed_data']['county_parse']['base_subdivision_candidates'], ['LAKE HIDEAWAY'])

    def test_citrus_keeps_unit_capture_separate_from_phase(self):
        config = {
            'column_mapping': {
                'grantor': 'Grantor',
                'grantee': 'Grantee',
                'date': 'Record Date',
                'instrument': 'Doc Type',
                'legal': 'Legal',
            },
            'phase_keywords': ['Phase', 'Ph.?', 'PH', 'Unit'],
            'delimiters': [','],
        }
        row = pd.Series({
            'Grantor': 'Seller Name',
            'Grantee': 'Buyer Name',
            'Record Date': '01/02/2024',
            'Doc Type': 'DEED',
            'Legal': 'L: 10 Blk: 315 Sub: PINE RIDGE U: 3\nL: 7 Blk: 319 Sub: PINE RIDGE U: 3\n',
        })
        matcher = ConfiguredSubdivisionMatcher({
            ('PINE RIDGE', 'Citrus'): (21, 'PINE RIDGE', None),
        })

        result = transform_row(
            row,
            'Citrus',
            config,
            sub_matcher=matcher,
            builder_matcher=FakeMatcher({}),
            land_banker_matcher=FakeMatcher({}),
        )

        self.assertEqual(result['legal_desc'], 'L: 10 Blk: 315 Sub: PINE RIDGE U: 3; L: 7 Blk: 319 Sub: PINE RIDGE U: 3')
        self.assertEqual(result['subdivision_id'], 21)
        self.assertEqual(result['subdivision'], 'PINE RIDGE')
        self.assertIsNone(result['phase'])
        self.assertEqual(result['lots'], 2)
        self.assertFalse(result['review_flag'])
        self.assertEqual(result['parsed_data']['review_reasons'], [])
        self.assertEqual(matcher.calls[0][0], 'PINE RIDGE')
        self.assertEqual(result['parsed_data']['county_parse']['unit_values'], ['3'])
        self.assertEqual(result['parsed_data']['county_parse']['structured_unit_values'], ['3'])
        self.assertEqual(result['parsed_data']['phase_candidate_values'], [])
        self.assertEqual(result['parsed_data']['county_parse']['normalized_subdivision_values'], ['PINE RIDGE'])

    def test_escambia_captures_geo_and_condo_details(self):
        config = {
            'column_mapping': {
                'grantor': 'Direct Name',
                'grantee': 'Reverse Name',
                'date': 'Record Date',
                'instrument': 'Doc Type',
                'legal': 'Legal',
            },
            'phase_keywords': ['Phase', 'Ph.?', 'PH', 'Unit'],
            'delimiters': [','],
        }
        row = pd.Series({
            'Direct Name': 'Seller Name',
            'Reverse Name': 'Buyer Name',
            'Record Date': '01/03/2024',
            'Doc Type': 'DEED',
            'Legal': 'LOT:31 BLK:A SUB:TURTLE CREEK\nSEC:16 TWP:2S RGE:30W\nUNI:D 303 CON:MARINER\n',
        })

        result = transform_row(
            row,
            'Escambia',
            config,
            sub_matcher=ConfiguredSubdivisionMatcher({}),
            builder_matcher=FakeMatcher({}),
            land_banker_matcher=FakeMatcher({}),
        )

        self.assertEqual(result['subdivision'], 'TURTLE CREEK')
        self.assertEqual(result['lots'], 1)
        self.assertEqual(result['parsed_data']['county_parse']['section_values'], ['16'])
        self.assertEqual(result['parsed_data']['county_parse']['township_values'], ['2S'])
        self.assertEqual(result['parsed_data']['county_parse']['range_values'], ['30W'])
        self.assertEqual(result['parsed_data']['county_parse']['condo_values'], ['MARINER'])
        self.assertEqual(result['parsed_data']['county_parse']['unit_values'], ['D 303'])

    def test_bay_parses_freeform_legal_and_normalizes_subdivision_alias(self):
        config = {
            'column_mapping': {
                'grantor': 'Grantor',
                'grantee': 'Grantee',
                'date': 'Record Date Search',
                'instrument': 'Doc Type',
                'legal': 'Legal',
            },
            'phase_keywords': ['Phase', 'Ph.?', 'PH', 'Unit'],
            'delimiters': [','],
        }
        row = pd.Series({
            'Grantor': 'Seller Name',
            'Grantee': 'Buyer Name',
            'Record Date Search': '01/02/2024',
            'Doc Type': 'DEED',
            'Legal': '07384-206-000 | LOT 4 BLK 13 EASTBAY PH IA\n',
        })
        matcher = ConfiguredSubdivisionMatcher({
            ('EAST BAY', 'Bay'): (31, 'EAST BAY', None),
        })

        result = transform_row(
            row,
            'Bay',
            config,
            sub_matcher=matcher,
            builder_matcher=FakeMatcher({}),
            land_banker_matcher=FakeMatcher({}),
        )

        self.assertEqual(result['legal_desc'], 'LOT 4 BLK 13 EASTBAY PH IA')
        self.assertEqual(result['subdivision_id'], 31)
        self.assertEqual(result['subdivision'], 'EAST BAY')
        self.assertEqual(result['phase'], '1A')
        self.assertEqual(result['lots'], 1)
        self.assertTrue(result['review_flag'])
        self.assertIn('phase_not_confirmed_by_lookup', result['parsed_data']['review_reasons'])
        self.assertEqual(matcher.calls[0][0], 'EAST BAY')
        self.assertEqual(result['parsed_data']['county_parse']['parcel_references'], ['07384-206-000'])
        self.assertEqual(result['parsed_data']['county_parse']['structured_block_values'], ['13'])

    def test_walton_parses_freeform_lot_ranges(self):
        config = {
            'column_mapping': {
                'grantor': 'Grantor',
                'grantee': 'Grantee',
                'date': 'Record Date',
                'instrument': 'Doc Type',
                'legal': 'Legal',
            },
            'phase_keywords': ['Phase', 'Ph.?', 'PH', 'Unit'],
            'delimiters': [','],
        }
        row = pd.Series({
            'Grantor': 'Seller Name',
            'Grantee': 'Buyer Name',
            'Record Date': '01/03/2024',
            'Doc Type': 'DEED',
            'Legal': 'Legal LOTS 80-82 MAGNOLIA AT THE BLUFFS PH 1\n',
        })

        result = transform_row(
            row,
            'Walton',
            config,
            sub_matcher=ConfiguredSubdivisionMatcher({}),
            builder_matcher=FakeMatcher({}),
            land_banker_matcher=FakeMatcher({}),
        )

        self.assertEqual(result['legal_desc'], 'LOTS 80-82 MAGNOLIA AT THE BLUFFS PH 1')
        self.assertEqual(result['subdivision'], 'MAGNOLIA AT THE BLUFFS')
        self.assertEqual(result['phase'], '1')
        self.assertEqual(result['lots'], 3)
        self.assertEqual(result['parsed_data']['county_parse']['lot_values'], ['80-82'])
        self.assertEqual(result['parsed_data']['county_parse']['lot_identifiers'], ['80', '81', '82'])

    def test_bay_captures_unit_building_and_locker_without_using_phase(self):
        config = {
            'column_mapping': {
                'grantor': 'Grantor',
                'grantee': 'Grantee',
                'date': 'Record Date Search',
                'instrument': 'Doc Type',
                'legal': 'Legal',
            },
            'phase_keywords': ['Phase', 'Ph.?', 'PH', 'Unit'],
            'delimiters': [','],
        }
        row = pd.Series({
            'Grantor': 'Seller Name',
            'Grantee': 'Buyer Name',
            'Record Date Search': '01/04/2025',
            'Doc Type': 'DEED',
            'Legal': 'UNIT 13 & STORAGE LOCKER NO 4-59 TIDEWATER BEACH II\n',
        })

        result = transform_row(
            row,
            'Bay',
            config,
            sub_matcher=ConfiguredSubdivisionMatcher({}),
            builder_matcher=FakeMatcher({}),
            land_banker_matcher=FakeMatcher({}),
        )

        self.assertEqual(result['subdivision'], 'TIDEWATER BEACH II')
        self.assertIsNone(result['phase'])
        self.assertEqual(result['parsed_data']['phase_candidate_values'], [])
        self.assertEqual(result['parsed_data']['county_parse']['unit_values'], ['13'])
        self.assertEqual(result['parsed_data']['county_parse']['structured_storage_locker_values'], ['4-59'])

    def test_walton_keeps_unit_designator_separate_from_phase(self):
        config = {
            'column_mapping': {
                'grantor': 'Grantor',
                'grantee': 'Grantee',
                'date': 'Record Date',
                'instrument': 'Doc Type',
                'legal': 'Legal',
            },
            'phase_keywords': ['Phase', 'Ph.?', 'PH', 'Unit'],
            'delimiters': [','],
        }
        row = pd.Series({
            'Grantor': 'Seller Name',
            'Grantee': 'Buyer Name',
            'Record Date': '01/05/2025',
            'Doc Type': 'DEED',
            'Legal': 'Legal LOT 11 & 12 UNIT 1 OF OAKWOOD HILLS\n',
        })

        result = transform_row(
            row,
            'Walton',
            config,
            sub_matcher=ConfiguredSubdivisionMatcher({}),
            builder_matcher=FakeMatcher({}),
            land_banker_matcher=FakeMatcher({}),
        )

        self.assertEqual(result['subdivision'], 'OAKWOOD HILLS')
        self.assertIsNone(result['phase'])
        self.assertEqual(result['lots'], 2)
        self.assertEqual(result['parsed_data']['phase_candidate_values'], [])
        self.assertEqual(result['parsed_data']['county_parse']['structured_unit_values'], ['1'])

    def test_bay_aliases_breakfast_point_variant(self):
        config = {
            'column_mapping': {
                'grantor': 'Grantor',
                'grantee': 'Grantee',
                'date': 'Record Date Search',
                'instrument': 'Doc Type',
                'legal': 'Legal',
            },
            'phase_keywords': ['Phase', 'Ph.?', 'PH', 'Unit'],
            'delimiters': [','],
        }
        row = pd.Series({
            'Grantor': 'Seller Name',
            'Grantee': 'Buyer Name',
            'Record Date Search': '02/09/2024',
            'Doc Type': 'DEED',
            'Legal': 'L 234 BREAKFAST PIONT EAST PH 1C\n',
        })

        result = transform_row(
            row,
            'Bay',
            config,
            sub_matcher=ConfiguredSubdivisionMatcher({}),
            builder_matcher=FakeMatcher({}),
            land_banker_matcher=FakeMatcher({}),
        )

        self.assertEqual(result['subdivision'], 'BREAKFAST POINT EAST')
        self.assertEqual(result['phase'], '1C')
        self.assertEqual(
            result['parsed_data']['county_parse']['normalized_subdivision_candidates'][0]['details']['alias_source'],
            'BREAKFAST PIONT EAST',
        )

    def test_bay_aliases_caballeros_estates_variant(self):
        config = {
            'column_mapping': {
                'grantor': 'Grantor',
                'grantee': 'Grantee',
                'date': 'Record Date Search',
                'instrument': 'Doc Type',
                'legal': 'Legal',
            },
            'phase_keywords': ['Phase', 'Ph.?', 'PH', 'Unit'],
            'delimiters': [','],
        }
        row = pd.Series({
            'Grantor': 'Seller Name',
            'Grantee': 'Buyer Name',
            'Record Date Search': '07/01/2024',
            'Doc Type': 'DEED',
            'Legal': 'LOT 74 CABELLEROS ESTATES AT HOMBRE\n',
        })

        result = transform_row(
            row,
            'Bay',
            config,
            sub_matcher=ConfiguredSubdivisionMatcher({}),
            builder_matcher=FakeMatcher({}),
            land_banker_matcher=FakeMatcher({}),
        )

        self.assertEqual(result['subdivision'], 'CABALLEROS ESTATES AT HOMBRE')
        self.assertIsNone(result['phase'])
        self.assertEqual(
            result['parsed_data']['county_parse']['normalized_subdivision_candidates'][0]['details']['alias_source'],
            'CABELLEROS ESTATES AT HOMBRE',
        )

    def test_walton_aliases_watersound_origins_naturewalk_variant(self):
        config = {
            'column_mapping': {
                'grantor': 'Grantor',
                'grantee': 'Grantee',
                'date': 'Record Date',
                'instrument': 'Doc Type',
                'legal': 'Legal',
            },
            'phase_keywords': ['Phase', 'Ph.?', 'PH', 'Unit'],
            'delimiters': [','],
        }
        row = pd.Series({
            'Grantor': 'Seller Name',
            'Grantee': 'Buyer Name',
            'Record Date': '01/29/2024',
            'Doc Type': 'DEED',
            'Legal': 'Legal LOT 246 WATERSOUNDS ORIGINS NATUREWALK PH 3\n',
        })

        result = transform_row(
            row,
            'Walton',
            config,
            sub_matcher=ConfiguredSubdivisionMatcher({}),
            builder_matcher=FakeMatcher({}),
            land_banker_matcher=FakeMatcher({}),
        )

        self.assertEqual(result['subdivision'], 'WATERSOUND ORIGINS NATUREWALK')
        self.assertEqual(result['phase'], '3')
        self.assertEqual(
            result['parsed_data']['county_parse']['normalized_subdivision_candidates'][0]['details']['alias_source'],
            'WATERSOUNDS ORIGINS NATUREWALK',
        )

    def test_citrus_aliases_sportsmens_park(self):
        config = {
            'column_mapping': {
                'grantor': 'Grantor',
                'grantee': 'Grantee',
                'date': 'Record Date',
                'instrument': 'Doc Type',
                'legal': 'Legal',
            },
            'phase_keywords': ['Phase', 'Ph.?', 'PH'],
            'delimiters': [','],
        }
        row = pd.Series({
            'Grantor': 'Seller Name',
            'Grantee': 'Buyer Name',
            'Record Date': '06/25/2024',
            'Doc Type': 'DEED',
            'Legal': 'L: 40 Sub: SPORTMENS PARK\n',
        })

        result = transform_row(
            row,
            'Citrus',
            config,
            sub_matcher=ConfiguredSubdivisionMatcher({}),
            builder_matcher=FakeMatcher({}),
            land_banker_matcher=FakeMatcher({}),
        )

        self.assertEqual(result['subdivision'], 'SPORTSMENS PARK')
        self.assertIsNone(result['phase'])
        self.assertEqual(
            result['parsed_data']['county_parse']['normalized_subdivision_candidates'][0]['details']['alias_source'],
            'SPORTMENS PARK',
        )

    def test_escambia_aliases_pecan_valley(self):
        config = {
            'column_mapping': {
                'grantor': 'Direct Name',
                'grantee': 'Reverse Name',
                'date': 'Record Date',
                'instrument': 'Doc Type',
                'legal': 'Legal',
            },
            'phase_keywords': ['Phase', 'Ph.?', 'PH'],
            'delimiters': [','],
        }
        row = pd.Series({
            'Direct Name': 'Seller Name',
            'Reverse Name': 'Buyer Name',
            'Record Date': '04/02/2024',
            'Doc Type': 'WARRANTY DEED',
            'Legal': 'LOT:32 BLK:B SUB:PEACAN VALLEY\n',
        })

        result = transform_row(
            row,
            'Escambia',
            config,
            sub_matcher=ConfiguredSubdivisionMatcher({}),
            builder_matcher=FakeMatcher({}),
            land_banker_matcher=FakeMatcher({}),
        )

        self.assertEqual(result['subdivision'], 'PECAN VALLEY')
        self.assertIsNone(result['phase'])
        self.assertEqual(
            result['parsed_data']['county_parse']['normalized_subdivision_candidates'][0]['details']['alias_source'],
            'PEACAN VALLEY',
        )

    def test_escambia_aliases_sanctuary(self):
        config = {
            'column_mapping': {
                'grantor': 'Direct Name',
                'grantee': 'Reverse Name',
                'date': 'Record Date',
                'instrument': 'Doc Type',
                'legal': 'Legal',
            },
            'phase_keywords': ['Phase', 'Ph.?', 'PH'],
            'delimiters': [','],
        }
        row = pd.Series({
            'Direct Name': 'Seller Name',
            'Reverse Name': 'Buyer Name',
            'Record Date': '10/23/2025',
            'Doc Type': 'WARRANTY DEED',
            'Legal': 'LOT:14 BLK:B SUB:SANTUARY PH 1\n',
        })

        result = transform_row(
            row,
            'Escambia',
            config,
            sub_matcher=ConfiguredSubdivisionMatcher({}),
            builder_matcher=FakeMatcher({}),
            land_banker_matcher=FakeMatcher({}),
        )

        self.assertEqual(result['subdivision'], 'SANCTUARY')
        self.assertEqual(result['phase'], '1')
        self.assertEqual(
            result['parsed_data']['county_parse']['normalized_subdivision_candidates'][0]['details']['alias_source'],
            'SANTUARY',
        )


if __name__ == '__main__':
    unittest.main()
