"""
gis_parcel_client.py - ArcGIS parcel layer scraper for counties without usable deed portals.

Queries ArcGIS FeatureServer/MapServer parcel layers by sale date range,
extracting deed references, owner names, addresses, values, and centroid
coordinates. Used when the county's deed portal is too complex to automate
but the GIS layer contains the same transaction data.

Usage:
    from county_scrapers.gis_parcel_client import GISParcelSession

    session = GISParcelSession(
        "https://webmap.co.jackson.ms.us/arcgis107/rest/services/JacksonCounty/Parcel_2_Web/MapServer/2",
        field_map=JACKSON_FIELDS,
    )
    session.connect()
    rows = session.search_by_date_range("01/01/2025", "01/31/2025")
"""

import logging
import time
from datetime import datetime, timedelta

from curl_cffi import requests as cf_requests

log = logging.getLogger(__name__)


# Per-county field maps: standard key -> GIS field name
JACKSON_FIELDS = {
    'owner': 'NAME',
    'owner2': 'NAME2',
    'address': 'LOCATION',
    'deed_book': 'DB',
    'deed_page': 'DP',
    'subdivision': 'SUBD',
    'lot': 'LOTNUM2',
    'acreage': 'ACREAGE',
    'total_value': 'TOTALVAL',
    'sale_amount': 'SAMT',
    'sale_date': 'SDAT',
    'section': 'SECTION',
    'township': 'TOWN',
    'range': 'RANGE',
    'legal': 'DESC1',
    'parcel_id': 'PIDN',
}


def _build_out_fields(field_map: dict) -> str:
    """Build outFields parameter from field map values."""
    fields = set()
    for val in field_map.values():
        if val:
            fields.add(val)
    return ','.join(sorted(fields))


def _centroid(geometry: dict) -> tuple[float, float] | None:
    """Calculate centroid (lat, lon) from polygon rings."""
    rings = geometry.get('rings')
    if not rings:
        return None
    all_x, all_y = [], []
    for ring in rings:
        for pt in ring:
            all_x.append(pt[0])
            all_y.append(pt[1])
    if not all_x:
        return None
    return (sum(all_y) / len(all_y), sum(all_x) / len(all_x))


class GISParcelSession:
    """Stateful client for querying ArcGIS parcel layers by sale date."""

    def __init__(self, layer_url: str, field_map: dict,
                 page_size: int = 1000, request_delay: float = 1.0):
        self.layer_url = layer_url.rstrip('/')
        self.field_map = field_map
        self.page_size = page_size
        self.request_delay = request_delay

        self._session = cf_requests.Session(impersonate='chrome')
        self._connected = False

    def connect(self) -> None:
        """Verify the layer is accessible."""
        log.info('Connecting to %s', self.layer_url)
        resp = self._session.get(f'{self.layer_url}?f=json', timeout=30)
        resp.raise_for_status()
        data = resp.json()
        log.info('Layer: %s, max records: %s',
                 data.get('name', '?'), data.get('maxRecordCount', '?'))
        self._connected = True

    def search_by_date_range(self, begin_date: str, end_date: str) -> list[dict]:
        """
        Query parcels with sale dates in the given range.

        Args:
            begin_date: MM/DD/YYYY
            end_date: MM/DD/YYYY

        Returns list of parsed record dicts.
        """
        self._ensure_connected()

        start = datetime.strptime(begin_date, '%m/%d/%Y')
        end = datetime.strptime(end_date, '%m/%d/%Y') + timedelta(days=1)

        date_field = self.field_map.get('sale_date', 'SDAT')
        where = (f"{date_field} >= date '{start.strftime('%Y-%m-%d')}' "
                 f"AND {date_field} < date '{end.strftime('%Y-%m-%d')}'")

        log.info('Searching parcels %s to %s', begin_date, end_date)

        out_fields = _build_out_fields(self.field_map)
        all_rows = []
        offset = 0

        while True:
            resp = self._session.get(
                f'{self.layer_url}/query',
                params={
                    'where': where,
                    'outFields': out_fields,
                    'returnGeometry': 'true',
                    'outSR': '4326',
                    'f': 'json',
                    'resultRecordCount': str(self.page_size),
                    'resultOffset': str(offset),
                },
                timeout=60,
            )
            resp.raise_for_status()
            data = resp.json()
            features = data.get('features', [])

            if not features:
                break

            for feat in features:
                parsed = self._parse_feature(feat)
                if parsed:
                    all_rows.append(parsed)

            log.info('  fetched %d records (offset %d)', len(features), offset)

            if len(features) < self.page_size:
                break
            offset += len(features)
            time.sleep(self.request_delay)

        log.info('Total records: %d', len(all_rows))
        return all_rows

    def _parse_feature(self, feature: dict) -> dict | None:
        """Parse a GIS feature into a record dict matching pull_records format."""
        attrs = feature.get('attributes', {})
        fm = self.field_map

        # Sale date
        sdat_raw = attrs.get(fm.get('sale_date', ''))
        if sdat_raw:
            record_date = datetime.fromtimestamp(
                int(sdat_raw) / 1000).strftime('%m/%d/%Y')
        else:
            record_date = ''

        # Sale amount
        samt = attrs.get(fm.get('sale_amount', '')) or 0

        # Build legal from structured fields
        legal_text = str(attrs.get(fm.get('legal', ''), '') or '')
        subdivision = str(attrs.get(fm.get('subdivision', ''), '') or '').strip()

        parsed = {
            'grantor': '',  # GIS only has current owner, not transaction parties
            'grantee': str(attrs.get(fm.get('owner', ''), '') or '').strip(),
            'doc_type': 'DEED',
            'record_date': record_date,
            'legal': legal_text,
            'book': str(attrs.get(fm.get('deed_book', ''), '') or '').strip(),
            'page': str(attrs.get(fm.get('deed_page', ''), '') or '').strip(),
            'book_type': '',
            'instrument': '',
            'subdivision': subdivision,
            'lot': str(attrs.get(fm.get('lot', ''), '') or '').strip(),
            'situs_address': str(attrs.get(fm.get('address', ''), '') or '').strip(),
            'gis_acreage': '',
            'gis_value': '',
        }

        # Acreage
        acreage = attrs.get(fm.get('acreage', ''))
        if acreage and float(acreage) > 0:
            parsed['gis_acreage'] = f'{float(acreage):.3f}'

        # Value
        total_val = attrs.get(fm.get('total_value', ''))
        if total_val and float(total_val) > 0:
            parsed['gis_value'] = str(int(float(total_val)))

        # Sale amount as price (unique to GIS-sourced data)
        if samt and float(samt) > 0:
            parsed['sale_amount'] = str(int(float(samt)))

        # Centroid
        geom = feature.get('geometry')
        if geom:
            centroid = _centroid(geom)
            if centroid:
                parsed['latitude'] = f'{centroid[0]:.6f}'
                parsed['longitude'] = f'{centroid[1]:.6f}'

        # Parcel ID
        pidn = attrs.get(fm.get('parcel_id', ''))
        if pidn:
            parsed['parcel_id'] = str(pidn).strip()

        return parsed if parsed.get('grantee') or parsed.get('book') else None

    def _ensure_connected(self) -> None:
        if not self._connected:
            self.connect()

    def close(self) -> None:
        self._session.close()
        self._connected = False

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
