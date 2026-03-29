from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import re

import yaml

from utils.county_utils import normalize_county_key


_CATEGORY_PATH = Path(__file__).resolve().parents[1] / 'reference_data' / 'inventory_categories.yaml'


def _normalize_subdivision_name(name: str | None) -> str:
    if not name:
        return ''
    normalized = re.sub(r'\s+', ' ', str(name)).strip()
    return normalized.upper()


@lru_cache(maxsize=None)
def load_inventory_categories() -> dict[str, dict[str, set[str]]]:
    if not _CATEGORY_PATH.exists():
        return {}

    with open(_CATEGORY_PATH, encoding='utf-8') as handle:
        raw_data = yaml.safe_load(handle) or {}

    normalized_data: dict[str, dict[str, set[str]]] = {}
    for category, counties in raw_data.items():
        if not isinstance(counties, dict):
            continue

        normalized_counties: dict[str, set[str]] = {}
        for county, subdivisions in counties.items():
            county_key = normalize_county_key(county)
            normalized_subdivisions = {
                _normalize_subdivision_name(subdivision)
                for subdivision in (subdivisions or [])
                if _normalize_subdivision_name(subdivision)
            }
            normalized_counties[county_key] = normalized_subdivisions

        normalized_data[str(category).strip()] = normalized_counties

    return normalized_data


def classify_inventory_category(county: str, subdivision: str | None) -> str | None:
    county_key = normalize_county_key(county)
    subdivision_key = _normalize_subdivision_name(subdivision)
    if not county_key or not subdivision_key:
        return None

    for category, counties in load_inventory_categories().items():
        if subdivision_key in counties.get(county_key, set()):
            return category

    return None
