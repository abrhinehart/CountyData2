import unittest
from unittest.mock import MagicMock, patch

from county_scrapers.gis_parcel_client import (
    GISParcelSession,
    JACKSON_FIELDS,
    _centroid,
)


class CentroidTests(unittest.TestCase):
    def test_simple(self):
        geom = {'rings': [[[-88.5, 30.3], [-88.6, 30.3],
                           [-88.6, 30.4], [-88.5, 30.4], [-88.5, 30.3]]]}
        lat, lon = _centroid(geom)
        self.assertAlmostEqual(lat, 30.34, places=1)
        self.assertAlmostEqual(lon, -88.54, places=1)

    def test_empty(self):
        self.assertIsNone(_centroid({}))


class ParseFeatureTests(unittest.TestCase):
    def test_basic(self):
        session = GISParcelSession('https://example.com/MapServer/2',
                                   field_map=JACKSON_FIELDS)
        feature = {
            'attributes': {
                'NAME': 'SMITH JOHN',
                'NAME2': '',
                'LOCATION': '123 MAIN ST',
                'DB': '2200',
                'DP': '100',
                'SUBD': 'OAK GROVE',
                'LOTNUM2': '5',
                'ACREAGE': 0.25,
                'TOTALVAL': 150000,
                'SAMT': 180000,
                'SDAT': 1740848400000,  # 3/1/2025
                'DESC1': 'LOT 5 OAK GROVE S/D',
                'SECTION': '6',
                'TOWN': '7',
                'RANGE': '8',
                'PIDN': '1234-56-789',
            },
            'geometry': {
                'rings': [[[-88.5, 30.3], [-88.51, 30.3],
                           [-88.51, 30.31], [-88.5, 30.31], [-88.5, 30.3]]]
            },
        }
        result = session._parse_feature(feature)

        self.assertEqual(result['grantee'], 'SMITH JOHN')
        self.assertEqual(result['book'], '2200')
        self.assertEqual(result['page'], '100')
        self.assertEqual(result['subdivision'], 'OAK GROVE')
        self.assertEqual(result['lot'], '5')
        self.assertEqual(result['situs_address'], '123 MAIN ST')
        self.assertEqual(result['gis_acreage'], '0.250')
        self.assertEqual(result['gis_value'], '150000')
        self.assertEqual(result['sale_amount'], '180000')
        self.assertEqual(result['record_date'], '03/01/2025')
        self.assertIn('latitude', result)
        self.assertIn('longitude', result)
        self.assertEqual(result['parcel_id'], '1234-56-789')
        session.close()

    def test_empty_returns_none(self):
        session = GISParcelSession('https://example.com/MapServer/2',
                                   field_map=JACKSON_FIELDS)
        feature = {
            'attributes': {k: '' for k in JACKSON_FIELDS.values()},
            'geometry': None,
        }
        result = session._parse_feature(feature)
        self.assertIsNone(result)
        session.close()

    def test_zero_sale_amount_not_set(self):
        session = GISParcelSession('https://example.com/MapServer/2',
                                   field_map=JACKSON_FIELDS)
        feature = {
            'attributes': {
                'NAME': 'OWNER',
                'DB': '100', 'DP': '50',
                'SAMT': 0, 'SDAT': 1740848400000,
                **{k: '' for k in JACKSON_FIELDS.values()
                   if k not in ('NAME', 'DB', 'DP', 'SAMT', 'SDAT')},
            },
            'geometry': None,
        }
        result = session._parse_feature(feature)
        self.assertNotIn('sale_amount', result)
        session.close()


class SearchTests(unittest.TestCase):
    @patch('county_scrapers.gis_parcel_client.cf_requests.Session')
    def test_search_paginates(self, MockSessionClass):
        mock_session = MagicMock()
        MockSessionClass.return_value = mock_session

        # Mock connect
        connect_resp = MagicMock()
        connect_resp.json.return_value = {'name': 'Parcels', 'maxRecordCount': 1000}
        connect_resp.raise_for_status = MagicMock()

        # Mock query page 1
        page1 = {
            'features': [{
                'attributes': {
                    'NAME': f'OWNER {i}', 'DB': '100', 'DP': str(i),
                    'SDAT': 1740848400000, 'SAMT': 0,
                    **{k: '' for k in JACKSON_FIELDS.values()
                       if k not in ('NAME', 'DB', 'DP', 'SDAT', 'SAMT')},
                },
                'geometry': None,
            } for i in range(1000)],
        }
        query_resp1 = MagicMock()
        query_resp1.json.return_value = page1
        query_resp1.raise_for_status = MagicMock()

        # Mock query page 2 (partial)
        page2 = {
            'features': [{
                'attributes': {
                    'NAME': f'OWNER {i}', 'DB': '100', 'DP': str(i),
                    'SDAT': 1740848400000, 'SAMT': 0,
                    **{k: '' for k in JACKSON_FIELDS.values()
                       if k not in ('NAME', 'DB', 'DP', 'SDAT', 'SAMT')},
                },
                'geometry': None,
            } for i in range(1000, 1200)],
        }
        query_resp2 = MagicMock()
        query_resp2.json.return_value = page2
        query_resp2.raise_for_status = MagicMock()

        mock_session.get.side_effect = [connect_resp, query_resp1, query_resp2]

        session = GISParcelSession(
            'https://example.com/MapServer/2',
            field_map=JACKSON_FIELDS,
            page_size=1000, request_delay=0,
        )
        session._session = mock_session
        session.connect()

        rows = session.search_by_date_range('03/01/2025', '03/31/2025')
        self.assertEqual(len(rows), 1200)
        session.close()


if __name__ == '__main__':
    unittest.main()
