import re

import pandas as pd

from processors.county_parsers import (
    parse_bay_row,
    parse_citrus_row,
    parse_escambia_row,
    parse_hernando_row,
    parse_marion_row,
    parse_okaloosa_row,
    parse_okeechobee_row,
    parse_santarosa_row,
    parse_walton_row,
)
from utils.county_utils import normalize_county_key
from utils.date_utils import parse_date
from utils.inventory_categories import classify_inventory_category
from utils.subdivision_reference import resolve_county_subdivision_reference
from utils.text_cleaning import (
    split_parties,
    before_first_delimiter,
    extract_phase,
    remove_phase_from_text,
    clean_subdivision,
    remove_santarosa_unit,
    fix_phase_typos,
    remove_after_parcel,
    remove_after_section,
)
from utils.transaction_utils import classify_transaction_type, extract_acres


_HERNANDO_SUBDIVISION_ALIASES = {
    'SPRINGHILL': 'SPRING HILL',
    'SPRNG HILL': 'SPRING HILL',
    'SPIRNG HILL': 'SPRING HILL',
    'SPRING HLIL': 'SPRING HILL',
    'SPRING BILL': 'SPRING HILL',
    'ROYAL HIGLANDS': 'ROYAL HIGHLANDS',
    'ROYAI HIGHLANDS': 'ROYAL HIGHLANDS',
}
_SUBDIVISION_ALIASES = {
    'BAY': {
        'EASTBAY': 'EAST BAY',
        'E BAY': 'EAST BAY',
        'BREAKFAST POINT E': 'BREAKFAST POINT EAST',
        'BREAKFAST PT E': 'BREAKFAST POINT EAST',
        'BREAKFAST PIONT EAST': 'BREAKFAST POINT EAST',
        'CABELLEROS ESTATES AT HOMBRE': 'CABALLEROS ESTATES AT HOMBRE',
        'CABALLEROS EST AT HOMBRE': 'CABALLEROS ESTATES AT HOMBRE',
        'CABALLEROS ESTAES AT HOMBRE': 'CABALLEROS ESTATES AT HOMBRE',
        'CABALLEROS ESTATS AT HOMBRE': 'CABALLEROS ESTATES AT HOMBRE',
        'CABALLEROS ESTATES AT HOBRE': 'CABALLEROS ESTATES AT HOMBRE',
        'CABALLEROS ESTATES OF HOMBRE': 'CABALLEROS ESTATES AT HOMBRE',
    },
    'WALTON': {
        'WATERSOUNDS ORIGINS NATUREWALK': 'WATERSOUND ORIGINS NATUREWALK',
        'WATERSOUND ORIGINS NAUTUREWALK': 'WATERSOUND ORIGINS NATUREWALK',
        "HAWK'S LANDING": 'HAWKS LANDING',
        "OWL'S HEAD FARMS": 'OWLS HEAD FARMS',
        'STARBURST HAMMOCK BAY': 'STARBURST AT HAMMOCK BAY',
        'NATUREVIEW': 'NATURE VIEW',
        'MAGNOLIA AT THE BUFFS': 'MAGNOLIA AT THE BLUFFS',
        'MAGNOLIA AT THE BLUFS': 'MAGNOLIA AT THE BLUFFS',
        'MAGNOLAI AT THE BLUFFS': 'MAGNOLIA AT THE BLUFFS',
    },
    'CITRUS': {
        'SPORTMENS PARK': 'SPORTSMENS PARK',
    },
    'ESCAMBIA': {
        'PEACAN VALLEY': 'PECAN VALLEY',
        'SADDLE RDIGE': 'SADDLE RIDGE',
        'SACTUARY': 'SANCTUARY',
        'SANTUARY': 'SANCTUARY',
        'RESIDENCE AT NATURE CREEK': 'RESIDENCES AT NATURE CREEK',
    },
    'OKEECHOBEE': {
        'BASSWOOD INC': 'BASSWOOD',
        'PALM CREEK ESTATES': 'PALMCREEK ESTATES',
        'PALMCREEEK ESTATES': 'PALMCREEK ESTATES',
        'PALMCREEK ESATES': 'PALMCREEK ESTATES',
    },
    'OKALOOSA': {
        'ASHTON VIEW SUBDIVISION': 'ASHTON VIEW',
        'YOUNG OAKS SUBDIVISION': 'YOUNG OAKS',
        'DAYS LANDING SUBDIVISION': 'DAYS LANDING',
        'HIDDEN LAKE SUBDIVISION': 'HIDDEN LAKE',
    },
}
_IGNORED_SUBDIVISION_EXACT = {
    'BAY': {
        'CONFIDENTIAL',
    },
    'CITRUS': {
        'REDACTION APPLIED PURSUANT TO FLORIDA PUBLIC RECORDS LAWS',
    },
    'OKALOOSA': {
        'COUNTRY CLUB (CONDO)',
        'CRESTVIEW',
    },
    'WALTON': {
        'TO CORRECT',
    },
}
_IGNORED_SUBDIVISION_PATTERNS = [
    ('document_redaction', re.compile(r'^DOCUMENT HAS BEEN MODIFIED PER F\.S\.', re.IGNORECASE)),
    ('redaction', re.compile(r'^REDACTION APPLIED\b', re.IGNORECASE)),
    ('confidential', re.compile(r'^CONFIDENTIAL\b', re.IGNORECASE)),
    ('parcel_reference', re.compile(r'^(?:MISC\s+)?PCLS?\b', re.IGNORECASE)),
    ('parcel_reference', re.compile(r'^PCL\b', re.IGNORECASE)),
    ('section_reference', re.compile(r'^SEC[:\s]', re.IGNORECASE)),
    ('section_reference', re.compile(r'^S:\s*\d+\s+T:\s*\d+[NS]\s+R:\s*\d+[EW]$', re.IGNORECASE)),
    ('section_reference', re.compile(r'^S\d+\s+T\d+[NS]\s+R\d+[EW]$', re.IGNORECASE)),
    ('section_reference', re.compile(r'^[A-Z0-9/.-]+\s+SEC\s+\d{1,2}-\d[NS]-\d{1,2}[EW]$', re.IGNORECASE)),
    ('section_reference', re.compile(r'^(?:NE|NW|SE|SW)/C\b', re.IGNORECASE)),
    ('section_reference', re.compile(r'^[NSEW]1/4\b', re.IGNORECASE)),
    ('easement', re.compile(r'^CONSERVATION EASEMENT\b', re.IGNORECASE)),
    ('common_area', re.compile(r'^ALL ROADS\b', re.IGNORECASE)),
    ('tract_reference', re.compile(r'^TRACT\s+[A-Z0-9-]+\b.*\bPLAT\b', re.IGNORECASE)),
    ('tract_reference', re.compile(r'^IN\s+\d+-\d+-\d+(?:/O)?$', re.IGNORECASE)),
    ('range_only', re.compile(r'^\d+[EW]$', re.IGNORECASE)),
    ('range_only', re.compile(r'^\d+\s+\d+[EW]$', re.IGNORECASE)),
    ('parcel_reference', re.compile(r'^R\d{10,}', re.IGNORECASE)),
]

_DEED_LOCATOR_COLUMN_MAP = {
    'book_type': ['Book Type'],
    'book': ['Book'],
    'page': ['Page'],
    'book_page': ['Book/Page'],
    'instrument_number': ['Instrument #', 'Doc #'],
    'clerk_file_number': ['Clerk File #'],
    'cfn': ['CFN'],
    'file_number': ['File No.'],
    'reference': ['Reference'],
    'case_number': ['Case #'],
}
_DEED_LINK_COLUMNS = ['DocLinks', 'DocLinks.1', 'Doc Link']
_DEED_IMAGE_COLUMNS = ['Images']


def _append_unique(items: list[str], value: str | None) -> None:
    if value and value not in items:
        items.append(value)


def _clean_locator_value(value) -> str | None:
    if value is None or pd.isna(value):
        return None

    text = str(value).strip()
    if not text or text.lower() == 'nan':
        return None
    return text


def _is_descriptor_connector(token: str) -> bool:
    return token.upper() in {'AND', '&', '/'}


def _is_hernando_tract_designator(token: str) -> bool:
    upper = token.upper().strip('.,;:')
    if not upper or _is_descriptor_connector(upper):
        return False
    return bool(re.fullmatch(r'(?:-?\d+[A-Z]?|[A-Z]{1,3}(?:-?\d*[A-Z]?)?(?:-[A-Z0-9]+)*)', upper))


def _is_hernando_pod_designator(token: str) -> bool:
    upper = token.upper().strip('.,;:')
    if not upper or _is_descriptor_connector(upper):
        return False
    return bool(re.fullmatch(r'[A-Z0-9]{1,3}(?:&[A-Z0-9]{1,3})?', upper))


def _normalize_descriptor_reference(value: str) -> str:
    cleaned = re.sub(r'\bAND\b', '&', value, flags=re.IGNORECASE)
    cleaned = re.sub(r'\s*&\s*', ' & ', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned)
    return cleaned.strip(' ,;:')


def _phase_keywords_without_unit(phase_keywords: list[str]) -> list[str]:
    filtered = []
    for keyword in phase_keywords:
        letters_only = re.sub(r'[^A-Z]', '', str(keyword).upper())
        if letters_only == 'UNIT':
            continue
        filtered.append(keyword)
    return filtered


def _ignored_subdivision_reason(county_key: str, subdivision: str | None) -> str | None:
    if not subdivision:
        return None

    normalized = re.sub(r'\s+', ' ', str(subdivision)).strip(' ,;:.')
    if not normalized:
        return None

    upper = normalized.upper()
    if upper in _IGNORED_SUBDIVISION_EXACT.get(county_key, set()):
        return 'exact_ignore'

    for reason, pattern in _IGNORED_SUBDIVISION_PATTERNS:
        if pattern.match(normalized):
            return reason

    return None


def _derive_subdivision_from_legal_remarks(legal_remarks: str | None, phase_keywords: list[str]) -> tuple[str | None, bool]:
    if not legal_remarks:
        return (None, False)

    stripped = re.sub(r'(?i)^UNREC(?:ORDED)?\.?\s*', '', str(legal_remarks)).strip(' ,;:')
    if not stripped:
        return (None, False)

    cleaned = clean_subdivision(stripped, phase_keywords).strip(' ,;:') if stripped else ''
    candidate = cleaned or stripped
    upper = candidate.upper()
    if (
        len(candidate.split()) < 2
        or upper.startswith(('COMM ', 'COM ', 'BEG ', 'BEGIN ', 'NORTH ', 'SOUTH ', 'EAST ', 'WEST ', 'PARCEL '))
        or ('COUNTY PROPERTY' in upper)
    ):
        return (None, False)

    has_plat_detail = bool(re.search(r'(?i)\b(?:LOTS?|BLK|BLOCK|UNIT)\b', stripped))
    has_named_place = bool(re.search(r'(?i)\b(?:ADDITION|SUBDIVISION)\b', candidate))
    if not has_plat_detail and not has_named_place:
        return (None, False)

    return (candidate, bool(re.match(r'(?i)^UNREC(?:ORDED)?\.?', str(legal_remarks).strip())))


def _extract_record_acres(row, cols: dict, export_legal_desc: str | None, county_parse: dict) -> tuple[float | None, str | None]:
    explicit_columns = []
    for key in ('acres', 'acreage'):
        column_name = cols.get(key)
        if column_name:
            explicit_columns.append(column_name)

    for column_name in row.index:
        normalized = re.sub(r'\s+', '', str(column_name).strip().lower())
        if normalized in {'acres', 'acreage'} and column_name not in explicit_columns:
            explicit_columns.append(column_name)

    for column_name in explicit_columns:
        acres_value = extract_acres(row.get(column_name))
        if acres_value is not None:
            return acres_value, 'column'

        raw_value = row.get(column_name)
        if pd.notna(raw_value):
            try:
                return float(str(raw_value).strip()), 'column'
            except (ValueError, TypeError):
                pass

    legal_candidates = []
    if export_legal_desc:
        legal_candidates.append(export_legal_desc)
    for value in county_parse.get('legal_remarks_values') or []:
        if value:
            legal_candidates.append(value)

    for candidate in legal_candidates:
        acres_value = extract_acres(candidate)
        if acres_value is not None:
            return acres_value, 'legal'

    return None, None


def _extract_hernando_subdivision_unit(text: str) -> tuple[str | None, str | None]:
    match = re.search(r'^(?P<base>.*?)\s+\b[A-Z]*NIT\s*NO\.?\s*(?P<unit>[A-Z0-9-]+)\b\s*$', text, re.IGNORECASE)
    if not match:
        return (None, None)

    base = re.sub(r'\s+', ' ', match.group('base')).strip(' ,;:')
    unit_value = match.group('unit').strip().upper()
    if not base or not unit_value:
        return (None, None)
    return (base, unit_value)


def _apply_hernando_subdivision_alias(name: str | None) -> tuple[str | None, str | None]:
    if not name:
        return (name, None)

    normalized = re.sub(r'\s+', ' ', name).strip()
    alias = _HERNANDO_SUBDIVISION_ALIASES.get(normalized.upper())
    if alias:
        return (alias, normalized)

    return (normalized, None)


def _extract_marker_references(tokens: list[str], marker_tokens: set[str], predicate) -> tuple[list[str], set[int]]:
    references = []
    used_indices = set()
    index = 0

    while index < len(tokens):
        token = tokens[index].upper().strip('.,;:')
        if token not in marker_tokens:
            index += 1
            continue

        used_indices.add(index)
        index += 1
        collected = []
        while index < len(tokens):
            current = tokens[index].strip('.,;:')
            upper = current.upper()
            if not current or upper in marker_tokens:
                break
            if predicate(current):
                collected.append(current)
                used_indices.add(index)
                index += 1
                continue
            if _is_descriptor_connector(current):
                next_index = index + 1
                next_token = tokens[next_index].strip('.,;:') if next_index < len(tokens) else ''
                if next_token and predicate(next_token):
                    collected.append(current.upper())
                    used_indices.add(index)
                    index += 1
                    continue
            break

        while collected and _is_descriptor_connector(collected[-1]):
            collected.pop()

        if collected:
            references.append(_normalize_descriptor_reference(' '.join(collected)))

    return references, used_indices


def _extract_hernando_subdivision_details(text: str) -> dict:
    normalized = re.sub(r'\bPODA\b', 'POD A', str(text).strip(), flags=re.IGNORECASE)
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    tokens = normalized.split()

    tract_values, tract_indices = _extract_marker_references(tokens, {'TR', 'TRACT', 'TRACTS'}, _is_hernando_tract_designator)
    pod_values, pod_indices = _extract_marker_references(tokens, {'POD', 'PODS'}, _is_hernando_pod_designator)

    unrecorded = bool(re.search(r'\bUNREC(?:ORDED)?\b', normalized, re.IGNORECASE))
    replat = bool(re.search(r'\bREPLAT\b', normalized, re.IGNORECASE))

    removable_indices = set(tract_indices) | set(pod_indices)
    for idx, token in enumerate(tokens):
        upper = token.upper().strip('.,;:')
        if upper in {'UNREC', 'UNRECORDED', 'REPLAT'}:
            removable_indices.add(idx)

    base_tokens = [token for idx, token in enumerate(tokens) if idx not in removable_indices]
    base_candidate = re.sub(r'\s+', ' ', ' '.join(base_tokens)).strip(' ,;:')
    unit_base, subdivision_unit = _extract_hernando_subdivision_unit(base_candidate)
    if unit_base:
        base_candidate = unit_base

    aliased_base_candidate, alias_source = _apply_hernando_subdivision_alias(base_candidate or None)

    return {
        'tract_values': tract_values,
        'pod_values': pod_values,
        'unrecorded': unrecorded,
        'replat': replat,
        'subdivision_unit': subdivision_unit,
        'base_candidate': aliased_base_candidate or None,
        'alias_source': alias_source,
    }


def _normalize_hernando_subdivision_candidates(subdivision_values: list[str], phase_keywords: list[str]) -> list[dict]:
    candidates = []
    seen = set()

    for raw_value in subdivision_values:
        raw_text = str(raw_value).strip()
        if not raw_text:
            continue

        normalized_raw = ' '.join(raw_text.split())
        subdivision_clean = clean_subdivision(normalized_raw, phase_keywords) or normalized_raw
        phase = fix_phase_typos(extract_phase(normalized_raw, phase_keywords)) or None
        details = _extract_hernando_subdivision_details(subdivision_clean)
        subdivision = subdivision_clean
        if (
            details['base_candidate']
            and (
                (details['tract_values'] and not details['pod_values'])
                or details.get('alias_source')
                or details.get('subdivision_unit')
            )
        ):
            subdivision = details['base_candidate']
        key = (subdivision.upper(), phase or '')
        if key in seen:
            continue
        seen.add(key)
        candidates.append({
            'raw': normalized_raw,
            'subdivision_clean': subdivision_clean,
            'subdivision': subdivision,
            'phase': phase,
            'details': details,
        })

    return candidates


def _normalize_labeled_subdivision_candidates(
    county_key: str,
    legal_lines: list[dict],
    phase_keywords: list[str],
) -> list[dict]:
    candidates = []
    seen = set()

    for line in legal_lines:
        raw_subdivision = line.get('subdivision')
        remarks_unrecorded = False
        if not raw_subdivision:
            raw_subdivision, remarks_unrecorded = _derive_subdivision_from_legal_remarks(
                line.get('legal_remarks'),
                phase_keywords,
            )
        if not raw_subdivision:
            continue

        normalized_raw = ' '.join(str(raw_subdivision).split())
        subdivision_clean = clean_subdivision(normalized_raw, phase_keywords) or normalized_raw
        subdivision_clean, alias_source, alias_details = _apply_subdivision_alias(county_key, subdivision_clean)
        if _ignored_subdivision_reason(county_key, subdivision_clean):
            continue
        phase = fix_phase_typos(extract_phase(normalized_raw, phase_keywords)) or None
        unit_value = line.get('unit')
        condo_value = line.get('condo')

        key = (
            subdivision_clean.upper(),
            phase or '',
            unit_value or '',
            condo_value or '',
            tuple(alias_details.get('prefix_tokens', [])),
            tuple(alias_details.get('suffix_tokens', [])),
        )
        if key in seen:
            continue
        seen.add(key)
        candidates.append({
            'raw': normalized_raw,
            'subdivision': subdivision_clean,
            'phase': phase,
            'details': {
                'lot': line.get('lot'),
                'block': line.get('block'),
                'unit': unit_value,
                'condo': condo_value,
                'section': line.get('section'),
                'township': line.get('township'),
                'range': line.get('range'),
                'parcel_reference': line.get('parcel'),
                'legal_remarks': line.get('legal_remarks'),
                'quarter_section': line.get('quarter_section'),
                'location_prefix': line.get('location_prefix'),
                'remarks_unrecorded': remarks_unrecorded,
                'alias_source': alias_source,
                'reference_match_type': alias_details.get('match_type'),
                'subdivision_prefix_tokens': list(alias_details.get('prefix_tokens', [])),
                'subdivision_suffix_tokens': list(alias_details.get('suffix_tokens', [])),
                'line_index': line.get('line_index'),
            },
        })

    return candidates


def _apply_subdivision_alias(county_key: str, subdivision: str) -> tuple[str, str | None, dict]:
    reference_match = resolve_county_subdivision_reference(county_key, subdivision)
    if reference_match:
        alias_source = None
        if reference_match['canonical_name'].upper() != subdivision.upper():
            alias_source = subdivision
        return (
            reference_match['canonical_name'],
            alias_source,
            {
                'match_type': reference_match['match_type'],
                'prefix_tokens': list(reference_match.get('prefix_tokens', [])),
                'suffix_tokens': list(reference_match.get('suffix_tokens', [])),
            },
        )

    alias_map = _SUBDIVISION_ALIASES.get(county_key, {})
    alias = alias_map.get(subdivision.upper())
    if alias:
        return (
            alias,
            subdivision,
            {
                'match_type': 'hardcoded_alias',
                'prefix_tokens': [],
                'suffix_tokens': [],
            },
        )
    return (
        subdivision,
        None,
        {
            'match_type': None,
            'prefix_tokens': [],
            'suffix_tokens': [],
        },
    )


def _normalize_phase_for_comparison(phase: str | None) -> str | None:
    if not phase:
        return None

    normalized = fix_phase_typos(str(phase).strip()).upper()
    word_number_map = {
        'ONE': '1',
        'TWO': '2',
        'THREE': '3',
        'FOUR': '4',
        'FIVE': '5',
        'SIX': '6',
        'SEVEN': '7',
        'EIGHT': '8',
        'NINE': '9',
        'TEN': '10',
        'ELEVEN': '11',
        'TWELVE': '12',
    }
    for word, number in word_number_map.items():
        normalized = re.sub(rf'^{word}(?=-[A-Z]$)', number, normalized)
    normalized = re.sub(r'\s*([/&-])\s*', r'\1', normalized)
    normalized = re.sub(r'^([0-9]+[A-Z]?)/[O0]$', r'\1', normalized)
    normalized = re.sub(r'^([0-9]+)-([A-Z])$', r'\1\2', normalized)
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    return normalized or None


def _coerce_phase_to_known(phase: str | None, known_phases: list[str] | None) -> tuple[str | None, bool]:
    normalized_phase = _normalize_phase_for_comparison(phase)
    if not normalized_phase or not known_phases:
        return phase, False

    for candidate in known_phases:
        normalized_candidate = _normalize_phase_for_comparison(candidate)
        if normalized_candidate == normalized_phase:
            return candidate, True

    return phase, False


def _build_transaction_segments(normalized_candidates: list[dict], county: str,
                                phase_keywords: list[str], sub_matcher,
                                parent_match: dict | None = None) -> list[dict]:
    segments = []

    for segment_index, candidate in enumerate(normalized_candidates):
        lookup_text = candidate.get('subdivision') or candidate.get('raw')
        raw_subdivision = candidate.get('raw')
        normalized_subdivision = candidate.get('subdivision')
        phase_raw = candidate.get('phase')

        subdivision_id = None
        canonical_subdivision = normalized_subdivision
        known_phases = []

        if (
            parent_match
            and len(normalized_candidates) == 1
            and parent_match.get('subdivision_id') is not None
        ):
            subdivision_id = parent_match.get('subdivision_id')
            canonical_subdivision = parent_match.get('subdivision') or normalized_subdivision
            known_phases = list(parent_match.get('known_phases') or [])
        elif sub_matcher and lookup_text:
            match_result = sub_matcher.match(lookup_text, county, phase_keywords)
            if isinstance(match_result, tuple) and len(match_result) == 4:
                subdivision_id, canonical_subdivision, _matched_phase, known_phases = match_result
            else:
                subdivision_id, canonical_subdivision, _matched_phase = match_result
                known_phases = []

        phase = phase_raw
        phase_confirmed = None
        review_reasons = []

        if subdivision_id is None:
            review_reasons.append('subdivision_unmatched')
        elif phase_raw:
            phase, phase_confirmed = _coerce_phase_to_known(phase_raw, known_phases)
            if not phase_confirmed:
                review_reasons.append('phase_not_confirmed_by_lookup')

        segments.append({
            'segment_index': segment_index,
            'county': county,
            'subdivision_lookup_text': lookup_text,
            'raw_subdivision': raw_subdivision,
            'subdivision': canonical_subdivision or normalized_subdivision,
            'subdivision_id': subdivision_id,
            'phase_raw': phase_raw,
            'phase': phase,
            'phase_confirmed': phase_confirmed,
            'review_reasons': review_reasons,
            'segment_data': {
                'raw': raw_subdivision,
                'subdivision_clean': candidate.get('subdivision_clean'),
                'details': dict(candidate.get('details') or {}),
                'known_phases': list(known_phases or []),
            },
        })

    return segments


def _normalize_freeform_subdivision_candidates(
    county_key: str,
    freeform_segments: list[dict],
    phase_keywords: list[str],
) -> list[dict]:
    candidates = []
    seen = set()

    for segment in freeform_segments:
        raw_subdivision = segment.get('subdivision_raw') or segment.get('subdivision')
        if not raw_subdivision:
            continue

        subdivision_phase_keywords = _phase_keywords_without_unit(phase_keywords)
        normalized_raw = ' '.join(str(raw_subdivision).split())
        normalized_subdivision = segment.get('subdivision') or normalized_raw
        subdivision_clean = clean_subdivision(normalized_subdivision, subdivision_phase_keywords) or normalized_subdivision
        subdivision_clean, alias_source, alias_details = _apply_subdivision_alias(county_key, subdivision_clean)
        if _ignored_subdivision_reason(county_key, subdivision_clean):
            continue
        phase = fix_phase_typos(extract_phase(normalized_raw, subdivision_phase_keywords)) or None

        key = (
            subdivision_clean.upper(),
            phase or '',
            segment.get('lot') or '',
            segment.get('block') or '',
            segment.get('unit') or '',
            segment.get('building') or '',
            segment.get('storage_locker') or '',
            tuple(alias_details.get('prefix_tokens', [])),
            tuple(alias_details.get('suffix_tokens', [])),
        )
        if key in seen:
            continue
        seen.add(key)
        candidates.append({
            'raw': normalized_raw,
            'subdivision': subdivision_clean,
            'phase': phase,
            'details': {
                'lot': segment.get('lot'),
                'partial_lot_values': segment.get('partial_lot_values', []),
                'block': segment.get('block'),
                'unit': segment.get('unit'),
                'building': segment.get('building'),
                'storage_locker': segment.get('storage_locker'),
                'condo': segment.get('condo'),
                'misc_lots': segment.get('misc_lots'),
                'parcel_references': segment.get('parcel_references', []),
                'parcel_designators': segment.get('parcel_designators', []),
                'section': segment.get('section'),
                'township': segment.get('township'),
                'range': segment.get('range'),
                'tract': segment.get('tract'),
                'common_area_code': segment.get('common_area_code'),
                'subdivision_partial': segment.get('subdivision_partial', False),
                'subdivision_flags': segment.get('subdivision_flags', []),
                'no_phase_value': segment.get('no_phase_value'),
                'alias_source': alias_source,
                'reference_match_type': alias_details.get('match_type'),
                'subdivision_prefix_tokens': list(alias_details.get('prefix_tokens', [])),
                'subdivision_suffix_tokens': list(alias_details.get('suffix_tokens', [])),
                'line_index': segment.get('line_index'),
            },
        })

    return candidates


def _resolve_party(raw, delimiters, builder_matcher, land_banker_matcher):
    """
    Split a multi-party field, check each name against builder and land banker
    matchers, and return (display_name, builder_id, land_banker_id, land_banker_category, parties).

    Keep the original source text for storage, but allow IDs to match against
    any individual party within the field.
    """
    display_name = str(raw).strip()
    parties = split_parties(display_name, delimiters)
    if not parties:
        return '', None, None, None, []

    builder_id = None
    land_banker_id = None
    land_banker_category = None

    for name in parties:
        if builder_matcher and builder_id is None:
            builder_id, _canonical = builder_matcher.match(name)
        if land_banker_matcher and land_banker_id is None:
            land_banker_id, _canonical, land_banker_category = land_banker_matcher.match(name)
        if builder_id is not None and land_banker_id is not None:
            break

    return display_name, builder_id, land_banker_id, land_banker_category, parties


def _build_deed_locator(row: pd.Series) -> dict:
    locator = {}
    raw_fields = {}

    for target_key, column_names in _DEED_LOCATOR_COLUMN_MAP.items():
        for column_name in column_names:
            if column_name not in row:
                continue

            value = _clean_locator_value(row.get(column_name))
            if not value:
                continue

            raw_fields[column_name] = value
            locator.setdefault(target_key, value)

    doc_links = []
    for column_name in _DEED_LINK_COLUMNS:
        if column_name not in row:
            continue
        value = _clean_locator_value(row.get(column_name))
        if value:
            raw_fields[column_name] = value
            _append_unique(doc_links, value)
    if doc_links:
        locator['doc_links'] = doc_links
        locator['doc_link'] = doc_links[0]

    image_links = []
    for column_name in _DEED_IMAGE_COLUMNS:
        if column_name not in row:
            continue
        value = _clean_locator_value(row.get(column_name))
        if value:
            raw_fields[column_name] = value
            _append_unique(image_links, value)
    if image_links:
        locator['image_links'] = image_links
        locator['image_link'] = image_links[0]

    book_page = locator.get('book_page')
    if book_page and (not locator.get('book') or not locator.get('page')):
        parts = re.split(r'\s*/\s*', book_page, maxsplit=1)
        if len(parts) == 2:
            locator.setdefault('book', parts[0].strip() or None)
            locator.setdefault('page', parts[1].strip() or None)

    if raw_fields:
        locator['raw_fields'] = raw_fields

    locator = {key: value for key, value in locator.items() if value not in (None, '', [], {})}
    return locator


def _prepare_party_text(raw, county_key: str, role: str, delimiters: list[str]) -> str:
    if pd.isna(raw) or raw is None:
        return ''

    text = str(raw).strip()
    if not text:
        return ''

    if county_key == 'OKALOOSA' and role == 'grantee':
        non_party_delimiters = [
            d for d in delimiters
            if str(d).strip().upper() in {'PARCEL', 'SECTION'}
        ]
        if non_party_delimiters:
            return before_first_delimiter(text, non_party_delimiters)

    return text


def transform_row(row: pd.Series, county: str, config: dict,
                  sub_matcher=None, builder_matcher=None,
                  land_banker_matcher=None) -> dict | None:
    """
    Transform a raw source row into a clean dict ready for DB insert.
    Returns None if the row should be skipped (missing grantor).
    """
    cols = config['column_mapping']
    delimiters = config.get('delimiters', [])
    county_key = normalize_county_key(county)
    county_parse = {}
    preparsed_subdivision = None
    subdivision_lookup_text = None
    normalized_candidates = []
    transaction_segments = []
    deed_locator = _build_deed_locator(row)
    force_review_flag = False
    review_reasons = []
    swap_reason = None
    phase_candidate_values = []
    phase_keywords = config.get('phase_keywords', [])
    subdivision_phase_keywords = (
        _phase_keywords_without_unit(phase_keywords)
        if county_key in {'BAY', 'WALTON', 'OKEECHOBEE', 'MARION', 'SANTAROSA'}
        else phase_keywords
    )

    # --- Grantor / Grantee (multi-party with entity matching) ---
    grantor_raw = _prepare_party_text(
        row.get(cols.get('grantor', ''), pd.NA),
        county_key,
        'grantor',
        delimiters,
    )
    if not grantor_raw:
        return None

    grantor, grantor_builder_id, grantor_land_banker_id, _grantor_lb_cat, grantor_parties = _resolve_party(
        grantor_raw, delimiters, builder_matcher, land_banker_matcher
    )

    grantee_raw = _prepare_party_text(
        row.get(cols.get('grantee', ''), pd.NA),
        county_key,
        'grantee',
        delimiters,
    )
    grantee, grantee_builder_id, grantee_land_banker_id, grantee_land_banker_category, grantee_parties = _resolve_party(
        grantee_raw, delimiters, builder_matcher, land_banker_matcher
    )

    # Keep legacy builder_id populated for compatibility, preferring the buyer side.
    builder_id = grantee_builder_id or grantor_builder_id

    # --- County-specific party swaps ---
    if county_key == 'MARION':
        star_col = cols.get('star', 'Star')
        if star_col in row and str(row[star_col]).strip() != '*':
            grantor, grantee = grantee, grantor
            grantor_builder_id, grantee_builder_id = grantee_builder_id, grantor_builder_id
            grantor_land_banker_id, grantee_land_banker_id = grantee_land_banker_id, grantor_land_banker_id
            _grantor_lb_cat, grantee_land_banker_category = grantee_land_banker_category, _grantor_lb_cat
            grantor_parties, grantee_parties = grantee_parties, grantor_parties
            swap_reason = 'marion_star_swap'

    elif county_key == 'SANTAROSA':
        party_type_col = cols.get('party_type', 'Party Type')
        if party_type_col in row:
            if 'to' in str(row[party_type_col]).strip().lower():
                grantor, grantee = grantee, grantor
                grantor_builder_id, grantee_builder_id = grantee_builder_id, grantor_builder_id
                grantor_land_banker_id, grantee_land_banker_id = grantee_land_banker_id, grantor_land_banker_id
                _grantor_lb_cat, grantee_land_banker_category = grantee_land_banker_category, _grantor_lb_cat
                grantor_parties, grantee_parties = grantee_parties, grantor_parties
                swap_reason = 'santarosa_party_type_swap'

    # --- Export legal text (dual output: raw + cleaned approximation) ---
    legal_src = row.get(cols.get('legal', ''), pd.NA)
    export_legal_raw = ''
    if pd.notna(legal_src):
        export_legal_raw = (
            str(legal_src)
            .replace('\r\n', '\n')
            .replace('\r', '\n')
            .strip()
        )
    export_legal_desc = re.sub(r'\s+', ' ', export_legal_raw).strip() if export_legal_raw else ''

    if county_key == 'WALTON':
        county_parse = parse_walton_row(row, cols)
        export_legal_desc = county_parse['legal']
    elif county_key == 'BAY':
        county_parse = parse_bay_row(row, cols)
        export_legal_desc = county_parse['legal']
    elif county_key == 'MARION':
        county_parse = parse_marion_row(row, cols)
        export_legal_desc = county_parse['legal']
    elif county_key == 'HERNANDO':
        county_parse = parse_hernando_row(row, cols)
        export_legal_desc = county_parse['legal']
    elif county_key == 'CITRUS':
        county_parse = parse_citrus_row(row, cols)
        export_legal_desc = county_parse['legal']
    elif county_key == 'ESCAMBIA':
        county_parse = parse_escambia_row(row, cols)
        export_legal_desc = county_parse['legal']
    elif county_key == 'OKALOOSA':
        county_parse = parse_okaloosa_row(row, cols)
        export_legal_desc = county_parse['legal']
    elif county_key == 'OKEECHOBEE':
        county_parse = parse_okeechobee_row(row, cols)
        export_legal_desc = county_parse['legal']
    elif county_key == 'SANTAROSA':
        county_parse = parse_santarosa_row(row, cols)
        export_legal_desc = county_parse['legal']

    export_legal_raw = export_legal_raw or None
    export_legal_desc = export_legal_desc or None

    if county_key == 'HERNANDO':
        subdivision_values = county_parse.get('subdivision_values', [])
        normalized_candidates = _normalize_hernando_subdivision_candidates(subdivision_values, phase_keywords)
        normalized_subdivision_values = []
        base_subdivision_candidates = []
        tract_values = []
        pod_values = []
        subdivision_unit_values = []
        subdivision_flags = []
        for candidate in normalized_candidates:
            _append_unique(normalized_subdivision_values, candidate['subdivision'])
            _append_unique(phase_candidate_values, candidate['phase'])
            _append_unique(base_subdivision_candidates, candidate['details'].get('base_candidate'))
            for tract_value in candidate['details'].get('tract_values', []):
                _append_unique(tract_values, tract_value)
            for pod_value in candidate['details'].get('pod_values', []):
                _append_unique(pod_values, pod_value)
            _append_unique(subdivision_unit_values, candidate['details'].get('subdivision_unit'))
            if candidate['details'].get('unrecorded'):
                _append_unique(subdivision_flags, 'unrecorded')
            if candidate['details'].get('replat'):
                _append_unique(subdivision_flags, 'replat')

        county_parse['normalized_subdivision_candidates'] = normalized_candidates
        county_parse['normalized_subdivision_values'] = normalized_subdivision_values
        county_parse['base_subdivision_candidates'] = base_subdivision_candidates
        county_parse['phase_values'] = phase_candidate_values
        county_parse['tract_values'] = tract_values
        county_parse['pod_values'] = pod_values
        county_parse['subdivision_unit_values'] = subdivision_unit_values
        county_parse['subdivision_flags'] = subdivision_flags

        if county_parse.get('unparsed_lines'):
            force_review_flag = True
            review_reasons.append('hernando_unparsed_lines')

        if len(normalized_candidates) == 1:
            preparsed_subdivision = normalized_candidates[0]['subdivision']
            subdivision_lookup_text = normalized_candidates[0]['subdivision']
        elif len(normalized_subdivision_values) == 1:
            preparsed_subdivision = normalized_subdivision_values[0]
            subdivision_lookup_text = normalized_subdivision_values[0]
            force_review_flag = True
            review_reasons.append('subdivision_ambiguous_candidates')
            if len(phase_candidate_values) > 1:
                review_reasons.append('multiple_phase_candidates')
        elif len(normalized_subdivision_values) > 1:
            preparsed_subdivision = ' / '.join(normalized_subdivision_values)
            subdivision_lookup_text = ''
            force_review_flag = True
            review_reasons.append('multiple_subdivision_candidates')
        else:
            subdivision_lookup_text = export_legal_desc
    elif county_key in {'CITRUS', 'ESCAMBIA', 'OKALOOSA'}:
        normalized_candidates = _normalize_labeled_subdivision_candidates(
            county_key,
            county_parse.get('labeled_lines', []),
            phase_keywords,
        )
        normalized_subdivision_values = []
        structured_lot_values = []
        structured_block_values = []
        structured_unit_values = []
        structured_condo_values = []
        structured_section_values = []
        structured_township_values = []
        structured_range_values = []
        structured_parcel_references = []
        legal_remarks_values = []
        quarter_section_values = []
        location_prefix_values = []
        for candidate in normalized_candidates:
            _append_unique(normalized_subdivision_values, candidate['subdivision'])
            _append_unique(phase_candidate_values, candidate['phase'])
            _append_unique(structured_lot_values, candidate['details'].get('lot'))
            _append_unique(structured_block_values, candidate['details'].get('block'))
            _append_unique(structured_unit_values, candidate['details'].get('unit'))
            _append_unique(structured_condo_values, candidate['details'].get('condo'))
            _append_unique(structured_section_values, candidate['details'].get('section'))
            _append_unique(structured_township_values, candidate['details'].get('township'))
            _append_unique(structured_range_values, candidate['details'].get('range'))
            _append_unique(structured_parcel_references, candidate['details'].get('parcel_reference'))
            _append_unique(legal_remarks_values, candidate['details'].get('legal_remarks'))
            _append_unique(quarter_section_values, candidate['details'].get('quarter_section'))
            _append_unique(location_prefix_values, candidate['details'].get('location_prefix'))

        for structured_parcel_reference in county_parse.get('parcel_references', []):
            _append_unique(structured_parcel_references, structured_parcel_reference)
        for legal_remarks_value in county_parse.get('legal_remarks_values', []):
            _append_unique(legal_remarks_values, legal_remarks_value)
        for quarter_section_value in county_parse.get('quarter_section_values', []):
            _append_unique(quarter_section_values, quarter_section_value)
        for location_prefix_value in county_parse.get('location_prefix_values', []):
            _append_unique(location_prefix_values, location_prefix_value)
        for structured_section_value in county_parse.get('section_values', []):
            _append_unique(structured_section_values, structured_section_value)
        for structured_township_value in county_parse.get('township_values', []):
            _append_unique(structured_township_values, structured_township_value)
        for structured_range_value in county_parse.get('range_values', []):
            _append_unique(structured_range_values, structured_range_value)
        for structured_lot_value in county_parse.get('lot_values', []):
            _append_unique(structured_lot_values, structured_lot_value)
        for structured_block_value in county_parse.get('block_values', []):
            _append_unique(structured_block_values, structured_block_value)
        for structured_unit_value in county_parse.get('unit_values', []):
            _append_unique(structured_unit_values, structured_unit_value)

        county_parse['normalized_subdivision_candidates'] = normalized_candidates
        county_parse['normalized_subdivision_values'] = normalized_subdivision_values
        county_parse['phase_values'] = phase_candidate_values
        county_parse['structured_lot_values'] = structured_lot_values
        county_parse['structured_block_values'] = structured_block_values
        county_parse['structured_unit_values'] = structured_unit_values
        county_parse['structured_condo_values'] = structured_condo_values
        county_parse['structured_section_values'] = structured_section_values
        county_parse['structured_township_values'] = structured_township_values
        county_parse['structured_range_values'] = structured_range_values
        county_parse['structured_parcel_references'] = structured_parcel_references
        county_parse['legal_remarks_values'] = legal_remarks_values
        county_parse['quarter_section_values'] = quarter_section_values
        county_parse['location_prefix_values'] = location_prefix_values

        if len(normalized_candidates) == 1:
            preparsed_subdivision = normalized_candidates[0]['subdivision']
            subdivision_lookup_text = normalized_candidates[0]['subdivision']
        elif len(normalized_subdivision_values) == 1:
            preparsed_subdivision = normalized_subdivision_values[0]
            subdivision_lookup_text = normalized_subdivision_values[0]
            force_review_flag = True
            review_reasons.append('subdivision_ambiguous_candidates')
            if len(phase_candidate_values) > 1:
                review_reasons.append('multiple_phase_candidates')
        elif len(normalized_subdivision_values) > 1:
            preparsed_subdivision = ' / '.join(normalized_subdivision_values)
            subdivision_lookup_text = ''
            force_review_flag = True
            review_reasons.append('multiple_subdivision_candidates')
        else:
            subdivision_lookup_text = '' if county_key == 'OKALOOSA' else export_legal_desc
    elif county_key in {'BAY', 'WALTON', 'OKEECHOBEE', 'MARION', 'SANTAROSA'}:
        normalized_candidates = _normalize_freeform_subdivision_candidates(
            county_key,
            county_parse.get('freeform_segments', []),
            phase_keywords,
        )
        normalized_subdivision_values = []
        structured_block_values = []
        structured_unit_values = []
        structured_building_values = []
        structured_storage_locker_values = []
        condo_flags = []
        parcel_references = []
        partial_lot_values = []
        partial_lot_identifiers = []
        section_values = []
        township_values = []
        range_values = []
        tract_values = []
        common_area_codes = []
        parcel_designators = []
        subdivision_prefix_values = []
        subdivision_suffix_values = []
        subdivision_flags = []
        no_phase_values = []
        for candidate in normalized_candidates:
            _append_unique(normalized_subdivision_values, candidate['subdivision'])
            _append_unique(phase_candidate_values, candidate['phase'])
            _append_unique(structured_block_values, candidate['details'].get('block'))
            _append_unique(structured_unit_values, candidate['details'].get('unit'))
            _append_unique(structured_building_values, candidate['details'].get('building'))
            _append_unique(structured_storage_locker_values, candidate['details'].get('storage_locker'))
            _append_unique(tract_values, candidate['details'].get('tract'))
            _append_unique(common_area_codes, candidate['details'].get('common_area_code'))
            if candidate['details'].get('condo'):
                _append_unique(condo_flags, 'condo')
            for parcel_reference in candidate['details'].get('parcel_references', []):
                _append_unique(parcel_references, parcel_reference)
            for parcel_designator in candidate['details'].get('parcel_designators', []):
                _append_unique(parcel_designators, parcel_designator)
            for partial_lot_value in candidate['details'].get('partial_lot_values', []):
                _append_unique(partial_lot_values, partial_lot_value)
            _append_unique(section_values, candidate['details'].get('section'))
            _append_unique(township_values, candidate['details'].get('township'))
            _append_unique(range_values, candidate['details'].get('range'))
            if candidate['details'].get('subdivision_partial'):
                _append_unique(subdivision_flags, 'partial_subdivision')
            for prefix_token in candidate['details'].get('subdivision_prefix_tokens', []):
                _append_unique(subdivision_prefix_values, prefix_token)
            for suffix_token in candidate['details'].get('subdivision_suffix_tokens', []):
                _append_unique(subdivision_suffix_values, suffix_token)
            for subdivision_flag in candidate['details'].get('subdivision_flags', []):
                _append_unique(subdivision_flags, subdivision_flag)
            _append_unique(no_phase_values, candidate['details'].get('no_phase_value'))

        for parcel_reference in county_parse.get('parcel_references', []):
            _append_unique(parcel_references, parcel_reference)
        for block_value in county_parse.get('block_values', []):
            _append_unique(structured_block_values, block_value)
        for unit_value in county_parse.get('unit_values', []):
            _append_unique(structured_unit_values, unit_value)
        for section_value in county_parse.get('section_values', []):
            _append_unique(section_values, section_value)
        for township_value in county_parse.get('township_values', []):
            _append_unique(township_values, township_value)
        for range_value in county_parse.get('range_values', []):
            _append_unique(range_values, range_value)
        for tract_value in county_parse.get('tract_values', []):
            _append_unique(tract_values, tract_value)
        for common_area_code in county_parse.get('common_area_codes', []):
            _append_unique(common_area_codes, common_area_code)
        for parcel_designator in county_parse.get('parcel_designators', []):
            _append_unique(parcel_designators, parcel_designator)
        for partial_lot_value in county_parse.get('partial_lot_values', []):
            _append_unique(partial_lot_values, partial_lot_value)
        for partial_lot_identifier in county_parse.get('partial_lot_identifiers', []):
            _append_unique(partial_lot_identifiers, partial_lot_identifier)
        for subdivision_flag in county_parse.get('subdivision_flags', []):
            _append_unique(subdivision_flags, subdivision_flag)
        for no_phase_value in county_parse.get('no_phase_values', []):
            _append_unique(no_phase_values, no_phase_value)

        county_parse['normalized_subdivision_candidates'] = normalized_candidates
        county_parse['normalized_subdivision_values'] = normalized_subdivision_values
        county_parse['phase_values'] = phase_candidate_values
        county_parse['structured_block_values'] = structured_block_values
        county_parse['structured_unit_values'] = structured_unit_values
        county_parse['structured_building_values'] = structured_building_values
        county_parse['structured_storage_locker_values'] = structured_storage_locker_values
        county_parse['condo_flags'] = condo_flags
        county_parse['structured_parcel_references'] = parcel_references
        county_parse['structured_partial_lot_values'] = partial_lot_values
        county_parse['structured_partial_lot_identifiers'] = partial_lot_identifiers
        county_parse['structured_section_values'] = section_values
        county_parse['structured_township_values'] = township_values
        county_parse['structured_range_values'] = range_values
        county_parse['tract_values'] = tract_values
        county_parse['common_area_codes'] = common_area_codes
        county_parse['parcel_designators'] = parcel_designators
        county_parse['subdivision_prefix_values'] = subdivision_prefix_values
        county_parse['subdivision_suffix_values'] = subdivision_suffix_values
        county_parse['subdivision_flags'] = subdivision_flags
        county_parse['no_phase_values'] = no_phase_values

        if county_key == 'SANTAROSA' and county_parse.get('unparsed_lines'):
            force_review_flag = True
            review_reasons.append('santarosa_unparsed_lines')

        if len(normalized_candidates) == 1:
            preparsed_subdivision = normalized_candidates[0]['subdivision']
            subdivision_lookup_text = normalized_candidates[0]['subdivision']
        elif len(normalized_subdivision_values) == 1:
            preparsed_subdivision = normalized_subdivision_values[0]
            subdivision_lookup_text = normalized_subdivision_values[0]
            force_review_flag = True
            review_reasons.append('subdivision_ambiguous_candidates')
            if len(phase_candidate_values) > 1:
                review_reasons.append('multiple_phase_candidates')
        elif len(normalized_subdivision_values) > 1:
            preparsed_subdivision = ' / '.join(normalized_subdivision_values)
            subdivision_lookup_text = ''
            force_review_flag = True
            review_reasons.append('multiple_subdivision_candidates')
        else:
            subdivision_lookup_text = '' if county_key in {'OKEECHOBEE', 'SANTAROSA'} else export_legal_desc
    else:
        subdivision_lookup_text = export_legal_desc

    # --- Subdivision and phase (lookup-first, regex fallback) ---
    review_flag = False
    subdivision_id = None
    subdivision = None
    phase = None
    known_phases = []
    ignored_subdivision_reason = None

    if sub_matcher and subdivision_lookup_text:
        match_result = sub_matcher.match(
            subdivision_lookup_text, county, phase_keywords
        )
        if isinstance(match_result, tuple) and len(match_result) == 4:
            subdivision_id, subdivision, phase, known_phases = match_result
        else:
            subdivision_id, subdivision, phase = match_result

    if subdivision_id is not None:
        phase, phase_is_known = _coerce_phase_to_known(phase, known_phases)
        if phase is None and len(phase_candidate_values) == 1:
            phase = phase_candidate_values[0]
            phase, phase_is_known = _coerce_phase_to_known(phase, known_phases)
            if phase and not phase_is_known:
                review_flag = True
                review_reasons.append('phase_not_confirmed_by_lookup')
        elif phase is None:
            phase = fix_phase_typos(extract_phase(subdivision_lookup_text, subdivision_phase_keywords))
            phase, phase_is_known = _coerce_phase_to_known(phase, known_phases)
            if phase and not phase_is_known:
                review_flag = True
                review_reasons.append('phase_not_confirmed_by_lookup')
    else:
        fallback_text = preparsed_subdivision or subdivision_lookup_text
        if 'multiple_subdivision_candidates' in review_reasons:
            subdivision = None
            phase = None
        elif not fallback_text:
            subdivision = None
            phase = None
        else:
            ignored_subdivision_reason = _ignored_subdivision_reason(county_key, fallback_text)
        if fallback_text and not ignored_subdivision_reason and 'multiple_subdivision_candidates' not in review_reasons:
            review_flag = True
            review_reasons.append('subdivision_unmatched')
            if len(phase_candidate_values) == 1:
                phase = phase_candidate_values[0]
            elif len(phase_candidate_values) > 1:
                phase = None
            else:
                phase = fix_phase_typos(extract_phase(fallback_text, subdivision_phase_keywords))
            subdivision = clean_subdivision(fallback_text, subdivision_phase_keywords)

            if county_key in {'SANTAROSA', 'CITRUS'}:
                subdivision = remove_santarosa_unit(subdivision)

            subdivision = subdivision.strip() if subdivision else None

    if force_review_flag:
        review_flag = True

    if len(phase_candidate_values) > 1 and 'multiple_phase_candidates' not in review_reasons:
        review_flag = True
        review_reasons.append('multiple_phase_candidates')

    parent_match = {
        'subdivision_id': subdivision_id,
        'subdivision': subdivision,
        'phase': phase,
        'known_phases': known_phases,
    }
    if normalized_candidates:
        transaction_segments = _build_transaction_segments(
            normalized_candidates,
            county,
            phase_keywords,
            sub_matcher,
            parent_match=parent_match,
        )

    inventory_category = classify_inventory_category(county, subdivision)
    for segment in transaction_segments:
        segment_inventory_category = classify_inventory_category(county, segment.get('subdivision'))
        segment['inventory_category'] = segment_inventory_category
        segment['segment_data'].pop('inventory_category', None)

    instrument = str(row.get(cols.get('instrument', ''), '')).strip()
    date = parse_date(row.get(cols.get('date', ''), pd.NA))

    price_raw = row.get(cols.get('price', ''), '')
    try:
        price = float(str(price_raw).replace(',', '').strip()) if str(price_raw).strip() else None
    except (ValueError, TypeError):
        price = None

    lots_col = cols.get('lots', '')
    lots_raw = row.get(lots_col, '') if lots_col else ''
    try:
        lots = int(float(str(lots_raw).strip())) if str(lots_raw).strip() else 1
    except (ValueError, TypeError):
        lots = 1

    helper_lot_count = county_parse.get('lot_count')
    if helper_lot_count is not None:
        lots = helper_lot_count

    acres, acres_source = _extract_record_acres(row, cols, export_legal_desc, county_parse)
    county_parse_for_storage = dict(county_parse)
    county_parse_for_storage.pop('legal', None)

    parsed_data = {
        'grantor_parties': grantor_parties,
        'grantee_parties': grantee_parties,
        'swap': {
            'applied': swap_reason is not None,
            'reason': swap_reason,
        },
        'subdivision_lookup_text': subdivision_lookup_text or None,
        'preparsed_subdivision': preparsed_subdivision,
        'ignored_subdivision_reason': ignored_subdivision_reason,
        'phase_candidate_values': phase_candidate_values,
        'review_reasons': review_reasons,
        'county_parse': county_parse_for_storage,
    }

    trans_type = classify_transaction_type(
        grantor_builder_id,
        grantee_builder_id,
        grantor_land_banker_id,
        grantee_land_banker_id,
        grantee=grantee,
        instrument=instrument,
        export_legal_desc=export_legal_desc,
        subdivision=subdivision,
        county_parse=county_parse_for_storage,
        acres=acres,
        grantee_land_banker_category=grantee_land_banker_category,
    )

    return {
        'grantor':                 grantor,
        'grantee':                 grantee or None,
        'type':                    trans_type,
        'instrument':              instrument or None,
        'date':                    date,
        'export_legal_desc':       export_legal_desc,
        'export_legal_raw':        export_legal_raw,
        'deed_locator':            deed_locator,
        'deed_legal_desc':         None,
        'deed_legal_parsed':       {},
        'subdivision':             subdivision or None,
        'subdivision_id':          subdivision_id,
        'phase':                   phase or None,
        'inventory_category':      inventory_category,
        'lots':                    lots,
        'acres':                   acres,
        'acres_source':            acres_source,
        'price':                   price,
        'parsed_data':             parsed_data,
        'transaction_segments':    transaction_segments,
        'county':                  county,
        'builder_id':              builder_id,
        'grantor_builder_id':      grantor_builder_id,
        'grantee_builder_id':      grantee_builder_id,
        'grantor_land_banker_id':  grantor_land_banker_id,
        'grantee_land_banker_id':  grantee_land_banker_id,
        'review_flag':             review_flag,
    }
