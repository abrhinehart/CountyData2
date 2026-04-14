"""Unit tests for the Citrus County (Accela CITRUS) adapter.

Models ``tests/test_davenport_adapter.py`` and the Accela sibling suite:
  1. Instantiation / attribute sanity (slug, agency_code, search_url,
     target record type).
  2. Search URL construction and request headers.
  3. End-to-end parsing against a trimmed + anonymized Accela grid HTML
     fixture.
"""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock

from modules.permits.scrapers.adapters.accela_citizen_access import AccelaCitizenAccessAdapter
from modules.permits.scrapers.adapters.citrus_county import CitrusCountyAdapter


# ── Instantiation ─────────────────────────────────────────────────────────

def test_citrus_county_instantiates_with_expected_attributes():
    adapter = CitrusCountyAdapter()
    assert adapter.slug == "citrus-county"
    assert adapter.display_name == "Citrus County"
    assert adapter.agency_code == "CITRUS"
    assert adapter.module_name == "Building"
    assert adapter.target_record_type == "Building/Residential/NA/NA"
    assert adapter.mode == "live"
    assert isinstance(adapter, AccelaCitizenAccessAdapter)
    assert adapter.search_url == (
        "https://aca-prod.accela.com/CITRUS/Cap/CapHome.aspx"
        "?module=Building&TabName=Building"
    )


def test_citrus_county_request_headers_reference_accela_citrus():
    adapter = CitrusCountyAdapter()
    headers = adapter.request_headers
    assert "User-Agent" in headers
    assert headers["Referer"] == adapter.search_url
    assert "CITRUS" in headers["Referer"]


# ── fetch_permits mocked (end-to-end parse) ───────────────────────────────

def test_citrus_county_fetch_permits_mocked(monkeypatch):
    """Mock the Accela POST + detail GET with anonymized HTML; confirm
    canonical fields come out correctly and the Citrus-specific
    ``Building/Residential/NA/NA`` record type is sent."""

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
          <td>03/12/2026</td>
          <td><a href="/CITRUS/Cap/CapDetail.aspx?Module=Building&amp;capID1=DEF&amp;capID2=00002&amp;capID3=00002">PERMIT-0002</a></td>
          <td>Building/Residential/NA/NA</td>
          <td>456 SAMPLE AVE, INVERNESS FL 34450</td>
          <td>Issued</td>
        </tr>
      </table>
    </form>
    </body></html>
    """

    DETAIL_HTML = """
    <html><body>
    <div>Parcel Number: 00-00-00-000000-000002</div>
    <div>Job Value($): $310,000.00</div>
    <div>Subdivision: SAMPLE SUBDIVISION PHASE 2</div>
    <div>Fees</div>
    <div>Applicant: SAMPLE APPLICANT LLC</div>
    <div>Licensed Professional: SAMPLE CONTRACTOR INC</div>
    <div>Project Description: NEW SFR</div>
    <div>More Details</div>
    </body></html>
    """

    adapter = CitrusCountyAdapter()
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
    detail_response.url = "https://aca-prod.accela.com/CITRUS/Cap/CapDetail.aspx"
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
    assert p["permit_number"] == "PERMIT-0002"
    assert p["address"] == "456 SAMPLE AVE, INVERNESS, FL 34450"
    assert p["parcel_id"] == "00-00-00-000000-000002"
    assert p["issue_date"] == "2026-03-12"
    assert p["status"] == "Issued"
    assert p["permit_type"] == "Building/Residential/NA/NA"
    assert p["valuation"] == 310000.0
    assert p["raw_subdivision_name"] == "SAMPLE SUBDIVISION PHASE 2"
    assert p["raw_applicant_name"] == "SAMPLE APPLICANT LLC"
    assert p["raw_licensed_professional_name"] == "SAMPLE CONTRACTOR INC"
    assert p["raw_contractor_name"] == "SAMPLE CONTRACTOR INC"
    assert p["inspections"] is None

    # Verify Citrus-specific target_record_type was posted.
    posted_payload = mock_session.post.call_args.kwargs.get("data") or {}
    assert posted_payload["ctl00$PlaceHolderMain$generalSearchForm$ddlGSPermitType"] == (
        "Building/Residential/NA/NA"
    )
