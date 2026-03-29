import unittest

from utils.raw_land_benchmark import (
    compare_legal_texts,
    extract_legal_candidate,
    normalize_legal_text,
    validate_legal_candidate,
)


class RawLandBenchmarkTests(unittest.TestCase):
    def test_extract_legal_candidate_spans_multiple_pages(self):
        pages = [
            """
            File # 2024046523, OR BK: 4828 PG: 1761, Pages: 1 of 5
            WARRANTY DEED
            WITNESSETH: The grantor ... all that certain land situate in Bay County, FL, to-wit:
            Parcel 1: Commence at the SE Corner of Section 14, T2S, R13W; thence N02°23'18"W, 2090.53';
            """,
            """
            File # 2024046523 BK: 4828 PG: 1762, Pages: 2 of 5
            Parcel 2: Commence at the SE Corner of Section 14, T2S, R13W; thence S87°36'42"W, 2034.44';
            Subject to all reservations, covenants, conditions, restrictions and easements of record.
            """,
        ]

        extracted = extract_legal_candidate(pages)

        self.assertEqual(extracted['status'], 'ok')
        self.assertEqual(extracted['start_page'], 1)
        self.assertEqual(extracted['end_page'], 2)
        self.assertEqual(extracted['start_marker'], 'to_wit')
        self.assertEqual(extracted['end_marker'], 'subject_to')
        self.assertIn('Parcel 1:', extracted['candidate_legal_desc'])
        self.assertIn('Parcel 2:', extracted['candidate_legal_desc'])
        self.assertNotIn('Subject to', extracted['candidate_legal_desc'])

    def test_normalize_legal_text_ignores_case_and_whitespace(self):
        normalized = normalize_legal_text(" Parcel 1:\nCommence at the SE Corner   of Section 14 ")
        self.assertEqual(normalized, 'PARCEL 1 COMMENCE AT THE SE CORNER OF SECTION 14')

    def test_extract_legal_candidate_follows_exhibit_reference(self):
        pages = [
            """
            WARRANTY DEED
            all that certain land situate in Bay County, FL, to-wit:
            See Exhibit "A" attached hereto
            Subject to all reservations and easements of record.
            """,
            """
            EXHIBIT "A"

            Legal Description

            Parcel 1:
            Commence at the SE Corner of Section 14, T2S, R13W; thence N02°23'18"W, 1550.53';
            Parcel 2:
            Commence at the SE Corner of Section 14, T2S, R13W; thence N02°23'18"W, 1650.53';
            """,
        ]

        extracted = extract_legal_candidate(pages)

        self.assertEqual(extracted['status'], 'ok')
        self.assertEqual(extracted['start_page'], 2)
        self.assertEqual(extracted['start_marker'], 'legal_description')
        self.assertIn('Parcel 1:', extracted['candidate_legal_desc'])
        self.assertNotIn('See Exhibit', extracted['candidate_legal_desc'])

    def test_compare_legal_texts_treats_whitespace_only_differences_as_exact(self):
        metrics = compare_legal_texts(
            "Parcel 1:\nCommence at the SE Corner of Section 14",
            "PARCEL 1: COMMENCE AT THE SE CORNER OF SECTION 14",
        )

        self.assertTrue(metrics['normalized_exact'])
        self.assertEqual(metrics['similarity_ratio'], 1.0)

    def test_validate_legal_candidate_accepts_targeted_single_parcel(self):
        pages = [
            """
            EXHIBIT "A"
            Legal Description
            Parcel 1:
            Commence at the SE Corner of Section 14, T2S, R13W; thence N02°23'18"W, 1550.53';
            thence S87°36'42"W, 1137.23'; thence S43°23'22"W, 420.08'; thence S37°09'22"W, 130';
            Parcel 2:
            Commence at the SE Corner of Section 14, T2S, R13W; thence N02°23'18"W, 1650.53';
            """,
        ]
        candidate = (
            'Commence at the SE Corner of Section 14, T2S, R13W; thence N02°23\'18"W, 1550.53\'; '
            'thence S87°36\'42"W, 1137.23\'; thence S43°23\'22"W, 420.08\'; thence S37°09\'22"W, 130\';'
        )

        validation = validate_legal_candidate(candidate, pages, 'Parcel 1 only')

        self.assertTrue(validation['passed'])
        self.assertEqual(validation['target_parcel'], 1)
        self.assertGreaterEqual(validation['similarity_ratio'], 0.75)

    def test_validate_legal_candidate_rejects_multiple_parcels_for_target(self):
        pages = [
            """
            EXHIBIT "A"
            Legal Description
            Parcel 1:
            Commence at the SE Corner of Section 14, T2S, R13W; thence N02°23'18"W, 1550.53';
            Parcel 2:
            Commence at the SE Corner of Section 14, T2S, R13W; thence N02°23'18"W, 1650.53';
            """,
        ]
        candidate = (
            'Parcel 1: Commence at the SE Corner of Section 14, T2S, R13W; thence N02°23\'18"W, 1550.53\'; '
            'Parcel 2: Commence at the SE Corner of Section 14, T2S, R13W; thence N02°23\'18"W, 1650.53\';'
        )

        validation = validate_legal_candidate(candidate, pages, 'Parcel 1 only')

        self.assertFalse(validation['passed'])
        self.assertIn('target_parcel_mismatch', validation['reasons'])
        self.assertIn('multiple_candidate_parcels_for_target', validation['reasons'])

    def test_validate_legal_candidate_uses_extracted_span_for_non_parcel_legal(self):
        pages = [
            """
            File # 2025073136 BK: 4983 PG: 1951, Pages: 3 of 3
            Legal Description
            OF THE PROPERTY
            Lot(s) 37, 40, 41, 42, 64, and 65, MAGNOLIA RIDGE PHASE 1, according to the plat thereof.
            AND
            Lot(s) 87, 88, and 89, MAGNOLIA RIDGE PHASE 2, according to the plat thereof.
            Deed 110041-001514-7-FL
            """,
        ]
        candidate = (
            'Lot(s) 37, 40, 41, 42, 64, and 65, MAGNOLIA RIDGE PHASE 1, according to the plat thereof. '
            'AND Lot(s) 87, 88, and 89, MAGNOLIA RIDGE PHASE 2, according to the plat thereof.'
        )

        validation = validate_legal_candidate(candidate, pages, '')

        self.assertTrue(validation['passed'])
        self.assertGreaterEqual(validation['similarity_ratio'], 0.85)


if __name__ == '__main__':
    unittest.main()
