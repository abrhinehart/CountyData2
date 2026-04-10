import unittest
from unittest.mock import MagicMock, patch

from county_scrapers.gis_enrichment import (
    enrich_from_gis, _centroid, MADISON_FIELDS, DESOTO_FIELDS,
)


class CentroidTests(unittest.TestCase):
    def test_simple_square(self):
        geom = {'rings': [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]}
        lat, lon = _centroid(geom)
        self.assertAlmostEqual(lat, 0.4, places=1)
        self.assertAlmostEqual(lon, 0.4, places=1)

    def test_real_coordinates(self):
        # Approximate polygon near DeSoto County
        geom = {'rings': [[[-89.75, 34.95], [-89.76, 34.95],
                           [-89.76, 34.96], [-89.75, 34.96], [-89.75, 34.95]]]}
        lat, lon = _centroid(geom)
        self.assertAlmostEqual(lat, 34.954, places=2)
        self.assertAlmostEqual(lon, -89.754, places=2)

    def test_empty_geometry(self):
        self.assertIsNone(_centroid({}))
        self.assertIsNone(_centroid({'rings': []}))


class EnrichMadisonFieldsTests(unittest.TestCase):
    @patch('county_scrapers.gis_enrichment._build_session')
    def test_enriches_with_geometry(self, mock_build):
        mock_session = MagicMock()
        mock_build.return_value = mock_session

        gis_response = {
            'features': [{
                'attributes': {
                    'deed_book': '100',
                    'deed_page': '       50',
                    'street_number': 123.0,
                    'street_name': 'MAIN ST',
                    'arcacres': 0.25,
                    'total_acres': 0.0,
                    'true_total_value': 150000.0,
                },
                'geometry': {
                    'rings': [[[-90.0, 32.0], [-90.001, 32.0],
                               [-90.001, 32.001], [-90.0, 32.001], [-90.0, 32.0]]]
                },
            }],
        }
        mock_resp = MagicMock()
        mock_resp.json.return_value = gis_response
        mock_resp.raise_for_status = MagicMock()
        mock_session.get.return_value = mock_resp

        rows = [
            {'book': '100', 'page': '50', 'grantor': 'SELLER A'},
            {'book': '200', 'page': '75', 'grantor': 'SELLER B'},
        ]
        count = enrich_from_gis(rows, 'https://example.com/FeatureServer/0',
                                field_map=MADISON_FIELDS)

        self.assertEqual(count, 1)
        self.assertEqual(rows[0]['situs_address'], '123 MAIN ST')
        self.assertEqual(rows[0]['gis_acreage'], '0.250')
        self.assertEqual(rows[0]['gis_value'], '150000')
        self.assertIn('latitude', rows[0])
        self.assertIn('longitude', rows[0])
        self.assertAlmostEqual(float(rows[0]['latitude']), 32.0, places=1)
        self.assertAlmostEqual(float(rows[0]['longitude']), -90.0, places=1)
        # Second row should not have GIS fields
        self.assertNotIn('situs_address', rows[1])
        self.assertNotIn('latitude', rows[1])


class EnrichDeSotoFieldsTests(unittest.TestCase):
    @patch('county_scrapers.gis_enrichment._build_session')
    def test_enriches_with_desoto_fields(self, mock_build):
        mock_session = MagicMock()
        mock_build.return_value = mock_session

        gis_response = {
            'features': [{
                'attributes': {
                    'DEED_BOOK1': '999',
                    'DEED_PAGE1': '426',
                    'FULL_ADDR': '6761 WHITE HAWK LN',
                    'ACREAGE': 0.251,
                    'TOT_APVAL': 167655,
                },
                'geometry': {
                    'rings': [[[-89.75, 34.95], [-89.76, 34.95],
                               [-89.76, 34.96], [-89.75, 34.96], [-89.75, 34.95]]]
                },
            }],
        }
        mock_resp = MagicMock()
        mock_resp.json.return_value = gis_response
        mock_resp.raise_for_status = MagicMock()
        mock_session.get.return_value = mock_resp

        rows = [{'book': '999', 'page': '426', 'grantor': 'TEST'}]
        count = enrich_from_gis(rows, 'https://example.com/FeatureServer/11',
                                field_map=DESOTO_FIELDS)

        self.assertEqual(count, 1)
        self.assertEqual(rows[0]['situs_address'], '6761 WHITE HAWK LN')
        self.assertEqual(rows[0]['gis_acreage'], '0.251')
        self.assertEqual(rows[0]['gis_value'], '167655')
        self.assertIn('latitude', rows[0])
        self.assertIn('longitude', rows[0])


class EnrichNoBookFieldTests(unittest.TestCase):
    def test_no_deed_book_skips(self):
        """Counties without deed_book in GIS should skip enrichment."""
        field_map = {'deed_book': None, 'deed_page': None, 'address': 'addr',
                     'acreage': 'ac', 'value': None}
        rows = [{'book': '100', 'page': '50'}]
        count = enrich_from_gis(rows, 'https://example.com/FeatureServer/0',
                                field_map=field_map)
        self.assertEqual(count, 0)


class EnrichDefaultFieldMapTests(unittest.TestCase):
    @patch('county_scrapers.gis_enrichment._build_session')
    def test_default_uses_madison_fields(self, mock_build):
        """When no field_map is passed, defaults to Madison format."""
        mock_session = MagicMock()
        mock_build.return_value = mock_session

        gis_response = {
            'features': [{
                'attributes': {
                    'deed_book': '100',
                    'deed_page': '50',
                    'street_number': 100.0,
                    'street_name': 'OAK ST',
                    'arcacres': 1.0,
                    'total_acres': 0.0,
                    'true_total_value': 50000.0,
                },
                'geometry': {'rings': [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]},
            }],
        }
        mock_resp = MagicMock()
        mock_resp.json.return_value = gis_response
        mock_resp.raise_for_status = MagicMock()
        mock_session.get.return_value = mock_resp

        rows = [{'book': '100', 'page': '50'}]
        count = enrich_from_gis(rows, 'https://example.com/FeatureServer/0')
        self.assertEqual(count, 1)
        self.assertEqual(rows[0]['situs_address'], '100 OAK ST')


class EnrichNoBooksTests(unittest.TestCase):
    @patch('county_scrapers.gis_enrichment._build_session')
    def test_no_books_returns_zero(self, mock_build):
        rows = [{'book': '', 'page': '', 'grantor': 'TEST'}]
        count = enrich_from_gis(rows, 'https://example.com/FeatureServer/0')
        self.assertEqual(count, 0)
        mock_build.assert_not_called()

    @patch('county_scrapers.gis_enrichment._build_session')
    def test_non_numeric_books_skipped(self, mock_build):
        rows = [{'book': 'CH21', 'page': '100', 'grantor': 'TEST'}]
        count = enrich_from_gis(rows, 'https://example.com/FeatureServer/0')
        self.assertEqual(count, 0)
        mock_build.assert_not_called()


if __name__ == '__main__':
    unittest.main()
