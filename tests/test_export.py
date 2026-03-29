import unittest
from unittest.mock import patch

from export import build_query, fetch_data


class _FakeCursor:
    def __init__(self, rows, columns):
        self._rows = rows
        self.description = [(column, None, None, None, None, None, None) for column in columns]
        self.executed = []

    def execute(self, sql, params):
        self.executed.append((sql, params))

    def fetchall(self):
        return list(self._rows)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class _FakeConnection:
    def __init__(self, cursor):
        self._cursor = cursor
        self.closed = False

    def cursor(self):
        return self._cursor

    def close(self):
        self.closed = True


class ExportTests(unittest.TestCase):
    def test_build_query_supports_inventory_category_filters(self):
        sql, params, col_map = build_query(
            county='Citrus',
            subdivision=None,
            date_from=None,
            date_to=None,
            inventory_categories=['scattered_legacy_lots'],
            exclude_inventory_categories=['finished_lot_inventory'],
        )

        self.assertIn('inventory_category = %s', sql)
        self.assertIn('inventory_category IS DISTINCT FROM %s', sql)
        self.assertEqual(params, ['Citrus', 'scattered_legacy_lots', 'finished_lot_inventory'])
        self.assertIn('inventory_category', col_map)
        self.assertIn('export_legal_desc', col_map)

    def test_build_query_includes_export_legal_raw_only_when_requested(self):
        sql, _, col_map = build_query(
            county=None,
            subdivision=None,
            date_from=None,
            date_to=None,
            include_raw=True,
        )

        self.assertIn('export_legal_desc', sql)
        self.assertIn('export_legal_raw', sql)
        self.assertEqual(col_map['export_legal_desc'], 'Export Legal Description')
        self.assertEqual(col_map['export_legal_raw'], 'Export Legal Raw')

    def test_fetch_data_uses_cursor_fetch_and_preserves_display_columns(self):
        cursor = _FakeCursor(
            rows=[('Seller Name', 'Buyer Name', 'Bay')],
            columns=['grantor', 'grantee', 'county'],
        )
        conn = _FakeConnection(cursor)
        col_map = {
            'grantor': 'Grantor',
            'grantee': 'Grantee',
            'price': 'Price',
            'county': 'County',
        }

        with patch('export.psycopg2.connect', return_value=conn), patch(
            'export.pd.read_sql_query',
            side_effect=AssertionError('fetch_data should not call pandas.read_sql_query'),
        ):
            df = fetch_data('SELECT grantor, grantee, county FROM transactions', ['Bay'], col_map)

        self.assertEqual(
            cursor.executed,
            [('SELECT grantor, grantee, county FROM transactions', ['Bay'])],
        )
        self.assertTrue(conn.closed)
        self.assertEqual(list(df.columns), ['Grantor', 'Grantee', 'Price', 'County'])
        self.assertEqual(df.iloc[0].to_dict()['Grantor'], 'Seller Name')
        self.assertEqual(df.iloc[0].to_dict()['Grantee'], 'Buyer Name')
        self.assertEqual(df.iloc[0].to_dict()['County'], 'Bay')
        self.assertIsNone(df.iloc[0].to_dict()['Price'])


if __name__ == '__main__':
    unittest.main()
