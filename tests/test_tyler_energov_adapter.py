"""Unit tests for the Tyler EnerGov generalizable adapter and its five county subclasses."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from modules.permits.scrapers.adapters.tyler_energov import TylerEnerGovAdapter


# ── Fixtures ────────────────────────────────────────────────────────────

TENANT_RESPONSE = {
    "Result": [
        {"TenantID": "abc-123", "TenantName": "testcountyprod"}
    ]
}

CRITERIA_TEMPLATE = {
    "Result": {
        "SearchModule": 0,
        "FilterModule": 0,
        "PageNumber": 0,
        "PageSize": 0,
        "SortBy": "",
        "SortAscending": True,
        "PermitCriteria": {
            "IssueDateFrom": None,
            "IssueDateTo": None,
            "PageNumber": 0,
            "PageSize": 0,
            "SortBy": "",
            "SortAscending": True,
        },
        "SortLists": [
            {"SortColumn": "IssueDate", "SortDirection": "desc"}
        ],
    }
}


def _make_search_response(entities, total_pages=1):
    return {
        "Result": {
            "EntityResults": entities,
            "TotalPages": total_pages,
        }
    }


ENTITY_RESIDENTIAL = {
    "CaseNumber": "BP2407-0001",
    "CaseType": "Building - Residential",
    "CaseWorkclass": "Residential",
    "CaseStatus": "Issued",
    "IssueDate": "2025-06-03T00:00:00",
    "AddressDisplay": "100 MAIN ST SOMETOWN FL 12345",
    "MainParcel": "1234-5678",
    "ProjectName": "Oak Estates Phase 2",
    "Description": "new single family dwelling",
}

ENTITY_RESIDENTIAL_2 = {
    "CaseNumber": "BP2407-0002",
    "CaseType": "Building - New Single Family",
    "CaseWorkclass": "Residential",
    "CaseStatus": "Finaled",
    "IssueDate": "2025-06-05T00:00:00",
    "AddressDisplay": "200 OAK AVE SOMETOWN FL 12345",
    "MainParcel": None,
    "ProjectName": "",
    "Description": "new SFD",
}

ENTITY_ELECTRICAL = {
    "CaseNumber": "EP2407-0010",
    "CaseType": "Electrical - Residential",
    "CaseWorkclass": "Residential",
    "CaseStatus": "Issued",
    "IssueDate": "2025-06-04T00:00:00",
    "AddressDisplay": "300 ELM ST SOMETOWN FL 12345",
    "MainParcel": None,
    "ProjectName": "",
    "Description": "upgrade 200amp",
}

ENTITY_POOL = {
    "CaseNumber": "PP2407-0020",
    "CaseType": "Pool - Residential",
    "CaseWorkclass": "Residential",
    "CaseStatus": "Issued",
    "IssueDate": "2025-06-04T00:00:00",
    "AddressDisplay": "400 PINE ST SOMETOWN FL 12345",
    "MainParcel": None,
    "ProjectName": "",
    "Description": "in-ground pool",
}

ENTITY_COMMERCIAL = {
    "CaseNumber": "BP2407-0030",
    "CaseType": "Building - Commercial",
    "CaseWorkclass": "Commercial",
    "CaseStatus": "Issued",
    "IssueDate": "2025-06-04T00:00:00",
    "AddressDisplay": "500 COMMERCE DR SOMETOWN FL 12345",
    "MainParcel": None,
    "ProjectName": "",
    "Description": "new commercial building",
}


# ── Helpers ──────────────────────────────────────────────────────────────

class _TestAdapter(TylerEnerGovAdapter):
    slug = "test-energov"
    display_name = "Test EnerGov"
    base_url = "https://test-energovweb.tylerhost.net/apps/selfservice"


def _mock_response(json_data, status_code=200, url="https://example.com"):
    resp = MagicMock()
    resp.json.return_value = json_data
    resp.text = json.dumps(json_data)
    resp.status_code = status_code
    resp.url = url
    resp.headers = {"Content-Type": "application/json"}
    resp.request = MagicMock()
    resp.request.method = "GET"
    resp.raise_for_status = MagicMock()
    return resp


# ── Tests ────────────────────────────────────────────────────────────────

def test_fetch_permits_basic():
    """Mock all three endpoints, assert 2-permit return with correct field mapping."""
    adapter = _TestAdapter()

    search_data = _make_search_response([ENTITY_RESIDENTIAL, ENTITY_RESIDENTIAL_2])

    with patch("modules.permits.scrapers.adapters.tyler_energov.requests.Session") as MockSession:
        mock_session = MagicMock()
        mock_session.headers = {}

        mock_session.get.side_effect = [
            _mock_response(TENANT_RESPONSE),
            _mock_response(CRITERIA_TEMPLATE),
        ]
        mock_session.post.return_value = _mock_response(search_data)

        # Bypass build_session to use our mock
        with patch.object(adapter, "build_session", return_value=mock_session):
            from datetime import date
            permits = adapter.fetch_permits(date(2025, 6, 1), date(2025, 6, 7))

    assert len(permits) == 2
    p1 = permits[0]
    assert p1["permit_number"] == "BP2407-0001"
    assert p1["address"] == "100 MAIN ST SOMETOWN FL 12345"
    assert p1["issue_date"] == "2025-06-03"
    assert p1["permit_type"] == "Building - Residential"
    assert p1["status"] == "Issued"
    assert p1["parcel_id"] == "1234-5678"
    assert p1["raw_subdivision_name"] == "Oak Estates Phase 2"
    assert p1["valuation"] is None
    assert p1["raw_contractor_name"] is None
    assert p1["latitude"] is None

    p2 = permits[1]
    assert p2["permit_number"] == "BP2407-0002"
    assert p2["raw_subdivision_name"] is None  # empty string → None
    assert p2["parcel_id"] is None


def test_pagination():
    """Mock search returning TotalPages=3, assert all pages collected."""
    adapter = _TestAdapter()

    page1 = _make_search_response([ENTITY_RESIDENTIAL], total_pages=3)
    page2 = _make_search_response([ENTITY_RESIDENTIAL_2], total_pages=3)
    page3 = _make_search_response([], total_pages=3)

    with patch.object(adapter, "build_session") as mock_build:
        mock_session = MagicMock()
        mock_session.headers = {}
        mock_build.return_value = mock_session

        mock_session.get.side_effect = [
            _mock_response(TENANT_RESPONSE),
            _mock_response(CRITERIA_TEMPLATE),
        ]
        mock_session.post.side_effect = [
            _mock_response(page1),
            _mock_response(page2),
            _mock_response(page3),
        ]

        from datetime import date
        permits = adapter.fetch_permits(date(2025, 6, 1), date(2025, 6, 7))

    assert len(permits) == 2
    assert mock_session.post.call_count == 3


def test_residential_filtering():
    """5 mixed-type entities, assert only matching residential ones pass."""
    adapter = _TestAdapter()

    entities = [
        ENTITY_RESIDENTIAL,
        ENTITY_RESIDENTIAL_2,
        ENTITY_ELECTRICAL,
        ENTITY_POOL,
        ENTITY_COMMERCIAL,
    ]
    search_data = _make_search_response(entities)

    with patch.object(adapter, "build_session") as mock_build:
        mock_session = MagicMock()
        mock_session.headers = {}
        mock_build.return_value = mock_session

        mock_session.get.side_effect = [
            _mock_response(TENANT_RESPONSE),
            _mock_response(CRITERIA_TEMPLATE),
        ]
        mock_session.post.return_value = _mock_response(search_data)

        from datetime import date
        permits = adapter.fetch_permits(date(2025, 6, 1), date(2025, 6, 7))

    assert len(permits) == 2
    numbers = {p["permit_number"] for p in permits}
    assert numbers == {"BP2407-0001", "BP2407-0002"}


def test_date_parsing():
    """ISO-T format -> date-only string, None -> None."""
    adapter = _TestAdapter()
    assert adapter._parse_api_date("2025-06-03T00:00:00") == "2025-06-03"
    assert adapter._parse_api_date("2025-12-25T14:30:00") == "2025-12-25"
    assert adapter._parse_api_date(None) is None
    assert adapter._parse_api_date("") is None
    assert adapter._parse_api_date("2025-06-03") == "2025-06-03"


def test_all_five_adapters_instantiate():
    """Import all five county adapters and verify slug/display_name/base_url."""
    from modules.permits.scrapers.adapters.okeechobee import OkeechobeeAdapter
    from modules.permits.scrapers.adapters.hernando_county import HernandoCountyAdapter
    from modules.permits.scrapers.adapters.marion_county import MarionCountyAdapter
    from modules.permits.scrapers.adapters.walton_county import WaltonCountyAdapter
    from modules.permits.scrapers.adapters.desoto_county_ms import DeSotoCountyMsAdapter

    adapters = [
        (OkeechobeeAdapter, "okeechobee", "Okeechobee County",
         "https://okeechobeecountyfl-energovweb.tylerhost.net/apps/selfservice"),
        (HernandoCountyAdapter, "hernando-county", "Hernando County",
         "https://hernandocountyfl-energovweb.tylerhost.net/apps/selfservice"),
        (MarionCountyAdapter, "marion-county", "Marion County",
         "https://selfservice.marionfl.org/energov_prod/selfservice"),
        (WaltonCountyAdapter, "walton-county", "Walton County",
         "https://waltoncountyfl-energovweb.tylerhost.net/apps/SelfService"),
        (DeSotoCountyMsAdapter, "desoto-county-ms", "DeSoto County, MS",
         "https://energovweb.desotocountyms.gov/energov_prod/selfservice"),
    ]

    for cls, expected_slug, expected_name, expected_url in adapters:
        adapter = cls()
        assert adapter.slug == expected_slug
        assert adapter.display_name == expected_name
        assert adapter.base_url == expected_url
        assert adapter.mode == "live"
        assert isinstance(adapter, TylerEnerGovAdapter)


def test_search_body_preserves_sort_lists():
    """Build search body, assert SortLists key still exists."""
    adapter = _TestAdapter()
    adapter._criteria_template = CRITERIA_TEMPLATE["Result"]

    from datetime import date
    body = adapter._build_search_body(date(2025, 6, 1), date(2025, 6, 7), page=1)

    assert "SortLists" in body
    assert body["SortLists"] == [
        {"SortColumn": "IssueDate", "SortDirection": "desc"}
    ]
    assert body["SearchModule"] == 1
    assert body["FilterModule"] == 2
    assert body["PermitCriteria"]["IssueDateFrom"] == "06/01/2025"
    assert body["PermitCriteria"]["IssueDateTo"] == "06/07/2025"
    assert body["PermitCriteria"]["PageNumber"] == 1
    assert body["PageNumber"] == 1

    # Ensure deep copy — original template unchanged
    assert adapter._criteria_template["SearchModule"] == 0
    assert adapter._criteria_template["PermitCriteria"]["IssueDateFrom"] is None
