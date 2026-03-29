import unittest

from tools.raw_land_legal_benchmark import _mark_cache_hit, _should_reuse_existing_result


class RawLandLegalBenchmarkToolTests(unittest.TestCase):
    def test_should_reuse_existing_result_requires_matching_model_and_hint(self):
        row = {
            'transaction_id': '77',
            'status': 'ok',
            'model': 'claude-opus-4-6',
            'target_hint': 'Parcel 9 only',
        }

        self.assertTrue(
            _should_reuse_existing_result(
                row,
                model='claude-opus-4-6',
                target_hint='Parcel 9 only',
            )
        )
        self.assertFalse(
            _should_reuse_existing_result(
                row,
                model='claude-sonnet-4-6',
                target_hint='Parcel 9 only',
            )
        )
        self.assertFalse(
            _should_reuse_existing_result(
                row,
                model='claude-opus-4-6',
                target_hint='Parcel 10 only',
            )
        )

    def test_mark_cache_hit_sets_flag_and_preserves_existing_note(self):
        row = {
            'transaction_id': '95',
            'status': 'ok',
            'note': 'Selected OCR-text extraction after validation.',
        }

        cached = _mark_cache_hit(row)

        self.assertEqual(cached['cache_hit'], 'True')
        self.assertIn('Reused existing model result', cached['note'])
        self.assertIn('Selected OCR-text extraction after validation.', cached['note'])


if __name__ == '__main__':
    unittest.main()
