"""Unit tests for the Lake Alfred (Accela COLA) adapter.

Models ``tests/test_davenport_adapter.py`` and ``tests/test_accela_citizen_access_adapter.py``:
  1. Instantiation / attribute sanity (slug, agency_code, search_url, target record type).
  2. Search URL construction and request headers.
  3. End-to-end parsing against a trimmed + anonymized Accela grid HTML
     fixture, exercising the Citizen Access POST-back + detail-page flow.
"""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock

from modules.permits.scrapers.adapters.accela_citizen_access import AccelaCitizenAccessAdapter
from modules.permits.scrapers.adapters.lake_alfred import LakeAlfredAdapter


# ── Instantiation ─────────────────────────────────────────────────────────

def test_lake_alfred_instantiates_with_expected_attributes():
    adapter = LakeAlfredAdapter()
    assert adapter.slug == "lake-alfred"
    assert adapter.display_name == "Lake Alfred"
    assert adapter.agency_code == "COLA"
    assert adapter.module_name == "Building"
    assert adapter.target_record_type == "Building/Residential/New/NA"
    assert adapter.mode == "live"
    assert isinstance(adapter, AccelaCitizenAccessAdapter)
    # search_url is built from agency_code + module_name
    assert "COLA" in adapter.search_url
    assert adapter.search_url == (
        "https://aca-prod.accela.com/COLA/Cap/CapHome.aspx"
        "?module=Building&TabName=Building"
    )


def test_lake_alfred_request_headers_reference_accela_cola():
    adapter = LakeAlfredAdapter()
    headers = adapter.request_headers
    assert "User-Agent" in headers
    assert headers["Referer"] == adapter.search_url
    assert "COLA" in headers["Referer"]


# ── fetch_permits mocked (end-to-end parse) ───────────────────────────────

def test_lake_alfred_fetch_permits_mocked(monkeypatch):
    """Mock the Accela POST + detail GET with anonymized HTML; confirm
    canonical fields come out correctly and target_record_type is set."""

    SEARCH_HTML = """
    <html><body>
    <form id="aspnetForm" action="CapHome.aspx" method="post">
      <input type="hidden" name="__VIEWSTATE" value="abc" />
      <input type="hidden" name="__EVENTTARGET" value="" />
      <input type="hidden" name="__EVENTARGUMENT" value="" />
      <input type="hidden" name="__EVENTVALIDATION" value="xyz" />
      <div>Showing 1-1 of 1 Result</div>
      <table id="ctl00_PlaceHolderMain_dgvPermitList_gdvPermitList">
        <tr><th>Date</th><th>Record Number</th><th>Record Type</th><th>Address</th><th>Status</th></tr>
        <tr>
          <td>03/10/2026</td>
          <td><a href="/COLA/Cap/CapDetail.aspx?Module=Building&amp;capID1=ABC&amp;capID2=00001&amp;capID3=00001">PERMIT-0001</a></td>
          <td>Building/Residential/New/NA</td>
          <td>123 FAKE ST, LAKE ALFRED FL 33850</td>
          <td>Issued</td>
        </tr>
      </table>
    </form>
    </body></html>
    """

    DETAIL_HTML = """
    <html><body>
    <div>Parcel Number: 00-00-00-000000-000001</div>
    <div>Job Value($): $275,000.00</div>
    <div>Subdivision: SAMPLE SUBDIVISION PHASE 1</div>
    <div>Fees</div>
    <div>Applicant: SAMPLE APPLICANT LLC</div>
    <div>Licensed Professional: SAMPLE CONTRACTOR INC</div>
    <div>Project Description: NEW SFR 3BR 2BA</div>
    <div>More Details</div>
    </body></html>
    """

    adapter = LakeAlfredAdapter()
    mock_session = MagicMock()

    initial_response = MagicMock()
    initial_response.text = SEARCH_HTML
    initial_response.status_code = 200
    initial_response.raise_for_status = MagicMock()

    search_response = MagicMock()
    search_response.text = SEARCH_HTML
    search_response.status_code = 200
    search_response.url = adapter.search_url
    search_response.headers = {"Content-Type": "text/html"}
    search_response.raise_for_status = MagicMock()
    search_response.request = MagicMock()
    search_response.request.method = "POST"

    detail_response = MagicMock()
    detail_response.text = DETAIL_HTML
    detail_response.status_code = 200
    detail_response.url = "https://aca-prod.accela.com/COLA/Cap/CapDetail.aspx"
    detail_response.headers = {"Content-Type": "text/html"}
    detail_response.raise_for_status = MagicMock()
    detail_response.request = MagicMock()
    detail_response.request.method = "GET"

    mock_session.get = MagicMock(side_effect=[initial_response, detail_response])
    mock_session.post = MagicMock(return_value=search_response)
    mock_session.request = MagicMock(return_value=detail_response)
    mock_session.headers = {}

    monkeypatch.setattr(adapter, "build_session", lambda **kwargs: mock_session)

    permits = adapter.fetch_permits(
        start_date=date(2026, 3, 1),
        end_date=date(2026, 3, 31),
    )

    assert len(permits) == 1
    p = permits[0]
    assert p["permit_number"] == "PERMIT-0001"
    assert p["address"] == "123 FAKE ST, LAKE ALFRED, FL 33850"
    assert p["parcel_id"] == "00-00-00-000000-000001"
    assert p["issue_date"] == "2026-03-10"
    assert p["status"] == "Issued"
    assert p["permit_type"] == "Building/Residential/New/NA"
    assert p["valuation"] == 275000.0
    assert p["raw_subdivision_name"] == "SAMPLE SUBDIVISION PHASE 1"
    assert p["raw_applicant_name"] == "SAMPLE APPLICANT LLC"
    assert p["raw_licensed_professional_name"] == "SAMPLE CONTRACTOR INC"
    assert p["raw_contractor_name"] == "SAMPLE CONTRACTOR INC"
    assert p["inspections"] is None

    # Verify the POST-back used the target_record_type.
    posted_payload = mock_session.post.call_args.kwargs.get("data") or (
        mock_session.post.call_args.args[1] if len(mock_session.post.call_args.args) > 1 else {}
    )
    assert posted_payload["ctl00$PlaceHolderMain$generalSearchForm$ddlGSPermitType"] == (
        "Building/Residential/New/NA"
    )
