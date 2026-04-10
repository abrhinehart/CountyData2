from __future__ import annotations

import re
from difflib import SequenceMatcher


COMMON_BUILDER_SUFFIXES = {
    "INC",
    "INCORPORATED",
    "LLC",
    "L L C",
    "LTD",
    "CO",
    "COMPANY",
    "CORP",
    "CORPORATION",
    "HOMEBUILDERS",
    "HOMEBUILDER",
}

CONTACT_SECTION_PATTERNS = (
    r"\bWORK PHONE\b",
    r"\bMOBILE PHONE\b",
    r"\bHOME PHONE\b",
    r"\bMAILING\b",
    r"\bUNITED STATES\b",
)

KNOWN_BUILDER_PATTERNS = {
    "DR HORTON": "DR Horton",
    "D R HORTON": "DR Horton",
    "ADAMS HOMES OF NORTH WEST FLORIDA": "Adams Homes",
    "ADAMS HOMES OF NORTHWEST FLORIDA": "Adams Homes",
    "ADAMS HOMES OF NW FLORIDA": "Adams Homes",
    "ADAMS HOMES OF NW FL": "Adams Homes",
    "ADAMS HOMES": "Adams Homes",
    "HARRIS DOYLE HOMES": "Harris Doyle Homes",
    "SAMUEL TAYLOR HOMES": "Samuel Taylor Homes",
    "TRULAND HOMES": "Truland Homes",
    "TRULAND": "Truland Homes",
    "LGI HOMES": "LGI Homes",
    "RYAN HOMES": "Ryan Homes",
    "HIGHLAND HOMES": "Highland Homes",
    "MARONDA HOMES": "Maronda Homes",
    "TAYLOR MORRISON": "Taylor Morrison",
    "STANLEY MARTIN HOMES": "Stanley Martin Homes",
    "STARLIGHT HOMES": "Starlight Homes",
    "LENNAR HOMES": "Lennar Homes",
    "LENNAR": "Lennar Homes",
    "M I HOMES": "M/I Homes",
    "HOLIDAY BUILDERS": "Holiday Builders",
    "SOUTHERN HOMES OF POLK COUNTY": "Southern Homes",
    "SOUTHERN HOMES": "Southern Homes",
    "WILLIAMS CONSTRUCTION": "Williams Construction",
    "JBV EXPEDITING": "JBV Expediting",
    "SUNCOAST PERMITS": "Suncoast Permits",
    "DONE DEAL RUNNERS": "Done Deal Runners",
    "ASHBUILT CONSTRUCTION": "Ashbuilt Construction",
    "TAPIA CONSTRUCTION": "Tapia Construction",
    "HULBERT HOMES": "Hulbert Homes",
    "PORTICO HOMES": "Portico Homes",
    "EAGLE BUILDING CONTRACTORS": "Eagle Building Contractors",
    "FORGUE GENERAL CONTRACTING": "Forgue General Contracting",
    "ABD DEVELOPMENT": "ABD Development",
}

KNOWN_BUILDER_EMAIL_DOMAINS = {
    "drhorton.com": "DR Horton",
    "lgihomes.com": "LGI Homes",
    "adamshomes.com": "Adams Homes",
    "nvrinc.com": "Ryan Homes",
    "taylormorrison.com": "Taylor Morrison",
    "maronda.com": "Maronda Homes",
    "highlandhomes.org": "Highland Homes",
    "mihomes.com": "M/I Homes",
    "stanleymartin.com": "Stanley Martin Homes",
    "starlighthomes.com": "Starlight Homes",
    "ashtonwoods.com": "Starlight Homes",
    "holidaybuilders.com": "Holiday Builders",
    "mysouthernhome.com": "Southern Homes",
    "lennar.com": "Lennar Homes",
    "jbvexpediting.com": "JBV Expediting",
    "suncoastpermits.com": "Suncoast Permits",
    "williamsconstructionfl.com": "Williams Construction",
}

PERMIT_STATUS_ALIASES = {
    "PERMIT S ISSUED": "Issued",
    "PERMIT ISSUED": "Issued",
    "ISSUED": "Issued",
    "FINALED": "Finaled",
    "CLOSED": "Closed",
    "FINISHED": "Closed",
    "CONSTRUCTION STARTED": "Construction Started",
    "IN REVIEW": "In Review",
    "PLAN REVIEW": "In Review",
    "IN PLAN CHECK": "In Review",
    "READY FOR ISSUANCE": "Ready for Issuance",
    "EXPIRED": "Expired",
    "INVALID LICENSE": "Invalid License",
    "PERMIT HOLD": "Permit Hold",
    "REVOKED": "Revoked",
    "WITHDRAWN": "Withdrawn",
    "FINALED PENDING CO COC": "Finaled - Pending CO / COC",
}


def normalize_text(value: str | None) -> str:
    if not value:
        return ""
    cleaned = re.sub(r"[^A-Za-z0-9 ]+", " ", value.upper())
    return " ".join(cleaned.split())


def normalize_permit_status(value: str | None) -> str:
    normalized = normalize_text(value)
    if not normalized:
        return "Unknown"
    if normalized in PERMIT_STATUS_ALIASES:
        return PERMIT_STATUS_ALIASES[normalized]
    return " ".join(word.capitalize() for word in normalized.split())


def canonicalize_builder_name(value: str | None) -> str:
    raw_value = value or ""
    if not raw_value.strip():
        return "Unknown Builder"

    email_domains = {
        domain.lower()
        for domain in re.findall(r"[A-Z0-9._%+-]+@([A-Z0-9.-]+\.[A-Z]{2,})", raw_value.upper())
    }
    for domain, canonical in KNOWN_BUILDER_EMAIL_DOMAINS.items():
        if any(found == domain or found.endswith(f".{domain}") for found in email_domains):
            return canonical

    stripped = re.sub(r"\([^)]*\)", " ", raw_value.upper())
    stripped = re.sub(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", " ", stripped)
    stripped = re.sub(r"\b(?:\d{3}[-.\s]?){2}\d{4}\b", " ", stripped)
    for pattern in CONTACT_SECTION_PATTERNS:
        stripped = re.split(pattern, stripped, maxsplit=1)[0]
    stripped = re.sub(r"\bDBA\b", " DBA ", stripped)
    normalized = normalize_text(stripped)
    if not normalized:
        return "Unknown Builder"

    if " DBA " in normalized:
        normalized = normalized.split(" DBA ", 1)[1]

    if normalized.startswith("INDIVIDUAL "):
        normalized = normalized[len("INDIVIDUAL "):]

    for pattern, canonical in sorted(KNOWN_BUILDER_PATTERNS.items(), key=lambda item: len(item[0]), reverse=True):
        if pattern in normalized:
            return canonical

    parts = [part for part in normalized.split() if part not in COMMON_BUILDER_SUFFIXES]
    canonical = " ".join(parts) or normalized

    aliases = {
        "SAMUEL TAYLOR": "Samuel Taylor Homes",
        "SAMUEL TAYLOR HOMES": "Samuel Taylor Homes",
        "TRULAND": "Truland Homes",
        "TRULAND HOMES": "Truland Homes",
    }
    if canonical in aliases:
        return aliases[canonical]
    return " ".join(word.capitalize() for word in canonical.split())


def names_match(left: str | None, right: str | None, threshold: float = 0.88) -> bool:
    left_normalized = normalize_text(left)
    right_normalized = normalize_text(right)
    if not left_normalized or not right_normalized:
        return False
    if left_normalized == right_normalized:
        return True
    ratio = SequenceMatcher(a=left_normalized, b=right_normalized).ratio()
    return ratio >= threshold
