"""Offline tests for HernandoCountyAdapter.

Uses an anonymized live-capture fixture from tests/fixtures/tyler_hernando/
search_page1.json -- 8 entities, 3 residential (pass filter), 5 excluded
(no-date, roof, mechanical).
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

from modules.permits.scrapers.adapters.hernando_county import HernandoCountyAdapter
from modules.permits.scrapers.adapters.tyler_energov import TylerEnerGovAdapter

FIXTURE = Path(__file__).parent / "fixtures" / "tyler_hernando" / "search_page1.json"

EXPECTED_PERMIT_KEYS = {
    "permit_number", "address", "parcel_id", "issue_date", "status",
    "permit_type", "valuation", "raw_subdivision_name", "raw_contractor_name",
    "raw_applicant_name", "raw_licensed_professional_name",
    "latitude", "longitude",
}


def _fixture_entities():
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    return data["Result"]["EntityResults"]


def test_fixture_round_trips_to_canonical_permit():
    """Every fixture entity maps to a dict with the full canonical key set."""
    adapter = HernandoCountyAdapter()
    entities = _fixture_entities()
    assert entities, "fixture must have entities"
    for entity in entities:
        permit = adapter._map_entity_to_permit(entity)
        assert set(permit.keys()) == EXPECTED_PERMIT_KEYS
        # Canonical address format preserved
        assert permit["address"] == "100 MAIN ST SAMPLETOWN FL 00000"
        # Parcel anonymized
        if permit["parcel_id"] is not None:
            assert permit["parcel_id"].startswith("FAKE-PARCEL-")


def test_residential_filter_keeps_3_rejects_5():
    """Fixture has 3 residential permits w/ IssueDate that must pass the filter;
    5 are rejected (no-date commercial, reroof, mechanical)."""
    adapter = HernandoCountyAdapter()
    kept = []
    for entity in _fixture_entities():
        permit = adapter._map_entity_to_permit(entity)
        if not permit["issue_date"]:
            continue  # no issue date — scraper skips
        if adapter._is_target_permit_type(permit):
            kept.append(permit)
    assert len(kept) == 3
    kept_types = {p["permit_type"] for p in kept}
    # These three survive the residential/excluded-term filter
    assert "Residential - Alteration, Remodel, Repair" in kept_types
    assert "Residential - Accessory Permits" in kept_types
    # And these are rejected
    rejected_types = {
        e["CaseType"] for e in _fixture_entities()
        if adapter._is_target_permit_type(adapter._map_entity_to_permit(e)) is False
    }
    assert "Residential - Reroof" in rejected_types
    assert "Residential - Mechanical Changeout" in rejected_types


def test_adapter_identity_attributes():
    """Hernando-specific slug, display_name, base_url, mode, and subclass."""
    adapter = HernandoCountyAdapter()
    assert adapter.slug == "hernando-county"
    assert adapter.display_name == "Hernando County"
    assert adapter.base_url == "https://hernandocountyfl-energovweb.tylerhost.net/apps/selfservice"
    assert adapter.mode == "live"
    assert isinstance(adapter, TylerEnerGovAdapter)
    # No unexpected class-level override of the parent's search pipeline
    assert HernandoCountyAdapter.fetch_permits is TylerEnerGovAdapter.fetch_permits


def test_fetch_permits_with_fixture_end_to_end():
    """Drive fetch_permits offline using the fixture as the search response.
    Verifies the Tyler pipeline (tenant -> criteria -> search) produces
    the expected 3 residential permits without touching the network."""
    adapter = HernandoCountyAdapter()
    tenant_resp = MagicMock()
    tenant_resp.json.return_value = {"Result": [{"TenantID": "T", "TenantName": "TN"}]}
    tenant_resp.text = "{}"
    tenant_resp.headers = {"Content-Type": "application/json"}
    tenant_resp.status_code = 200
    tenant_resp.request = MagicMock(method="GET")
    tenant_resp.url = "http://fixture"
    tenant_resp.raise_for_status = MagicMock()

    criteria_resp = MagicMock()
    criteria_resp.json.return_value = {
        "Result": {
            "PermitCriteria": {},
            "SortLists": [{"SortColumn": "IssueDate", "SortDirection": "desc"}],
        }
    }
    criteria_resp.text = "{}"
    criteria_resp.headers = {"Content-Type": "application/json"}
    criteria_resp.status_code = 200
    criteria_resp.request = MagicMock(method="GET")
    criteria_resp.url = "http://fixture"
    criteria_resp.raise_for_status = MagicMock()

    search_resp = MagicMock()
    search_resp.json.return_value = json.loads(FIXTURE.read_text(encoding="utf-8"))
    search_resp.text = "{}"
    search_resp.headers = {"Content-Type": "application/json"}
    search_resp.status_code = 200
    search_resp.request = MagicMock(method="POST")
    search_resp.url = "http://fixture"
    search_resp.raise_for_status = MagicMock()

    with patch.object(adapter, "build_session") as mock_build:
        mock_session = MagicMock()
        mock_session.headers = {}
        mock_session.get.side_effect = [tenant_resp, criteria_resp]
        mock_session.post.return_value = search_resp
        mock_build.return_value = mock_session
        # Widen date range so fixture dates always fall within
        permits = adapter.fetch_permits(date(2025, 1, 1), date(2099, 12, 31))

    assert len(permits) == 3
    for p in permits:
        assert "residential" in (p["permit_type"] or "").lower()
        assert p["issue_date"] is not None
