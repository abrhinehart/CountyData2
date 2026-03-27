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


if __name__ == '__main__':
    unittest.main()
