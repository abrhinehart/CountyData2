# --- Approval type aliases (single source of truth) ---
APPROVAL_TYPE_ALIASES = {
    "pud": "zoning",
    "planned_development": "zoning",
    "site_plan": "development_review",
    "major_development": "development_review",
    "plat": "subdivision",
    # dsap removed — it's a planning district, not an action type
    # dri removed — defunct for new project approvals
}

# Canonical approval types (after alias resolution)
CANONICAL_APPROVAL_TYPES = {
    "annexation",
    "land_use",
    "zoning",
    "development_review",
    "subdivision",
    "developer_agreement",
    "conditional_use",
    "text_amendment",
}

# Types auto-passed by threshold filter (always significant)
AUTO_PASS_TYPES = {"developer_agreement", "development_review"}

# Conditional use minimum acreage
CONDITIONAL_USE_MIN_ACRES = 2

# Land use scale threshold (Florida)
LAND_USE_LARGE_SCALE_ACRES = 50

# --- Threshold filter constants ---
ANNEXATION_MIN_ACRES = 10
ANNEXATION_MULTI_PROJECT_ACRES = 500
REZONING_MIN_LOTS = 20
REZONING_MIN_ACRES = 10

# --- Auto-detection text window sizes ---
HEADER_NARROW_CHARS = 500
HEADER_WIDE_CHARS = 2000
MEETING_LINE_SCAN_CHARS = 1000

# --- API and file processing ---
MAX_EXTRACTION_TOKENS = 8192
FILE_READ_CHUNK_SIZE = 8192
RECOVERY_EXTRACTION_CHUNK_TARGET_CHARS = 8_000
RECOVERY_EXTRACTION_MIN_CHUNK_TARGET_CHARS = 4_000
RECOVERY_EXTRACTION_CHUNK_OVERLAP_CHARS = 1_000

# --- Scraping ---
SCRAPE_SEARCH_TIMEOUT = 30
SCRAPE_DOWNLOAD_TIMEOUT = 60

# --- Collection review ---
PRIMARY_AGENDA_MAX_PAGES = 75
PRIMARY_DOCUMENT_PACKET_TERMS = (
    "agenda packet",
    "meeting packet",
    "packet",
)

# --- Packet enrichment ---
PACKET_ENRICHMENT_MAX_PAGES = 3
