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
_FREEFORM_PARCEL_RE = re.compile(r'^\(?[A-Z]?\d[\d-]{5,}[A-Z0-9-]*\)?$', re.IGNORECASE)
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
        token_match = re.match(r'^(?P<token>\(?[A-Z]?\d[\d-]{5,}[A-Z0-9-]*\)?)\s*(?:\|\s*|[,;:.-]\s*|\s+)?', remaining)
        if not token_match:
            break

        token = token_match.group('token').strip('()')
        if not _FREEFORM_PARCEL_RE.fullmatch(token):
            break

        parcel_references.append(token)
        remaining = remaining[token_match.end():].strip()

    return remaining, parcel_references


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
