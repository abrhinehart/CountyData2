import csv
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from tools.apply_benchmark_results import _build_parsed, apply_results


class BuildParsedTests(unittest.TestCase):
    def test_extracts_core_metadata(self):
        row = {
            'method': 'anthropic_hybrid',
            'model': 'claude-opus-4-6',
            'selected_mode': 'text',
            'target_hint': 'Parcel 9 only',
            'candidate_chars': '486',
            'text_validation_similarity_ratio': '0.95',
            'text_validation_target_parcel': '9',
            'text_validation_candidate_bearings': '8',
            'text_validation_candidate_distances': '8',
            'text_validation_passed': 'True',
            'estimated_cost_usd': '0.03',
        }
        parsed = _build_parsed(row)
        self.assertEqual(parsed['extraction_method'], 'anthropic_hybrid')
        self.assertEqual(parsed['extraction_model'], 'claude-opus-4-6')
        self.assertEqual(parsed['selected_mode'], 'text')
        self.assertEqual(parsed['candidate_chars'], 486)
        self.assertAlmostEqual(parsed['similarity_ratio'], 0.95)
        self.assertEqual(parsed['target_parcel'], '9')
        self.assertEqual(parsed['candidate_bearings'], 8)
        self.assertEqual(parsed['candidate_distances'], 8)
        self.assertTrue(parsed['validation_passed'])
        self.assertAlmostEqual(parsed['estimated_cost_usd'], 0.03)

    def test_skips_empty_fields(self):
        row = {
            'method': 'anthropic_hybrid',
            'model': 'claude-opus-4-6',
            'selected_mode': 'text',
            'target_hint': '',
            'candidate_chars': '',
            'text_validation_similarity_ratio': '',
            'text_validation_target_parcel': '',
            'text_validation_candidate_bearings': '0',
            'text_validation_candidate_distances': '0',
            'text_validation_passed': 'True',
            'estimated_cost_usd': '',
        }
        parsed = _build_parsed(row)
        self.assertNotIn('candidate_chars', parsed)
        self.assertNotIn('similarity_ratio', parsed)
        self.assertNotIn('target_parcel', parsed)
        self.assertNotIn('estimated_cost_usd', parsed)


class ApplyResultsDryRunTests(unittest.TestCase):
    def test_dry_run_does_not_write(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'transaction_id', 'county', 'method', 'model', 'status',
                'target_hint', 'cache_hit', 'selected_mode',
                'candidate_legal_desc', 'candidate_chars',
                'input_tokens', 'output_tokens', 'estimated_cost_usd',
                'pdf_path', 'note',
            ])
            writer.writeheader()
            writer.writerow({
                'transaction_id': '999',
                'county': 'Bay',
                'method': 'anthropic_hybrid',
                'model': 'claude-opus-4-6',
                'status': 'ok',
                'target_hint': '',
                'cache_hit': 'False',
                'selected_mode': 'text',
                'candidate_legal_desc': 'Test legal description',
                'candidate_chars': '22',
                'input_tokens': '100',
                'output_tokens': '50',
                'estimated_cost_usd': '0.01',
                'pdf_path': '',
                'note': '',
            })
            tmp_path = Path(f.name)

        count = apply_results(tmp_path, dry_run=True)
        self.assertEqual(count, 1)
        tmp_path.unlink()

    def test_skips_non_ok_status(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'transaction_id', 'county', 'method', 'model', 'status',
                'target_hint', 'cache_hit', 'selected_mode',
                'candidate_legal_desc', 'candidate_chars',
                'input_tokens', 'output_tokens', 'estimated_cost_usd',
                'pdf_path', 'note',
            ])
            writer.writeheader()
            writer.writerow({
                'transaction_id': '999',
                'county': 'Bay',
                'method': 'anthropic_hybrid',
                'model': 'claude-opus-4-6',
                'status': 'error',
                'target_hint': '',
                'cache_hit': 'False',
                'selected_mode': 'text',
                'candidate_legal_desc': 'Should not be written',
                'candidate_chars': '21',
                'input_tokens': '100',
                'output_tokens': '50',
                'estimated_cost_usd': '0.01',
                'pdf_path': '',
                'note': '',
            })
            tmp_path = Path(f.name)

        count = apply_results(tmp_path, dry_run=True)
        self.assertEqual(count, 0)
        tmp_path.unlink()


if __name__ == '__main__':
    unittest.main()
