from __future__ import annotations

import re

import pandas as pd


_HERNANDO_HEADER_RE = re.compile(r'^\s*L\s*Blk\s*Un\s*Sub\s*S\s*T\s*R\s*$', re.IGNORECASE)
_HERNANDO_STR_TAIL_RE = re.compile(r'\s*S\s*T\s*R\s*$', re.IGNORECASE)
_HERNANDO_STR_INFO_RE = re.compile(
    r'^(?P<subdivision>.*?)(?:\s+S(?P<section>\d{1,2})\s*T(?P<township>\d{1,2}[NS]?)\s*R(?P<range>\d{1,2}[EW]?))\s*$',
    re.IGNORECASE,
)
_HELPER_PREFIX_RE = re.compile(r'(?i)^legalfield_')
_LOT_RANGE_RE = re.compile(r'^(?P<start>\d+)\s*-\s*(?P<end>\d+)$')
_LOT_TOKEN_RE = re.compile(r'(?:[A-Z]+-)?\d+[A-Z]?')
_HERNANDO_SEGMENT_RE = re.compile(
    r'^L(?P<lot>.*?)\s*Blk(?P<block>.*?)\s*Un(?P<unit>.*?)\s*Sub(?P<subdivision>.*?)\s*$',
    re.IGNORECASE,
)
_HERNANDO_PARCEL_RE = re.compile(r'^[A-Z]?\d[\d-]{10,}[A-Z0-9-]*$', re.IGNORECASE)
_LABELED_FIELD_RE = re.compile(r'(?P<label>[A-Z]{1,10})\s*:\s*', re.IGNORECASE)
_REDACTION_RE = re.compile(r'^REDACTION APPLIED\b', re.IGNORECASE)
_CITRUS_PART_LOT_RE = re.compile(r'^(?:PT|PART)\s+L(?:OTS?|TS?)?\s*(?P<lot>.+)$', re.IGNORECASE)
_CITRUS_CASE_RE = re.compile(r'^\d{4}\s+CA\s+\d+\s+[A-Z]\b', re.IGNORECASE)
_CITRUS_METES_RE = re.compile(r'^COM\s+AT\b', re.IGNORECASE)
_FREEFORM_PARCEL_RE = re.compile(r'^\(?[A-Z]?\d[A-Z0-9-]{5,}\)?$', re.IGNORECASE)
_FREEFORM_STORAGE_UNIT_RE = re.compile(
    r'^(?:(?P<condo>CONDO)\s+)?UNIT\s+(?P<unit>[A-Z0-9-]+)\s*&\s*STORAGE\s+LOCKER\s+NO\.?\s*(?P<locker>[A-Z0-9-]+)\s+(?P<subdivision>.+)$',
    re.IGNORECASE,
)
_FREEFORM_BUILDING_UNIT_RE = re.compile(
    r'^(?:(?P<condo>CONDO)\s+)?UNIT\s+(?P<unit>[A-Z0-9-]+)\s+(?:BLDG|BUILDING)\s+(?P<building>[A-Z0-9-]+)\s+(?P<subdivision>.+)$',
    re.IGNORECASE,
)
_FREEFORM_SIMPLE_UNIT_RE = re.compile(
    r'^(?:(?P<condo>CONDO)\s+)?UNIT\s+(?P<unit>[A-Z0-9-]+)\s+(?:OF\s+)?(?P<subdivision>.+)$',
    re.IGNORECASE,
)
_FREEFORM_TRAILING_UNIT_RE = re.compile(
    r'^(?P<subdivision>.+?)\s+UNIT\s+(?P<unit>[A-Z0-9-]+)\s*$',
    re.IGNORECASE,
)
_OKEECHOBEE_STR_RE = re.compile(r'(?P<section>\d{1,2})/(?P<township>\d{2})/(?P<range>\d{2})$')
_HELPER_FIELDS = (
    ('lot', 'lot', 'Lot'),
    ('building', 'building', 'Building'),
    ('block', 'block', 'Block'),
    ('unit', 'unit', 'Unit'),
    ('subdivision', 'sub', 'Subdivision'),
    ('section', 'section', 'Section'),
    ('township', 'township', 'Township'),
    ('range', 'range', 'Range'),
    ('land_lot', 'land_lot', 'Land Lot'),
    ('district', 'district', 'District'),
    ('property_section', 'property_section', 'Property Section'),
)
_CITRUS_LABEL_ALIASES = {
    'L': 'lot',
    'LOT': 'lot',
    'BLK': 'block',
    'BLOCK': 'block',
    'SUB': 'subdivision',
    'U': 'unit',
    'UNIT': 'unit',
    'S': 'section',
    'T': 'township',
    'R': 'range',
}
_ESCAMBIA_LABEL_ALIASES = {
    'LOT': 'lot',
    'BLK': 'block',
    'BLOCK': 'block',
    'SUB': 'subdivision',
    'SEC': 'section',
    'TWP': 'township',
    'RGE': 'range',
    'UNI': 'unit',
    'CON': 'condo',
}
_OKALOOSA_LABEL_ALIASES = {
    'LEGAL REMARKS': 'legal_remarks',
    'QUARTER SECTION': 'quarter_section',
    'TOWNSHIP': 'township',
    'SECTION': 'section',
    'BLOCK': 'block',
    'RANGE': 'range',
    'PARCEL': 'parcel',
    'LOT': 'lot',
    'UNIT': 'unit',
}
_OKALOOSA_FIELD_RE = re.compile(
    r'(?P<label>'
    + '|'.join(re.escape(label) for label in sorted(_OKALOOSA_LABEL_ALIASES, key=len, reverse=True))
    + r')\s*:\s*',
    re.IGNORECASE,
)
_MARION_LOT_RE = re.compile(
    r'^(?:(?P<partial>PT|PTN)\s+)?(?P<prefix>LT|LS)\s+(?P<lot>[A-Z0-9-]+(?:\s*(?:,|&|AND)\s*[A-Z0-9-]+)*)'
    r'(?:\s+(?:BK|BLK)\s+(?P<block>[A-Z0-9-]+))?\s+(?P<rest>.+)$',
    re.IGNORECASE,
)
_MARION_TRACT_RE = re.compile(
    r'^(?P<prefix>TR|TRS|TRACT|TRACTS)\s+(?P<tract>[A-Z0-9-]+)\s+(?P<rest>.+)$',
    re.IGNORECASE,
)
_MARION_UNIT_RE = re.compile(r'^(?P<subdivision>.+?)\s+U[-\s]?(?P<unit>[A-Z0-9./-]+)\s*$', re.IGNORECASE)
_MARION_REPLAT_RE = re.compile(r'^(?P<subdivision>.+?)\s+(?P<replat>\d+(?:ST|ND|RD|TH|SR)\s+REPLAT)\s*$', re.IGNORECASE)
_MARION_COMMON_AREA_CODE_RE = re.compile(r'^(?P<code>[A-Z]{2,5})\s+(?P<subdivision>.+)$')
_SANTAROSA_LOCATION_RE = re.compile(
    r'^(?P<section>\d{1,2})-(?P<township>\d{1,2}[NS])-(?P<range>\d{1,2}[EW])$',
    re.IGNORECASE,
)
_SANTAROSA_ENTRY_TOKEN_RE = r'(?:[A-Z]?\d+[A-Z]{0,3})(?:-\d+[A-Z]{0,3})?'
_SANTAROSA_ENTRY_SEPARATOR_RE = r'(?:\s*(?:,|&|AND)\s*)'
_SANTAROSA_SLASH_ENTRY_RE = re.compile(
    rf'(?P<partial>\bPT\s+)?'
    rf'(?P<lots>{_SANTAROSA_ENTRY_TOKEN_RE}(?:{_SANTAROSA_ENTRY_SEPARATOR_RE}{_SANTAROSA_ENTRY_TOKEN_RE})*)'
    r'\s*/\s*(?P<block>[A-Z0-9-]+)\b',
    re.IGNORECASE,
)
_SANTAROSA_EXPLICIT_LOT_RE = re.compile(
    rf'^(?P<header>.*?)'
    rf'(?:\s+(?P<partial>PT)\s+)?'
    rf'LOTS?\s+(?P<lots>{_SANTAROSA_ENTRY_TOKEN_RE}(?:{_SANTAROSA_ENTRY_SEPARATOR_RE}{_SANTAROSA_ENTRY_TOKEN_RE})*)\s*$',
    re.IGNORECASE,
)
_SANTAROSA_TRACT_RE = re.compile(
    r'^(?P<header>.*?)'
    r'(?:\s+(?P<partial>PT)\s+)?'
    r'TRACTS?\s+(?P<tract>[A-Z0-9-]+)\s*$',
    re.IGNORECASE,
)
_SANTAROSA_PARCEL_RE = re.compile(
    r'^(?:(?P<header>.*?)\s+)?'
    r'(?:ALL\s+COMMON\s+AREAS\s+)?'
    r'PARCELS?\s+(?P<parcel>[A-Z0-9-]+(?:\s*,\s*[A-Z0-9-]+)*)'
    r'(?:\s+(?P<suffix>ET\s+AL|LIFT\s+STATION))?\s*$',
    re.IGNORECASE,
)
_SANTAROSA_COMMON_AREA_RE = re.compile(
    r'^(?P<header>.*?)\s+COMMON\s+AREAS?(?:\s*,\s*(?P<suffix>EASEMENTS?))?\s*$',
    re.IGNORECASE,
)


def _split_helper_values(value) -> list[str]:
    if pd.isna(value) or value is None:
        return []

    values = []
    for line in str(value).replace('\r', '').split('\n'):
        normalized = _HELPER_PREFIX_RE.sub('', line).strip()
        if normalized:
            values.append(normalized)
    return values


def _unique_preserve_order(values: list[str]) -> list[str]:
    seen = set()
    ordered = []
    for value in values:
        key = value.upper()
        if key in seen:
            continue
        seen.add(key)
        ordered.append(value)
    return ordered


def _append_unique(items: list[str], value: str | None) -> None:
    if value and value not in items:
        items.append(value)


def _normalized_or_none(value: str) -> str | None:
    cleaned = re.sub(r'\s+', ' ', value).strip()
    return cleaned or None


def _clean_raw_helper_value(value) -> str | None:
    if pd.isna(value) or value is None:
        return None

    cleaned = str(value).replace('\r', '').strip()
    return cleaned or None


def _parse_labeled_fields(text: str, label_aliases: dict[str, str]) -> list[dict]:
    matches = list(_LABELED_FIELD_RE.finditer(text))
    if not matches:
        return []

    fields = []
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        raw_value = text[start:end].strip(' \t|,;')
        fields.append({
            'label': match.group('label').upper(),
            'canonical': label_aliases.get(match.group('label').upper()),
            'value': _normalized_or_none(raw_value),
        })
    return fields


def _build_labeled_line_entry(text: str, label_aliases: dict[str, str]) -> dict | None:
    fields = _parse_labeled_fields(text, label_aliases)
    if not fields:
        return None

    canonical_values = {}
    for field in fields:
        canonical = field['canonical']
        value = field['value']
        if canonical and value and canonical not in canonical_values:
            canonical_values[canonical] = value

    return {
        'kind': 'labeled_line',
        'raw': text,
        'fields': fields,
        'recognized_fields': [field['canonical'] for field in fields if field['canonical']],
        'lot': canonical_values.get('lot'),
        'block': canonical_values.get('block'),
        'unit': canonical_values.get('unit'),
        'subdivision': canonical_values.get('subdivision'),
        'section': canonical_values.get('section'),
        'township': canonical_values.get('township'),
        'range': canonical_values.get('range'),
        'condo': canonical_values.get('condo'),
    }


def _parse_citrus_special_line(text: str) -> dict | None:
    if _REDACTION_RE.match(text):
        return {
            'kind': 'redaction',
            'raw': text,
        }

    if _CITRUS_CASE_RE.match(text):
        return {
            'kind': 'case_reference',
            'raw': text,
            'case_reference': text,
        }

    if _CITRUS_METES_RE.match(text):
        return {
            'kind': 'metes_bounds_note',
            'raw': text,
            'metes_bounds_note': text,
        }

    part_lot_match = _CITRUS_PART_LOT_RE.match(text)
    if part_lot_match:
        return {
            'kind': 'part_lot',
            'raw': text,
            'part_lot': _normalized_or_none(part_lot_match.group('lot')),
        }

    return None


def _parse_labeled_row(legal_value, label_aliases: dict[str, str], special_line_parser=None) -> dict:
    legal_lines = []
    labeled_lines = []
    raw_legal_lines = []
    redaction_lines = []
    case_references = []
    metes_bounds_notes = []
    part_lot_values = []
    unparsed_lines = []

    if pd.notna(legal_value):
        for line_index, line in enumerate(str(legal_value).replace('\r', '').split('\n')):
            text = str(line).strip()
            if not text:
                continue

            raw_legal_lines.append(text)

            if special_line_parser:
                special_line = special_line_parser(text)
                if special_line is not None:
                    special_line['line_index'] = line_index
                    legal_lines.append(special_line)
                    if special_line['kind'] == 'redaction':
                        redaction_lines.append(special_line['raw'])
                    elif special_line['kind'] == 'case_reference' and special_line.get('case_reference'):
                        case_references.append(special_line['case_reference'])
                    elif special_line['kind'] == 'metes_bounds_note' and special_line.get('metes_bounds_note'):
                        metes_bounds_notes.append(special_line['metes_bounds_note'])
                    elif special_line['kind'] == 'part_lot' and special_line.get('part_lot'):
                        part_lot_values.append(special_line['part_lot'])
                    continue

            labeled_line = _build_labeled_line_entry(text, label_aliases)
            if labeled_line is None:
                entry = {
                    'kind': 'unparsed',
                    'raw': text,
                    'line_index': line_index,
                }
                legal_lines.append(entry)
                unparsed_lines.append(text)
                continue

            labeled_line['line_index'] = line_index
            legal_lines.append(labeled_line)
            labeled_lines.append(labeled_line)

    lot_values = _unique_preserve_order([line['lot'] for line in labeled_lines if line.get('lot')])
    block_values = _unique_preserve_order([line['block'] for line in labeled_lines if line.get('block')])
    unit_values = _unique_preserve_order([line['unit'] for line in labeled_lines if line.get('unit')])
    subdivision_values = _unique_preserve_order([line['subdivision'] for line in labeled_lines if line.get('subdivision')])
    section_values = _unique_preserve_order([line['section'] for line in labeled_lines if line.get('section')])
    township_values = _unique_preserve_order([line['township'] for line in labeled_lines if line.get('township')])
    range_values = _unique_preserve_order([line['range'] for line in labeled_lines if line.get('range')])
    condo_values = _unique_preserve_order([line['condo'] for line in labeled_lines if line.get('condo')])

    lot_identifiers = _unique_preserve_order([
        identifier
        for value in lot_values
        for identifier in _expand_identifier_value(value)
    ])
    unit_identifiers = _unique_preserve_order([
        identifier
        for value in unit_values
        for identifier in _expand_identifier_value(value)
    ])
    labels_present = _unique_preserve_order([
        field['label']
        for line in labeled_lines
        for field in line.get('fields', [])
    ])
    lot_count = sum(_count_lot_value(value) for value in lot_values) if lot_values else None

    return {
        'legal': '; '.join(line['raw'] for line in legal_lines) or '',
        'raw_legal_lines': raw_legal_lines,
        'legal_lines': legal_lines,
        'labeled_lines': labeled_lines,
        'redaction_lines': redaction_lines,
        'case_references': _unique_preserve_order(case_references),
        'metes_bounds_notes': _unique_preserve_order(metes_bounds_notes),
        'part_lot_values': _unique_preserve_order(part_lot_values),
        'unparsed_lines': unparsed_lines,
        'lot_values': lot_values,
        'block_values': block_values,
        'unit_values': unit_values,
        'subdivision_values': subdivision_values,
        'section_values': section_values,
        'township_values': township_values,
        'range_values': range_values,
        'condo_values': condo_values,
        'lot_identifiers': lot_identifiers,
        'unit_identifiers': unit_identifiers,
        'lot_count': lot_count,
        'segment_count': len(labeled_lines),
        'labels_present': labels_present,
        'redacted': bool(redaction_lines),
    }


def parse_citrus_row(row: pd.Series, cols: dict) -> dict:
    legal_value = row.get(cols.get('legal', ''), pd.NA)
    return _parse_labeled_row(legal_value, _CITRUS_LABEL_ALIASES, _parse_citrus_special_line)


def parse_escambia_row(row: pd.Series, cols: dict) -> dict:
    legal_value = row.get(cols.get('legal', ''), pd.NA)
    return _parse_labeled_row(legal_value, _ESCAMBIA_LABEL_ALIASES)


def _parse_okaloosa_fields(text: str) -> tuple[str | None, list[dict]]:
    matches = list(_OKALOOSA_FIELD_RE.finditer(text))
    if not matches:
        return (_normalized_or_none(text), [])

    leading_text = _normalized_or_none(text[:matches[0].start()].strip(' \t|,;'))
    fields = []
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        raw_value = text[start:end].strip(' \t|,;')
        label = match.group('label').upper()
        fields.append({
            'label': label,
            'canonical': _OKALOOSA_LABEL_ALIASES.get(label),
            'value': _normalized_or_none(raw_value),
        })

    return (leading_text, fields)


def _build_okaloosa_clause_entry(text: str) -> dict | None:
    normalized = _normalize_freeform_line(text)
    if not normalized:
        return None

    leading_text, fields = _parse_okaloosa_fields(normalized)
    if not fields:
        upper = normalized.upper()
        if (
            re.search(r'[A-Z]', upper)
            and ':' not in normalized
            and not any(
                marker in upper
                for marker in ('SECTION', 'TOWNSHIP', 'RANGE', 'PARCEL', 'LEGAL REMARKS', 'QUARTER')
            )
        ):
            return {
                'kind': 'subdivision_only',
                'raw': normalized,
                'leading_text': normalized,
                'location_prefix': None,
                'lot': None,
                'block': None,
                'unit': None,
                'subdivision': normalized,
                'section': None,
                'township': None,
                'range': None,
                'parcel': None,
                'legal_remarks': None,
                'quarter_section': None,
                'condo': None,
                'fields': [],
                'recognized_fields': [],
            }
        return {
            'kind': 'unparsed',
            'raw': normalized,
            'leading_text': leading_text,
        }

    canonical_values = {}
    for field in fields:
        canonical = field['canonical']
        value = field['value']
        if canonical and value and canonical not in canonical_values:
            canonical_values[canonical] = value

    subdivision = None
    location_prefix = leading_text
    if leading_text and any(canonical_values.get(key) for key in ('lot', 'block', 'unit')):
        subdivision = leading_text
        location_prefix = None

    return {
        'kind': 'labeled_line',
        'raw': normalized,
        'fields': fields,
        'recognized_fields': [field['canonical'] for field in fields if field['canonical']],
        'leading_text': leading_text,
        'location_prefix': location_prefix,
        'lot': canonical_values.get('lot'),
        'block': canonical_values.get('block'),
        'unit': canonical_values.get('unit'),
        'subdivision': subdivision,
        'section': canonical_values.get('section'),
        'township': canonical_values.get('township'),
        'range': canonical_values.get('range'),
        'parcel': canonical_values.get('parcel'),
        'legal_remarks': canonical_values.get('legal_remarks'),
        'quarter_section': canonical_values.get('quarter_section'),
        'condo': None,
    }


def parse_okaloosa_row(row: pd.Series, cols: dict) -> dict:
    legal_value = row.get(cols.get('legal', ''), pd.NA)

    legal_lines = []
    labeled_lines = []
    raw_legal_lines = []
    unparsed_lines = []
    parcel_references = []
    legal_remarks_values = []
    quarter_section_values = []
    location_prefix_values = []

    if pd.notna(legal_value):
        for line_index, line in enumerate(str(legal_value).replace('\r', '').split('\n')):
            text = str(line).strip()
            if not text:
                continue

            raw_legal_lines.append(text)
            for clause_index, clause in enumerate(re.split(r'\s*,\s*', text)):
                clause_text = str(clause).strip()
                if not clause_text:
                    continue

                entry = _build_okaloosa_clause_entry(clause_text)
                if entry is None:
                    continue

                entry['line_index'] = line_index
                entry['segment_index'] = clause_index
                legal_lines.append(entry)

                if entry['kind'] == 'subdivision_only':
                    labeled_lines.append(entry)
                    continue

                if entry['kind'] != 'labeled_line':
                    unparsed_lines.append(entry['raw'])
                    continue

                labeled_lines.append(entry)
                if entry.get('parcel'):
                    parcel_references.append(entry['parcel'])
                if entry.get('legal_remarks'):
                    legal_remarks_values.append(entry['legal_remarks'])
                if entry.get('quarter_section'):
                    quarter_section_values.append(entry['quarter_section'])
                if entry.get('location_prefix'):
                    location_prefix_values.append(entry['location_prefix'])

    lot_values = _unique_preserve_order([line['lot'] for line in labeled_lines if line.get('lot')])
    block_values = _unique_preserve_order([line['block'] for line in labeled_lines if line.get('block')])
    unit_values = _unique_preserve_order([line['unit'] for line in labeled_lines if line.get('unit')])
    subdivision_values = _unique_preserve_order([line['subdivision'] for line in labeled_lines if line.get('subdivision')])
    section_values = _unique_preserve_order([line['section'] for line in labeled_lines if line.get('section')])
    township_values = _unique_preserve_order([line['township'] for line in labeled_lines if line.get('township')])
    range_values = _unique_preserve_order([line['range'] for line in labeled_lines if line.get('range')])

    lot_identifiers = _unique_preserve_order([
        identifier
        for value in lot_values
        for identifier in _expand_identifier_value(value)
    ])
    unit_identifiers = _unique_preserve_order([
        identifier
        for value in unit_values
        for identifier in _expand_identifier_value(value)
    ])
    labels_present = _unique_preserve_order([
        field['label']
        for line in labeled_lines
        for field in line.get('fields', [])
    ])
    lot_count = sum(_count_lot_value(value) for value in lot_values) if lot_values else None

    return {
        'legal': '; '.join(line['raw'] for line in legal_lines) or '',
        'raw_legal_lines': raw_legal_lines,
        'legal_lines': legal_lines,
        'labeled_lines': labeled_lines,
        'unparsed_lines': unparsed_lines,
        'parcel_references': _unique_preserve_order(parcel_references),
        'legal_remarks_values': _unique_preserve_order(legal_remarks_values),
        'quarter_section_values': _unique_preserve_order(quarter_section_values),
        'location_prefix_values': _unique_preserve_order(location_prefix_values),
        'lot_values': lot_values,
        'block_values': block_values,
        'unit_values': unit_values,
        'subdivision_values': subdivision_values,
        'section_values': section_values,
        'township_values': township_values,
        'range_values': range_values,
        'lot_identifiers': lot_identifiers,
        'unit_identifiers': unit_identifiers,
        'lot_count': lot_count,
        'segment_count': len(labeled_lines),
        'labels_present': labels_present,
    }


def _extract_marion_subdivision_details(text: str | None, *, allow_common_area_code: bool = False) -> dict:
    subdivision_raw = _normalized_or_none(text or '')
    if not subdivision_raw:
        return {
            'subdivision_raw': None,
            'subdivision': None,
            'unit': None,
            'common_area_code': None,
            'subdivision_partial': False,
            'subdivision_flags': [],
        }

    common_area_code = None
    if allow_common_area_code:
        common_area_match = _MARION_COMMON_AREA_CODE_RE.match(subdivision_raw or '')
        if common_area_match:
            common_area_code = _normalized_or_none(common_area_match.group('code') or '')
            subdivision_raw = _normalized_or_none(common_area_match.group('subdivision') or '')
    elif subdivision_raw.upper().startswith('SCBDW '):
        common_area_code = 'SCBDW'
        subdivision_raw = _normalized_or_none(subdivision_raw[6:])

    subdivision_partial = False
    partial_match = re.match(r'^(?:PT|PTN)\s+(?P<subdivision>.+)$', subdivision_raw or '', re.IGNORECASE)
    if partial_match:
        subdivision_partial = True
        subdivision_raw = _normalized_or_none(partial_match.group('subdivision') or '')

    subdivision_flags = []
    replat_match = _MARION_REPLAT_RE.match(subdivision_raw or '')
    if replat_match:
        subdivision_raw = _normalized_or_none(replat_match.group('subdivision') or '')
        subdivision_flags.append('replat')

    unit_value = None
    unit_match = _MARION_UNIT_RE.match(subdivision_raw)
    if unit_match:
        subdivision_raw = _normalized_or_none(unit_match.group('subdivision') or '')
        unit_value = _normalized_or_none(unit_match.group('unit') or '')

    return {
        'subdivision_raw': subdivision_raw,
        'subdivision': _normalize_freeform_subdivision_text(subdivision_raw),
        'unit': unit_value,
        'common_area_code': common_area_code,
        'subdivision_partial': subdivision_partial,
        'subdivision_flags': subdivision_flags,
    }


def parse_marion_row(row: pd.Series, cols: dict) -> dict:
    legal_lines = []
    freeform_segments = []
    raw_legal_lines = []
    unparsed_lines = []
    legal_value = row.get(cols.get('legal', ''), pd.NA)

    if pd.notna(legal_value):
        for line_index, line in enumerate(str(legal_value).replace('\r', '').split('\n')):
            text = str(line).strip()
            if not text or text.lower() == 'nan':
                continue

            raw_legal_lines.append(text)
            normalized = _normalize_freeform_line(text)
            lot_match = _MARION_LOT_RE.match(normalized)
            tract_match = _MARION_TRACT_RE.match(normalized)

            parsed_segment = None
            if lot_match:
                subdivision_details = _extract_marion_subdivision_details(lot_match.group('rest'))
                parsed_segment = {
                    'kind': 'marion_segment',
                    'source_raw': normalized,
                    'raw': normalized,
                    'parcel_references': [],
                    'misc_lots': str(lot_match.group('prefix') or '').upper() == 'LS',
                    'lot': _normalized_or_none(lot_match.group('lot') or ''),
                    'partial_lot_values': [_normalized_or_none(lot_match.group('lot') or '')] if lot_match.group('partial') else [],
                    'block': _normalized_or_none(lot_match.group('block') or ''),
                    'subdivision_raw': subdivision_details['subdivision_raw'],
                    'subdivision': subdivision_details['subdivision'],
                    'unit': subdivision_details['unit'],
                    'building': None,
                    'storage_locker': None,
                    'condo': False,
                    'tract': None,
                    'common_area_code': subdivision_details['common_area_code'],
                    'subdivision_partial': subdivision_details['subdivision_partial'],
                    'subdivision_flags': subdivision_details['subdivision_flags'],
                    'line_index': line_index,
                    'segment_index': 0,
                }
            elif tract_match:
                subdivision_details = _extract_marion_subdivision_details(
                    tract_match.group('rest'),
                    allow_common_area_code=True,
                )
                parsed_segment = {
                    'kind': 'marion_segment',
                    'source_raw': normalized,
                    'raw': normalized,
                    'parcel_references': [],
                    'misc_lots': False,
                    'lot': None,
                    'partial_lot_values': [],
                    'block': None,
                    'subdivision_raw': subdivision_details['subdivision_raw'],
                    'subdivision': subdivision_details['subdivision'],
                    'unit': subdivision_details['unit'],
                    'building': None,
                    'storage_locker': None,
                    'condo': False,
                    'tract': _normalized_or_none(tract_match.group('tract') or ''),
                    'common_area_code': subdivision_details['common_area_code'],
                    'subdivision_partial': subdivision_details['subdivision_partial'],
                    'subdivision_flags': subdivision_details['subdivision_flags'],
                    'line_index': line_index,
                    'segment_index': 0,
                }
            else:
                subdivision_details = _extract_marion_subdivision_details(normalized)
                parsed_segment = {
                    'kind': 'marion_segment',
                    'source_raw': normalized,
                    'raw': normalized,
                    'parcel_references': [],
                    'misc_lots': False,
                    'lot': None,
                    'partial_lot_values': [],
                    'block': None,
                    'subdivision_raw': subdivision_details['subdivision_raw'],
                    'subdivision': subdivision_details['subdivision'],
                    'unit': subdivision_details['unit'],
                    'building': None,
                    'storage_locker': None,
                    'condo': False,
                    'tract': None,
                    'common_area_code': subdivision_details['common_area_code'],
                    'subdivision_partial': subdivision_details['subdivision_partial'],
                    'subdivision_flags': subdivision_details['subdivision_flags'],
                    'line_index': line_index,
                    'segment_index': 0,
                }

            if not parsed_segment.get('subdivision_raw') and not parsed_segment.get('lot') and not parsed_segment.get('tract'):
                unparsed_lines.append(normalized)

            legal_lines.append(parsed_segment)
            freeform_segments.append(parsed_segment)

    lot_values = _unique_preserve_order([segment['lot'] for segment in freeform_segments if segment.get('lot')])
    block_values = _unique_preserve_order([segment['block'] for segment in freeform_segments if segment.get('block')])
    unit_values = _unique_preserve_order([segment['unit'] for segment in freeform_segments if segment.get('unit')])
    subdivision_values = _unique_preserve_order([segment['subdivision_raw'] for segment in freeform_segments if segment.get('subdivision_raw')])
    tract_values = _unique_preserve_order([segment['tract'] for segment in freeform_segments if segment.get('tract')])
    common_area_codes = _unique_preserve_order([
        segment['common_area_code']
        for segment in freeform_segments
        if segment.get('common_area_code')
    ])
    partial_lot_values = _unique_preserve_order([
        value
        for segment in freeform_segments
        for value in segment.get('partial_lot_values', [])
        if value
    ])
    subdivision_flags = _unique_preserve_order([
        flag
        for segment in freeform_segments
        for flag in segment.get('subdivision_flags', [])
    ])
    if any(segment.get('subdivision_partial') for segment in freeform_segments):
        subdivision_flags = _unique_preserve_order(subdivision_flags + ['partial_subdivision'])
    lot_identifiers = _unique_preserve_order([
        identifier
        for value in lot_values
        for identifier in _expand_identifier_value(value)
    ])
    partial_lot_identifiers = _unique_preserve_order([
        identifier
        for value in partial_lot_values
        for identifier in _expand_identifier_value(value)
    ])
    unit_identifiers = _unique_preserve_order([
        identifier
        for value in unit_values
        for identifier in _expand_identifier_value(value)
    ])
    lot_count = sum(_count_lot_value(value) for value in lot_values) if lot_values else None

    return {
        'legal': '; '.join(segment['raw'] for segment in legal_lines) or '',
        'raw_legal_lines': raw_legal_lines,
        'legal_lines': legal_lines,
        'freeform_segments': freeform_segments,
        'unparsed_lines': _unique_preserve_order(unparsed_lines),
        'parcel_references': [],
        'lot_values': lot_values,
        'partial_lot_values': partial_lot_values,
        'block_values': block_values,
        'unit_values': unit_values,
        'subdivision_values': subdivision_values,
        'tract_values': tract_values,
        'common_area_codes': common_area_codes,
        'subdivision_flags': subdivision_flags,
        'lot_identifiers': lot_identifiers,
        'partial_lot_identifiers': partial_lot_identifiers,
        'unit_identifiers': unit_identifiers,
        'lot_count': lot_count,
        'segment_count': len(freeform_segments),
    }


def _is_connector_token(token: str) -> bool:
    return token.upper() in {'&', 'AND'}


def _is_lot_token(token: str) -> bool:
    upper = token.upper().strip('.,;:')
    if not upper:
        return False
    if upper in {'ETC', 'PART', 'PT', '&', 'AND'}:
        return True
    return bool(re.fullmatch(r'(?:TH)?[A-Z]?\d+[A-Z]?(?:-\d+[A-Z]?)?', upper))


def _is_block_token(token: str) -> bool:
    upper = token.upper().strip('.,;:')
    if not upper:
        return False
    if upper in {'PART', 'PT', '&', 'AND'}:
        return True
    return bool(re.fullmatch(r'[A-Z0-9]+(?:-[A-Z0-9]+)?', upper))


def _normalize_freeform_line(text: str, strip_legal_prefix: bool = False) -> str:
    normalized = str(text).replace('\r', ' ').replace('\n', ' ').strip()
    if strip_legal_prefix:
        normalized = re.sub(r'(?i)^LEGAL\s+', '', normalized)
    normalized = re.sub(r'(?i)^L(?=\d)', 'L ', normalized)
    normalized = re.sub(r'\s+', ' ', normalized)
    return normalized.strip()


def _normalize_freeform_subdivision_text(text: str | None) -> str | None:
    if not text:
        return None

    normalized = re.sub(r'\s+', ' ', str(text)).strip(' ,;:')
    normalized = re.sub(r'(?i)^OF\s+', '', normalized)
    normalized = re.sub(r'(?i)\s+S/D(?:\s+ETC)?$', '', normalized)
    normalized = re.sub(r'(?i)\s+ETC$', '', normalized)
    normalized = re.sub(r'\s+', ' ', normalized).strip(' ,;:')
    return normalized or None


def _extract_freeform_subdivision_details(text: str | None) -> dict:
    raw_text = _normalized_or_none(text or '')
    if not raw_text:
        return {
            'subdivision_raw': None,
            'subdivision': None,
            'unit': None,
            'building': None,
            'storage_locker': None,
            'condo': False,
        }

    for pattern in (_FREEFORM_STORAGE_UNIT_RE, _FREEFORM_BUILDING_UNIT_RE, _FREEFORM_SIMPLE_UNIT_RE):
        match = pattern.match(raw_text)
        if not match:
            continue

        return {
            'subdivision_raw': raw_text,
            'subdivision': _normalize_freeform_subdivision_text(match.group('subdivision')),
            'unit': _normalized_or_none(match.group('unit') or ''),
            'building': _normalized_or_none(match.groupdict().get('building') or ''),
            'storage_locker': _normalized_or_none(match.groupdict().get('locker') or ''),
            'condo': bool(match.groupdict().get('condo')),
        }

    trailing_match = _FREEFORM_TRAILING_UNIT_RE.match(raw_text)
    if trailing_match:
        return {
            'subdivision_raw': raw_text,
            'subdivision': _normalize_freeform_subdivision_text(trailing_match.group('subdivision')),
            'unit': _normalized_or_none(trailing_match.group('unit') or ''),
            'building': None,
            'storage_locker': None,
            'condo': False,
        }

    return {
        'subdivision_raw': raw_text,
        'subdivision': _normalize_freeform_subdivision_text(raw_text),
        'unit': None,
        'building': None,
        'storage_locker': None,
        'condo': False,
    }


def _consume_leading_parcel_references(text: str) -> tuple[str, list[str]]:
    remaining = text
    parcel_references = []

    while remaining:
        token_match = re.match(r'^(?P<token>\(?[A-Z]?\d[A-Z0-9-]{5,}\)?)\s*(?:\|\s*|[,;:.-]\s*|\s+)?', remaining)
        if not token_match:
            break

        token = token_match.group('token').strip('()')
        if not _FREEFORM_PARCEL_RE.fullmatch(token):
            break

        parcel_references.append(token)
        remaining = remaining[token_match.end():].strip()

    return remaining, parcel_references


def _is_okeechobee_lot_value(token: str) -> bool:
    upper = token.upper().strip('.,;:')
    return bool(re.fullmatch(r'\d+[A-Z]?(?:-\d+[A-Z]?)?', upper))


def _consume_okeechobee_lot_tokens(tokens: list[str]) -> tuple[list[str], list[str], int]:
    lot_values = []
    partial_lot_values = []
    index = 0

    while index < len(tokens):
        token = tokens[index].upper().strip('.,;:')
        partial = False

        if token == 'PTN':
            partial = True
            index += 1
            if index < len(tokens) and tokens[index].upper().strip('.,;:') in {'LOT', 'LOTS'}:
                index += 1
        elif token in {'LOT', 'LOTS'}:
            index += 1
        else:
            break

        if index >= len(tokens):
            break

        value = tokens[index].strip('.,;:')
        if not _is_okeechobee_lot_value(value):
            break

        lot_values.append(value)
        if partial:
            partial_lot_values.append(value)
        index += 1

        if index < len(tokens) and _is_connector_token(tokens[index].upper().strip('.,;:')):
            index += 1

    return (lot_values, partial_lot_values, index)


def _split_okeechobee_segments(text: str) -> list[str]:
    remaining = _normalized_or_none(text or '')
    if not remaining:
        return []

    pattern = re.compile(r'\s+&\s+(?=(?:PTN\s+)?LOTS?\s+\d)', re.IGNORECASE)
    segments = []

    while remaining:
        split_match = None
        for match in pattern.finditer(remaining):
            prefix = remaining[:match.start()]
            if re.search(r'\bBLK\b', prefix, re.IGNORECASE):
                split_match = match
                break

        if split_match is None:
            segments.append(remaining.strip())
            break

        segments.append(remaining[:split_match.start()].strip())
        remaining = remaining[split_match.end():].strip()

    return segments


def _extract_okeechobee_str(text: str) -> tuple[str, str | None, str | None, str | None]:
    normalized = _normalized_or_none(text or '')
    if not normalized:
        return ('', None, None, None)

    match = _OKEECHOBEE_STR_RE.search(normalized)
    if not match:
        return (normalized, None, None, None)

    cleaned = normalized[:match.start()].strip(' ,;:')
    return (
        cleaned,
        _normalized_or_none(match.group('section') or ''),
        _normalized_or_none(match.group('township') or ''),
        _normalized_or_none(match.group('range') or ''),
    )


def _build_okeechobee_unit_details(subdivision_raw: str | None) -> dict:
    normalized = _normalized_or_none(subdivision_raw or '')
    if not normalized:
        return {
            'subdivision_raw': None,
            'subdivision': None,
            'unit': None,
            'building': None,
            'storage_locker': None,
            'condo': False,
        }

    unit_only_match = re.fullmatch(r'UNIT\s+(?P<unit>[A-Z0-9-]+)', normalized, re.IGNORECASE)
    if unit_only_match:
        return {
            'subdivision_raw': None,
            'subdivision': None,
            'unit': _normalized_or_none(unit_only_match.group('unit') or ''),
            'building': None,
            'storage_locker': None,
            'condo': False,
        }

    return _extract_freeform_subdivision_details(normalized)


def parse_okeechobee_row(row: pd.Series, cols: dict) -> dict:
    legal_lines = []
    freeform_segments = []
    raw_legal_lines = []
    parcel_references = []
    unparsed_lines = []

    legal_value = row.get(cols.get('legal', ''), pd.NA)
    if pd.notna(legal_value):
        for line_index, line in enumerate(str(legal_value).replace('\r', '').split('\n')):
            text = str(line).strip()
            if not text:
                continue

            raw_legal_lines.append(text)
            normalized = _normalize_freeform_line(text)
            cleaned_text, line_parcel_references = _consume_leading_parcel_references(normalized)
            for parcel_reference in line_parcel_references:
                parcel_references.append(parcel_reference)

            if not cleaned_text:
                legal_lines.append({
                    'kind': 'parcel_reference',
                    'source_raw': normalized,
                    'raw': normalized,
                    'parcel_references': line_parcel_references,
                    'line_index': line_index,
                })
                continue

            for segment_index, segment_text in enumerate(_split_okeechobee_segments(cleaned_text)):
                segment_body, section_value, township_value, range_value = _extract_okeechobee_str(segment_text)
                tokens = segment_body.split()
                lot_parts, partial_lot_values, token_index = _consume_okeechobee_lot_tokens(tokens)
                block_value = None
                if token_index < len(tokens) and tokens[token_index].upper().strip('.,;:') in {'BLK', 'BLOCK'}:
                    block_tokens, token_index = _collect_block_tokens(tokens, token_index + 1)
                    block_value = _normalized_or_none(' '.join(block_tokens))

                subdivision_raw = _normalized_or_none(' '.join(tokens[token_index:]))
                subdivision_partial = False
                if subdivision_raw and subdivision_raw.upper().startswith('PTN '):
                    subdivision_partial = True
                    subdivision_raw = _normalized_or_none(subdivision_raw[4:])

                subdivision_details = _build_okeechobee_unit_details(subdivision_raw)
                lot_value = _normalized_or_none(' & '.join(lot_parts))

                cleaned_segments = []
                if lot_value:
                    lot_prefix = 'LOTS' if len(lot_parts) > 1 or any('-' in part for part in lot_parts) else 'LOT'
                    cleaned_segments.append(f'{lot_prefix} {lot_value}')
                if block_value:
                    cleaned_segments.append(f'BLK {block_value}')
                if subdivision_raw:
                    cleaned_segments.append(subdivision_raw)
                if section_value and township_value and range_value:
                    cleaned_segments.append(f'{section_value}/{township_value}/{range_value}')

                parsed_segment = {
                    'kind': 'freeform_segment',
                    'source_raw': normalized,
                    'raw': ' '.join(cleaned_segments) or segment_body,
                    'parcel_references': line_parcel_references,
                    'misc_lots': False,
                    'lot': lot_value,
                    'partial_lot_values': partial_lot_values,
                    'block': block_value,
                    'subdivision_raw': subdivision_details['subdivision_raw'],
                    'subdivision': subdivision_details['subdivision'],
                    'unit': subdivision_details['unit'],
                    'building': subdivision_details['building'],
                    'storage_locker': subdivision_details['storage_locker'],
                    'condo': subdivision_details['condo'],
                    'section': section_value,
                    'township': township_value,
                    'range': range_value,
                    'subdivision_partial': subdivision_partial,
                    'line_index': line_index,
                    'segment_index': segment_index,
                }
                legal_lines.append(parsed_segment)
                freeform_segments.append(parsed_segment)

    lot_values = _unique_preserve_order([line['lot'] for line in freeform_segments if line.get('lot')])
    partial_lot_values = _unique_preserve_order([
        partial_lot_value
        for line in freeform_segments
        for partial_lot_value in line.get('partial_lot_values', [])
    ])
    block_values = _unique_preserve_order([line['block'] for line in freeform_segments if line.get('block')])
    unit_values = _unique_preserve_order([line['unit'] for line in freeform_segments if line.get('unit')])
    subdivision_values = _unique_preserve_order([
        line['subdivision'] for line in freeform_segments if line.get('subdivision')
    ])
    section_values = _unique_preserve_order([
        line['section'] for line in freeform_segments if line.get('section')
    ])
    township_values = _unique_preserve_order([
        line['township'] for line in freeform_segments if line.get('township')
    ])
    range_values = _unique_preserve_order([
        line['range'] for line in freeform_segments if line.get('range')
    ])
    subdivision_flags = _unique_preserve_order([
        'partial_subdivision'
        for line in freeform_segments
        if line.get('subdivision_partial')
    ])
    lot_identifiers = _unique_preserve_order([
        identifier
        for value in lot_values
        for identifier in _expand_identifier_value(value)
    ])
    partial_lot_identifiers = _unique_preserve_order([
        identifier
        for value in partial_lot_values
        for identifier in _expand_identifier_value(value)
    ])
    lot_count = sum(_count_lot_value(value) for value in lot_values) if lot_values else None

    return {
        'legal': '; '.join(line['raw'] for line in legal_lines if line['kind'] == 'freeform_segment') or '',
        'raw_legal_lines': raw_legal_lines,
        'legal_lines': legal_lines,
        'freeform_segments': freeform_segments,
        'parcel_references': _unique_preserve_order(parcel_references),
        'unparsed_lines': unparsed_lines,
        'lot_values': lot_values,
        'partial_lot_values': partial_lot_values,
        'block_values': block_values,
        'unit_values': unit_values,
        'subdivision_values': subdivision_values,
        'section_values': section_values,
        'township_values': township_values,
        'range_values': range_values,
        'lot_identifiers': lot_identifiers,
        'partial_lot_identifiers': partial_lot_identifiers,
        'lot_count': lot_count,
        'segment_count': len(freeform_segments),
        'subdivision_flags': subdivision_flags,
    }


def _collect_prefixed_tokens(tokens: list[str], start_index: int, predicate) -> tuple[list[str], int]:
    collected = []
    index = start_index

    while index < len(tokens):
        token = tokens[index]
        upper = token.upper().strip('.,;:')
        if upper in {'BLK', 'BLOCK'}:
            break
        if predicate(token):
            collected.append(token)
            index += 1
            continue
        if _is_connector_token(upper):
            collected.append(upper)
            index += 1
            continue
        break

    while collected and _is_connector_token(collected[-1].upper().strip('.,;:')):
        collected.pop()

    return collected, index


def _collect_block_tokens(tokens: list[str], start_index: int) -> tuple[list[str], int]:
    if start_index >= len(tokens):
        return ([], start_index)

    first = tokens[start_index]
    if not _is_block_token(first):
        return ([], start_index)

    collected = [first]
    index = start_index + 1

    if first.upper().strip('.,;:') in {'PART', 'PT'} and index < len(tokens) and _is_block_token(tokens[index]):
        collected.append(tokens[index])
        index += 1

    return (collected, index)


def parse_freeform_legal_line(text: str, strip_legal_prefix: bool = False) -> dict | None:
    normalized = _normalize_freeform_line(text, strip_legal_prefix=strip_legal_prefix)
    if not normalized:
        return None

    cleaned_text, parcel_references = _consume_leading_parcel_references(normalized)
    if not cleaned_text:
        return {
            'kind': 'parcel_reference',
            'source_raw': normalized,
            'raw': normalized,
            'parcel_references': parcel_references,
        }

    tokens = cleaned_text.split()
    index = 0
    misc_lots = False
    lot_value = None
    block_value = None
    lot_prefix = None

    if len(tokens) >= 2 and tokens[0].upper() == 'MISC' and tokens[1].upper().startswith('LOT'):
        misc_lots = True
        index = 2
    elif tokens and tokens[0].upper() in {'LOT', 'LOTS', 'L'}:
        lot_prefix = tokens[0]
        lot_tokens, next_index = _collect_prefixed_tokens(tokens, 1, _is_lot_token)
        lot_value = _normalized_or_none(' '.join(lot_tokens))
        index = next_index

    if index < len(tokens) and tokens[index].upper() in {'BLK', 'BLOCK'}:
        block_tokens, next_index = _collect_block_tokens(tokens, index + 1)
        block_value = _normalized_or_none(' '.join(block_tokens))
        index = next_index

    subdivision_raw = _normalized_or_none(' '.join(tokens[index:]))
    subdivision_details = _extract_freeform_subdivision_details(subdivision_raw)
    cleaned_segments = []
    if lot_value:
        if lot_prefix and lot_prefix.upper() not in {'LOT', 'LOTS'}:
            prefix = 'LOTS' if re.search(r'(?i)\b(?:-|&|AND|ETC)\b', lot_value) else 'LOT'
        elif lot_prefix:
            prefix = lot_prefix
        else:
            prefix = 'LOTS' if re.search(r'(?i)\b(?:-|&|AND|ETC)\b', lot_value) else 'LOT'
        cleaned_segments.append(f'{prefix} {lot_value}')
    elif misc_lots:
        cleaned_segments.append('MISC LOTS')
    if block_value:
        cleaned_segments.append(f'BLK {block_value}')
    if subdivision_raw:
        cleaned_segments.append(subdivision_raw)
    cleaned_line = ' '.join(cleaned_segments) or cleaned_text

    return {
        'kind': 'freeform_segment',
        'source_raw': normalized,
        'raw': cleaned_line,
        'parcel_references': parcel_references,
        'misc_lots': misc_lots,
        'lot': lot_value,
        'block': block_value,
        'subdivision_raw': subdivision_details['subdivision_raw'],
        'subdivision': subdivision_details['subdivision'],
        'unit': subdivision_details['unit'],
        'building': subdivision_details['building'],
        'storage_locker': subdivision_details['storage_locker'],
        'condo': subdivision_details['condo'],
    }


def _parse_freeform_row(legal_value, strip_legal_prefix: bool = False) -> dict:
    legal_lines = []
    freeform_segments = []
    raw_legal_lines = []
    parcel_references = []
    unparsed_lines = []
    misc_lot_lines = []

    if pd.notna(legal_value):
        for line_index, line in enumerate(str(legal_value).replace('\r', '').split('\n')):
            text = str(line).strip()
            if not text:
                continue

            raw_legal_lines.append(text)
            parsed_line = parse_freeform_legal_line(text, strip_legal_prefix=strip_legal_prefix)
            if parsed_line is None:
                continue

            parsed_line['line_index'] = line_index
            legal_lines.append(parsed_line)
            if parsed_line['kind'] == 'freeform_segment':
                freeform_segments.append(parsed_line)
                parcel_references.extend(parsed_line.get('parcel_references', []))
                if parsed_line.get('misc_lots'):
                    misc_lot_lines.append(parsed_line['raw'])
            elif parsed_line['kind'] == 'parcel_reference':
                parcel_references.extend(parsed_line.get('parcel_references', []))
            else:
                unparsed_lines.append(parsed_line.get('raw'))

    lot_values = _unique_preserve_order([line['lot'] for line in freeform_segments if line.get('lot')])
    block_values = _unique_preserve_order([line['block'] for line in freeform_segments if line.get('block')])
    unit_values = _unique_preserve_order([line['unit'] for line in freeform_segments if line.get('unit')])
    building_values = _unique_preserve_order([line['building'] for line in freeform_segments if line.get('building')])
    storage_locker_values = _unique_preserve_order([
        line['storage_locker'] for line in freeform_segments if line.get('storage_locker')
    ])
    condo_flags = _unique_preserve_order([
        'condo'
        for line in freeform_segments
        if line.get('condo')
    ])
    subdivision_values = _unique_preserve_order([
        line['subdivision'] for line in freeform_segments if line.get('subdivision')
    ])
    lot_identifiers = _unique_preserve_order([
        identifier
        for value in lot_values
        for identifier in _expand_identifier_value(value)
    ])
    unit_identifiers = _unique_preserve_order([
        identifier
        for value in unit_values
        for identifier in _expand_identifier_value(value)
    ])
    lot_count = sum(_count_lot_value(value) for value in lot_values) if lot_values else None

    return {
        'legal': '; '.join(line['raw'] for line in legal_lines) or '',
        'raw_legal_lines': raw_legal_lines,
        'legal_lines': legal_lines,
        'freeform_segments': freeform_segments,
        'parcel_references': _unique_preserve_order(parcel_references),
        'misc_lot_lines': misc_lot_lines,
        'unparsed_lines': unparsed_lines,
        'lot_values': lot_values,
        'block_values': block_values,
        'unit_values': unit_values,
        'building_values': building_values,
        'storage_locker_values': storage_locker_values,
        'condo_flags': condo_flags,
        'subdivision_values': subdivision_values,
        'lot_identifiers': lot_identifiers,
        'unit_identifiers': unit_identifiers,
        'lot_count': lot_count,
        'segment_count': len(freeform_segments),
    }


def _split_santarosa_clauses(text: str) -> list[str]:
    normalized = _normalize_freeform_line(text)
    if not normalized:
        return []

    normalized = re.sub(r'(?<=\d)\\(?=[A-Z0-9-]+\b)', '/', normalized)
    normalized = re.sub(
        r'(?P<entry>/[A-Z0-9-]+)\s+(?=(?:PT\s+)?\d)',
        r'\g<entry>; ',
        normalized,
        flags=re.IGNORECASE,
    )
    normalized = re.sub(r'\s*;\s*', '; ', normalized)
    return [clause.strip(' ,') for clause in normalized.split(';') if clause.strip(' ,')]


def _extract_santarosa_location_values(parcel_references: list[str]) -> tuple[list[str], list[str], list[str]]:
    section_values = []
    township_values = []
    range_values = []

    for parcel_reference in parcel_references:
        match = _SANTAROSA_LOCATION_RE.fullmatch(parcel_reference.strip())
        if not match:
            continue
        _append_unique(section_values, _normalized_or_none(match.group('section') or ''))
        _append_unique(township_values, _normalized_or_none(match.group('township') or ''))
        _append_unique(range_values, _normalized_or_none(match.group('range') or ''))

    return (section_values, township_values, range_values)


def _extract_santarosa_subdivision_details(text: str | None) -> dict:
    raw_text = _normalized_or_none(text or '')
    if not raw_text:
        return {
            'subdivision_source_raw': None,
            'subdivision_raw': None,
            'subdivision': None,
            'unit': None,
            'building': None,
            'storage_locker': None,
            'condo': False,
            'subdivision_flags': [],
            'no_phase_value': None,
        }

    normalized = raw_text
    flags = []
    no_phase_value = None

    phase_word_map = {
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

    normalized = re.sub(
        r'(?i)\b(PH(?:ASE)?|PHS?)\s+([IVX]+|\d+)\s+([A-Z])\b',
        r'\1 \2\3',
        normalized,
    )
    normalized = re.sub(
        r'(?i)\b(?P<keyword>PH(?:ASE)?|PHS?)\s+(?P<phase_word>ONE|TWO|THREE|FOUR|FIVE|SIX|SEVEN|EIGHT|NINE|TEN|ELEVEN|TWELVE)\s+(?P<suffix>[A-Z])\b',
        lambda match: (
            f"{match.group('keyword')} {phase_word_map[match.group('phase_word').upper()]}{match.group('suffix').upper()}"
        ),
        normalized,
    )

    no_phase_match = re.search(r'(?i)\bNO\s+PH(?:ASE)?\b(?:\s+(?P<value>[A-Z0-9-]+))?', normalized)
    if no_phase_match:
        _append_unique(flags, 'no_phase')
        no_phase_value = _normalized_or_none(no_phase_match.group('value') or '')
        normalized = re.sub(
            r'(?i)\bNO\s+PH(?:ASE)?\b(?:\s+[A-Z0-9-]+)?',
            '',
            normalized,
        )

    if re.search(r'(?i)\bREPLAT\b', normalized):
        _append_unique(flags, 'replat')
        normalized = re.sub(r'(?i)\bREPLAT\b', '', normalized)

    if re.search(r'(?i)\bALL\s+COMMON\s+AREAS\b', normalized):
        _append_unique(flags, 'common_areas')
        normalized = re.sub(r'(?i)\bALL\s+COMMON\s+AREAS\b', '', normalized)
    elif re.search(r'(?i)\bCOMMON\s+AREAS?\b', normalized):
        _append_unique(flags, 'common_areas')
        normalized = re.sub(r'(?i)\bCOMMON\s+AREAS?\b', '', normalized)

    if re.search(r'(?i)\bEASEMENTS?\b', normalized):
        _append_unique(flags, 'easements')
        normalized = re.sub(r'(?i)\bEASEMENTS?\b', '', normalized)

    if re.search(r'(?i)\bLIFT\s+STATION\b', normalized):
        _append_unique(flags, 'lift_station')
        normalized = re.sub(r'(?i)\bLIFT\s+STATION\b', '', normalized)

    normalized = _normalized_or_none(normalized or '')
    extracted = _extract_freeform_subdivision_details(normalized)
    extracted['subdivision_source_raw'] = raw_text
    extracted['subdivision_flags'] = flags
    extracted['no_phase_value'] = no_phase_value
    return extracted


def _build_santarosa_segment(
    *,
    source_raw: str,
    subdivision_text: str | None,
    parcel_references: list[str],
    line_index: int,
    segment_index: int,
    lot_value: str | None = None,
    block_value: str | None = None,
    tract_value: str | None = None,
    partial_lot_values: list[str] | None = None,
    parcel_designators: list[str] | None = None,
    extra_flags: list[str] | None = None,
) -> dict:
    subdivision_details = _extract_santarosa_subdivision_details(subdivision_text)
    subdivision_flags = list(subdivision_details.get('subdivision_flags', []))
    for flag in extra_flags or []:
        _append_unique(subdivision_flags, flag)

    section_values, township_values, range_values = _extract_santarosa_location_values(parcel_references)

    cleaned_parts = []
    if lot_value:
        lot_prefix = 'LOTS' if _count_lot_value(lot_value) > 1 else 'LOT'
        if partial_lot_values:
            lot_prefix = f'PT {lot_prefix}'
        cleaned_parts.append(f'{lot_prefix} {lot_value}')
    if block_value:
        cleaned_parts.append(f'BLK {block_value}')
    if tract_value:
        tract_prefix = 'PT TRACT' if partial_lot_values else 'TRACT'
        cleaned_parts.append(f'{tract_prefix} {tract_value}')
    if subdivision_details.get('subdivision_source_raw'):
        cleaned_parts.append(subdivision_details['subdivision_source_raw'])
    if parcel_designators:
        cleaned_parts.append(f"PARCEL {', '.join(parcel_designators)}")

    return {
        'kind': 'freeform_segment',
        'source_raw': source_raw,
        'raw': ' '.join(cleaned_parts).strip() or source_raw,
        'parcel_references': list(parcel_references),
        'misc_lots': False,
        'lot': lot_value,
        'partial_lot_values': list(partial_lot_values or []),
        'block': block_value,
        'subdivision_source_raw': subdivision_details.get('subdivision_source_raw'),
        'subdivision_raw': subdivision_details.get('subdivision_raw'),
        'subdivision': subdivision_details.get('subdivision'),
        'unit': subdivision_details.get('unit'),
        'building': subdivision_details.get('building'),
        'storage_locker': subdivision_details.get('storage_locker'),
        'condo': subdivision_details.get('condo'),
        'section': section_values[0] if section_values else None,
        'township': township_values[0] if township_values else None,
        'range': range_values[0] if range_values else None,
        'tract': tract_value,
        'parcel_designators': list(parcel_designators or []),
        'subdivision_flags': subdivision_flags,
        'no_phase_value': subdivision_details.get('no_phase_value'),
        'line_index': line_index,
        'segment_index': segment_index,
    }


def _parse_santarosa_slash_clause(
    clause: str,
    current_subdivision: str | None,
    parcel_references: list[str],
    line_index: int,
    starting_segment_index: int,
) -> tuple[list[dict], str | None]:
    first_match = next(_SANTAROSA_SLASH_ENTRY_RE.finditer(clause), None)
    if not first_match:
        return ([], current_subdivision)

    header = clause[:first_match.start()].strip(' ,')
    if header:
        current_subdivision = header
    elif not current_subdivision:
        return ([], current_subdivision)

    segments = []
    for offset, match in enumerate(_SANTAROSA_SLASH_ENTRY_RE.finditer(clause[first_match.start():])):
        lot_value = _normalized_or_none(match.group('lots') or '')
        block_value = _normalized_or_none(match.group('block') or '')
        partial_lot_values = [lot_value] if match.group('partial') and lot_value else []
        segments.append(
            _build_santarosa_segment(
                source_raw=clause,
                subdivision_text=current_subdivision,
                parcel_references=parcel_references,
                line_index=line_index,
                segment_index=starting_segment_index + offset,
                lot_value=lot_value,
                block_value=block_value,
                partial_lot_values=partial_lot_values,
            )
        )

    return (segments, current_subdivision)


def _parse_santarosa_explicit_lot_clause(
    clause: str,
    current_subdivision: str | None,
    parcel_references: list[str],
    line_index: int,
    segment_index: int,
) -> tuple[dict | None, str | None]:
    match = _SANTAROSA_EXPLICIT_LOT_RE.match(clause)
    if not match:
        return (None, current_subdivision)

    header = _normalized_or_none(match.group('header') or '')
    if header:
        current_subdivision = header
    elif not current_subdivision:
        return (None, current_subdivision)

    lot_value = _normalized_or_none(match.group('lots') or '')
    partial_lot_values = [lot_value] if match.group('partial') and lot_value else []
    segment = _build_santarosa_segment(
        source_raw=clause,
        subdivision_text=current_subdivision,
        parcel_references=parcel_references,
        line_index=line_index,
        segment_index=segment_index,
        lot_value=lot_value,
        partial_lot_values=partial_lot_values,
    )
    return (segment, current_subdivision)


def _parse_santarosa_tract_clause(
    clause: str,
    current_subdivision: str | None,
    parcel_references: list[str],
    line_index: int,
    segment_index: int,
) -> tuple[dict | None, str | None]:
    match = _SANTAROSA_TRACT_RE.match(clause)
    if not match:
        return (None, current_subdivision)

    header = _normalized_or_none(match.group('header') or '')
    if header:
        current_subdivision = header
    elif not current_subdivision:
        return (None, current_subdivision)

    tract_value = _normalized_or_none(match.group('tract') or '')
    partial_lot_values = [tract_value] if match.group('partial') and tract_value else []
    segment = _build_santarosa_segment(
        source_raw=clause,
        subdivision_text=current_subdivision,
        parcel_references=parcel_references,
        line_index=line_index,
        segment_index=segment_index,
        tract_value=tract_value,
        partial_lot_values=partial_lot_values,
    )
    return (segment, current_subdivision)


def _parse_santarosa_descriptor_clause(
    clause: str,
    current_subdivision: str | None,
    parcel_references: list[str],
    line_index: int,
    segment_index: int,
) -> tuple[dict | None, str | None]:
    parcel_match = _SANTAROSA_PARCEL_RE.match(clause)
    if parcel_match:
        header = _normalized_or_none(parcel_match.group('header') or '')
        if header:
            current_subdivision = header
        elif not current_subdivision:
            return (None, current_subdivision)

        parcel_designators = _unique_preserve_order([
            value.strip()
            for value in re.split(r'\s*,\s*', parcel_match.group('parcel') or '')
            if value.strip()
        ])
        extra_flags = []
        if 'ALL COMMON AREAS' in clause.upper():
            _append_unique(extra_flags, 'common_areas')
        if parcel_match.group('suffix'):
            suffix = parcel_match.group('suffix').upper()
            if 'LIFT STATION' in suffix:
                _append_unique(extra_flags, 'lift_station')
            if 'ET AL' in suffix:
                _append_unique(extra_flags, 'et_al')

        segment = _build_santarosa_segment(
            source_raw=clause,
            subdivision_text=current_subdivision,
            parcel_references=parcel_references,
            line_index=line_index,
            segment_index=segment_index,
            parcel_designators=parcel_designators,
            extra_flags=extra_flags,
        )
        return (segment, current_subdivision)

    common_area_match = _SANTAROSA_COMMON_AREA_RE.match(clause)
    if common_area_match:
        header = _normalized_or_none(common_area_match.group('header') or '')
        if header:
            current_subdivision = header
        elif not current_subdivision:
            return (None, current_subdivision)

        extra_flags = ['common_areas']
        if common_area_match.group('suffix'):
            _append_unique(extra_flags, 'easements')

        segment = _build_santarosa_segment(
            source_raw=clause,
            subdivision_text=current_subdivision,
            parcel_references=parcel_references,
            line_index=line_index,
            segment_index=segment_index,
            extra_flags=extra_flags,
        )
        return (segment, current_subdivision)

    return (None, current_subdivision)


def _parse_santarosa_bare_subdivision_clause(
    clause: str,
    current_subdivision: str | None,
    parcel_references: list[str],
    line_index: int,
    segment_index: int,
) -> tuple[dict | None, str | None]:
    if re.fullmatch(r'(?i)REDACT(?:ED)?', clause):
        return ({
            'kind': 'ignored',
            'source_raw': clause,
            'raw': clause,
            'parcel_references': list(parcel_references),
            'line_index': line_index,
            'segment_index': segment_index,
        }, current_subdivision)

    if not re.search(r'[A-Z]', clause, re.IGNORECASE):
        return (None, current_subdivision)

    if clause[:1].isdigit():
        return (None, current_subdivision)

    current_subdivision = clause
    segment = _build_santarosa_segment(
        source_raw=clause,
        subdivision_text=current_subdivision,
        parcel_references=parcel_references,
        line_index=line_index,
        segment_index=segment_index,
    )
    return (segment, current_subdivision)


def parse_santarosa_row(row: pd.Series, cols: dict) -> dict:
    legal_lines = []
    freeform_segments = []
    raw_legal_lines = []
    parcel_references = []
    unparsed_lines = []

    legal_value = row.get(cols.get('legal', ''), pd.NA)
    if pd.notna(legal_value):
        for line_index, line in enumerate(str(legal_value).replace('\r', '').split('\n')):
            text = str(line).strip()
            if not text or text.lower() == 'nan':
                continue

            raw_legal_lines.append(text)
            current_subdivision = None
            line_parcel_references = []
            for clause in _split_santarosa_clauses(text):
                clause_text = re.sub(r'(?i)\bUNREC\b', '', clause)
                clause_text = re.sub(r'\s+', ' ', clause_text).strip(' ,')
                clause_parcels = []
                clause_text, clause_parcels = _consume_leading_parcel_references(clause_text)
                for parcel_reference in clause_parcels:
                    _append_unique(line_parcel_references, parcel_reference)
                    _append_unique(parcel_references, parcel_reference)

                if not clause_text:
                    legal_lines.append({
                        'kind': 'parcel_reference',
                        'source_raw': clause,
                        'raw': clause,
                        'parcel_references': list(clause_parcels),
                        'line_index': line_index,
                    })
                    continue

                segment_start = len(freeform_segments)
                slash_segments, current_subdivision = _parse_santarosa_slash_clause(
                    clause_text,
                    current_subdivision,
                    line_parcel_references,
                    line_index,
                    segment_start,
                )
                if slash_segments:
                    for segment in slash_segments:
                        if 'UNREC' in clause.upper():
                            _append_unique(segment['subdivision_flags'], 'unrecorded')
                        legal_lines.append(segment)
                        freeform_segments.append(segment)
                    continue

                explicit_segment, current_subdivision = _parse_santarosa_explicit_lot_clause(
                    clause_text,
                    current_subdivision,
                    line_parcel_references,
                    line_index,
                    segment_start,
                )
                if explicit_segment is not None:
                    if 'UNREC' in clause.upper():
                        _append_unique(explicit_segment['subdivision_flags'], 'unrecorded')
                    legal_lines.append(explicit_segment)
                    freeform_segments.append(explicit_segment)
                    continue

                tract_segment, current_subdivision = _parse_santarosa_tract_clause(
                    clause_text,
                    current_subdivision,
                    line_parcel_references,
                    line_index,
                    segment_start,
                )
                if tract_segment is not None:
                    if 'UNREC' in clause.upper():
                        _append_unique(tract_segment['subdivision_flags'], 'unrecorded')
                    legal_lines.append(tract_segment)
                    freeform_segments.append(tract_segment)
                    continue

                descriptor_segment, current_subdivision = _parse_santarosa_descriptor_clause(
                    clause_text,
                    current_subdivision,
                    line_parcel_references,
                    line_index,
                    segment_start,
                )
                if descriptor_segment is not None:
                    if 'UNREC' in clause.upper():
                        if descriptor_segment['kind'] == 'freeform_segment':
                            _append_unique(descriptor_segment['subdivision_flags'], 'unrecorded')
                    legal_lines.append(descriptor_segment)
                    if descriptor_segment['kind'] == 'freeform_segment':
                        freeform_segments.append(descriptor_segment)
                    continue

                bare_segment, current_subdivision = _parse_santarosa_bare_subdivision_clause(
                    clause_text,
                    current_subdivision,
                    line_parcel_references,
                    line_index,
                    segment_start,
                )
                if bare_segment is not None:
                    if bare_segment['kind'] == 'freeform_segment' and 'UNREC' in clause.upper():
                        _append_unique(bare_segment['subdivision_flags'], 'unrecorded')
                    legal_lines.append(bare_segment)
                    if bare_segment['kind'] == 'freeform_segment':
                        freeform_segments.append(bare_segment)
                    continue

                unparsed_lines.append(clause_text)

    lot_values = _unique_preserve_order([line['lot'] for line in freeform_segments if line.get('lot')])
    partial_lot_values = _unique_preserve_order([
        partial_lot_value
        for line in freeform_segments
        for partial_lot_value in line.get('partial_lot_values', [])
    ])
    block_values = _unique_preserve_order([line['block'] for line in freeform_segments if line.get('block')])
    unit_values = _unique_preserve_order([line['unit'] for line in freeform_segments if line.get('unit')])
    subdivision_values = _unique_preserve_order([
        line['subdivision'] for line in freeform_segments if line.get('subdivision')
    ])
    section_values = _unique_preserve_order([
        line['section'] for line in freeform_segments if line.get('section')
    ])
    township_values = _unique_preserve_order([
        line['township'] for line in freeform_segments if line.get('township')
    ])
    range_values = _unique_preserve_order([
        line['range'] for line in freeform_segments if line.get('range')
    ])
    all_section_values, all_township_values, all_range_values = _extract_santarosa_location_values(parcel_references)
    for section_value in all_section_values:
        _append_unique(section_values, section_value)
    for township_value in all_township_values:
        _append_unique(township_values, township_value)
    for range_value in all_range_values:
        _append_unique(range_values, range_value)
    tract_values = _unique_preserve_order([
        line['tract'] for line in freeform_segments if line.get('tract')
    ])
    parcel_designators = _unique_preserve_order([
        parcel_designator
        for line in freeform_segments
        for parcel_designator in line.get('parcel_designators', [])
    ])
    no_phase_values = _unique_preserve_order([
        line['no_phase_value'] for line in freeform_segments if line.get('no_phase_value')
    ])
    subdivision_flags = _unique_preserve_order([
        subdivision_flag
        for line in freeform_segments
        for subdivision_flag in line.get('subdivision_flags', [])
    ])
    lot_identifiers = _unique_preserve_order([
        identifier
        for value in lot_values
        for identifier in _expand_identifier_value(value)
    ])
    partial_lot_identifiers = _unique_preserve_order([
        identifier
        for value in partial_lot_values
        for identifier in _expand_identifier_value(value)
    ])
    lot_count = sum(_count_lot_value(value) for value in lot_values) if lot_values else None

    return {
        'legal': '; '.join(line['raw'] for line in legal_lines if line['kind'] == 'freeform_segment') or '',
        'raw_legal_lines': raw_legal_lines,
        'legal_lines': legal_lines,
        'freeform_segments': freeform_segments,
        'parcel_references': parcel_references,
        'unparsed_lines': _unique_preserve_order(unparsed_lines),
        'lot_values': lot_values,
        'partial_lot_values': partial_lot_values,
        'block_values': block_values,
        'unit_values': unit_values,
        'subdivision_values': subdivision_values,
        'section_values': section_values,
        'township_values': township_values,
        'range_values': range_values,
        'tract_values': tract_values,
        'parcel_designators': parcel_designators,
        'no_phase_values': no_phase_values,
        'subdivision_flags': subdivision_flags,
        'lot_identifiers': lot_identifiers,
        'partial_lot_identifiers': partial_lot_identifiers,
        'lot_count': lot_count,
        'segment_count': len(freeform_segments),
    }


def parse_bay_row(row: pd.Series, cols: dict) -> dict:
    legal_value = row.get(cols.get('legal', ''), pd.NA)
    return _parse_freeform_row(legal_value)


def parse_walton_row(row: pd.Series, cols: dict) -> dict:
    legal_value = row.get(cols.get('legal', ''), pd.NA)
    return _parse_freeform_row(legal_value, strip_legal_prefix=True)


def _extract_str_info(subdivision: str | None) -> tuple[str | None, str | None, str | None, str | None]:
    if not subdivision:
        return (None, None, None, None)

    normalized = _normalized_or_none(subdivision)
    if not normalized:
        return (None, None, None, None)

    match = _HERNANDO_STR_INFO_RE.match(normalized)
    if not match:
        return (normalized, None, None, None)

    cleaned_subdivision = _normalized_or_none(match.group('subdivision') or '')
    section = _normalized_or_none(match.group('section') or '')
    township = _normalized_or_none(match.group('township') or '')
    range_value = _normalized_or_none(match.group('range') or '')
    return (cleaned_subdivision, section, township, range_value)


def _count_lot_value(value: str) -> int:
    text = re.sub(r'(?i)\bLOTS?\b', '', value).strip()
    if not text:
        return 0

    range_match = _LOT_RANGE_RE.fullmatch(text)
    if range_match:
        start = int(range_match.group('start'))
        end = int(range_match.group('end'))
        if end >= start:
            return end - start + 1

    parts = [part.strip() for part in re.split(r'\s*(?:,|&|\band\b)\s*', text, flags=re.IGNORECASE) if part.strip()]
    if len(parts) > 1:
        return sum(_count_lot_value(part) for part in parts)

    if re.fullmatch(r'(?:[A-Z]-?\d+[A-Z]?)(?:\s+(?:[A-Z]-?\d+[A-Z]?))+', text):
        return len(text.split())

    return len(_LOT_TOKEN_RE.findall(text)) or 1


def _expand_identifier_value(value: str | None) -> list[str]:
    if not value:
        return []

    text = re.sub(r'(?i)\b(?:LOTS?|UNITS?)\b', '', value).strip()
    if not text:
        return []

    range_match = _LOT_RANGE_RE.fullmatch(text)
    if range_match:
        start = int(range_match.group('start'))
        end = int(range_match.group('end'))
        if end >= start:
            return [str(number) for number in range(start, end + 1)]

    parts = [part.strip() for part in re.split(r'\s*(?:,|&|\band\b)\s*', text, flags=re.IGNORECASE) if part.strip()]
    if len(parts) > 1:
        values = []
        for part in parts:
            expanded = _expand_identifier_value(part)
            values.extend(expanded or [part])
        return _unique_preserve_order(values)

    if re.fullmatch(r'(?:[A-Z]+-?\d+[A-Z]?)(?:\s+(?:[A-Z]+-?\d+[A-Z]?))+', text):
        return text.split()

    tokens = _LOT_TOKEN_RE.findall(text)
    if tokens:
        return _unique_preserve_order(tokens)

    return []


def _build_helper_capture(row: pd.Series, cols: dict) -> dict:
    helper_fields = {}
    for field_key, column_key, default_column in _HELPER_FIELDS:
        column_name = cols.get(column_key, default_column)
        raw_value = row.get(column_name, pd.NA)
        helper_fields[field_key] = {
            'column': column_name,
            'raw': _clean_raw_helper_value(raw_value),
            'values': _split_helper_values(raw_value),
        }
    return helper_fields


def _helper_value_for_segment(helper_values: list[str], segment_index: int, segment_count: int) -> tuple[str | None, str | None]:
    if not helper_values:
        return (None, None)

    if segment_count and len(helper_values) == segment_count:
        return (helper_values[segment_index], 'helper_aligned')

    if len(helper_values) == 1:
        return (helper_values[0], 'helper_shared')

    return (None, None)


def _build_effective_segment(segment: dict, segment_index: int, segment_count: int, helper_fields: dict) -> dict:
    effective = dict(segment)
    sources = {}

    for field_name in ('lot', 'block', 'unit', 'subdivision', 'section', 'township', 'range'):
        effective_value = segment.get(field_name)
        source = 'legal' if effective_value else None

        if not effective_value:
            helper_value, helper_source = _helper_value_for_segment(
                helper_fields.get(field_name, {}).get('values', []),
                segment_index,
                segment_count,
            )
            if helper_value:
                effective_value = helper_value
                source = helper_source

        effective[f'effective_{field_name}'] = effective_value
        if source:
            sources[field_name] = source

    effective['segment_index'] = segment_index
    effective['sources'] = sources
    effective['effective_lot_identifiers'] = _expand_identifier_value(effective.get('effective_lot'))
    effective['effective_unit_identifiers'] = _expand_identifier_value(effective.get('effective_unit'))
    effective['effective_lot_count'] = (
        _count_lot_value(effective['effective_lot']) if effective.get('effective_lot') else None
    )
    return effective


def parse_hernando_segment_line(line: str) -> dict | None:
    text = str(line).strip()
    if not text or _HERNANDO_HEADER_RE.fullmatch(text):
        return None

    without_tail = _HERNANDO_STR_TAIL_RE.sub('', text).strip()
    if not without_tail:
        return None

    if _HERNANDO_PARCEL_RE.fullmatch(without_tail):
        return {
            'kind': 'parcel_reference',
            'raw': without_tail,
            'parcel_reference': without_tail,
        }

    match = _HERNANDO_SEGMENT_RE.match(without_tail)
    if not match:
        return {
            'kind': 'unparsed',
            'raw': without_tail,
        }

    subdivision_raw = _normalized_or_none(match.group('subdivision'))
    subdivision, section, township, range_value = _extract_str_info(subdivision_raw)
    return {
        'kind': 'legal_segment',
        'raw': without_tail,
        'lot': _normalized_or_none(match.group('lot')),
        'block': _normalized_or_none(match.group('block')),
        'unit': _normalized_or_none(match.group('unit')),
        'subdivision_raw': subdivision_raw,
        'subdivision': subdivision,
        'section': section,
        'township': township,
        'range': range_value,
    }


def clean_hernando_legal(legal_value) -> str:
    if pd.isna(legal_value) or legal_value is None:
        return ''

    cleaned_lines = []
    for line in str(legal_value).replace('\r', '').split('\n'):
        parsed = parse_hernando_segment_line(line)
        if parsed is None:
            continue
        cleaned_lines.append(parsed['raw'])

    return '; '.join(cleaned_lines)


def parse_hernando_row(row: pd.Series, cols: dict) -> dict:
    legal_segments = []
    parcel_references = []
    unparsed_lines = []
    legal_lines = []
    raw_legal_lines = []
    helper_fields = _build_helper_capture(row, cols)

    legal_value = row.get(cols.get('legal', ''), pd.NA)
    if pd.notna(legal_value):
        for line_index, line in enumerate(str(legal_value).replace('\r', '').split('\n')):
            text = str(line).strip()
            if not text:
                continue

            raw_legal_lines.append(text)
            if _HERNANDO_HEADER_RE.fullmatch(text):
                legal_lines.append({
                    'kind': 'header',
                    'raw': text,
                    'line_index': line_index,
                })
                continue

            parsed = parse_hernando_segment_line(line)
            if parsed is None:
                continue
            parsed_with_index = dict(parsed)
            parsed_with_index['line_index'] = line_index
            legal_lines.append(parsed_with_index)
            if parsed['kind'] == 'legal_segment':
                legal_segments.append(parsed_with_index)
            elif parsed['kind'] == 'parcel_reference':
                parcel_references.append(parsed['parcel_reference'])
            else:
                unparsed_lines.append(parsed['raw'])

    helper_lot_values = helper_fields['lot']['values']
    helper_block_values = helper_fields['block']['values']
    helper_unit_values = helper_fields['unit']['values']
    helper_subdivision_values = helper_fields['subdivision']['values']
    helper_section_values = helper_fields['section']['values']
    helper_township_values = helper_fields['township']['values']
    helper_range_values = helper_fields['range']['values']

    parsed_lot_values = [segment['lot'] for segment in legal_segments if segment.get('lot')]
    parsed_block_values = [segment['block'] for segment in legal_segments if segment.get('block')]
    parsed_unit_values = [segment['unit'] for segment in legal_segments if segment.get('unit')]
    parsed_subdivision_values = [segment['subdivision'] for segment in legal_segments if segment.get('subdivision')]
    parsed_section_values = [segment['section'] for segment in legal_segments if segment.get('section')]
    parsed_township_values = [segment['township'] for segment in legal_segments if segment.get('township')]
    parsed_range_values = [segment['range'] for segment in legal_segments if segment.get('range')]

    lot_values = _unique_preserve_order(helper_lot_values + parsed_lot_values)
    block_values = _unique_preserve_order(helper_block_values + parsed_block_values)
    unit_values = _unique_preserve_order(helper_unit_values + parsed_unit_values)
    subdivision_values = _unique_preserve_order(helper_subdivision_values + parsed_subdivision_values)
    section_values = _unique_preserve_order(helper_section_values + parsed_section_values)
    township_values = _unique_preserve_order(helper_township_values + parsed_township_values)
    range_values = _unique_preserve_order(helper_range_values + parsed_range_values)

    effective_legal_segments = [
        _build_effective_segment(segment, index, len(legal_segments), helper_fields)
        for index, segment in enumerate(legal_segments)
    ]
    lot_identifiers = _unique_preserve_order([
        identifier
        for segment in effective_legal_segments
        for identifier in segment.get('effective_lot_identifiers', [])
    ])
    unit_identifiers = _unique_preserve_order([
        identifier
        for segment in effective_legal_segments
        for identifier in segment.get('effective_unit_identifiers', [])
    ])

    lot_count = None
    lot_count_source = []
    lot_count_source_name = None
    if helper_lot_values and len(helper_lot_values) >= len(parsed_lot_values):
        lot_count_source = helper_lot_values
        lot_count_source_name = 'helper'
    elif parsed_lot_values:
        lot_count_source = parsed_lot_values
        lot_count_source_name = 'legal'
    elif helper_lot_values:
        lot_count_source = helper_lot_values
        lot_count_source_name = 'helper'
    if lot_count_source:
        lot_count = sum(_count_lot_value(value) for value in lot_count_source)

    return {
        'legal': clean_hernando_legal(legal_value),
        'raw_legal_lines': raw_legal_lines,
        'legal_lines': legal_lines,
        'header_present': any(line['kind'] == 'header' for line in legal_lines),
        'helper_fields': helper_fields,
        'legal_segments': legal_segments,
        'effective_legal_segments': effective_legal_segments,
        'parcel_references': parcel_references,
        'unparsed_lines': unparsed_lines,
        'lot_values': lot_values,
        'block_values': block_values,
        'unit_values': unit_values,
        'subdivision_values': subdivision_values,
        'section_values': section_values,
        'township_values': township_values,
        'range_values': range_values,
        'lot_identifiers': lot_identifiers,
        'unit_identifiers': unit_identifiers,
        'lot_count': lot_count,
        'lot_count_source': lot_count_source_name,
        'segment_count': len(legal_segments),
    }
