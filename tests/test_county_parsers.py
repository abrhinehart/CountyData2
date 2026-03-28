import unittest

import pandas as pd

from processors.county_parsers import (
    parse_bay_row,
    parse_citrus_row,
    parse_escambia_row,
    parse_hernando_row,
    parse_hernando_segment_line,
    parse_marion_row,
    parse_okaloosa_row,
    parse_okeechobee_row,
    parse_santarosa_row,
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

    def test_parse_okaloosa_row_captures_subdivision_lot_and_parcel(self):
        row = pd.Series({
            'Legal': 'ASHTON VIEW SUBDIVISION Lot: 26 , Parcel: 25-4N-23-1050-0000-0260',
        })
        cols = {'legal': 'Legal'}

        result = parse_okaloosa_row(row, cols)

        self.assertEqual(result['subdivision_values'], ['ASHTON VIEW SUBDIVISION'])
        self.assertEqual(result['lot_values'], ['26'])
        self.assertEqual(result['parcel_references'], ['25-4N-23-1050-0000-0260'])
        self.assertEqual(result['lot_identifiers'], ['26'])
        self.assertEqual(result['lot_count'], 1)

    def test_parse_okaloosa_row_captures_unit_and_phase_source_text(self):
        row = pd.Series({
            'Legal': 'RIDGEWAY LANDING PHASE 2 Unit: 101 , Parcel: 05-3N-23-1500-0000-1010',
        })
        cols = {'legal': 'Legal'}

        result = parse_okaloosa_row(row, cols)

        self.assertEqual(result['subdivision_values'], ['RIDGEWAY LANDING PHASE 2'])
        self.assertEqual(result['unit_values'], ['101'])
        self.assertEqual(result['parcel_references'], ['05-3N-23-1500-0000-1010'])
        self.assertEqual(result['lot_count'], None)

    def test_parse_okaloosa_row_captures_subdivision_only_clause_before_parcel(self):
        row = pd.Series({
            'Legal': 'PATRIOT RIDGE PHASE PHASE 6 , Parcel: 33-3N-23-2810-0000-2440',
        })
        cols = {'legal': 'Legal'}

        result = parse_okaloosa_row(row, cols)

        self.assertEqual(result['subdivision_values'], ['PATRIOT RIDGE PHASE PHASE 6'])
        self.assertEqual(result['parcel_references'], ['33-3N-23-2810-0000-2440'])
        self.assertEqual(result['unparsed_lines'], [])

    def test_parse_okaloosa_row_captures_metes_bounds_fields(self):
        row = pd.Series({
            'Legal': 'Section: 29 Township: 4NRange: 22Legal Remarks: COMM AT SWC OF , Parcel: 29-4N-22-0000-0001-031A',
        })
        cols = {'legal': 'Legal'}

        result = parse_okaloosa_row(row, cols)

        self.assertEqual(result['subdivision_values'], [])
        self.assertEqual(result['section_values'], ['29'])
        self.assertEqual(result['township_values'], ['4N'])
        self.assertEqual(result['range_values'], ['22'])
        self.assertEqual(result['legal_remarks_values'], ['COMM AT SWC OF'])
        self.assertEqual(result['parcel_references'], ['29-4N-22-0000-0001-031A'])


class FreeformCountyParserTests(unittest.TestCase):
    def test_parse_marion_row_captures_lot_block_subdivision_and_unit(self):
        row = pd.Series({
            'Legal': 'LS 4-8 BK 208 OBH U-14/O',
        })
        cols = {'legal': 'Legal'}

        result = parse_marion_row(row, cols)

        self.assertEqual(result['lot_values'], ['4-8'])
        self.assertEqual(result['block_values'], ['208'])
        self.assertEqual(result['unit_values'], ['14/O'])
        self.assertEqual(result['subdivision_values'], ['OBH'])
        self.assertEqual(result['lot_identifiers'], ['4', '5', '6', '7', '8'])
        self.assertEqual(result['lot_count'], 5)

    def test_parse_marion_row_captures_tract_and_common_area_code(self):
        row = pd.Series({
            'Legal': 'TRACTS A-F SCBDW SUNDANCE PH 3/O',
        })
        cols = {'legal': 'Legal'}

        result = parse_marion_row(row, cols)

        self.assertEqual(result['tract_values'], ['A-F'])
        self.assertEqual(result['common_area_codes'], ['SCBDW'])
        self.assertEqual(result['subdivision_values'], ['SUNDANCE PH 3/O'])

    def test_parse_marion_row_captures_partial_lot_and_partial_subdivision(self):
        row = pd.Series({
            'Legal': 'PT LT 12 BK 4 RH U-1\nPT W OAK PH 1',
        })
        cols = {'legal': 'Legal'}

        result = parse_marion_row(row, cols)

        self.assertEqual(result['lot_values'], ['12'])
        self.assertEqual(result['partial_lot_values'], ['12'])
        self.assertEqual(result['partial_lot_identifiers'], ['12'])
        self.assertEqual(result['block_values'], ['4'])
        self.assertEqual(result['unit_values'], ['1'])
        self.assertEqual(result['subdivision_values'], ['RH', 'W OAK PH 1'])
        self.assertIn('partial_subdivision', result['subdivision_flags'])

    def test_parse_marion_row_handles_trs_abbreviation_and_common_area_code(self):
        row = pd.Series({
            'Legal': 'TRS A-E SCBDW SARATOGA PH 2/O',
        })
        cols = {'legal': 'Legal'}

        result = parse_marion_row(row, cols)

        self.assertEqual(result['tract_values'], ['A-E'])
        self.assertEqual(result['common_area_codes'], ['SCBDW'])
        self.assertEqual(result['subdivision_values'], ['SARATOGA PH 2/O'])

    def test_parse_santarosa_row_captures_slash_shorthand(self):
        row = pd.Series({
            'Legal': 'EMMALINE GARDENS 34/B',
        })
        cols = {'legal': 'Legal'}

        result = parse_santarosa_row(row, cols)

        self.assertEqual(result['lot_values'], ['34'])
        self.assertEqual(result['block_values'], ['B'])
        self.assertEqual(result['subdivision_values'], ['EMMALINE GARDENS'])
        self.assertEqual(result['lot_identifiers'], ['34'])
        self.assertEqual(result['lot_count'], 1)

    def test_parse_santarosa_row_captures_str_prefix_and_unrecorded_lot(self):
        row = pd.Series({
            'Legal': '14-3N-29W; 15-3N-29W THREE HOLLOW EAST LOT 33 UNREC',
        })
        cols = {'legal': 'Legal'}

        result = parse_santarosa_row(row, cols)

        self.assertEqual(result['parcel_references'], ['14-3N-29W', '15-3N-29W'])
        self.assertEqual(result['section_values'], ['14', '15'])
        self.assertEqual(result['township_values'], ['3N'])
        self.assertEqual(result['range_values'], ['29W'])
        self.assertEqual(result['lot_values'], ['33'])
        self.assertEqual(result['subdivision_values'], ['THREE HOLLOW EAST'])
        self.assertIn('unrecorded', result['subdivision_flags'])

    def test_parse_santarosa_row_captures_unit_without_promoting_phase(self):
        row = pd.Series({
            'Legal': 'TIGER POINT VILLAGE UNIT 7 4/C',
        })
        cols = {'legal': 'Legal'}

        result = parse_santarosa_row(row, cols)

        self.assertEqual(result['lot_values'], ['4'])
        self.assertEqual(result['block_values'], ['C'])
        self.assertEqual(result['unit_values'], ['7'])
        self.assertEqual(result['subdivision_values'], ['TIGER POINT VILLAGE'])
        self.assertEqual(result['lot_count'], 1)

    def test_parse_santarosa_row_captures_partial_tract(self):
        row = pd.Series({
            'Legal': 'HOLLEY BY THE SEA 1ST CORR & AMEND PT TRACT DDD',
        })
        cols = {'legal': 'Legal'}

        result = parse_santarosa_row(row, cols)

        self.assertEqual(result['tract_values'], ['DDD'])
        self.assertEqual(result['subdivision_values'], ['HOLLEY BY THE SEA 1ST CORR & AMEND'])
        self.assertEqual(result['parcel_designators'], [])

    def test_parse_santarosa_row_handles_plural_parcels_clause(self):
        row = pd.Series({
            'Legal': 'WINDSOR RIDGE LOTS 74 & 75; PARCELS A-E',
        })
        cols = {'legal': 'Legal'}

        result = parse_santarosa_row(row, cols)

        self.assertEqual(result['lot_values'], ['74 & 75'])
        self.assertEqual(result['subdivision_values'], ['WINDSOR RIDGE'])
        self.assertEqual(result['parcel_designators'], ['A-E'])
        self.assertEqual(result['lot_count'], 2)

    def test_parse_santarosa_row_handles_backslash_block_separator(self):
        row = pd.Series({
            'Legal': r'RIVERS COVE PH 2 9\D',
        })
        cols = {'legal': 'Legal'}

        result = parse_santarosa_row(row, cols)

        self.assertEqual(result['lot_values'], ['9'])
        self.assertEqual(result['block_values'], ['D'])
        self.assertEqual(result['subdivision_values'], ['RIVERS COVE PH 2'])

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

    def test_parse_okeechobee_row_captures_parcel_block_unit_and_subdivision(self):
        row = pd.Series({
            'Legal': '1-05-37-35-0020-00310-0130\nLOT 13 BLK 31 BASSWOOD INC UNIT 2',
        })
        cols = {'legal': 'Legal'}

        result = parse_okeechobee_row(row, cols)

        self.assertEqual(result['legal'], 'LOT 13 BLK 31 BASSWOOD INC UNIT 2')
        self.assertEqual(result['parcel_references'], ['1-05-37-35-0020-00310-0130'])
        self.assertEqual(result['lot_values'], ['13'])
        self.assertEqual(result['block_values'], ['31'])
        self.assertEqual(result['unit_values'], ['2'])
        self.assertEqual(result['subdivision_values'], ['BASSWOOD INC'])
        self.assertEqual(result['lot_identifiers'], ['13'])
        self.assertEqual(result['lot_count'], 1)

    def test_parse_okeechobee_row_captures_partial_lots_and_str_values(self):
        row = pd.Series({
            'Legal': (
                'LOT 3 & PTN LOT 2 BLK 3 SOUTHERN PINE ADDN\n'
                'LOT 9 UNIT 7 6/37/35'
            ),
        })
        cols = {'legal': 'Legal'}

        result = parse_okeechobee_row(row, cols)

        self.assertEqual(result['lot_values'], ['3 & 2', '9'])
        self.assertEqual(result['partial_lot_values'], ['2'])
        self.assertEqual(result['block_values'], ['3'])
        self.assertEqual(result['unit_values'], ['7'])
        self.assertEqual(result['subdivision_values'], ['SOUTHERN PINE ADDN'])
        self.assertEqual(result['section_values'], ['6'])
        self.assertEqual(result['township_values'], ['37'])
        self.assertEqual(result['range_values'], ['35'])
        self.assertEqual(result['partial_lot_identifiers'], ['2'])
        self.assertEqual(result['lot_count'], 3)


if __name__ == '__main__':
    unittest.main()
