import unittest

from utils.subdivision_reference import (
    resolve_county_subdivision_reference,
    resolve_marion_subdivision_reference,
)


class MarionSubdivisionReferenceTests(unittest.TestCase):
    def test_resolve_marion_reference_uses_yaml_aliases(self):
        cases = {
            'BRIDLEWOOD': 'Brindlewood',
            'BRIDELWOOD': 'Brindlewood',
            'LIBERTY VLG': 'LIBERTY VILLAGE',
            'JB RCH': 'JB RANCH',
            'LD N': 'LAKE DIAMOND NORTH',
            'OCR S': 'OCALA CROSSINGS SOUTH',
            'W OAK': 'WEST OAK',
            'RH': 'ROLLING HILLS',
            'MO': 'MARION OAKS',
            'CTPG': 'CALESA TOWNSHIP PERLINO GROVE',
            'JULIETTE FALLS': 'JULLIETTE FALLS',
            'OCP': 'OCALA PRESERVE',
        }

        for raw_value, canonical_name in cases.items():
            with self.subTest(raw_value=raw_value):
                result = resolve_marion_subdivision_reference(raw_value)
                self.assertIsNotNone(result)
                self.assertEqual(result['canonical_name'], canonical_name)
                self.assertEqual(result['match_type'], 'reference_alias')
                self.assertEqual(result['prefix_tokens'], [])
                self.assertEqual(result['suffix_tokens'], [])

    def test_resolve_marion_reference_heuristic_captures_prefix_tokens(self):
        result = resolve_marion_subdivision_reference('CH W ASHFORD & BALFOUR')

        self.assertIsNotNone(result)
        self.assertEqual(result['canonical_name'], 'ASHFORD & BALFOUR')
        self.assertEqual(result['match_type'], 'reference_heuristic')
        self.assertEqual(result['prefix_tokens'], ['CH', 'W'])
        self.assertEqual(result['suffix_tokens'], [])

    def test_resolve_marion_reference_returns_none_for_unknown_abbreviation(self):
        self.assertIsNone(resolve_marion_subdivision_reference('SSA'))


class CountySubdivisionReferenceTests(unittest.TestCase):
    def test_resolve_santarosa_reference_uses_yaml_aliases(self):
        cases = {
            'AIRWAY OAKS': 'AIRWAYS OAKS',
            'BLACKWATER RESERVE A': 'BLACKWATER RESERVE',
            'CHRISTOPERS LANDING': 'CHRISTOPHERS LANDING',
            'HIDDEN PINES ESTATES 1ST ADDITION': 'HIDDEN PINES ESTATES',
            'HOLLEY BY THE SEA 2ND CORR & AMEND': 'HOLLEY BY THE SEA',
            'HORIZON EDGE': 'HORIZONS EDGE',
            'LANCELOT HOMES': 'LANCELOT TOWNHOMES',
            'PARKERS GROVE TOWNHOMES': 'PARKER GROVE',
            'SENTINAL RIDGE': 'SENTINEL RIDGE',
            'WINSOR RIDGE': 'WINDSOR RIDGE',
            'WOODLAND': 'WOODLANDS',
        }

        for raw_value, canonical_name in cases.items():
            with self.subTest(raw_value=raw_value):
                result = resolve_county_subdivision_reference('Santa Rosa', raw_value)
                self.assertIsNotNone(result)
                self.assertEqual(result['canonical_name'], canonical_name)
                self.assertEqual(result['match_type'], 'reference_alias')
                self.assertEqual(result['prefix_tokens'], [])
                self.assertEqual(result['suffix_tokens'], [])
