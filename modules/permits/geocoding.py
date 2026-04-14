"""
Geocoding helpers for the Permit Tracker module.

Uses the US Census Bureau batch geocoder to resolve street addresses
to lat/lon coordinates.
"""
from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from typing import Generator

CENSUS_GEOCODER_URL = (
    "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"
)

# Jurisdiction-specific address suffixes the Census geocoder already knows.
_JURISDICTION_STATE_HINTS: dict[str, str] = {
    "Bay County": ", FL",
    "Davenport": ", FL",
    "Haines City": ", FL",
    "Lake Alfred": ", FL",
    "Lake Hamilton": ", FL",
    "Panama City": ", Panama City, FL",
    "Panama City Beach": ", Panama City Beach, FL",
    "Polk County": ", FL",
    "Winter Haven": ", FL",
}


def normalize_query_address(address: str) -> str:
    """Collapse whitespace and upper-case for dedup comparison."""
    return re.sub(r"\s+", " ", (address or "").strip().upper())


def prepare_address_for_geocoding(
    address: str,
    jurisdiction_name: str | None = None,
) -> str:
    """Append state/city hints so the Census geocoder resolves correctly."""
    cleaned = (address or "").strip()
    if not cleaned:
        return cleaned

    hint = _JURISDICTION_STATE_HINTS.get(jurisdiction_name or "")
    if hint and hint.upper() not in cleaned.upper():
        cleaned = cleaned + hint
    return cleaned


def batch_geocode_addresses(
    addresses: list[str],
    *,
    jurisdiction_name_by_address: dict[str, str] | None = None,
) -> Generator[dict, None, None]:
    """
    Geocode a list of addresses one at a time via the Census Bureau API.

    Yields one dict per address with keys:
        address, latitude, longitude, matched_address,
        match_type, match_status, matched (bool)
    """
    jurisdiction_name_by_address = jurisdiction_name_by_address or {}

    for raw_address in addresses:
        jurisdiction_name = jurisdiction_name_by_address.get(raw_address)
        prepared = prepare_address_for_geocoding(raw_address, jurisdiction_name)
        if not prepared:
            yield _no_match(raw_address, "unparseable")
            continue

        try:
            params = urllib.parse.urlencode({
                "address": prepared,
                "benchmark": "Public_AR_Current",
                "format": "json",
            })
            url = f"{CENSUS_GEOCODER_URL}?{params}"
            req = urllib.request.Request(
                url, headers={"User-Agent": "CountyData2/1.0"}
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode())

            matches = data.get("result", {}).get("addressMatches", [])
            if not matches:
                yield _no_match(raw_address, "no_match")
                continue

            best = matches[0]
            coords = best.get("coordinates", {})
            yield {
                "address": raw_address,
                "latitude": coords.get("y"),
                "longitude": coords.get("x"),
                "matched_address": best.get("matchedAddress", ""),
                "match_type": "exact" if len(matches) == 1 else "best",
                "match_status": "Match",
                "matched": True,
            }
        except Exception:
            yield _no_match(raw_address, "error")


def _no_match(address: str, match_type: str) -> dict:
    return {
        "address": address,
        "latitude": None,
        "longitude": None,
        "matched_address": None,
        "match_type": match_type,
        "match_status": "No_Match",
        "matched": False,
    }
