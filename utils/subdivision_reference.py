from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import re

import yaml

from utils.county_utils import normalize_county_key


_REFERENCE_DATA_PATH = Path(__file__).resolve().parents[1] / 'reference_data' / 'subdivisions.yaml'
_REFERENCE_STOPWORDS = {'AT', 'OF', 'THE'}
_TOKEN_RE = re.compile(r'[A-Z0-9]+')
_COMMON_ABBREVIATIONS = {
    'ESTATES': {'EST', 'ESTS'},
    'HEIGHTS': {'HT', 'HTS'},
    'LAKE': {'LK'},
    'PARK': {'PK', 'PRK'},
    'PRESERVE': {'PRES', 'PRSV'},
    'RANCH': {'RCH', 'RNCH'},
    'VILLAGE': {'VLG', 'VILLG'},
    'WEST': {'W'},
    'EAST': {'E'},
    'NORTH': {'N'},
    'SOUTH': {'S'},
}


def _normalize_reference_text(text: str) -> str:
    normalized = str(text).upper().replace('&', ' AND ')
    normalized = re.sub(r'[^A-Z0-9]+', ' ', normalized)
    return re.sub(r'\s+', ' ', normalized).strip()


def _reference_tokens(text: str) -> list[str]:
    return [token for token in _TOKEN_RE.findall(_normalize_reference_text(text)) if token]


def _significant_reference_tokens(text: str) -> list[str]:
    return [
        token
        for token in _reference_tokens(text)
        if token not in _REFERENCE_STOPWORDS and token != 'AND'
    ]


def _token_skeleton(token: str) -> str:
    normalized = re.sub(r'[^A-Z0-9]', '', str(token).upper())
    if not normalized:
        return ''
    if len(normalized) <= 2:
        return normalized
    return normalized[0] + re.sub(r'[AEIOUY]', '', normalized[1:])


def _candidate_token_matches_reference(candidate_token: str, reference_token: str) -> bool:
    candidate = str(candidate_token).upper()
    reference = str(reference_token).upper()

    if candidate == reference:
        return True
    if candidate in _COMMON_ABBREVIATIONS.get(reference, set()):
        return True
    if len(candidate) >= 3 and reference.startswith(candidate):
        return True

    candidate_skeleton = _token_skeleton(candidate)
    reference_skeleton = _token_skeleton(reference)
    if candidate_skeleton and candidate_skeleton == reference_skeleton:
        return True
    if len(candidate_skeleton) >= 2 and reference_skeleton.startswith(candidate_skeleton):
        return True

    return False


def _candidate_span_matches_reference(candidate_token: str, reference_tokens: tuple[str, ...]) -> bool:
    if not reference_tokens:
        return False

    candidate = str(candidate_token).upper()
    if len(reference_tokens) == 1:
        return _candidate_token_matches_reference(candidate, reference_tokens[0])

    initials = ''.join(token[0] for token in reference_tokens if token)
    return bool(initials) and candidate == initials


def _match_reference_sequence(candidate_tokens: tuple[str, ...], reference_tokens: tuple[str, ...]) -> bool:
    @lru_cache(maxsize=None)
    def _match(candidate_index: int, reference_index: int) -> bool:
        if candidate_index == len(candidate_tokens) and reference_index == len(reference_tokens):
            return True
        if candidate_index == len(candidate_tokens) or reference_index == len(reference_tokens):
            return False

        for span_end in range(reference_index + 1, len(reference_tokens) + 1):
            span = reference_tokens[reference_index:span_end]
            if _candidate_span_matches_reference(candidate_tokens[candidate_index], span):
                if _match(candidate_index + 1, span_end):
                    return True

        return False

    return _match(0, 0)


@lru_cache(maxsize=None)
def _load_subdivision_reference_data() -> dict[str, list[dict]]:
    with open(_REFERENCE_DATA_PATH, encoding='utf-8') as handle:
        raw_data = yaml.safe_load(handle) or {}

    by_county = {}
    for county, entries in raw_data.items():
        by_county[normalize_county_key(county)] = list(entries or [])
    return by_county


@lru_cache(maxsize=None)
def get_county_subdivision_alias_map(county_key: str) -> dict[str, str]:
    alias_map = {}
    for entry in _load_subdivision_reference_data().get(normalize_county_key(county_key), []):
        canonical_name = str(entry.get('canonical_name', '')).strip()
        if not canonical_name:
            continue

        alias_map[_normalize_reference_text(canonical_name)] = canonical_name
        for alias in entry.get('aliases', []) or []:
            alias_text = str(alias).strip()
            if not alias_text:
                continue
            alias_map[_normalize_reference_text(alias_text)] = canonical_name

    return alias_map


@lru_cache(maxsize=None)
def _marion_reference_entries() -> tuple[dict, ...]:
    entries = []
    for entry in _load_subdivision_reference_data().get('MARION', []):
        canonical_name = str(entry.get('canonical_name', '')).strip()
        if not canonical_name:
            continue

        entries.append({
            'canonical_name': canonical_name,
            'tokens': tuple(_significant_reference_tokens(canonical_name)),
        })

    return tuple(entries)


def resolve_county_subdivision_reference(county_key: str, subdivision: str) -> dict | None:
    normalized_county = normalize_county_key(county_key)
    if normalized_county == 'MARION':
        return resolve_marion_subdivision_reference(subdivision)
    if normalized_county != 'SANTAROSA':
        return None

    normalized = _normalize_reference_text(subdivision)
    if not normalized:
        return None

    alias_map = get_county_subdivision_alias_map(normalized_county)
    canonical_name = alias_map.get(normalized)
    if not canonical_name:
        return None

    match_type = 'reference_exact'
    if normalized != _normalize_reference_text(canonical_name):
        match_type = 'reference_alias'

    return {
        'canonical_name': canonical_name,
        'match_type': match_type,
        'prefix_tokens': [],
        'suffix_tokens': [],
    }


def resolve_marion_subdivision_reference(subdivision: str) -> dict | None:
    normalized = _normalize_reference_text(subdivision)
    if not normalized:
        return None

    alias_map = get_county_subdivision_alias_map('MARION')
    canonical_name = alias_map.get(normalized)
    if canonical_name:
        match_type = 'reference_exact'
        if normalized != _normalize_reference_text(canonical_name):
            match_type = 'reference_alias'

        return {
            'canonical_name': canonical_name,
            'match_type': match_type,
            'prefix_tokens': [],
            'suffix_tokens': [],
        }

    candidate_tokens = tuple(_significant_reference_tokens(normalized))
    if not candidate_tokens:
        return None

    best_match = None
    best_key = None

    for entry in _marion_reference_entries():
        reference_tokens = entry['tokens']
        if not reference_tokens:
            continue

        max_trim = min(2, len(candidate_tokens) - 1)
        for prefix_trim in range(0, max_trim + 1):
            for suffix_trim in range(0, min(2, len(candidate_tokens) - prefix_trim - 1) + 1):
                core_end = len(candidate_tokens) - suffix_trim if suffix_trim else len(candidate_tokens)
                core_tokens = candidate_tokens[prefix_trim:core_end]
                if not core_tokens:
                    continue

                if not _match_reference_sequence(core_tokens, reference_tokens):
                    continue

                prefix_tokens = list(candidate_tokens[:prefix_trim])
                suffix_tokens = list(candidate_tokens[core_end:])
                extras = len(prefix_tokens) + len(suffix_tokens)
                ranking = (
                    len(reference_tokens) * 10 + len(core_tokens) * 4 - extras * 3,
                    len(core_tokens),
                    -extras,
                    len(entry['canonical_name']),
                )
                if best_key is None or ranking > best_key:
                    best_key = ranking
                    best_match = {
                        'canonical_name': entry['canonical_name'],
                        'match_type': 'reference_heuristic',
                        'prefix_tokens': prefix_tokens,
                        'suffix_tokens': suffix_tokens,
                    }

    return best_match
