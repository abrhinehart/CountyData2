"""Offline tests for MarionCountyAdapter.

Uses an anonymized live-capture fixture from tests/fixtures/tyler_marion/
search_page1.json -- 8 entities, 3 residential (pass filter), 5 excluded.
Marion is the only Tyler subclass with a non-tylerhost.net base URL.
"""

from __future__ import annotations

import json
from pathlib import Path

from modules.permits.scrapers.adapters.marion_county import MarionCountyAdapter
from modules.permits.scrapers.adapters.tyler_energov import TylerEnerGovAdapter

FIXTURE = Path(__file__).parent / "fixtures" / "tyler_marion" / "search_page1.json"

EXPECTED_PERMIT_KEYS = {
    "permit_number", "address", "parcel_id", "issue_date", "status",
    "permit_type", "valuation", "raw_subdivision_name", "raw_contractor_name",
    "raw_applicant_name", "raw_licensed_professional_name",
    "latitude", "longitude",
}


def _fixture_entities():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))["Result"]["EntityResults"]


def test_fixture_round_trips_to_canonical_permit():
    adapter = MarionCountyAdapter()
    entities = _fixture_entities()
    assert entities
    for entity in entities:
        permit = adapter._map_entity_to_permit(entity)
        assert set(permit.keys()) == EXPECTED_PERMIT_KEYS
        if permit["parcel_id"] is not None:
            assert permit["parcel_id"].startswith("FAKE-PARCEL-")


def test_residential_filter_keeps_new_single_family_rejects_subs():
    """Marion fixture: New SF Residence + Residential Gas pass,
    Residential Roof/Mechanical/Private Provider/ROW-Electric are rejected."""
    adapter = MarionCountyAdapter()
    kept_types = []
    rejected_types = []
    for entity in _fixture_entities():
        permit = adapter._map_entity_to_permit(entity)
        if not permit["issue_date"]:
            continue
        if adapter._is_target_permit_type(permit):
            kept_types.append(permit["permit_type"])
        else:
            rejected_types.append(permit["permit_type"])
    assert len(kept_types) == 3
    assert "New Construction - Single Family Residence" in kept_types
    assert "Residential Gas" in kept_types
    assert "Residential Roof" in rejected_types
    assert "Residential Mechanical Scope" in rejected_types


def test_marion_nonstandard_base_url():
    """Marion is hosted on selfservice.marionfl.org (NOT tylerhost.net).
    This subclass-specific fact is easy to regress."""
    adapter = MarionCountyAdapter()
    assert adapter.slug == "marion-county"
    assert adapter.display_name == "Marion County"
    assert adapter.base_url == "https://selfservice.marionfl.org/energov_prod/selfservice"
    # Non-standard host: no "tylerhost.net" in URL
    assert "tylerhost.net" not in adapter.base_url
    assert "selfservice.marionfl.org" in adapter.base_url
    assert isinstance(adapter, TylerEnerGovAdapter)
    # API URL uses base_url + /api path
    assert adapter._api_url("/tenants/gettenantslist").startswith(
        "https://selfservice.marionfl.org/energov_prod/selfservice/api/"
    )
