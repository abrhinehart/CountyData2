"""
import_subdivision_polygons.py - Import subdivision boundary polygons from
Florida county ArcGIS REST services into the shared PostGIS database.

Fetches polygon geometries via paginated ArcGIS REST queries, converts to
PostGIS MultiPolygon (SRID 4326), and upserts into the subdivisions table.
Idempotent: safe to re-run. Matches on (canonical_name, county) to update
existing records rather than creating duplicates.

Usage:
    python -m tools.import_subdivision_polygons                        # All counties
    python -m tools.import_subdivision_polygons --county Bay           # Single county
    python -m tools.import_subdivision_polygons --county Bay Lee       # Multiple
    python -m tools.import_subdivision_polygons --dry-run              # Preview only
"""

from __future__ import annotations

import argparse
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import psycopg2
import requests
from shapely.geometry import MultiPolygon, Point, Polygon
from shapely.validation import make_valid

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import DATABASE_URL


# ---------------------------------------------------------------------------
# County layer configuration
# ---------------------------------------------------------------------------

COUNTY_LAYERS = {
    'Bay': {
        'url': 'https://gis.baycountyfl.gov/arcgis/rest/services/Property/MapServer/2',
        'name_field': 'SUBDIVID',
        'extra_fields': {
            'plat_book': 'PLATTBOOK',
            'plat_page': 'BOOKPAGE',
        },
    },
    'Brevard': {
        'url': 'https://gis.brevardfl.gov/gissrv/rest/services/Base_Map/Subdivisions_WKID2881/MapServer/0',
        'name_field': 'Name',
    },
    'Escambia': {
        'url': 'https://gismaps.myescambia.com/arcgis/rest/services/Escambia_County/MapServer/1',
        'name_field': 'NAME',
        'extra_fields': {
            'plat_page': 'BOOKPAGE',
        },
    },
    'Lake': {
        'url': 'https://gis.lakecountyfl.gov/lakegis/rest/services/InteractiveMap/MapServer/12',
        'name_field': 'Name',
    },
    'Lee': {
        'url': 'https://gissvr.leepa.org/gissvr/rest/services/ParcelDetails/MapServer/33',
        'name_field': 'Name',
    },
    'Leon': {
        'url': 'https://intervector.leoncountyfl.gov/intervector/rest/services/MapServices/TLC_OverlaySubdivision_D_WM/MapServer/0',
        'name_field': 'SUBDIVISION_NAME',
    },
    'Okaloosa': {
        'url': 'https://gis.myokaloosa.com/arcgis/rest/services/BaseMap_Layers/MapServer/108',
        'name_field': 'PATSUB_SUB_NAME',
    },
    'Orange': {
        'url': 'https://ocgis4.ocfl.net/arcgis/rest/services/Public_Dynamic/MapServer/111',
        'name_field': 'SUBDIVISION_NAME',
        'extra_fields': {
            'plat_book': 'SUBDIVISION_PLAT',
            'plat_page': 'SUBDIVISION_PAGE',
            'developer_name': 'DEVELOPER_NAME',
            'recorded_date': 'RECORDED_DATE',
            'platted_acreage': 'PLATTED_ACREAGE',
        },
    },
    'Polk': {
        'url': 'https://gis.polk-county.net/server/rest/services/Map_Property_Appraiser/MapServer/3',
        'name_field': 'NAME',
    },
    'Santa Rosa': {
        'url': 'https://services.arcgis.com/Eg4L1xEv2R3abuQd/arcgis/rest/services/SubdivisionsOpenData/FeatureServer/0',
        'name_field': 'Subdivisio',
    },
}


# ---------------------------------------------------------------------------
# ArcGIS REST fetching
# ---------------------------------------------------------------------------

REQUEST_TIMEOUT = 60
BATCH_SIZE = 1000
DELAY_SECONDS = 0.5


def fetch_features(url: str) -> list[dict]:
    """Paginate through an ArcGIS REST /query endpoint, returning all features."""
    all_features = []
    offset = 0

    while True:
        params = {
            'where': '1=1',
            'outFields': '*',
            'returnGeometry': 'true',
            'outSR': '4326',
            'f': 'json',
            'resultOffset': offset,
            'resultRecordCount': BATCH_SIZE,
        }

        resp = requests.get(f'{url}/query', params=params, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()

        if 'error' in data:
            raise RuntimeError(f"ArcGIS error: {data['error']}")

        features = data.get('features', [])
        if not features:
            break

        all_features.extend(features)
        print(f'    Fetched {len(all_features)} features so far...')

        if not data.get('exceededTransferLimit', False):
            break

        offset += len(features)
        time.sleep(DELAY_SECONDS)

    return all_features


# ---------------------------------------------------------------------------
# Geometry conversion (ArcGIS JSON → Shapely MultiPolygon)
# ---------------------------------------------------------------------------

def _signed_area(ring: list[list[float]]) -> float:
    """Signed area via shoelace formula. Negative = clockwise (ArcGIS exterior)."""
    return sum(
        ring[i][0] * ring[i + 1][1] - ring[i + 1][0] * ring[i][1]
        for i in range(len(ring) - 1)
    ) / 2


def arcgis_to_multipolygon(geometry: dict) -> MultiPolygon | None:
    """Convert an ArcGIS JSON geometry (rings) to a Shapely MultiPolygon."""
    rings = geometry.get('rings', [])
    if not rings:
        return None

    # Classify rings: clockwise (negative area) = exterior, else = hole
    exteriors = []
    holes = []
    for ring in rings:
        if len(ring) < 4:
            continue
        coords = [(pt[0], pt[1]) for pt in ring]
        if _signed_area(ring) < 0:
            exteriors.append(coords)
        else:
            holes.append(coords)

    if not exteriors:
        # Fallback: treat all rings as exteriors (server didn't follow convention)
        exteriors = [[(pt[0], pt[1]) for pt in r] for r in rings if len(r) >= 4]
        holes = []

    if not exteriors:
        return None

    # Single exterior: straightforward
    if len(exteriors) == 1:
        poly = Polygon(exteriors[0], holes)
        if not poly.is_valid:
            poly = make_valid(poly)
        return _ensure_multi(poly)

    # Multiple exteriors: assign each hole to its containing exterior
    polys = []
    unassigned_holes = list(holes)
    for ext_coords in exteriors:
        ext_poly = Polygon(ext_coords)
        my_holes = []
        still_unassigned = []
        for hole in unassigned_holes:
            if ext_poly.contains(Point(hole[0][0], hole[0][1])):
                my_holes.append(hole)
            else:
                still_unassigned.append(hole)
        unassigned_holes = still_unassigned
        poly = Polygon(ext_coords, my_holes)
        if not poly.is_valid:
            poly = make_valid(poly)
        # Flatten: make_valid can return MultiPolygon or GeometryCollection
        polys.extend(_flatten_to_polygons(poly))

    return MultiPolygon(polys) if polys else None


def _flatten_to_polygons(geom) -> list[Polygon]:
    """Extract all Polygon geometries from any geometry type."""
    if geom is None or geom.is_empty:
        return []
    if geom.geom_type == 'Polygon':
        return [geom]
    if geom.geom_type == 'MultiPolygon':
        return list(geom.geoms)
    if geom.geom_type == 'GeometryCollection':
        result = []
        for g in geom.geoms:
            result.extend(_flatten_to_polygons(g))
        return result
    return []


def _ensure_multi(geom) -> MultiPolygon | None:
    """Normalize any polygon-like geometry to MultiPolygon."""
    if geom is None or geom.is_empty:
        return None
    if geom.geom_type == 'MultiPolygon':
        return geom
    if geom.geom_type == 'Polygon':
        return MultiPolygon([geom])
    if geom.geom_type == 'GeometryCollection':
        polys = [g for g in geom.geoms if g.geom_type in ('Polygon', 'MultiPolygon')]
        flat = []
        for p in polys:
            if p.geom_type == 'MultiPolygon':
                flat.extend(p.geoms)
            else:
                flat.append(p)
        return MultiPolygon(flat) if flat else None
    return None


# ---------------------------------------------------------------------------
# Attribute extraction helpers
# ---------------------------------------------------------------------------

def _extract_name(attrs: dict, name_field: str) -> str | None:
    """Extract and clean the subdivision name from feature attributes."""
    raw = attrs.get(name_field)
    if raw is None:
        return None
    name = str(raw).strip()
    if not name or name.upper() in ('', 'NONE', 'NULL', 'N/A', 'UNPLATTED', 'UNKNOWN'):
        return None
    return name


def _extract_extra(attrs: dict, extra_fields: dict) -> dict:
    """Extract optional metadata fields based on county config."""
    result = {}
    for db_col, src_field in extra_fields.items():
        val = attrs.get(src_field)
        if val is None or str(val).strip() in ('', 'None', 'Null'):
            continue

        if db_col == 'recorded_date':
            result[db_col] = _parse_date(val)
        elif db_col == 'platted_acreage':
            try:
                result[db_col] = float(val)
            except (ValueError, TypeError):
                pass
        else:
            result[db_col] = str(val).strip()
    return result


def _parse_date(val) -> str | None:
    """Parse an ArcGIS date value (epoch millis or string) to ISO date string."""
    if isinstance(val, (int, float)) and val > 1e10:
        # Epoch milliseconds
        try:
            return datetime.fromtimestamp(val / 1000, tz=timezone.utc).strftime('%Y-%m-%d')
        except (OSError, ValueError):
            return None
    if isinstance(val, str):
        for fmt in ('%m/%d/%Y', '%Y-%m-%d', '%Y/%m/%d'):
            try:
                return datetime.strptime(val.strip(), fmt).strftime('%Y-%m-%d')
            except ValueError:
                continue
    return None


# ---------------------------------------------------------------------------
# Database operations
# ---------------------------------------------------------------------------

def load_county_ids(conn) -> dict[str, int]:
    """Load county name → id mapping from the counties table."""
    with conn.cursor() as cur:
        cur.execute("SELECT id, name FROM counties")
        return {name: cid for cid, name in cur.fetchall()}


def upsert_subdivision(cur, canonical_name: str, county: str, county_id: int,
                       wkb_hex: str, extras: dict) -> str:
    """
    Upsert a subdivision with geometry. Returns 'inserted', 'updated', or 'skipped'.

    Uses case-insensitive lookup to match existing records, avoiding duplicates
    when GIS names differ in case from seed data.
    """
    # Check for existing record (case-insensitive)
    cur.execute("""
        SELECT id, canonical_name FROM subdivisions
        WHERE UPPER(canonical_name) = UPPER(%s) AND UPPER(county) = UPPER(%s)
    """, (canonical_name, county))
    existing = cur.fetchone()

    if existing:
        sub_id, existing_name = existing
        set_parts = [
            "geom = ST_GeomFromWKB(decode(%s, 'hex'), 4326)",
            "source = %s",
            "county_id = COALESCE(county_id, %s)",
            "updated_at = NOW()",
        ]
        params = [wkb_hex, 'gis_import', county_id]

        for col in ('plat_book', 'plat_page', 'developer_name', 'recorded_date', 'platted_acreage'):
            if col in extras:
                set_parts.append(f"{col} = COALESCE(%s, {col})")
                params.append(extras[col])

        params.append(sub_id)
        cur.execute(
            f"UPDATE subdivisions SET {', '.join(set_parts)} WHERE id = %s",
            params,
        )
        return 'updated'
    else:
        cols = ['canonical_name', 'county', 'county_id', 'geom', 'source', 'updated_at']
        vals = [canonical_name, county, county_id,
                "placeholder", 'gis_import', "placeholder"]
        placeholders = [
            '%s', '%s', '%s',
            "ST_GeomFromWKB(decode(%s, 'hex'), 4326)",
            '%s', 'NOW()',
        ]
        params = [canonical_name, county, county_id, wkb_hex, 'gis_import']

        for col in ('plat_book', 'plat_page', 'developer_name', 'recorded_date', 'platted_acreage'):
            if col in extras:
                cols.append(col)
                placeholders.append('%s')
                params.append(extras[col])

        cur.execute(
            f"INSERT INTO subdivisions ({', '.join(cols)}) VALUES ({', '.join(placeholders)})",
            params,
        )
        return 'inserted'


# ---------------------------------------------------------------------------
# Per-county import
# ---------------------------------------------------------------------------

def import_county(county_name: str, layer_config: dict, conn,
                  county_ids: dict, dry_run: bool = False) -> dict:
    """
    Import all subdivision polygons for one county.
    Returns summary dict with counts.
    """
    summary = {'fetched': 0, 'inserted': 0, 'updated': 0, 'skipped': 0, 'errors': 0}

    county_id = county_ids.get(county_name)
    if county_id is None:
        print(f'  [{county_name}] ERROR: County not found in counties table')
        summary['errors'] = 1
        return summary

    url = layer_config['url']
    name_field = layer_config['name_field']
    extra_fields = layer_config.get('extra_fields', {})

    # Fetch all features
    print(f'  [{county_name}] Fetching from {url}')
    try:
        features = fetch_features(url)
    except Exception as e:
        print(f'  [{county_name}] ERROR fetching: {e}')
        summary['errors'] = 1
        return summary

    summary['fetched'] = len(features)
    print(f'  [{county_name}] {len(features)} features fetched')

    if not features:
        return summary

    # Group features by subdivision name (merge multi-feature subdivisions)
    by_name: dict[str, dict] = {}
    for feature in features:
        attrs = feature.get('attributes', {})
        geom_json = feature.get('geometry')

        name = _extract_name(attrs, name_field)
        if not name:
            summary['skipped'] += 1
            continue

        if name not in by_name:
            by_name[name] = {
                'geometries': [],
                'extras': _extract_extra(attrs, extra_fields),
            }

        if geom_json:
            mp = arcgis_to_multipolygon(geom_json)
            if mp:
                by_name[name]['geometries'].extend(mp.geoms)

    print(f'  [{county_name}] {len(by_name)} unique subdivisions')

    if dry_run:
        for name in sorted(by_name)[:10]:
            n_polys = len(by_name[name]['geometries'])
            print(f'    {name} ({n_polys} polygon(s))')
        if len(by_name) > 10:
            print(f'    ... and {len(by_name) - 10} more')
        summary['skipped'] = len(by_name)  # all counted as skipped in dry-run
        return summary

    # Upsert each subdivision
    with conn.cursor() as cur:
        for name, data in by_name.items():
            if not data['geometries']:
                summary['skipped'] += 1
                continue

            try:
                merged = MultiPolygon(data['geometries'])
                if not merged.is_valid:
                    merged = make_valid(merged)
                    merged = _ensure_multi(merged)
                if merged is None or merged.is_empty:
                    summary['skipped'] += 1
                    continue

                wkb_hex = merged.wkb_hex
                result = upsert_subdivision(
                    cur, name, county_name, county_id, wkb_hex, data['extras'],
                )
                summary[result] += 1
            except Exception as e:
                conn.rollback()
                print(f'  [{county_name}] ERROR upserting "{name}": {e}')
                summary['errors'] += 1

    conn.commit()
    return summary


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description='Import subdivision polygons from Florida county GIS servers',
    )
    parser.add_argument(
        '--county', nargs='+', metavar='COUNTY',
        help=f'County/counties to import (default: all). Available: {", ".join(sorted(COUNTY_LAYERS))}',
    )
    parser.add_argument(
        '--dry-run', action='store_true',
        help='Fetch and preview without writing to database',
    )
    args = parser.parse_args()

    # Determine which counties to process
    if args.county:
        layer_keys = {k.upper(): k for k in COUNTY_LAYERS}
        to_run = {}
        for requested in args.county:
            match = layer_keys.get(requested.upper())
            if match is None:
                print(f"Unknown county: {requested}")
                print(f"Available: {', '.join(sorted(COUNTY_LAYERS))}")
                sys.exit(1)
            to_run[match] = COUNTY_LAYERS[match]
    else:
        to_run = COUNTY_LAYERS

    conn = psycopg2.connect(DATABASE_URL)
    try:
        county_ids = load_county_ids(conn)
        results = {}

        for county_name, layer_config in to_run.items():
            print(f'\n[{county_name}]')
            results[county_name] = import_county(
                county_name, layer_config, conn, county_ids, dry_run=args.dry_run,
            )

    finally:
        conn.close()

    # Print summary
    print()
    print(f"{'County':<15} {'Fetched':>8} {'Unique':>8} {'Inserted':>9} {'Updated':>8} {'Skipped':>8} {'Errors':>7}")
    print('-' * 70)
    totals = {'fetched': 0, 'inserted': 0, 'updated': 0, 'skipped': 0, 'errors': 0}
    for county_name, s in results.items():
        unique = s['inserted'] + s['updated'] + s['skipped']
        print(f"{county_name:<15} {s['fetched']:>8} {unique:>8} {s['inserted']:>9} {s['updated']:>8} {s['skipped']:>8} {s['errors']:>7}")
        for k in totals:
            totals[k] += s[k]
    total_unique = totals['inserted'] + totals['updated'] + totals['skipped']
    print('-' * 70)
    print(f"{'TOTAL':<15} {totals['fetched']:>8} {total_unique:>8} {totals['inserted']:>9} {totals['updated']:>8} {totals['skipped']:>8} {totals['errors']:>7}")


if __name__ == '__main__':
    main()
