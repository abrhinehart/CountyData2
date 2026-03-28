import unittest

from utils.text_cleaning import clean_subdivision, extract_phase, remove_phase_from_text


class TextCleaningTests(unittest.TestCase):
    def test_extract_phase_handles_plural_multi_value_phase(self):
        phase = extract_phase('CALDERA PHASES 3 & 4', ['Phase', 'PH', 'PHS'])

        self.assertEqual(phase, '3 & 4')

    def test_extract_phase_handles_configured_ph_wildcard_keyword(self):
        phase = extract_phase('CALDERA PHS 3 & 4', ['Phase', 'Ph.?', 'PH'])

        self.assertEqual(phase, '3 & 4')

    def test_remove_phase_from_text_keeps_base_subdivision(self):
        cleaned = remove_phase_from_text('CALDERA PHASE 3 & 4', ['Phase', 'PH', 'PHS'])

        self.assertEqual(cleaned, 'CALDERA')

    def test_clean_subdivision_handles_compound_phase_text(self):
        cleaned = clean_subdivision('CALDERA PHASES 3 & 4', ['Phase', 'PH', 'PHS'])

        self.assertEqual(cleaned, 'CALDERA')

    def test_clean_subdivision_handles_phs_abbreviation(self):
        cleaned = clean_subdivision('CALDERA PHS 3 & 4', ['Phase', 'Ph.?', 'PH'])

        self.assertEqual(cleaned, 'CALDERA')

    def test_clean_subdivision_strips_trailing_subdivision_suffix(self):
        cleaned = clean_subdivision('SOUTHERN DAY CHATEAU SUBDIVISION', ['Phase', 'PH'])

        self.assertEqual(cleaned, 'SOUTHERN DAY CHATEAU')

    def test_clean_subdivision_handles_duplicate_phase_keyword_typo(self):
        cleaned = clean_subdivision('PATRIOT RIDGE PHASE PHASE 6', ['Phase', 'Ph.?', 'PH'])
        phase = extract_phase('PATRIOT RIDGE PHASE PHASE 6', ['Phase', 'Ph.?', 'PH'])

        self.assertEqual(cleaned, 'PATRIOT RIDGE')
        self.assertEqual(phase, '6')

    def test_clean_subdivision_removes_lot_ranges_from_plat_style_text(self):
        cleaned = clean_subdivision(
            'OPPORTUNITY ADDITION TO SHOFFNER CITY LOTS 26-29 BLK 13',
            ['Phase', 'PH'],
        )

        self.assertEqual(cleaned, 'OPPORTUNITY ADDITION TO SHOFFNER CITY')

    def test_extract_phase_handles_compact_ph_keyword(self):
        phase = extract_phase('WOODLAND PH1', ['Phase', 'Ph.?', 'PH'])

        self.assertEqual(phase, '1')

    def test_clean_subdivision_removes_subd_suffix(self):
        cleaned = clean_subdivision('PLANTATION WOODS SUBD PH VIII', ['Phase', 'Ph.?', 'PH'])

        self.assertEqual(cleaned, 'PLANTATION WOODS')


if __name__ == '__main__':
    unittest.main()
