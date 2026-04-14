"""Unit tests for the Accela Citizen Access base adapter and its three county subclasses."""

from __future__ import annotations

from datetime import date

import pytest

from modules.permits.scrapers.adapters.accela_citizen_access import AccelaCitizenAccessAdapter


# ── Instantiation ─────────────────────────────────────────────────────────

def test_all_three_accela_adapters_instantiate():
    """Import Polk/Citrus, verify slug/display_name/agency_code/search_url."""
    from modules.permits.scrapers.adapters.polk_county import PolkCountyAdapter
    from modules.permits.scrapers.adapters.citrus_county import CitrusCountyAdapter

    adapters = [
        (PolkCountyAdapter, "polk-county", "Polk County", "POLKCO"),
        (CitrusCountyAdapter, "citrus-county", "Citrus County", "CITRUS"),
    ]

    for cls, expected_slug, expected_name, expected_agency in adapters:
        adapter = cls()
        assert adapter.slug == expected_slug
        assert adapter.display_name == expected_name
        assert adapter.agency_code == expected_agency
        assert expected_agency in adapter.search_url
        assert adapter.mode == "live"
        assert isinstance(adapter, AccelaCitizenAccessAdapter)


# ── search_url construction ───────────────────────────────────────────────

def test_search_url_construction():
    """Verify search_url property produces correct URL from agency_code + module_name."""
    from modules.permits.scrapers.adapters.polk_county import PolkCountyAdapter
    from modules.permits.scrapers.adapters.citrus_county import CitrusCountyAdapter

    polk = PolkCountyAdapter()
    assert polk.search_url == (
        "https://aca-prod.accela.com/POLKCO/Cap/CapHome.aspx"
        "?module=Building&TabName=Building"
    )

    citrus = CitrusCountyAdapter()
    assert citrus.search_url == (
        "https://aca-prod.accela.com/CITRUS/Cap/CapHome.aspx"
        "?module=Building&TabName=Building"
    )


# ── request_headers ───────────────────────────────────────────────────────

def test_request_headers_referer_matches_search_url():
    """Verify Referer header matches search_url for each adapter."""
    from modules.permits.scrapers.adapters.polk_county import PolkCountyAdapter
    from modules.permits.scrapers.adapters.citrus_county import CitrusCountyAdapter

    for cls in (PolkCountyAdapter, CitrusCountyAdapter):
        adapter = cls()
        headers = adapter.request_headers
        assert headers["Referer"] == adapter.search_url
        assert "User-Agent" in headers


# ── _parse_display_date ───────────────────────────────────────────────────

def test_parse_display_date():
    """Valid date, empty, None."""
    from modules.permits.scrapers.adapters.polk_county import PolkCountyAdapter

    adapter = PolkCountyAdapter()
    assert adapter._parse_display_date("03/15/2026") == date(2026, 3, 15)
    assert adapter._parse_display_date("12/31/2025") == date(2025, 12, 31)
    assert adapter._parse_display_date("") is None
    assert adapter._parse_display_date("   ") is None
    # Bad format
    assert adapter._parse_display_date("2026-03-15") is None


# ── _parse_money ──────────────────────────────────────────────────────────

def test_parse_money():
    """$123,456.78, None, empty string."""
    from modules.permits.scrapers.adapters.polk_county import PolkCountyAdapter

    adapter = PolkCountyAdapter()
    assert adapter._parse_money("$123,456.78") == 123456.78
    assert adapter._parse_money("$0.00") == 0.0
    assert adapter._parse_money("250000") == 250000.0
    assert adapter._parse_money(None) is None
    assert adapter._parse_money("") is None


# ── _format_address ───────────────────────────────────────────────────────

def test_format_address():
    """Accela address string parsing."""
    from modules.permits.scrapers.adapters.polk_county import PolkCountyAdapter

    adapter = PolkCountyAdapter()
    assert adapter._format_address("123 MAIN ST, LAKELAND FL 33801") == (
        "123 MAIN ST, LAKELAND, FL 33801"
    )
    # Already clean but no match pattern
    assert adapter._format_address("NO MATCH") == "NO MATCH"
    # Asterisk cleaning
    assert adapter._format_address("123*MAIN*ST, LAKELAND FL 33801") == (
        "123 MAIN ST, LAKELAND, FL 33801"
    )


# ── fetch_permits mocked ────────────────────────────────────────────────

def test_fetch_permits_mocked(monkeypatch):
    """Mock session.get/post with canned Accela HTML, verify parsing end-to-end."""
    from unittest.mock import MagicMock
    from modules.permits.scrapers.adapters.polk_county import PolkCountyAdapter

    # Minimal Accela search results HTML with one record row
    SEARCH_HTML = """
    <html><body>
    <form id="aspnetForm" action="CapHome.aspx" method="post">
      <input type="hidden" name="__VIEWSTATE" value="abc123" />
      <input type="hidden" name="__EVENTTARGET" value="" />
      <input type="hidden" name="__EVENTARGUMENT" value="" />
      <input type="hidden" name="__EVENTVALIDATION" value="xyz" />
      <div>Showing 1-1 of 1 Result</div>
      <table id="ctl00_PlaceHolderMain_dgvPermitList_gdvPermitList">
        <tr><th>Date</th><th>Record Number</th><th>Record Type</th><th>Address</th><th>Status</th></tr>
        <tr>
          <td>03/01/2026</td>
          <td><a href="/POLKCO/Cap/CapDetail.aspx?Module=Building&amp;TabName=Building&amp;capID1=ABC&amp;capID2=00001&amp;capID3=00001">BLD2026-00001</a></td>
          <td>Building/Residential/New/NA</td>
          <td>100 TEST DR, LAKELAND FL 33801</td>
          <td>Issued</td>
        </tr>
      </table>
    </form>
    </body></html>
    """

    DETAIL_HTML = """
    <html><body>
    <div>Parcel Number: 25-29-01-000000-012340</div>
    <div>Job Value($): $350,000.00</div>
    <div>Subdivision: OAK MEADOWS PHASE 2</div>
    <div>Fees</div>
    <div>Applicant: SMITH BUILDERS INC</div>
    <div>Licensed Professional: JOHN DOE</div>
    <div>Project Description: NEW SFR 4BR 2BA</div>
    <div>More Details</div>
    </body></html>
    """

    adapter = PolkCountyAdapter()

    # Build a mock session that returns initial GET (form) then POST (search)
    # then detail GET
    mock_session = MagicMock()

    initial_response = MagicMock()
    initial_response.text = SEARCH_HTML
    initial_response.status_code = 200
    initial_response.raise_for_status = MagicMock()

    search_response = MagicMock()
    search_response.text = SEARCH_HTML
    search_response.status_code = 200
    search_response.url = "https://aca-prod.accela.com/POLKCO/Cap/CapHome.aspx"
    search_response.headers = {"Content-Type": "text/html"}
    search_response.raise_for_status = MagicMock()
    search_response.request = MagicMock()
    search_response.request.method = "POST"

    detail_response = MagicMock()
    detail_response.text = DETAIL_HTML
    detail_response.status_code = 200
    detail_response.url = "https://aca-prod.accela.com/POLKCO/Cap/CapDetail.aspx"
    detail_response.headers = {"Content-Type": "text/html"}
    detail_response.raise_for_status = MagicMock()
    detail_response.request = MagicMock()
    detail_response.request.method = "GET"

    # session.get returns initial page, then detail page
    mock_session.get = MagicMock(side_effect=[initial_response, detail_response])
    mock_session.post = MagicMock(return_value=search_response)
    mock_session.request = MagicMock(return_value=detail_response)
    mock_session.headers = {}

    # Patch build_session to return our mock
    monkeypatch.setattr(adapter, "build_session", lambda **kwargs: mock_session)

    permits = adapter.fetch_permits(
        start_date=date(2026, 3, 1),
        end_date=date(2026, 3, 7),
    )

    assert len(permits) == 1
    p = permits[0]
    assert p["permit_number"] == "BLD2026-00001"
    assert p["address"] == "100 TEST DR, LAKELAND, FL 33801"
    assert p["parcel_id"] == "25-29-01-000000-012340"
    assert p["issue_date"] == "2026-03-01"
    assert p["status"] == "Issued"
    assert p["permit_type"] == "Building/Residential/New/NA"
    assert p["valuation"] == 350000.0
    assert p["raw_subdivision_name"] == "OAK MEADOWS PHASE 2"
    assert p["raw_contractor_name"] == "JOHN DOE"
    assert p["raw_applicant_name"] == "SMITH BUILDERS INC"
    assert p["raw_licensed_professional_name"] == "JOHN DOE"
    # No inspections section in this fixture
    assert p["inspections"] is None


# ── Inspection parsing ──────────────────────────────────────────────────

def test_parse_inspections_table():
    """Verify table-based inspection parsing from detail HTML."""
    from bs4 import BeautifulSoup

    adapter = AccelaCitizenAccessAdapter.__new__(AccelaCitizenAccessAdapter)

    html = """
    <html><body>
    <h3>Inspections</h3>
    <table>
      <tr><th>Type</th><th>Status</th><th>Scheduled Date</th><th>Result</th><th>Inspector</th></tr>
      <tr>
        <td>Foundation</td>
        <td>Completed</td>
        <td>03/10/2026</td>
        <td>Pass</td>
        <td>Bob Smith</td>
      </tr>
      <tr>
        <td>Framing</td>
        <td>Scheduled</td>
        <td>03/20/2026</td>
        <td></td>
        <td>Jane Doe</td>
      </tr>
    </table>
    </body></html>
    """
    soup = BeautifulSoup(html, "html.parser")
    result = adapter._parse_inspections(soup)

    assert result is not None
    assert len(result) == 2
    assert result[0]["type"] == "Foundation"
    assert result[0]["status"] == "Completed"
    assert result[0]["scheduled_date"] == "03/10/2026"
    assert result[0]["result"] == "Pass"
    assert result[0]["inspector"] == "Bob Smith"
    assert result[1]["type"] == "Framing"
    assert result[1]["status"] == "Scheduled"
    assert result[1]["result"] is None


def test_parse_inspections_no_section():
    """Return None when no inspection section exists."""
    from bs4 import BeautifulSoup

    adapter = AccelaCitizenAccessAdapter.__new__(AccelaCitizenAccessAdapter)

    html = """
    <html><body>
    <div>Parcel Number: 12-34-56</div>
    <div>No inspections here</div>
    </body></html>
    """
    soup = BeautifulSoup(html, "html.parser")
    result = adapter._parse_inspections(soup)
    assert result is None


def test_parse_inspections_empty_table():
    """Return None when inspection table has headers but no data rows."""
    from bs4 import BeautifulSoup

    adapter = AccelaCitizenAccessAdapter.__new__(AccelaCitizenAccessAdapter)

    html = """
    <html><body>
    <h3>Inspections</h3>
    <table>
      <tr><th>Type</th><th>Status</th><th>Scheduled Date</th><th>Result</th><th>Inspector</th></tr>
    </table>
    </body></html>
    """
    soup = BeautifulSoup(html, "html.parser")
    result = adapter._parse_inspections(soup)
    assert result is None


def test_parse_inspections_malformed_html_returns_none():
    """Malformed or unexpected HTML returns None, never raises."""
    from bs4 import BeautifulSoup

    adapter = AccelaCitizenAccessAdapter.__new__(AccelaCitizenAccessAdapter)

    # Inspection heading but no table — just random text
    html = """
    <html><body>
    <h3>Inspections</h3>
    <p>Something went wrong with the rendering.</p>
    </body></html>
    """
    soup = BeautifulSoup(html, "html.parser")
    result = adapter._parse_inspections(soup)
    assert result is None


def test_fetch_permits_with_inspections(monkeypatch):
    """Verify inspections are included when detail page contains inspection table."""
    from unittest.mock import MagicMock
    from modules.permits.scrapers.adapters.polk_county import PolkCountyAdapter

    SEARCH_HTML = """
    <html><body>
    <form id="aspnetForm" action="CapHome.aspx" method="post">
      <input type="hidden" name="__VIEWSTATE" value="abc123" />
      <input type="hidden" name="__EVENTTARGET" value="" />
      <input type="hidden" name="__EVENTARGUMENT" value="" />
      <input type="hidden" name="__EVENTVALIDATION" value="xyz" />
      <div>Showing 1-1 of 1 Result</div>
      <table id="ctl00_PlaceHolderMain_dgvPermitList_gdvPermitList">
        <tr><th>Date</th><th>Record Number</th><th>Record Type</th><th>Address</th><th>Status</th></tr>
        <tr>
          <td>03/01/2026</td>
          <td><a href="/POLKCO/Cap/CapDetail.aspx?capID1=X&amp;capID2=Y&amp;capID3=Z">BLD2026-00099</a></td>
          <td>Building/Residential/New/NA</td>
          <td>200 OAK AVE, LAKELAND FL 33801</td>
          <td>Issued</td>
        </tr>
      </table>
    </form>
    </body></html>
    """

    DETAIL_HTML_WITH_INSPECTIONS = """
    <html><body>
    <div>Parcel Number: 99-99-99-000000-000001</div>
    <div>Job Value($): $250,000.00</div>
    <div>Subdivision: TEST ACRES</div>
    <div>Fees</div>
    <div>Applicant: TEST BUILDER</div>
    <div>Licensed Professional: TEST PRO</div>
    <div>Project Description: NEW SFR</div>
    <h4>Inspections</h4>
    <table>
      <tr><th>Type</th><th>Status</th><th>Scheduled Date</th><th>Result</th><th>Inspector</th></tr>
      <tr><td>Slab</td><td>Completed</td><td>02/15/2026</td><td>Pass</td><td>Inspector A</td></tr>
      <tr><td>Electrical</td><td>Pending</td><td>03/05/2026</td><td></td><td>Inspector B</td></tr>
    </table>
    <div>More Details</div>
    </body></html>
    """

    adapter = PolkCountyAdapter()
    mock_session = MagicMock()

    initial_response = MagicMock()
    initial_response.text = SEARCH_HTML
    initial_response.status_code = 200
    initial_response.raise_for_status = MagicMock()

    search_response = MagicMock()
    search_response.text = SEARCH_HTML
    search_response.status_code = 200
    search_response.url = "https://aca-prod.accela.com/POLKCO/Cap/CapHome.aspx"
    search_response.headers = {"Content-Type": "text/html"}
    search_response.raise_for_status = MagicMock()
    search_response.request = MagicMock()
    search_response.request.method = "POST"

    detail_response = MagicMock()
    detail_response.text = DETAIL_HTML_WITH_INSPECTIONS
    detail_response.status_code = 200
    detail_response.url = "https://aca-prod.accela.com/POLKCO/Cap/CapDetail.aspx"
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
        end_date=date(2026, 3, 7),
    )

    assert len(permits) == 1
    p = permits[0]
    assert p["inspections"] is not None
    assert len(p["inspections"]) == 2
    assert p["inspections"][0]["type"] == "Slab"
    assert p["inspections"][0]["result"] == "Pass"
    assert p["inspections"][1]["type"] == "Electrical"
    assert p["inspections"][1]["status"] == "Pending"
    assert p["inspections"][1]["result"] is None
