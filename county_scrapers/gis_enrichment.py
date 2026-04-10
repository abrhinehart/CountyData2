"""
gis_enrichment.py - Enrich deed records with parcel data from ArcGIS FeatureServer.

Joins deed records (by book/page) to GIS parcels to add situs address,
acreage, assessed values, and centroid lat/lon. Best-effort: only matches
when the deed in our data is still the most recent deed on the parcel in GIS.

Usage:
    from county_scrapers.gis_enrichment import enrich_from_gis

    enrich_from_gis(rows, gis_url="https://gis.cmpdd.org/server/rest/...",
                    field_map=MADISON_FIELDS)
"""

import logging
import time

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

log = logging.getLogger(__name__)

# Standard field maps per county GIS layer.
# Keys: deed_book, deed_page, address (str or [num, name]), acreage, value
MADISON_FIELDS = {
    'deed_book': 'deed_book',
    'deed_page': 'deed_page',
    'address': ['street_number', 'street_name'],
    'acreage': ['arcacres', 'total_acres'],
    'value': 'true_total_value',
}

DESOTO_FIELDS = {
    'deed_book': 'DEED_BOOK1',
    'deed_page': 'DEED_PAGE1',
    'address': 'FULL_ADDR',
    'acreage': 'ACREAGE',
    'value': 'TOT_APVAL',
}

HARRISON_FIELDS = {
    'deed_book': None,  # no deed cross-ref
    'deed_page': None,
    'address': 'addCalc',
    'acreage': 'CALC_ACRE',
    'value': None,
}

# Default field map (Madison CMPDD format)
DEFAULT_FIELDS = MADISON_FIELDS


def _build_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=1.5,
                  status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('https://', adapter)
    session.mount('http://', adapter)
    return session


def _build_out_fields(field_map: dict) -> str:
    """Build the outFields parameter from a field map."""
    fields = set()
    for key, val in field_map.items():
        if val is None:
            continue
        if isinstance(val, list):
            fields.update(val)
        else:
            fields.add(val)
    return ','.join(sorted(fields))


def _centroid(geometry: dict) -> tuple[float, float] | None:
    """Calculate centroid (lat, lon) from ArcGIS polygon geometry."""
    rings = geometry.get('rings')
    if not rings:
        return None
    # Use all points from all rings
    all_x = []
    all_y = []
    for ring in rings:
        for point in ring:
            all_x.append(point[0])
            all_y.append(point[1])
    if not all_x:
        return None
    return (sum(all_y) / len(all_y), sum(all_x) / len(all_x))  # (lat, lon)


def _query_gis_by_books(gis_url: str, books: list[str],
                        field_map: dict,
                        session: requests.Session) -> dict[tuple[str, str], dict]:
    """Query GIS for all parcels in the given deed books.

    Returns a dict keyed by (book, page) -> {attributes, centroid}.
    """
    book_field = field_map.get('deed_book')
    page_field = field_map.get('deed_page')
    if not book_field or not page_field:
        return {}

    lookup = {}
    book_list = ','.join(f"'{b}'" for b in books)
    where = f"{book_field} IN ({book_list})"

    out_fields = _build_out_fields(field_map)
    offset = 0
    page_size = 2000

    while True:
        resp = session.get(
            f'{gis_url}/query',
            params={
                'where': where,
                'outFields': out_fields,
                'returnGeometry': 'true',
                'outSR': '4326',
                'f': 'json',
                'resultRecordCount': str(page_size),
                'resultOffset': str(offset),
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        features = data.get('features', [])

        if not features:
            break

        for feat in features:
            attrs = feat.get('attributes', {})
            book = str(attrs.get(book_field) or '').strip()
            page = str(attrs.get(page_field) or '').strip()
            if book and page:
                entry = dict(attrs)
                geom = feat.get('geometry')
                if geom:
                    entry['_centroid'] = _centroid(geom)
                lookup[(book, page)] = entry

        if len(features) < page_size:
            break
        offset += page_size
        time.sleep(0.5)

    return lookup


def _get_address(parcel: dict, field_map: dict) -> str | None:
    """Extract address from parcel using field_map."""
    addr_spec = field_map.get('address')
    if not addr_spec:
        return None
    if isinstance(addr_spec, list):
        # [street_number, street_name] format
        num = parcel.get(addr_spec[0])
        name = parcel.get(addr_spec[1]) or ''
        if num and name:
            return f'{int(num)} {name}'.strip()
        if name:
            return name.strip()
        return None
    else:
        # Single combined address field
        val = parcel.get(addr_spec) or ''
        return val.strip() or None


def _get_acreage(parcel: dict, field_map: dict) -> float | None:
    """Extract acreage from parcel using field_map."""
    spec = field_map.get('acreage')
    if not spec:
        return None
    if isinstance(spec, list):
        # Try fields in order, take first non-zero
        for field in spec:
            val = parcel.get(field)
            if val and float(val) > 0:
                return float(val)
        return None
    else:
        val = parcel.get(spec)
        if val and float(val) > 0:
            return float(val)
        return None


def _get_value(parcel: dict, field_map: dict) -> float | None:
    """Extract assessed value from parcel using field_map."""
    spec = field_map.get('value')
    if not spec:
        return None
    val = parcel.get(spec)
    if val and float(val) > 0:
        return float(val)
    return None


def enrich_from_gis(rows: list[dict], gis_url: str,
                    field_map: dict | None = None,
                    request_delay: float = 0.5) -> int:
    """Enrich deed records in-place with GIS parcel data.

    Joins on book + page. Adds situs_address, gis_acreage, gis_value,
    latitude, longitude fields.
    Returns the number of records enriched.
    """
    if field_map is None:
        field_map = DEFAULT_FIELDS

    book_field = field_map.get('deed_book')
    if not book_field:
        log.info('No deed_book field in GIS config — skipping enrichment')
        return 0

    # Collect unique deed books
    books = set()
    for row in rows:
        book = row.get('book', '').strip()
        if book and book.isdigit():
            books.add(book)

    if not books:
        log.info('No deed book references to look up in GIS')
        return 0

    log.info('Looking up %d unique deed books in GIS...', len(books))

    session = _build_session()

    # Query in batches of 50 books at a time
    book_list = sorted(books)
    lookup = {}
    batch_size = 50

    for i in range(0, len(book_list), batch_size):
        batch = book_list[i:i + batch_size]
        batch_results = _query_gis_by_books(gis_url, batch, field_map, session)
        lookup.update(batch_results)
        if i + batch_size < len(book_list):
            time.sleep(request_delay)

    log.info('GIS lookup returned %d parcels', len(lookup))

    # Enrich rows
    enriched = 0
    for row in rows:
        book = row.get('book', '').strip()
        page = row.get('page', '').strip()
        key = (book, page)

        parcel = lookup.get(key)
        if not parcel:
            continue

        added = False

        address = _get_address(parcel, field_map)
        if address:
            row['situs_address'] = address
            added = True

        acreage = _get_acreage(parcel, field_map)
        if acreage:
            row['gis_acreage'] = f'{acreage:.3f}'
            added = True

        value = _get_value(parcel, field_map)
        if value:
            row['gis_value'] = str(int(value))
            added = True

        centroid = parcel.get('_centroid')
        if centroid:
            row['latitude'] = f'{centroid[0]:.6f}'
            row['longitude'] = f'{centroid[1]:.6f}'
            added = True

        if added:
            enriched += 1

    log.info('Enriched %d/%d records from GIS (%d%%)',
             enriched, len(rows),
             100 * enriched // max(len(rows), 1))
    return enriched
