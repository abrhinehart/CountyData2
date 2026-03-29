import unittest

from apply_migrations import MIGRATIONS_DIR, get_sql_migrations


class ApplyMigrationsTests(unittest.TestCase):
    def test_get_sql_migrations_returns_sorted_sql_files(self):
        migrations = get_sql_migrations()

        self.assertTrue(migrations)
        self.assertEqual(
            [path.name for path in migrations],
            [
                '001_reference_tables.sql',
                '002_alter_transactions.sql',
                '004_party_entities.sql',
                '005_parsed_data.sql',
                '006_transaction_segments.sql',
                '007_deed_locator.sql',
                '008_inventory_category.sql',
                '009_canonical_transaction_shape.sql',
            ],
        )
        self.assertTrue(all(path.parent == MIGRATIONS_DIR for path in migrations))


if __name__ == '__main__':
    unittest.main()
