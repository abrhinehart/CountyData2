"""
lookup.py - Lookup-based matching for subdivisions and named parties.

All matchers load reference data once at ETL startup and perform
in-memory matching per row. No per-row database queries.
"""

import re

from utils.county_utils import normalize_county_key


class SubdivisionMatcher:
    """
    Matches legal description text against known subdivision aliases.
    Uses longest-match-first substring search, then validates phase
    against known phases for the matched subdivision.
    """

    def __init__(self, conn):
        self._by_county = {}  # { county_upper: [(alias_upper, sub_id, canonical, phases), ...] }
        self._load(conn)

    def _load(self, conn):
        with conn.cursor() as cur:
            cur.execute("""
                SELECT sa.alias, s.id, s.canonical_name, s.county, s.phases
                FROM subdivision_aliases sa
                JOIN subdivisions s ON s.id = sa.subdivision_id
            """)
            for alias, sub_id, canonical, county, phases in cur.fetchall():
                key = normalize_county_key(county)
                self._by_county.setdefault(key, []).append(
                    (alias.upper().strip(), sub_id, canonical, phases or [])
                )

        # Sort each county's aliases by length descending (longest match first)
        for key in self._by_county:
            self._by_county[key].sort(key=lambda t: len(t[0]), reverse=True)

    def match(self, legal_text: str, county: str, phase_keywords: list[str] = None):
        """
        Match legal text against known subdivisions for a county.

        Returns (subdivision_id, canonical_name, phase) or (None, None, None).
        Phase is extracted from legal_text and validated against known phases.
        """
        if not legal_text:
            return None, None, None

        text_upper = legal_text.upper()
        county_key = normalize_county_key(county)
        aliases = self._by_county.get(county_key, [])

        for alias_upper, sub_id, canonical, known_phases in aliases:
            if alias_upper in text_upper:
                phase = self._extract_phase(legal_text, phase_keywords, known_phases)
                return sub_id, canonical, phase

        return None, None, None

    def _extract_phase(self, text: str, phase_keywords: list[str] | None,
                       known_phases: list[str]) -> str | None:
        if not phase_keywords:
            return None

        kw_str = '|'.join(phase_keywords)
        pattern = rf'(?:{kw_str})\s*([A-Za-z0-9]+(?:[-]?[A-Za-z])?)'
        matches = re.findall(pattern, text, re.IGNORECASE)

        if not matches:
            return None

        phase = matches[-1].strip()
        phase = self._fix_phase_typos(phase)

        if known_phases and phase not in known_phases:
            return None

        return phase

    @staticmethod
    def _fix_phase_typos(phase: str) -> str:
        roman_map = {
            'I': '1', 'IA': '1A', 'IB': '1B', 'IC': '1C',
            'II': '2', 'III': '3', 'IV': '4', 'V': '5',
            'VI': '6', 'VII': '7', 'VIII': '8', 'IX': '9',
            'X': '10', 'XI': '11', 'XII': '12',
            'TWO': '2',
        }
        return roman_map.get(phase.upper(), phase)


class _PartyAliasMatcher:
    """
    Matches party names against known aliases.
    Uses exact match after normalization (strip, collapse whitespace, uppercase).
    """

    def __init__(self, conn, entity_table: str, alias_table: str, alias_fk: str):
        self._aliases = {}  # { alias_upper: (entity_id, canonical_name) }
        self._entity_table = entity_table
        self._alias_table = alias_table
        self._alias_fk = alias_fk
        self._load(conn)

    def _load(self, conn):
        query = f"""
            SELECT a.alias, e.id, e.canonical_name
            FROM {self._alias_table} a
            JOIN {self._entity_table} e ON e.id = a.{self._alias_fk}
        """
        with conn.cursor() as cur:
            cur.execute(query)
            for alias, entity_id, canonical in cur.fetchall():
                normalized = self._normalize_name(alias)
                self._aliases[normalized] = (entity_id, canonical)

    def match(self, name: str):
        """
        Match a party name against known aliases.

        Returns (entity_id, canonical_name) or (None, None).
        """
        if not name:
            return None, None

        normalized = self._normalize_name(name)
        return self._aliases.get(normalized, (None, None))

    @staticmethod
    def _normalize_name(name: str) -> str:
        return re.sub(r'\s+', ' ', name.strip()).upper()


class BuilderMatcher(_PartyAliasMatcher):
    def __init__(self, conn):
        super().__init__(conn, 'builders', 'builder_aliases', 'builder_id')


class LandBankerMatcher(_PartyAliasMatcher):
    def __init__(self, conn):
        super().__init__(conn, 'land_bankers', 'land_banker_aliases', 'land_banker_id')
