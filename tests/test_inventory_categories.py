import unittest
from unittest.mock import mock_open, patch

from utils.inventory_categories import classify_inventory_category, load_inventory_categories


class InventoryCategoriesTests(unittest.TestCase):
    def tearDown(self):
        load_inventory_categories.cache_clear()

    def test_classify_inventory_category_matches_curated_subdivision(self):
        yaml_text = """
scattered_legacy_lots:
  Citrus:
    - Inverness Highlands
  Hernando:
    - Spring Hill
"""
        with patch('utils.inventory_categories.Path.exists', return_value=True), patch(
            'builtins.open',
            mock_open(read_data=yaml_text),
        ):
            self.assertEqual(
                classify_inventory_category('Citrus', 'INVERNESS HIGHLANDS'),
                'scattered_legacy_lots',
            )
            self.assertEqual(
                classify_inventory_category('Hernando', 'Spring Hill'),
                'scattered_legacy_lots',
            )
            self.assertIsNone(classify_inventory_category('Citrus', 'Citrus Springs'))


if __name__ == '__main__':
    unittest.main()
