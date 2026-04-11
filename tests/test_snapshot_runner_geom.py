"""Unit tests for _geojson_to_wkb in snapshot_runner.

Guards Entry 3 from post-merge-quirks.md: invalid source GIS polygons must be
healed by the writer before they reach PostGIS. Tests exercise the happy path
and the bowtie / spike drift classes that make_valid handles.
"""

import unittest

from shapely.geometry import MultiPolygon, Polygon
from shapely import wkb as shapely_wkb

from modules.inventory.services.snapshot_runner import _geojson_to_wkb


def _wkb_to_shape(wkb_element):
    """Unwrap a geoalchemy2 WKBElement back to a shapely geometry."""
    # WKBElement.desc is a hex string; shapely.wkb.loads accepts the bytes
    return shapely_wkb.loads(bytes.fromhex(wkb_element.desc))


class GeoJsonToWkbTests(unittest.TestCase):
    def test_valid_polygon_happy_path(self):
        geojson = {
            "type": "Polygon",
            "coordinates": [[[0, 0], [0, 1], [1, 1], [1, 0], [0, 0]]],
        }
        geom_wkb, centroid_wkb = _geojson_to_wkb(geojson)
        self.assertIsNotNone(geom_wkb)
        self.assertIsNotNone(centroid_wkb)
        geom = _wkb_to_shape(geom_wkb)
        self.assertTrue(geom.is_valid)
        self.assertIsInstance(geom, MultiPolygon)
        # Area unchanged from the 1x1 square
        self.assertAlmostEqual(geom.area, 1.0, places=6)

    def test_bowtie_self_intersection_is_healed(self):
        # Classic self-intersecting "bowtie" ring
        geojson = {
            "type": "Polygon",
            "coordinates": [[[0, 0], [1, 1], [1, 0], [0, 1], [0, 0]]],
        }
        geom_wkb, centroid_wkb = _geojson_to_wkb(geojson)
        self.assertIsNotNone(geom_wkb)
        geom = _wkb_to_shape(geom_wkb)
        self.assertTrue(geom.is_valid, "make_valid should heal bowtie")
        self.assertIsInstance(geom, MultiPolygon)
        # Bowtie resolves to two triangles each of area 0.25
        self.assertAlmostEqual(geom.area, 0.5, places=6)

    def test_valid_multipolygon_passthrough(self):
        geojson = {
            "type": "MultiPolygon",
            "coordinates": [
                [[[0, 0], [0, 1], [1, 1], [1, 0], [0, 0]]],
                [[[2, 2], [2, 3], [3, 3], [3, 2], [2, 2]]],
            ],
        }
        geom_wkb, centroid_wkb = _geojson_to_wkb(geojson)
        self.assertIsNotNone(geom_wkb)
        geom = _wkb_to_shape(geom_wkb)
        self.assertTrue(geom.is_valid)
        self.assertIsInstance(geom, MultiPolygon)
        self.assertEqual(len(geom.geoms), 2)
        self.assertAlmostEqual(geom.area, 2.0, places=6)

    def test_ring_with_spike_still_parses(self):
        # Polygon with a sliver/spike — still valid after healing
        geojson = {
            "type": "Polygon",
            "coordinates": [
                [[0, 0], [2, 0], [2, 2], [1, 2], [1, 3], [1, 2], [0, 2], [0, 0]]
            ],
        }
        geom_wkb, _ = _geojson_to_wkb(geojson)
        self.assertIsNotNone(geom_wkb)
        geom = _wkb_to_shape(geom_wkb)
        self.assertTrue(geom.is_valid)
        self.assertIsInstance(geom, MultiPolygon)

    def test_empty_input_returns_nones(self):
        self.assertEqual(_geojson_to_wkb(None), (None, None))
        self.assertEqual(_geojson_to_wkb({}), (None, None))


if __name__ == "__main__":
    unittest.main()
