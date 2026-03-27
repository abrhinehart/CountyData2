import unittest

import pandas as pd

from processors.county_parsers import (
    parse_bay_row,
    parse_citrus_row,
    parse_escambia_row,
    parse_hernando_row,
    parse_hernando_segment_line,
    parse_walton_row,
)


class HernandoParserTests(unittest.TestCase):
    def test_parse_hernando_segment_line_extracts_categories(self):
        result = parse_hernando_segment_line('L11,12 Blk389 Un6 SubROYAL HIGHLANDS S T R')

        self.assertEqual(result['kind'], 'legal_segment')
        self.assertEqual(result['lot'], '11,12')
        self.assertEqual(result['block'], '389')
        self.assertEqual(result['unit'], '6')
        self.assertEqual(result['subdivision_raw'], 'ROYAL HIGHLANDS')
        self.assertEqual(result['subdivision'], 'ROYAL HIGHLANDS')
        self.assertIsNone(result['section'])
        self.assertIsNone(result['township'])
        self.assertIsNone(result['range'])
        self.assertEqual(result['raw'], 'L11,12 Blk389 Un6 SubROYAL HIGHLANDS')

    def test_parse_hernando_segment_line_detects_parcel_reference(self):
        result = parse_hernando_segment_line('R3232317510006090180')

        self.assertEqual(result['kind'], 'parcel_reference')
        self.assertEqual(result['parcel_reference'], 'R3232317510006090180')

    def test_parse_hernando_segment_line_allows_blank_subdivision(self):
        result = parse_hernando_segment_line('L131 - 135 Blk Un Sub S T R')

        self.assertEqual(result['kind'], 'legal_segment')
        self.assertEqual(result['lot'], '131 - 135')
        self.assertIsNone(result['block'])
        self.assertIsNone(result['unit'])
        self.assertIsNone(result['subdivision'])
        self.assertIsNone(result['section'])
        self.assertIsNone(result['township'])
        self.assertIsNone(result['range'])

    def test_parse_hernando_segment_line_extracts_str_tail(self):
        result = parse_hernando_segment_line('L17 BlkP Un SubHIGHLAND LAKES S25 T22 R17')

        self.assertEqual(result['kind'], 'legal_segment')
        self.assertEqual(result['lot'], '17')
        self.assertEqual(result['block'], 'P')
        self.assertIsNone(result['unit'])
        self.assertEqual(result['subdivision_raw'], 'HIGHLAND LAKES S25 T22 R17')
        self.assertEqual(result['subdivision'], 'HIGHLAND LAKES')
        self.assertEqual(result['section'], '25')
        self.assertEqual(result['township'], '22')
        self.assertEqual(result['range'], '17')

    def test_parse_hernando_row_merges_helper_and_segment_capture(self):
        row = pd.Series({
            'Legal': (
                'L Blk Un Sub S T R\n'
                'R3232317510006090180\n'
                'L4 & 5 Blk487 Un7 SubROYAL HIGHLANDS S T R\n'
            ),
            'Lot': 'legalfield_4 & 5',
            'Block': 'legalfield_487',
            'Unit': 'legalfield_7',
            'Subdivision': 'legalfield_ROYAL HIGHLANDS',
        })
        cols = {
            'legal': 'Legal',
            'lot': 'Lot',
            'block': 'Block',
            'unit': 'Unit',
            'sub': 'Subdivision',
        }

        result = parse_hernando_row(row, cols)

        self.assertEqual(result['legal'], 'R3232317510006090180; L4 & 5 Blk487 Un7 SubROYAL HIGHLANDS')
        self.assertEqual(result['raw_legal_lines'][0], 'L Blk Un Sub S T R')
        self.assertTrue(result['header_present'])
        self.assertEqual(result['parcel_references'], ['R3232317510006090180'])
        self.assertEqual(result['lot_values'], ['4 & 5'])
        self.assertEqual(result['block_values'], ['487'])
        self.assertEqual(result['unit_values'], ['7'])
        self.assertEqual(result['subdivision_values'], ['ROYAL HIGHLANDS'])
        self.assertEqual(result['lot_identifiers'], ['4', '5'])
        self.assertEqual(result['unit_identifiers'], ['7'])
        self.assertEqual(result['lot_count'], 2)
        self.assertEqual(result['lot_count_source'], 'helper')
        self.assertEqual(len(result['legal_segments']), 1)
        self.assertEqual(len(result['effective_legal_segments']), 1)
        self.assertEqual(
            result['effective_legal_segments'][0]['sources'],
            {
                'lot': 'legal',
                'block': 'legal',
                'unit': 'legal',
                'subdivision': 'legal',
            },
        )
        self.assertEqual(result['helper_fields']['lot']['values'], ['4 & 5'])

    def test_parse_hernando_row_aligns_helper_values_into_effective_segments(self):
        row = pd.Series({
            'Legal': (
                'L Blk Un Sub S T R\n'
                'L193 Blk Un SubCALDERA PHS 3 & 4 S T R\n'
                'L195 Blk Un Sub S T R\n'
                'L205 Blk Un SubCALDERA PHS 3 & 4 S T R\n'
            ),
            'Lot': 'legalfield_193\n195\n205',
            'Block': 'legalfield_',
            'Unit': 'legalfield_',
            'Subdivision': 'legalfield_CALDERA PHS 3 & 4',
        })
        cols = {
            'legal': 'Legal',
            'lot': 'Lot',
            'block': 'Block',
            'unit': 'Unit',
            'sub': 'Subdivision',
        }

        result = parse_hernando_row(row, cols)

        self.assertEqual(result['unparsed_lines'], [])
        self.assertEqual(result['subdivision_values'], ['CALDERA PHS 3 & 4'])
        self.assertEqual(result['lot_identifiers'], ['193', '195', '205'])
        self.assertEqual(result['lot_count'], 3)
        self.assertEqual(
            [segment['effective_subdivision'] for segment in result['effective_legal_segments']],
            ['CALDERA PHS 3 & 4', 'CALDERA PHS 3 & 4', 'CALDERA PHS 3 & 4'],
        )
        self.assertEqual(
            result['effective_legal_segments'][1]['sources']['subdivision'],
            'helper_shared',
        )


class LabeledCountyParserTests(unittest.TestCase):
    def test_parse_citrus_row_captures_labeled_segments_and_special_lines(self):
        row = pd.Series({
            'Legal': (
                'L: 10 Blk: 315 Sub: PINE RIDGE U: 3\n'
                'PT LTS 30-31 & 43\n'
                'S: 16 T: 19S R: 21E\n'
                'REDACTION APPLIED PURSUANT TO FLORIDA PUBLIC RECORDS LAWS\n'
            ),
        })
        cols = {'legal': 'Legal'}

        result = parse_citrus_row(row, cols)

        self.assertEqual(result['lot_values'], ['10'])
        self.assertEqual(result['block_values'], ['315'])
        self.assertEqual(result['unit_values'], ['3'])
        self.assertEqual(result['subdivision_values'], ['PINE RIDGE'])
        self.assertEqual(result['part_lot_values'], ['30-31 & 43'])
        self.assertEqual(result['section_values'], ['16'])
        self.assertEqual(result['township_values'], ['19S'])
        self.assertEqual(result['range_values'], ['21E'])
        self.assertEqual(result['lot_identifiers'], ['10'])
        self.assertEqual(result['lot_count'], 1)
        self.assertTrue(result['redacted'])
        self.assertEqual(
            result['redaction_lines'],
            ['REDACTION APPLIED PURSUANT TO FLORIDA PUBLIC RECORDS LAWS'],
        )
        self.assertEqual(result['labels_present'], ['L', 'BLK', 'SUB', 'U', 'S', 'T', 'R'])

    def test_parse_escambia_row_captures_geo_and_condo_fields(self):
        row = pd.Series({
            'Legal': (
                'LOT:31 BLK:A SUB:TURTLE CREEK\n'
                'SEC:16 TWP:2S RGE:30W\n'
                'UNI:D 303 CON:MARINER\n'
            ),
        })
        cols = {'legal': 'Legal'}

        result = parse_escambia_row(row, cols)

        self.assertEqual(result['lot_values'], ['31'])
        self.assertEqual(result['block_values'], ['A'])
        self.assertEqual(result['subdivision_values'], ['TURTLE CREEK'])
        self.assertEqual(result['section_values'], ['16'])
        self.assertEqual(result['township_values'], ['2S'])
        self.assertEqual(result['range_values'], ['30W'])
        self.assertEqual(result['unit_values'], ['D 303'])
        self.assertEqual(result['condo_values'], ['MARINER'])
        self.assertEqual(result['lot_identifiers'], ['31'])
        self.assertEqual(result['lot_count'], 1)

    def test_parse_citrus_row_captures_case_reference_and_metes_bounds_note(self):
        row = pd.Series({
            'Legal': (
                '2023 CA 000798 A\n'
                'COM AT SW COR ETC\n'
                'Sub: RUTLAND ESTATES U: 1\n'
            ),
        })
        cols = {'legal': 'Legal'}

        result = parse_citrus_row(row, cols)

        self.assertEqual(result['case_references'], ['2023 CA 000798 A'])
        self.assertEqual(result['metes_bounds_notes'], ['COM AT SW COR ETC'])
        self.assertEqual(result['unparsed_lines'], [])
        self.assertEqual(result['subdivision_values'], ['RUTLAND ESTATES'])
        self.assertEqual(result['unit_values'], ['1'])


class FreeformCountyParserTests(unittest.TestCase):
    def test_parse_bay_row_captures_parcel_lot_block_and_subdivision(self):
        row = pd.Series({
            'Legal': '07384-206-000 | LOT 4 BLK 13 EASTBAY PH IA\n',
        })
        cols = {'legal': 'Legal'}

        result = parse_bay_row(row, cols)

        self.assertEqual(result['legal'], 'LOT 4 BLK 13 EASTBAY PH IA')
        self.assertEqual(result['parcel_references'], ['07384-206-000'])
        self.assertEqual(result['lot_values'], ['4'])
        self.assertEqual(result['block_values'], ['13'])
        self.assertEqual(result['subdivision_values'], ['EASTBAY PH IA'])
        self.assertEqual(result['lot_identifiers'], ['4'])
        self.assertEqual(result['lot_count'], 1)

    def test_parse_walton_row_handles_prefix_and_lot_ranges(self):
        row = pd.Series({
            'Legal': 'Legal LOTS 80-82 MAGNOLIA AT THE BLUFFS PH 1\n',
        })
        cols = {'legal': 'Legal'}

        result = parse_walton_row(row, cols)

        self.assertEqual(result['legal'], 'LOTS 80-82 MAGNOLIA AT THE BLUFFS PH 1')
        self.assertEqual(result['lot_values'], ['80-82'])
        self.assertEqual(result['subdivision_values'], ['MAGNOLIA AT THE BLUFFS PH 1'])
        self.assertEqual(result['lot_identifiers'], ['80', '81', '82'])
        self.assertEqual(result['lot_count'], 3)

    def test_parse_bay_row_captures_unit_building_and_storage_details(self):
        row = pd.Series({
            'Legal': (
                'UNIT 36 BLDG A ENDLESS SUMMER I\n'
                'UNIT 13 & STORAGE LOCKER NO 4-59 TIDEWATER BEACH II\n'
            ),
        })
        cols = {'legal': 'Legal'}

        result = parse_bay_row(row, cols)

        self.assertEqual(result['unit_values'], ['36', '13'])
        self.assertEqual(result['building_values'], ['A'])
        self.assertEqual(result['storage_locker_values'], ['4-59'])
        self.assertEqual(result['subdivision_values'], ['ENDLESS SUMMER I', 'TIDEWATER BEACH II'])

    def test_parse_walton_row_captures_unit_designator_without_promoting_phase(self):
        row = pd.Series({
            'Legal': 'Legal LOT 11 & 12 UNIT 1 OF OAKWOOD HILLS\n',
        })
        cols = {'legal': 'Legal'}

        result = parse_walton_row(row, cols)

        self.assertEqual(result['lot_values'], ['11 & 12'])
        self.assertEqual(result['unit_values'], ['1'])
        self.assertEqual(result['subdivision_values'], ['OAKWOOD HILLS'])
        self.assertEqual(result['lot_identifiers'], ['11', '12'])


if __name__ == '__main__':
    unittest.main()
