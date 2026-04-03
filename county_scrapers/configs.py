"""
configs.py - Per-county configuration for LandmarkWeb portals.

Each entry maps a county name (matching counties.yaml) to its portal
base URL, deed-related doc type IDs, and column index mappings.

Column indices and status were verified via live testing on 2026-04-03.

To add a new LandmarkWeb county:
    1. Find the portal URL (usually ends with /LandmarkWeb or /LandmarkWebLive)
    2. Run a test search and inspect the JSON column indices
    3. Add an entry below with the correct column_map
"""

from county_scrapers.landmark_client import DEFAULT_COLUMN_MAP

# Column maps observed per county version.
# Hernando (v1.5.87) has extended legal fields in columns 14-25, doc_id at 26.
_HERNANDO_COLUMN_MAP = {
    'grantor': '5',
    'grantee': '6',
    'record_date': '7',
    'doc_type': '8',
    'book_type': '9',
    'book': '10',
    'page': '11',
    'instrument': '12',
    'legal': '14',      # column 13 is empty; 14 has the full L/Blk/Un/Sub format
    'subdivision': '19', # hidden_legalfield_ — subdivision name from structured legal
}

# Okeechobee (v1.5.93) has slightly different layout — legal at 14, doc_id at 17.
_OKEECHOBEE_COLUMN_MAP = {
    'grantor': '5',
    'grantee': '6',
    'record_date': '7',
    'doc_type': '8',
    'book_type': '9',
    'book': '10',
    'page': '11',
    'instrument': '12',
    'legal': '14',      # column 13 appears to be a secondary instrument/case number
}


# Status key:
#   working   = live-tested, returns data via API without CAPTCHA
#   captcha   = ShowCaptcha=True AND enforced (search returns 0 results)
#   blocked   = HTTP 403 or connection reset
#   untested  = not yet verified

LANDMARK_COUNTIES = {
    'Hernando': {
        'base_url': 'https://or.hernandoclerk.com/LandmarkWeb',
        'doc_types': '',  # empty = all types; verify deed ID later
        'column_map': _HERNANDO_COLUMN_MAP,
        'status': 'working',
    },
    'Okeechobee': {
        'base_url': 'https://pioneer.okeechobeelandmark.com/LandmarkWebLive',
        'doc_types': '',
        'column_map': _OKEECHOBEE_COLUMN_MAP,
        'status': 'working',
    },
    'Citrus': {
        'base_url': 'https://search.citrusclerk.org/LandmarkWeb',
        'doc_types': '17',
        'column_map': None,  # default — untested since captcha blocks results
        'status': 'captcha',
    },
    'Escambia': {
        'base_url': 'https://dory.escambiaclerk.com/LandmarkWeb',
        'doc_types': '',
        'column_map': None,
        'status': 'blocked',  # HTTP 403
    },
    'Walton': {
        'base_url': 'https://orsearch.clerkofcourts.co.walton.fl.us/LandmarkWeb',
        'doc_types': '',
        'column_map': None,
        'status': 'blocked',  # connection reset
    },
    'Okaloosa': {
        'base_url': 'https://clerkapps.okaloosaclerk.com/LandmarkWeb',
        'doc_types': '',
        'column_map': None,
        'status': 'untested',
    },
}


def get_landmark_config(county: str) -> dict | None:
    """Return the LandmarkWeb config for a county, or None if not a Landmark county."""
    config = LANDMARK_COUNTIES.get(county)
    if config is None:
        return None
    result = dict(config)
    if result['column_map'] is None:
        result['column_map'] = dict(DEFAULT_COLUMN_MAP)
    return result


def list_working_counties() -> list[str]:
    """Return county names with 'working' status."""
    return [name for name, cfg in LANDMARK_COUNTIES.items()
            if cfg.get('status') == 'working']
