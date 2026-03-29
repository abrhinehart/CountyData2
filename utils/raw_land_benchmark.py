from __future__ import annotations

import re
from difflib import SequenceMatcher


_START_MARKERS = (
    ('to_wit', re.compile(r'\bto[\s-]*wit\s*[:;]?', re.IGNORECASE)),
    ('described_as', re.compile(r'\bdescribed\s+as\s+follows\s*[:;]?', re.IGNORECASE)),
    ('legal_description', re.compile(r'\blegal\s+description\s*[:;]?', re.IGNORECASE)),
    ('all_that_certain_land', re.compile(r'\ball\s+that\s+certain\s+land\b', re.IGNORECASE)),
    ('parcel_one', re.compile(r'\bparcel\s+1\s*:', re.IGNORECASE)),
    ('commence_at', re.compile(r'\bcomm(?:ence)?\s+at\b', re.IGNORECASE)),
)

_END_MARKERS = (
    ('subject_to', re.compile(r'\bsubject\s+to\b', re.IGNORECASE)),
    ('together_with', re.compile(r'\btogether\s+with\b', re.IGNORECASE)),
    ('to_have_and_to_hold', re.compile(r'\bto\s+have\s+and\s+to\s+hold\b', re.IGNORECASE)),
    ('homestead', re.compile(r'\bthe\s+land\s+is\s+not\s+the\s+homestead\b', re.IGNORECASE)),
    ('in_witness_whereof', re.compile(r'\bin\s+witness\s+whereof\b', re.IGNORECASE)),
    ('notary', re.compile(r'\bstate\s+of\s+florida\b', re.IGNORECASE)),
)

_PAGE_HEADER_PATTERNS = (
    re.compile(r'^\s*File\s*#.*?Pages?\s*:\s*\d+\s+of\s+\d+\s*', re.IGNORECASE | re.DOTALL),
    re.compile(r'^\s*File\s*#.*?Page\s+\d+\s+of\s+\d+\s*', re.IGNORECASE | re.DOTALL),
)
_PAGE_FOOTER_PATTERNS = (
    re.compile(r'\bPage\s+\d+\s+of\s+\d+\b', re.IGNORECASE),
)
_EXHIBIT_REFERENCE_PATTERN = re.compile(r'\bsee\s+exhibit\b', re.IGNORECASE)
_EXHIBIT_PAGE_PATTERN = re.compile(r'\bexhibit\b', re.IGNORECASE)
_PARCEL_LABEL_PATTERN = re.compile(r'\bPARCEL\s+(\d+)\s*:', re.IGNORECASE)
_BEARING_PATTERN = re.compile(
    r'\b[NS]\s*\d{1,3}(?:[°º]|\s+DEG)?\s*\d{0,2}(?:[\'’]\s*\d{0,2}(?:["”])?)?\s*[EW]\b',
    re.IGNORECASE,
)
_DISTANCE_PATTERN = re.compile(r'\b\d+(?:\.\d+)?\s*(?:\'|FT|FEET)\b', re.IGNORECASE)
_WRAPPER_PATTERNS = (
    re.compile(r'\bWARRANTY\s+DEED\b', re.IGNORECASE),
    re.compile(r'\bTHIS\s+INDENTURE\b', re.IGNORECASE),
    re.compile(r'\bIN\s+WITNESS\s+WHEREOF\b', re.IGNORECASE),
    re.compile(r'\bSTATE\s+OF\s+FLORIDA\b', re.IGNORECASE),
    re.compile(r'\bNOTARY\b', re.IGNORECASE),
    re.compile(r'\bPREPARED\s+BY\b', re.IGNORECASE),
    re.compile(r'\bRETURN\s+TO\b', re.IGNORECASE),
)
_QUOTE_TRANSLATION = str.maketrans({
    '\u2018': "'",
    '\u2019': "'",
    '\u201c': '"',
    '\u201d': '"',
    '\u00a0': ' ',
})


def clean_ocr_page_text(text: str | None) -> str:
    if not text:
        return ''

    cleaned = str(text).translate(_QUOTE_TRANSLATION).replace('\r', '\n')
    cleaned = re.sub(r'[ \t]+', ' ', cleaned)
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned).strip()

    for pattern in _PAGE_HEADER_PATTERNS:
        cleaned = pattern.sub('', cleaned, count=1)

    for pattern in _PAGE_FOOTER_PATTERNS:
        cleaned = pattern.sub('', cleaned)

    return cleaned.strip()


def normalize_legal_text(text: str | None) -> str:
    if not text:
        return ''

    normalized = clean_ocr_page_text(text)
    normalized = normalized.upper()
    normalized = normalized.replace('°', ' DEG ')
    normalized = normalized.replace('’', "'")
    normalized = re.sub(r'[^A-Z0-9/.\'"()\-]+', ' ', normalized)
    normalized = re.sub(r'\s+', ' ', normalized)
    return normalized.strip()


def _find_first_marker(text: str, markers: tuple[tuple[str, re.Pattern[str]], ...]) -> tuple[str | None, re.Match[str] | None]:
    best_label = None
    best_match = None

    for label, pattern in markers:
        match = pattern.search(text)
        if match is None:
            continue
        if best_match is None or match.start() < best_match.start():
            best_label = label
            best_match = match

    return best_label, best_match


def _find_marker_by_priority(text: str, markers: tuple[tuple[str, re.Pattern[str]], ...]) -> tuple[str | None, re.Match[str] | None]:
    for label, pattern in markers:
        match = pattern.search(text)
        if match is not None:
            return label, match
    return None, None


def _find_exhibit_legal_start(page_texts: list[str]) -> tuple[int | None, str | None, re.Match[str] | None]:
    if not any(_EXHIBIT_REFERENCE_PATTERN.search(text or '') for text in page_texts):
        return None, None, None

    exhibit_markers = (
        ('legal_description', re.compile(r'\blegal\s+description\s*[:;]?', re.IGNORECASE)),
        ('parcel_one', re.compile(r'\bparcel\s+1\s*:', re.IGNORECASE)),
        ('commence_at', re.compile(r'\bcomm(?:ence)?\s+at\b', re.IGNORECASE)),
    )
    for page_index, page_text in enumerate(page_texts, start=1):
        if not _EXHIBIT_PAGE_PATTERN.search(page_text or ''):
            continue
        label, match = _find_marker_by_priority(page_text, exhibit_markers)
        if match is not None:
            return page_index, label, match

    return None, None, None


def extract_legal_candidate(page_texts: list[str]) -> dict:
    cleaned_pages = [clean_ocr_page_text(text) for text in page_texts]
    exhibit_start_page, exhibit_start_marker, exhibit_start_match = _find_exhibit_legal_start(cleaned_pages)

    started = False
    collected: list[str] = []
    start_page = None
    end_page = None
    start_marker = None
    end_marker = None
    last_page_seen = None

    for page_index, page_text in enumerate(cleaned_pages, start=1):
        last_page_seen = page_index
        if not page_text:
            continue

        if not started:
            if exhibit_start_page is not None and page_index == exhibit_start_page:
                start_marker = exhibit_start_marker
                start_match = exhibit_start_match
            elif exhibit_start_page is not None and page_index < exhibit_start_page:
                continue
            else:
                start_marker, start_match = _find_marker_by_priority(page_text, _START_MARKERS)
            if start_match is None:
                continue
            started = True
            start_page = page_index
            page_text = page_text[start_match.end():].strip()

        current_end_marker, end_match = _find_first_marker(page_text, _END_MARKERS)
        if end_match is not None:
            collected.append(page_text[:end_match.start()].strip())
            end_page = page_index
            end_marker = current_end_marker
            break

        collected.append(page_text)

    candidate = '\n\n'.join(part for part in collected if part).strip()
    return {
        'candidate_legal_desc': candidate or None,
        'start_page': start_page,
        'end_page': end_page or (last_page_seen if started else None),
        'start_marker': start_marker,
        'end_marker': end_marker,
        'status': 'ok' if candidate else 'legal_not_found',
    }


def compare_legal_texts(candidate: str | None, gold: str | None) -> dict:
    candidate_normalized = normalize_legal_text(candidate)
    gold_normalized = normalize_legal_text(gold)

    if not candidate_normalized or not gold_normalized:
        similarity_ratio = None
    else:
        similarity_ratio = round(
            SequenceMatcher(None, candidate_normalized, gold_normalized).ratio(),
            4,
        )

    return {
        'candidate_normalized': candidate_normalized,
        'gold_normalized': gold_normalized,
        'normalized_exact': bool(candidate_normalized and candidate_normalized == gold_normalized),
        'similarity_ratio': similarity_ratio,
        'candidate_chars': len(candidate or ''),
        'gold_chars': len(gold or ''),
    }


def extract_target_parcel_number(target_hint: str | None) -> int | None:
    if not target_hint:
        return None
    match = re.search(r'\bPARCEL\s+(\d+)\b', str(target_hint), re.IGNORECASE)
    if not match:
        return None
    return int(match.group(1))


def extract_parcel_segments(text: str | None) -> list[dict]:
    if not text:
        return []

    segments = []
    matches = list(_PARCEL_LABEL_PATTERN.finditer(str(text)))
    if not matches:
        return segments

    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(str(text))
        segments.append({
            'parcel_number': int(match.group(1)),
            'text': str(text)[start:end].strip(),
        })
    return segments


def _count_pattern_matches(text: str | None, pattern: re.Pattern[str]) -> int:
    if not text:
        return 0
    return len(pattern.findall(str(text)))


def _has_wrapper_text(text: str | None) -> bool:
    if not text:
        return False
    return any(pattern.search(str(text)) for pattern in _WRAPPER_PATTERNS)


def validate_legal_candidate(candidate: str | None, page_texts: list[str], target_hint: str | None = None) -> dict:
    cleaned_pages = [clean_ocr_page_text(text) for text in page_texts or []]
    source_text = '\n\n'.join(text for text in cleaned_pages if text).strip()
    target_parcel = extract_target_parcel_number(target_hint)
    extracted_source_candidate = extract_legal_candidate(cleaned_pages).get('candidate_legal_desc')

    candidate_segments = extract_parcel_segments(candidate)
    source_segments = extract_parcel_segments(source_text)
    candidate_parcel_numbers = [segment['parcel_number'] for segment in candidate_segments]
    source_parcel_numbers = [segment['parcel_number'] for segment in source_segments]

    source_reference_text = source_text
    if target_parcel is not None:
        for segment in source_segments:
            if segment['parcel_number'] == target_parcel:
                source_reference_text = segment['text']
                break
    elif extracted_source_candidate:
        source_reference_text = extracted_source_candidate

    comparison = compare_legal_texts(candidate, source_reference_text)
    candidate_bearing_count = _count_pattern_matches(candidate, _BEARING_PATTERN)
    source_bearing_count = _count_pattern_matches(source_reference_text, _BEARING_PATTERN)
    candidate_distance_count = _count_pattern_matches(candidate, _DISTANCE_PATTERN)
    source_distance_count = _count_pattern_matches(source_reference_text, _DISTANCE_PATTERN)

    reasons = []
    if not (candidate or '').strip():
        reasons.append('missing_candidate')
    if _has_wrapper_text(candidate):
        reasons.append('wrapper_text_detected')
    if target_parcel is not None:
        if candidate_parcel_numbers:
            unique_candidate_parcels = sorted(set(candidate_parcel_numbers))
            if unique_candidate_parcels != [target_parcel]:
                reasons.append('target_parcel_mismatch')
        if len(set(candidate_parcel_numbers)) > 1:
            reasons.append('multiple_candidate_parcels_for_target')
    if comparison['similarity_ratio'] is not None and comparison['similarity_ratio'] < 0.75:
        reasons.append('low_similarity_to_source')
    if source_bearing_count >= 2 and candidate_bearing_count == 0:
        reasons.append('missing_bearings')
    if source_distance_count >= 2 and candidate_distance_count == 0:
        reasons.append('missing_distances')
    if comparison['gold_chars'] >= 200 and comparison['candidate_chars'] < max(80, int(comparison['gold_chars'] * 0.4)):
        reasons.append('candidate_too_short')

    return {
        'passed': not reasons,
        'reasons': reasons,
        'target_parcel': target_parcel,
        'candidate_parcel_numbers': candidate_parcel_numbers,
        'source_parcel_numbers': source_parcel_numbers,
        'similarity_ratio': comparison['similarity_ratio'],
        'candidate_bearing_count': candidate_bearing_count,
        'source_bearing_count': source_bearing_count,
        'candidate_distance_count': candidate_distance_count,
        'source_distance_count': source_distance_count,
        'candidate_chars': comparison['candidate_chars'],
        'source_chars': comparison['gold_chars'],
    }
