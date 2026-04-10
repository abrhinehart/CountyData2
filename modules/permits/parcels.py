"""
Parcel ID lookup helpers for the Permit Tracker module.

Queries Bay County's public ArcGIS REST endpoint to resolve a street
address to a parcel ID.
"""
from __future__ import annotations

import json
import urllib.parse
import urllib.request
from typing import Generator

BAY_COUNTY_ARCGIS_URL = (
    "https://gis.baycountyfl.gov/arcgis/rest/services/Parcels/MapServer/0/query"
)


def batch_lookup_bay_county_parcels(
    addresses: list[str],
) -> Generator[dict, None, None]:
    """
    Look up parcel IDs for a list of addresses against the Bay County
    ArcGIS parcel layer.

    Yields one dict per address with keys:
        address, parcel_id, matched_address, site_address,
        owner_name, match_type, match_status, matched (bool)
    """
    for address in addresses:
        if not (address or "").strip():
            yield _no_match(address)
            continue

        try:
            # Escape single quotes for the ArcGIS WHERE clause
            safe_addr = address.replace("'", "''")
            params = urllib.parse.urlencode({
                "where": f"SITEADDR LIKE '{safe_addr}%'",
                "outFields": "PARCELID,SITEADDR,OWNNAME1",
                "returnGeometry": "false",
                "f": "json",
            })
            url = f"{BAY_COUNTY_ARCGIS_URL}?{params}"
            req = urllib.request.Request(
                url, headers={"User-Agent": "CountyData2/1.0"}
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode())

            features = data.get("features", [])
            if not features:
                yield _no_match(address)
                continue

            attrs = features[0].get("attributes", {})
            parcel_id = attrs.get("PARCELID")
            site_addr = attrs.get("SITEADDR", "")
            owner_name = attrs.get("OWNNAME1", "")

            yield {
                "address": address,
                "parcel_id": parcel_id,
                "matched_address": site_addr,
                "site_address": site_addr,
                "owner_name": owner_name,
                "match_type": "exact" if len(features) == 1 else "best",
                "match_status": "Match",
                "matched": bool(parcel_id),
            }
        except Exception:
            yield _no_match(address)


def _no_match(address: str) -> dict:
    return {
        "address": address,
        "parcel_id": None,
        "matched_address": None,
        "site_address": None,
        "owner_name": None,
        "match_type": None,
        "match_status": "No_Match",
        "matched": False,
    }
