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
        'portal': 'landmark',
    },
    'Okeechobee': {
        'base_url': 'https://pioneer.okeechobeelandmark.com/LandmarkWebLive',
        'doc_types': '',
        'column_map': _OKEECHOBEE_COLUMN_MAP,
        'status': 'working',
        'portal': 'landmark',
    },
    'Citrus': {
        'base_url': 'https://search.citrusclerk.org/LandmarkWeb',
        'doc_types': '17',
        'column_map': None,  # default — works with curl_cffi TLS impersonation
        'status': 'cloudflare',  # needs curl_cffi TLS impersonation
        'portal': 'landmark',
    },
    'Escambia': {
        'base_url': 'https://dory.escambiaclerk.com/LandmarkWeb',
        'doc_types': '',
        'column_map': None,
        'status': 'cloudflare',
        'portal': 'landmark',
    },
    'Walton': {
        'base_url': 'https://orsearch.clerkofcourts.co.walton.fl.us/LandmarkWeb',
        'doc_types': '',
        'column_map': None,
        'status': 'cloudflare',  # needs curl_cffi TLS impersonation
        'portal': 'landmark',
    },
    'Okaloosa': {
        'base_url': 'https://clerkapps.okaloosaclerk.com/LandmarkWeb',
        'doc_types': '',
        'column_map': None,
        'status': 'blocked',  # 503 Service Unavailable (server-side, not Cloudflare). Verified 2026-04-12.
        'portal': 'landmark',
    },
    'Bay': {
        'base_url': 'https://records2.baycoclerk.com/Recording',
        'doc_types': '',
        'column_map': None,  # uses DEFAULT_COLUMN_MAP — legal at column 13
        'status': 'captcha_hybrid',
        'portal': 'landmark',
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


COUNTYGOV_COUNTIES = {
    'Madison AL': {
        'base_url': 'https://madisonprobate.countygovservices.com',
        'search_type': 'deed',
        'doc_types': '',
        'status': 'working',
        'portal': 'countygov',
    },
}


def get_countygov_config(county: str) -> dict | None:
    """Return the CountyGovServices config for a county, or None."""
    return COUNTYGOV_COUNTIES.get(county)


DUPROCESS_COUNTIES = {
    'Madison MS': {
        'base_url': 'http://records.madison-co.com/DuProcessWebInquiry',
        'search_type': 'deed',
        'doc_types': '',
        'status': 'working',
        'portal': 'duprocess',
        'gis_url': 'https://gis.cmpdd.org/server/rest/services/Hosted/Madison_County_Map/FeatureServer/36',
        'gis_fields': 'madison',
    },
    'Rankin MS': {
        'base_url': 'https://www2.rankincounty.org/duprocesswebinquiry',
        'search_type': 'deed',
        'doc_types': '',
        'status': 'working',
        'portal': 'duprocess',
        'gis_url': 'https://gis.cmpdd.org/arcgis/rest/services/Hosted/Rankin_County_Feature_Layer/FeatureServer/8',
    },
    'Harrison MS': {
        'base_url': 'https://landrecords.co.harrison.ms.us/DuProcessWebInquiry',
        'search_type': 'deed',
        'doc_types': '',
        'status': 'working',
        'portal': 'duprocess',
        'gis_url': 'https://geo.co.harrison.ms.us/server/rest/services/AS400/liveParcels/FeatureServer/0',
    },
}


def get_duprocess_config(county: str) -> dict | None:
    """Return the DuProcess config for a county, or None."""
    return DUPROCESS_COUNTIES.get(county)


GINDEX_COUNTIES = {
    'Hinds MS': {
        'base_url': 'https://www.co.hinds.ms.us/pgs/apps',
        'book_type': '2',  # Deed Book only
        'status': 'cloudflare',  # needs curl_cffi TLS impersonation
        'portal': 'gindex',
    },
}


ACCLAIMWEB_COUNTIES = {
    'DeSoto MS': {
        'base_url': 'https://landrecords.desotocountyms.gov/AcclaimWeb',
        'doc_types': '1509,1342,1080',  # WAR + QCL + DEE
        'status': 'working',
        'portal': 'acclaimweb',
        'gis_url': 'https://services6.arcgis.com/4Zxj9BGpFPVGgwpo/arcgis/rest/services/Parcels_2025/FeatureServer/11',
        'gis_fields': 'desoto',
    },
    'Santa Rosa': {
        'base_url': 'https://acclaim.srccol.com/AcclaimWeb',
        'doc_types': '79',  # DEED (D) — single type covers all deeds
        'status': 'working',
        'portal': 'acclaimweb',
    },
}


def get_acclaimweb_config(county: str) -> dict | None:
    """Return the AcclaimWeb config for a county, or None."""
    return ACCLAIMWEB_COUNTIES.get(county)


BROWSERVIEW_COUNTIES = {
    'Marion': {
        'base_url': 'https://nvweb.marioncountyclerk.org/BrowserView',
        'doc_types': 'D,D2,DD',  # D=Deed, D2=Deed, DD=Deed
        'status': 'captcha_hybrid',  # user does one manual search, then automation takes over
        'portal': 'browserview',
    },
}


def get_browserview_config(county: str) -> dict | None:
    """Return the BrowserView config for a county, or None."""
    return BROWSERVIEW_COUNTIES.get(county)


GIS_PARCEL_COUNTIES = {
    'Jackson MS': {
        'layer_url': 'https://webmap.co.jackson.ms.us/arcgis107/rest/services/JacksonCounty/Parcel_2_Web/MapServer/2',
        'gis_fields': 'jackson',
        'status': 'working',
        'portal': 'gis_parcel',
    },
}


def get_gis_parcel_config(county: str) -> dict | None:
    """Return the GIS parcel-only config for a county, or None."""
    return GIS_PARCEL_COUNTIES.get(county)


def get_gindex_config(county: str) -> dict | None:
    """Return the General Index config for a county, or None."""
    return GINDEX_COUNTIES.get(county)


def list_working_counties() -> list[str]:
    """Return county names with 'working' status across all portals."""
    counties = [name for name, cfg in LANDMARK_COUNTIES.items()
                if cfg.get('status') in ('working', 'captcha_hybrid', 'cloudflare')]
    counties.extend(name for name, cfg in COUNTYGOV_COUNTIES.items()
                    if cfg.get('status') in ('working', 'captcha_hybrid', 'cloudflare'))
    counties.extend(name for name, cfg in DUPROCESS_COUNTIES.items()
                    if cfg.get('status') in ('working', 'captcha_hybrid', 'cloudflare'))
    counties.extend(name for name, cfg in GINDEX_COUNTIES.items()
                    if cfg.get('status') in ('working', 'captcha_hybrid', 'cloudflare'))
    counties.extend(name for name, cfg in ACCLAIMWEB_COUNTIES.items()
                    if cfg.get('status') in ('working', 'captcha_hybrid', 'cloudflare'))
    counties.extend(name for name, cfg in GIS_PARCEL_COUNTIES.items()
                    if cfg.get('status') in ('working', 'captcha_hybrid', 'cloudflare'))
    counties.extend(name for name, cfg in BROWSERVIEW_COUNTIES.items()
                    if cfg.get('status') in ('working', 'captcha_hybrid', 'cloudflare'))
    return counties
