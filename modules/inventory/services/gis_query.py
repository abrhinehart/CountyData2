"""ArcGIS REST API query engine with pagination and per-county field mapping."""

import logging
import math
import re
import time
from dataclasses import dataclass, field

import httpx

from modules.inventory.models import BiCountyConfig, County

logger = logging.getLogger(__name__)

SQFT_PER_ACRE = 43_560
SQM_PER_ACRE = 4_046.8564224

# Acreage field names that are geometry-computed area in Web Mercator (EPSG:3857).
# These need cos²(lat) correction before converting sqm → acres.
_GEO_AREA_TOKENS = ("shapestarea", "shapearea", "shape__area")

# Acreage field names that contain square footage instead of acres.
_SQFT_TOKENS = ("gissquarefoot", "lotsize")


def _is_geo_area_field(field_name: str | None) -> bool:
    if not field_name:
        return False
    normalized = field_name.lower().replace("_", "").replace(".", "").replace("(", "").replace(")", "")
    return normalized in _GEO_AREA_TOKENS


def _is_sqft_field(field_name: str | None) -> bool:
    if not field_name:
        return False
    normalized = field_name.lower().replace("_", "").replace(".", "")
    return normalized in _SQFT_TOKENS


def _centroid_lat(geom_raw: dict | None) -> float | None:
    """Extract approximate latitude from ArcGIS geometry (already in 4326)."""
    if not geom_raw:
        return None
    rings = geom_raw.get("rings")
    if not rings or not rings[0]:
        return None
    # Average the y-coordinates of the first ring
    ys = [pt[1] for pt in rings[0] if len(pt) >= 2]
    return sum(ys) / len(ys) if ys else None


def _mercator_sqm_to_acres(sqm: float, lat_deg: float) -> float:
    """Convert Web Mercator square meters to true acres using cos²(lat) correction."""
    lat_rad = math.radians(lat_deg)
    true_sqm = sqm * math.cos(lat_rad) ** 2
    return round(true_sqm / SQM_PER_ACRE, 4)


def _parse_acreage(raw, geo_area: bool = False, sqft: bool = False, lat: float | None = None) -> float | None:
    """Parse acreage from numeric or string values.

    Handles formats like: 0.25, "0.1687 a", "107338 sq.ft", "0.25"
    When geo_area=True, treats plain numeric values as Web Mercator sqm
    and applies cos²(lat) correction.
    When sqft=True, treats plain numeric values as square feet and converts to acres.
    """
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        if geo_area and lat is not None:
            return _mercator_sqm_to_acres(float(raw), lat)
        if sqft:
            return round(float(raw) / SQFT_PER_ACRE, 4)
        return float(raw)
    s = str(raw).strip().lower()
    if not s:
        return None
    # Try plain numeric first
    try:
        val = float(s)
        if geo_area and lat is not None:
            return _mercator_sqm_to_acres(val, lat)
        if sqft:
            return round(val / SQFT_PER_ACRE, 4)
        return val
    except ValueError:
        pass
    # Extract leading number, then check unit suffix
    m = re.match(r"^([\d.,]+)\s*(.*)", s)
    if not m:
        return None
    try:
        value = float(m.group(1).replace(",", ""))
    except ValueError:
        return None
    unit = m.group(2).strip()
    if unit in ("a", "ac", "acre", "acres"):
        return value
    if unit in ("sq.ft", "sqft", "sq ft", "sf"):
        return round(value / SQFT_PER_ACRE, 4)
    # Unknown unit — assume acres
    return value

def _parse_numeric(raw) -> float | None:
    """Parse a numeric value from various formats."""
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        return float(raw)
    try:
        return float(str(raw).strip())
    except (ValueError, TypeError):
        return None


class AdaptiveDelay:
    """Adaptive politeness delay that adjusts based on server response behavior.

    Starts at `base` seconds. Backs off when responses are slow (>5s) or on
    errors. Recovers toward the base after consecutive fast successes.
    """

    def __init__(self, base: float = 0.3, floor: float = 0.2, ceiling: float = 3.0):
        self.base = base
        self.floor = floor
        self.ceiling = ceiling
        self.current = base
        self._consecutive_fast = 0

    def record_success(self, response_time: float) -> None:
        """Adjust delay after a successful request."""
        if response_time > 5.0:
            # Server is slow — increase delay
            self.current = min(self.current + 0.2, self.ceiling)
            self._consecutive_fast = 0
        elif response_time < 2.0:
            self._consecutive_fast += 1
            if self._consecutive_fast >= 3:
                # 3 fast responses in a row — ease off
                self.current = max(self.current - 0.1, self.floor)
                self._consecutive_fast = 0
        else:
            # Normal speed — hold steady
            self._consecutive_fast = 0

    def record_error(self) -> None:
        """Double the delay after an error (up to ceiling)."""
        self.current = min(self.current * 2, self.ceiling)
        self._consecutive_fast = 0

    def wait(self) -> None:
        """Sleep for the current delay."""
        time.sleep(self.current)


@dataclass
class GISFieldMapping:
    owner: str
    parcel: str
    address: str
    use_type: str
    acreage: str
    subdivision: str | None = None
    building_value: str | None = None
    appraised_value: str | None = None
    deed_date: str | None = None
    previous_owner: str | None = None
    acreage_is_geo_area: bool = False
    acreage_is_sqft: bool = False


@dataclass
class GISConfig:
    endpoint: str
    fields: GISFieldMapping
    max_records: int = 1000
    max_aliases_per_batch: int | None = None


@dataclass
class ParsedParcel:
    parcel_number: str
    owner_name: str | None = None
    site_address: str | None = None
    use_type: str | None = None
    acreage: float | None = None
    subdivision_name: str | None = None
    building_value: float | None = None
    appraised_value: float | None = None
    deed_date: str | None = None  # ISO string or epoch ms
    previous_owner: str | None = None
    geometry: dict | None = None  # GeoJSON dict


class GISQueryEngine:
    def __init__(self, config: GISConfig, client: httpx.Client | None = None):
        self.config = config
        self.client = client or httpx.Client(timeout=60.0)
        self.delay = AdaptiveDelay(base=0.3)

    # Max WHERE clause length before splitting a batch into multiple queries.
    MAX_WHERE_LENGTH = 2000

    def _query_with_where(self, where: str, label: str = "") -> list[ParsedParcel]:
        """Execute a paginated ArcGIS query with the given WHERE clause."""
        all_parcels: list[ParsedParcel] = []
        offset = 0

        while True:
            params = {
                "where": where,
                "outFields": "*",
                "returnGeometry": "true",
                "outSR": "4326",
                "f": "json",
                "resultOffset": str(offset),
                "resultRecordCount": str(self.config.max_records),
            }

            url = f"{self.config.endpoint}/query"
            logger.debug(f"GIS query: {url} offset={offset} {label}")

            t0 = time.monotonic()
            resp = self.client.get(url, params=params)
            resp.raise_for_status()
            elapsed = time.monotonic() - t0
            data = resp.json()

            if "error" in data:
                logger.error(f"ArcGIS error {label}: {data['error']}")
                self.delay.record_error()
                break

            self.delay.record_success(elapsed)

            features = data.get("features", [])
            for feat in features:
                parsed = self._parse_feature(feat)
                if parsed and parsed.parcel_number:
                    all_parcels.append(parsed)

            exceeded = data.get("exceededTransferLimit", False)
            if exceeded and len(features) > 0:
                offset += len(features)
                self.delay.wait()
            else:
                break

        return all_parcels

    def query_by_owner(self, alias: str) -> list[ParsedParcel]:
        """Query all parcels matching owner LIKE '%alias%', with pagination."""
        safe_alias = alias.replace("'", "''")
        where = f"{self.config.fields.owner} LIKE '%{safe_alias}%'"
        results = self._query_with_where(where, label=f"alias='{alias}'")
        logger.info(f"Alias '{alias}': {len(results)} parcels returned")
        return results

    def _build_or_where(self, aliases: list[str]) -> str:
        """Build a WHERE clause combining multiple aliases with OR."""
        owner = self.config.fields.owner
        clauses = [f"{owner} LIKE '%{a.replace(chr(39), chr(39)*2)}%'" for a in aliases]
        return " OR ".join(clauses)

    def query_by_owner_batch(self, aliases: list[str]) -> list[ParsedParcel]:
        """Query parcels matching any of several aliases in a single request.

        Batches aliases into combined OR WHERE clauses. If the WHERE would
        exceed MAX_WHERE_LENGTH, or the county-specific alias cap is reached,
        splits into multiple queries.
        """
        if not aliases:
            return []
        if len(aliases) == 1:
            return self.query_by_owner(aliases[0])

        # Split into chunks that fit within the WHERE length limit
        all_parcels: list[ParsedParcel] = []
        chunk: list[str] = []
        max_aliases = self.config.max_aliases_per_batch

        for alias in aliases:
            test_chunk = chunk + [alias]
            test_where = self._build_or_where(test_chunk)
            exceeds_alias_cap = bool(max_aliases and len(test_chunk) > max_aliases)
            if (len(test_where) > self.MAX_WHERE_LENGTH or exceeds_alias_cap) and chunk:
                # Execute current chunk, start new one
                where = self._build_or_where(chunk)
                label = f"batch({len(chunk)} aliases)"
                all_parcels.extend(self._query_with_where(where, label=label))
                logger.info(f"{label}: {len(all_parcels)} parcels so far")
                self.delay.wait()
                chunk = [alias]
            else:
                chunk = test_chunk

        # Execute remaining chunk
        if chunk:
            where = self._build_or_where(chunk)
            label = f"batch({len(chunk)} aliases)"
            results = self._query_with_where(where, label=label)
            all_parcels.extend(results)
            logger.info(f"{label}: {len(results)} parcels returned")

        return all_parcels

    def _parse_feature(self, feature: dict) -> ParsedParcel | None:
        attrs = feature.get("attributes", {})
        geom_raw = feature.get("geometry")

        f = self.config.fields
        parcel_number = attrs.get(f.parcel)
        if not parcel_number:
            return None

        acreage_raw = attrs.get(f.acreage)
        lat = _centroid_lat(geom_raw) if f.acreage_is_geo_area else None
        acreage = _parse_acreage(acreage_raw, geo_area=f.acreage_is_geo_area, sqft=f.acreage_is_sqft, lat=lat)

        geometry = None
        if geom_raw:
            geometry = self._arcgis_to_geojson(geom_raw)

        subdivision_name = None
        if f.subdivision:
            raw_sub = attrs.get(f.subdivision)
            if raw_sub and str(raw_sub).strip():
                subdivision_name = str(raw_sub).strip()

        building_value = _parse_numeric(attrs.get(f.building_value)) if f.building_value else None
        appraised_value = _parse_numeric(attrs.get(f.appraised_value)) if f.appraised_value else None

        deed_date = None
        if f.deed_date:
            raw_deed = attrs.get(f.deed_date)
            if raw_deed is not None:
                deed_date = str(raw_deed)

        previous_owner = None
        if f.previous_owner:
            raw_prev = attrs.get(f.previous_owner)
            if raw_prev and str(raw_prev).strip():
                previous_owner = str(raw_prev).strip()

        return ParsedParcel(
            parcel_number=str(parcel_number).strip(),
            owner_name=attrs.get(f.owner),
            site_address=attrs.get(f.address),
            use_type=attrs.get(f.use_type),
            acreage=acreage,
            subdivision_name=subdivision_name,
            building_value=building_value,
            appraised_value=appraised_value,
            deed_date=deed_date,
            previous_owner=previous_owner,
            geometry=geometry,
        )

    @staticmethod
    def _signed_area(ring: list) -> float:
        """Signed area via shoelace formula. Negative = clockwise (ArcGIS exterior)."""
        return sum(
            ring[i][0] * ring[i + 1][1] - ring[i + 1][0] * ring[i][1]
            for i in range(len(ring) - 1)
        ) / 2

    def _arcgis_to_geojson(self, geom: dict) -> dict | None:
        """Convert ArcGIS JSON geometry to GeoJSON.

        ArcGIS convention: clockwise rings are exterior shells,
        counter-clockwise rings are holes.  Multiple exteriors
        produce a MultiPolygon; holes are assigned to the exterior
        that contains their first vertex.
        """
        rings = geom.get("rings")
        if not rings:
            return None

        # Single ring — fast path
        if len(rings) == 1:
            return {"type": "Polygon", "coordinates": rings}

        # Classify rings as exterior (clockwise, negative area) or hole
        exteriors = []
        holes = []
        for ring in rings:
            if len(ring) < 4:
                continue
            if self._signed_area(ring) < 0:
                exteriors.append(ring)
            else:
                holes.append(ring)

        # Fallback: if classification found no exteriors, treat all as exteriors
        if not exteriors:
            exteriors = [r for r in rings if len(r) >= 4]
            holes = []

        if not exteriors:
            return None

        # Single exterior — all holes belong to it
        if len(exteriors) == 1:
            return {"type": "Polygon", "coordinates": [exteriors[0]] + holes}

        # Multiple exteriors — assign each hole to the containing exterior
        from shapely.geometry import Point, Polygon as ShapelyPolygon

        poly_coords: list[list] = []
        unassigned = list(holes)
        for ext in exteriors:
            ext_poly = ShapelyPolygon([(pt[0], pt[1]) for pt in ext])
            my_holes = []
            still_unassigned = []
            for hole in unassigned:
                if ext_poly.contains(Point(hole[0][0], hole[0][1])):
                    my_holes.append(hole)
                else:
                    still_unassigned.append(hole)
            unassigned = still_unassigned
            poly_coords.append([ext] + my_holes)

        if len(poly_coords) == 1:
            return {"type": "Polygon", "coordinates": poly_coords[0]}

        return {"type": "MultiPolygon", "coordinates": poly_coords}


def _batch_rules_for_county(county: County) -> dict[str, int]:
    """County-scoped query batching overrides for problematic endpoints."""
    if county.name == "Jefferson" and county.state == "AL":
        return {"max_aliases_per_batch": 4}
    return {}


def build_engine_for_county(county: County, config: BiCountyConfig | None = None) -> GISQueryEngine | None:
    """Build a GISQueryEngine from a County and its BiCountyConfig.

    If `config` is not provided, the caller must have already verified that
    the county has a BiCountyConfig with a gis_endpoint. Pass the config
    explicitly to avoid an extra DB query.

    Returns None if not configured.
    """
    if config is None:
        return None
    if not config.gis_endpoint:
        return None

    fields = GISFieldMapping(
        owner=config.gis_owner_field,
        parcel=config.gis_parcel_field,
        address=config.gis_address_field,
        use_type=config.gis_use_field,
        acreage=config.gis_acreage_field,
        subdivision=config.gis_subdivision_field,
        building_value=config.gis_building_value_field,
        appraised_value=config.gis_appraised_value_field,
        deed_date=config.gis_deed_date_field,
        previous_owner=config.gis_previous_owner_field,
        acreage_is_geo_area=_is_geo_area_field(config.gis_acreage_field),
        acreage_is_sqft=_is_sqft_field(config.gis_acreage_field),
    )
    gis_config = GISConfig(
        endpoint=config.gis_endpoint,
        fields=fields,
        max_records=config.gis_max_records or 1000,
        **_batch_rules_for_county(county),
    )
    return GISQueryEngine(gis_config)
