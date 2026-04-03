"""
entity_filter.py - Filter scraped records against known builders and land bankers.

Loads aliases from the same YAML reference files the ETL uses, then checks
whether a record's grantor or grantee matches any known entity.
"""

import logging
from pathlib import Path

import yaml

log = logging.getLogger(__name__)

_REF_DIR = Path(__file__).resolve().parent.parent / 'reference_data'


def load_aliases_from_yaml(path: Path) -> set[str]:
    """Load all aliases from a YAML reference file, uppercased."""
    if not path.exists():
        log.warning('Reference file not found: %s', path)
        return set()

    with open(path, encoding='utf-8') as f:
        entries = yaml.safe_load(f) or []

    aliases = set()
    for entry in entries:
        for alias in entry.get('aliases', []):
            aliases.add(alias.strip().upper())
    return aliases


def build_entity_set() -> set[str]:
    """Build the combined set of all builder + land banker aliases (uppercased)."""
    builders = load_aliases_from_yaml(_REF_DIR / 'builders.yaml')
    land_bankers = load_aliases_from_yaml(_REF_DIR / 'land_bankers.yaml')
    combined = builders | land_bankers
    log.info('Loaded %d entity aliases (%d builders, %d land bankers)',
             len(combined), len(builders), len(land_bankers))
    return combined


def matches_entity(text: str, entity_set: set[str]) -> bool:
    """Check if any entity alias appears as a substring in the given text."""
    if not text:
        return False
    text_upper = text.upper()
    for alias in entity_set:
        if alias in text_upper:
            return True
    return False


def filter_rows(rows: list[dict], entity_set: set[str]) -> list[dict]:
    """Return rows where grantor OR grantee matches a known entity."""
    matched = []
    for row in rows:
        grantor = row.get('grantor', '')
        grantee = row.get('grantee', '')
        if matches_entity(grantor, entity_set) or matches_entity(grantee, entity_set):
            matched.append(row)
    return matched
