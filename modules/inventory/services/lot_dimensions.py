"""Calculate lot dimensions (width, depth, area) from parcel geometry.

Uses the minimum rotated rectangle of the polygon to approximate
lot width (shorter side) and lot depth (longer side). Area comes
directly from the polygon.

All measurements are converted from WGS84 degrees to feet using a
local equirectangular approximation at the parcel's latitude.
"""

import math
from dataclasses import dataclass

from shapely.geometry import MultiPolygon, Polygon

# Conversion constants
METERS_PER_DEGREE_LAT = 111_320.0
FEET_PER_METER = 3.28084


@dataclass
class LotDimensions:
    width_ft: float
    depth_ft: float
    area_sqft: float


def _meters_per_degree_lon(lat_deg: float) -> float:
    """Meters per degree of longitude at a given latitude."""
    return METERS_PER_DEGREE_LAT * math.cos(math.radians(lat_deg))


def _distance_ft(p1: tuple, p2: tuple, lat_deg: float) -> float:
    """Approximate distance in feet between two WGS84 points."""
    dx = (p2[0] - p1[0]) * _meters_per_degree_lon(lat_deg)
    dy = (p2[1] - p1[1]) * METERS_PER_DEGREE_LAT
    return math.sqrt(dx * dx + dy * dy) * FEET_PER_METER


def compute_lot_dimensions(geom: Polygon | MultiPolygon) -> LotDimensions | None:
    """Compute approximate lot width, depth, and area from a parcel polygon.

    Returns None if the geometry is empty or degenerate.
    """
    if geom is None or geom.is_empty:
        return None

    # Use the largest polygon if MultiPolygon
    if isinstance(geom, MultiPolygon):
        geom = max(geom.geoms, key=lambda g: g.area)

    if not isinstance(geom, Polygon) or geom.is_empty:
        return None

    centroid = geom.centroid
    lat = centroid.y

    # Area: convert from square degrees to square feet
    m_per_deg_lon = _meters_per_degree_lon(lat)
    area_sq_m = geom.area * METERS_PER_DEGREE_LAT * m_per_deg_lon
    area_sqft = round(area_sq_m * FEET_PER_METER * FEET_PER_METER, 1)

    # Minimum rotated rectangle for width/depth
    mrr = geom.minimum_rotated_rectangle
    if mrr is None or mrr.is_empty:
        return LotDimensions(width_ft=0, depth_ft=0, area_sqft=area_sqft)

    coords = list(mrr.exterior.coords)
    # Rectangle has 5 coords (closed ring), 4 unique corners
    side1 = _distance_ft(coords[0], coords[1], lat)
    side2 = _distance_ft(coords[1], coords[2], lat)

    width_ft = round(min(side1, side2), 1)
    depth_ft = round(max(side1, side2), 1)

    return LotDimensions(width_ft=width_ft, depth_ft=depth_ft, area_sqft=area_sqft)
