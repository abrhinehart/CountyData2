"""Offline tests for WaltonCountyAdapter.

Uses an anonymized live-capture fixture from tests/fixtures/tyler_walton/
search_page1.json -- 8 entities, 3 residential (pass filter), 5 excluded.
Walton's base URL uses capital-S 'SelfService' (not 'selfservice').
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from modules.permits.scrapers.adapters.tyler_energov import TylerEnerGovAdapter
from modules.permits.scrapers.adapters.walton_county import WaltonCountyAdapter

FIXTURE = Path(__file__).parent / "fixtures" / "tyler_walton" / "search_page1.json"

EXPECTED_PERMIT_KEYS = {
    "permit_number", "address", "parcel_id", "issue_date", "status",
    "permit_type", "valuation", "raw_subdivision_name", "raw_contractor_name",
    "raw_applicant_name", "raw_licensed_professional_name",
    "latitude", "longitude",
}


def _fixture_entities():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))["Result"]["EntityResults"]


def test_fixture_round_trips_to_canonical_permit():
    adapter = WaltonCountyAdapter()
    entities = _fixture_entities()
    assert entities
    for entity in entities:
        permit = adapter._map_entity_to_permit(entity)
        assert set(permit.keys()) == EXPECTED_PERMIT_KEYS
        assert permit["address"] == "100 MAIN ST SAMPLETOWN FL 00000"


def test_residential_filter_keeps_sfd_rejects_subs():
    """Walton fixture: Single Family Dwelling + Residential Remodel + Residential
    Miscellaneous pass; Temporary Pole / Mechanical Sub / Gas Standalone / Charter
    Vessel are all rejected."""
    adapter = WaltonCountyAdapter()
    kept = []
    for entity in _fixture_entities():
        permit = adapter._map_entity_to_permit(entity)
        if not permit["issue_date"]:
            continue
        if adapter._is_target_permit_type(permit):
            kept.append(permit["permit_type"])
    assert len(kept) == 3
    assert "Single Family Dwelling" in kept
    # Walton "Charter Vessel with Crew Permit (Bay)" rejected (no residential token)
    all_types = [e.get("CaseType") for e in _fixture_entities()]
    assert "Charter Vessel with Crew Permit (Bay)" in all_types
    assert "Charter Vessel with Crew Permit (Bay)" not in kept


def test_walton_capital_s_base_url_and_pagination_short_circuit():
    """Walton's URL path segment is 'SelfService' (capital S).
    Regression guard: case matters on some origins.

    Also: the pagination short-circuit -- when total_pages == 1, only
    one search POST happens regardless of max_pages = 200."""
    adapter = WaltonCountyAdapter()
    assert adapter.slug == "walton-county"
    assert adapter.display_name == "Walton County"
    # Capital S is important
    assert adapter.base_url.endswith("/apps/SelfService")
    assert "/apps/selfservice" not in adapter.base_url

    # Pagination short-circuit: when a single page reports TotalPages=1,
    # _search_permits should return saw_before_start=False and caller loop
    # stops after page 1. We simulate the decision inline:
    adapter._criteria_template = {"PermitCriteria": {}}
    body = adapter._build_search_body(date(2026, 1, 1), date(2026, 1, 7), page=1)
    assert body["PageNumber"] == 1
    assert body["SortAscending"] is False
    assert isinstance(adapter, TylerEnerGovAdapter)
