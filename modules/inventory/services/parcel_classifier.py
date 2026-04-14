"""Classify parcels as lot, common_area, tract, or other based on use_type and acreage.

Classes:
  lot          — individual buildable lot (the default / desired inventory)
  common_area  — retention ponds, buffers, HOA common elements, rights of way
  tract        — raw undeveloped land, large acreage holdings, future development sites
  other        — commercial, institutional, agricultural, or unclassifiable
"""

import re

# Use type patterns (case-insensitive) → class
# Order matters: first match wins
_COMMON_AREA_PATTERNS = [
    r"common\s*(area|elem)",
    r"res(idential)?\s*common",
    r"common\s*-\s*(vac|imp)",
    r"right.of.way",
    r"r/?w",
    r"streets.*retention",
    r"retention",
    r"buffer",
    r"conservation",
    r"pond",
    r"lake(?!\s*front)",  # "LAKE" but not "LAKEFRONT"
    r"wetland",
    r"subm(erge|rg)",  # submerged land
    r"sewage|sewg|waste\s*land",
    r"vacant\s*(non-)?appurtenant",
    r"mineral\s*rights",
    r"unbuildable",
    r"parking\s*(lot|garage)",
    r"recreational\s*area",
]

_TRACT_PATTERNS = [
    r"unplatted",
    r"acreage.*non.ag",
    r"non.ag.*acreage",
    r"no\s*ag\s*acreage",
    r"acrg\s*not\s*zn",
    r"acreage\s*not\s*zoned",
    r"timber",
    r"pasture",
    r"mining",
]

_OTHER_PATTERNS = [
    r"commercial",
    r"office",
    r"warehouse",
    r"nursing",
    r"church",
    r"county(?!\s*road)",
    r"utilities",
    r"mobile\s*home",
    r"multi.?family",
    r"condominium\s*reserve",
]

_COMPILED_COMMON = [re.compile(p, re.IGNORECASE) for p in _COMMON_AREA_PATTERNS]
_COMPILED_TRACT = [re.compile(p, re.IGNORECASE) for p in _TRACT_PATTERNS]
_COMPILED_OTHER = [re.compile(p, re.IGNORECASE) for p in _OTHER_PATTERNS]

# Acreage thresholds
TRACT_ACREAGE_THRESHOLD = 5.0  # parcels above this with no specific use type → tract


def classify_parcel(use_type: str | None, acreage: float | None) -> str:
    """Classify a single parcel. Returns one of: lot, common_area, tract, other."""
    ut = str(use_type).strip() if use_type is not None else ""

    # Check use_type patterns first
    if ut:
        for pattern in _COMPILED_COMMON:
            if pattern.search(ut):
                return "common_area"

        for pattern in _COMPILED_TRACT:
            if pattern.search(ut):
                return "tract"

        for pattern in _COMPILED_OTHER:
            if pattern.search(ut):
                return "other"

    # Acreage-based fallback
    if acreage is not None and acreage >= TRACT_ACREAGE_THRESHOLD:
        return "tract"

    return "lot"
