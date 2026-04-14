"""Offline tests for OkeechobeeAdapter.

Uses an anonymized live-capture fixture from tests/fixtures/tyler_okeechobee/
search_page1.json -- 8 entities, 3 residential (pass filter), 5 excluded.
"""

from __future__ import annotations

import json
from pathlib import Path

from modules.permits.scrapers.adapters.okeechobee import OkeechobeeAdapter
from modules.permits.scrapers.adapters.tyler_energov import TylerEnerGovAdapter

FIXTURE = Path(__file__).parent / "fixtures" / "tyler_okeechobee" / "search_page1.json"

EXPECTED_PERMIT_KEYS = {
    "permit_number", "address", "parcel_id", "issue_date", "status",
    "permit_type", "valuation", "raw_subdivision_name", "raw_contractor_name",
    "raw_applicant_name", "raw_licensed_professional_name",
    "latitude", "longitude",
}


def _fixture_entities():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))["Result"]["EntityResults"]


def test_fixture_round_trips_to_canonical_permit():
    adapter = OkeechobeeAdapter()
    for entity in _fixture_entities():
        permit = adapter._map_entity_to_permit(entity)
        assert set(permit.keys()) == EXPECTED_PERMIT_KEYS


def test_residential_filter_keeps_sfr_rejects_subs():
    """Okeechobee: Residential Renovate + Residential Building w/ Subs CBS +
    SFR Driveway pass. Plumbing Sub / Mechanical Sub / Electrical-Residential /
    Concrete Slab / Manufactured Home all rejected."""
    adapter = OkeechobeeAdapter()
    kept = []
    rejected = []
    for entity in _fixture_entities():
        permit = adapter._map_entity_to_permit(entity)
        if not permit["issue_date"]:
            continue
        if adapter._is_target_permit_type(permit):
            kept.append(permit["permit_type"])
        else:
            rejected.append(permit["permit_type"])
    assert len(kept) == 3
    # SFR driveway passes because of "sfr" token + "residential" suffix
    assert any("SFR" in t for t in kept)
    # Electrical-Residential is rejected despite "residential" -- electrical is excluded
    assert "Electrical - Residential" in rejected
    assert "Plumbing - Sub" in rejected


def test_okeechobee_identity_and_abc_override():
    """Okeechobee-specific identity. Also guard against the parent's
    fetch_permits being replaced by an abstract raise in a refactor."""
    adapter = OkeechobeeAdapter()
    assert adapter.slug == "okeechobee"
    assert adapter.display_name == "Okeechobee County"
    assert adapter.base_url == "https://okeechobeecountyfl-energovweb.tylerhost.net/apps/selfservice"
    assert adapter.mode == "live"
    assert isinstance(adapter, TylerEnerGovAdapter)
    # fetch_permits is the parent's concrete implementation (overrides ABC)
    assert OkeechobeeAdapter.fetch_permits is TylerEnerGovAdapter.fetch_permits
    # And it's NOT the unimplemented base-class abstractmethod
    from modules.permits.scrapers.base import JurisdictionAdapter
    assert OkeechobeeAdapter.fetch_permits is not JurisdictionAdapter.fetch_permits
