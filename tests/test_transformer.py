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
        self.assertEqual(matcher.calls[0][0], 'BASSWOOD PHASE 2')

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
        self.assertEqual(result['subdivision'], 'ROYAL HIGHLANDS / SPRING HILL')
        self.assertTrue(result['review_flag'])
        self.assertEqual(result['lots'], 2)
        self.assertEqual(matcher.calls, [])
        self.assertIn('multiple_subdivision_candidates', result['parsed_data']['review_reasons'])
        self.assertEqual(
            result['parsed_data']['county_parse']['subdivision_values'],
            ['ROYAL HIGHLANDS', 'SPRING HILL'],
        )

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
            sub_matcher=ConfiguredSubdivisionMatcher({}),
            builder_matcher=FakeMatcher({}),
            land_banker_matcher=FakeMatcher({}),
        )

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
