import re


_ASSOCIATION_PATTERNS = (
    re.compile(r'\bHOMEOWNERS?\s+ASS(?:OCIATION|N|OC)\b', re.IGNORECASE),
    re.compile(r'\bPROPERTY\s+OWNERS?\s+ASS(?:OCIATION|N|OC)\b', re.IGNORECASE),
    re.compile(r'\bCONDOMINIUM\s+ASS(?:OCIATION|N|OC)\b', re.IGNORECASE),
    re.compile(r'\bCOMMUNITY\s+ASS(?:OCIATION|N|OC)\b', re.IGNORECASE),
    re.compile(r'\bMASTER\s+ASS(?:OCIATION|N|OC)\b', re.IGNORECASE),
)
_CDD_PATTERNS = (
    re.compile(r'\bCOMMUNITY\s+DEVELOPMENT\s+DISTRICT\b', re.IGNORECASE),
    re.compile(r'\bCDD\b', re.IGNORECASE),
)
_QUIT_CLAIM_PATTERNS = (
    re.compile(r'\bQUIT\s*CLAIM\b', re.IGNORECASE),
    re.compile(r'\bQUITCLAIM\b', re.IGNORECASE),
    re.compile(r'\bQCD\b', re.IGNORECASE),
    re.compile(r'\bQC\s+DEED\b', re.IGNORECASE),
)
_CORRECTION_PATTERNS = (
    re.compile(r'\bTO\s+CORRECT\b', re.IGNORECASE),
    re.compile(r'\bCORRECTIVE\b', re.IGNORECASE),
    re.compile(r'\bCORRECTION\b', re.IGNORECASE),
)
_ACREAGE_PATTERN = re.compile(
    r'(?P<value>\d+\s+\d+/\d+|\d+/\d+|\d+(?:\.\d+)?)\s*(?:M/L|MOL|MORE OR LESS)?\s*(?:ACRES?|ACS?|AC)\b',
    re.IGNORECASE,
)
_RAW_LAND_PATTERNS = (
    re.compile(r'\bCOMM(?:ENCE)?\s+AT\b', re.IGNORECASE),
    re.compile(r'\bPARCEL\b', re.IGNORECASE),
    re.compile(r'\bPCLS?\b', re.IGNORECASE),
    re.compile(r'\bSECTION\b', re.IGNORECASE),
    re.compile(r'\bSEC[:\s]', re.IGNORECASE),
    re.compile(r'\bTOWNSHIP\b', re.IGNORECASE),
    re.compile(r'\bRANGE\b', re.IGNORECASE),
    re.compile(r'\bQUARTER\s+SECTION\b', re.IGNORECASE),
    re.compile(r'\bSIXTEENTH\s+SECTION\b', re.IGNORECASE),
)
_PLATTED_LOT_KEYS = (
    'lot_values',
    'structured_lot_values',
    'lot_identifiers',
    'partial_lot_values',
    'partial_lot_identifiers',
    'block_values',
    'structured_block_values',
    'unit_values',
    'structured_unit_values',
    'condo_values',
    'structured_condo_values',
)
_RAW_LAND_COUNTY_PARSE_KEYS = (
    'section_values',
    'structured_section_values',
    'township_values',
    'structured_township_values',
    'range_values',
    'structured_range_values',
    'parcel_references',
    'structured_parcel_references',
    'legal_remarks_values',
    'quarter_section_values',
    'location_prefix_values',
)


def _normalize_text(value: str | None) -> str:
    if not value:
        return ''
    return re.sub(r'\s+', ' ', str(value)).strip()


def _matches_any(text: str, patterns: tuple[re.Pattern[str], ...]) -> bool:
    return any(pattern.search(text) for pattern in patterns)


def _parse_fractional_number(value: str) -> float | None:
    text = str(value).strip()
    if not text:
        return None

    if ' ' in text:
        whole, remainder = text.split(None, 1)
        whole_value = _parse_fractional_number(whole)
        remainder_value = _parse_fractional_number(remainder)
        if whole_value is None or remainder_value is None:
            return None
        return whole_value + remainder_value

    if '/' in text:
        numerator, denominator = text.split('/', 1)
        try:
            denominator_value = float(denominator)
            if denominator_value == 0:
                return None
            return float(numerator) / denominator_value
        except ValueError:
            return None

    try:
        return float(text)
    except ValueError:
        return None


def extract_acres(value: str | None) -> float | None:
    text = _normalize_text(value)
    if not text:
        return None

    match = _ACREAGE_PATTERN.search(text)
    if not match:
        return None
    return _parse_fractional_number(match.group('value'))


def _is_association_transfer(grantee: str | None) -> bool:
    text = _normalize_text(grantee)
    return bool(text) and _matches_any(text, _ASSOCIATION_PATTERNS)


def _is_cdd_transfer(grantee: str | None) -> bool:
    text = _normalize_text(grantee)
    return bool(text) and _matches_any(text, _CDD_PATTERNS)


def _is_correction_record(instrument: str | None, export_legal_desc: str | None) -> bool:
    instrument_text = _normalize_text(instrument)
    legal_text = _normalize_text(export_legal_desc)
    if instrument_text and _matches_any(instrument_text, _QUIT_CLAIM_PATTERNS):
        return True
    return bool(legal_text) and _matches_any(legal_text, _CORRECTION_PATTERNS)


def _has_values(county_parse: dict | None, keys: tuple[str, ...]) -> bool:
    if not isinstance(county_parse, dict):
        return False

    for key in keys:
        value = county_parse.get(key)
        if isinstance(value, (list, tuple, set, dict)) and value:
            return True
        if not isinstance(value, (list, tuple, set, dict)) and value not in (None, ''):
            return True
    return False


def _classify_base_transaction_type(
    grantor_builder_id: int | None,
    grantee_builder_id: int | None,
    grantor_land_banker_id: int | None,
    grantee_land_banker_id: int | None,
) -> str:
    if grantor_builder_id is not None and grantee_builder_id is not None:
        return 'Builder to Builder'

    if grantee_builder_id is not None:
        return 'Builder Purchase'

    if grantee_land_banker_id is not None:
        return 'Land Banker Purchase'

    return 'House Sale'


def _is_raw_land_purchase(
    base_type: str,
    subdivision: str | None,
    export_legal_desc: str | None,
    county_parse: dict | None,
    acres: float | None,
) -> bool:
    if base_type not in {'Builder to Builder', 'Builder Purchase', 'Land Banker Purchase'}:
        return False
    if subdivision:
        return False
    if _has_values(county_parse, _PLATTED_LOT_KEYS):
        return False
    if acres is not None and acres > 0:
        return True

    if _has_values(county_parse, _RAW_LAND_COUNTY_PARSE_KEYS):
        return True

    text = _normalize_text(export_legal_desc)
    return bool(text) and _matches_any(text, _RAW_LAND_PATTERNS)


def classify_transaction_type(
    grantor_builder_id: int | None,
    grantee_builder_id: int | None,
    grantor_land_banker_id: int | None,
    grantee_land_banker_id: int | None,
    *,
    grantee: str | None = None,
    instrument: str | None = None,
    export_legal_desc: str | None = None,
    subdivision: str | None = None,
    county_parse: dict | None = None,
    acres: float | None = None,
) -> str:
    if _is_cdd_transfer(grantee):
        return 'CDD Transfer'

    if _is_association_transfer(grantee):
        return 'Association Transfer'

    if _is_correction_record(instrument, export_legal_desc):
        return 'Correction / Quit Claim'

    base_type = _classify_base_transaction_type(
        grantor_builder_id,
        grantee_builder_id,
        grantor_land_banker_id,
        grantee_land_banker_id,
    )
    if _is_raw_land_purchase(base_type, subdivision, export_legal_desc, county_parse, acres):
        return 'Raw Land Purchase'

    return base_type
