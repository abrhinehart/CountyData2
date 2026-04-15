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
    <div>Applicant: John Smith SMITH BUILDERS INC Work Phone: 8135551234 jsmith@smithbuilders.com</div>
    <div>Licensed Professional: JOHN DOE doe@abcroofing.com ABC ROOFING LLC 100 PARK AVE ORLANDO, FL, 32801 Roofing CCC1234567 View Additional Licensed Professionals&gt;&gt; 1) Sub Plumber sub@plumb.com SUB PLUMBING LLC 200 OAK AVE TAMPA, FL, 33601 Plumbing CFC2222222 2) Sub Electric esub@elec.com SUB ELECTRIC LLC 300 PINE ST MIAMI, FL, 33101 Electric With Alarm EC13099999</div>
    <div>Project Description: NEW SFR 4BR 2BA</div>
    <h1><span>Owner:</span></h1>
    <span>
      <table><tr><td>
        <table><tr><td>
          <table>
            <tr><td>SMITH FAMILY TRUST<Span style='color:blue';> *</Span></td></tr>
            <tr><td>500 BEACON ST</td></tr>
            <tr><td>BOSTON MA 02108</td></tr>
            <tr><td>OWNER: SMITH FAMILY TRUST</td></tr>
          </table>
        </td></tr></table>
      </td></tr></table>
    </span>
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
    # Existing applicant/LP regexes are greedy-section-capture (ACCELA-03
    # shape): raw_applicant_name captures the full applicant block, and
    # raw_contractor_name falls back to the LP name when applicant is distinct.
    assert p["raw_applicant_name"] == (
        "John Smith SMITH BUILDERS INC Work Phone: 8135551234 "
        "jsmith@smithbuilders.com"
    )
    assert p["raw_licensed_professional_name"] == (
        "JOHN DOE doe@abcroofing.com ABC ROOFING LLC 100 PARK AVE "
        "ORLANDO, FL, 32801 Roofing CCC1234567"
    )
    assert p["raw_contractor_name"] == p["raw_licensed_professional_name"]
    assert p["raw_owner_name"] == "SMITH FAMILY TRUST"
    assert p["raw_owner_address"] == "500 BEACON ST BOSTON MA 02108"
    # ACCELA-04: structured sub-fields from Applicant / Licensed Professional.
    assert p["raw_applicant_company"] == "John Smith SMITH BUILDERS INC"
    assert p["raw_applicant_address"] is None  # no applicant address in synth
    assert p["raw_applicant_phone"] == "8135551234"
    assert p["raw_applicant_email"] == "jsmith@smithbuilders.com"
    assert p["raw_contractor_license_number"] == "CCC1234567"
    assert p["raw_contractor_license_type"] == "Roofing"
    # ACCELA-04a: subcontractor list captured from "View Additional Licensed
    # Professionals>>" segment, serialized as "NAME|LICENSE|TYPE; ..." per LP.
    assert p["raw_additional_licensed_professionals"] is not None
    parts = p["raw_additional_licensed_professionals"].split("; ")
    assert len(parts) == 2
    assert parts[0].startswith("Sub Plumber|")
    assert "|CFC2222222|" in parts[0]
    assert parts[0].endswith("|Plumbing")
    assert parts[1].startswith("Sub Electric|")
    assert "|EC13099999|" in parts[1]
    assert parts[1].endswith("|Electric With Alarm")
    # Polk has inspections_on_separate_tab=True, so base adapter short-circuits
    # and emits an empty list regardless of detail-page contents (ACCELA-05).
    assert p["inspections"] == []


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
    """Verify inspections are included when detail page contains inspection table.

    Uses a throwaway subclass that opts out of the separate-tab behavior so the
    inline-parse path is exercised (Polk/Citrus now default to skipping it;
    see ACCELA-05).
    """
    from unittest.mock import MagicMock

    class _InlineInspectionsAccela(AccelaCitizenAccessAdapter):
        slug = "inline-test"
        display_name = "Inline Test"
        agency_code = "POLKCO"
        target_record_type = "Building/Residential/New/NA"
        inspections_on_separate_tab = False  # opt-in to the inline-parse path

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

    adapter = _InlineInspectionsAccela()
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
    # ACCELA-03: no Owner block in this fixture — regex must not spuriously match.
    assert p["raw_owner_name"] is None
    assert p["raw_owner_address"] is None


def test_fetch_permits_inspections_skipped_for_separate_tab_agencies(monkeypatch):
    """Pin ACCELA-05 + ACCELA-06 behavior: Polk (inspections_on_separate_tab=True)
    MUST emit inspections: [] even when the detail page contains an inline
    inspection table, because anonymous Accela ACA does not expose real
    inspection rows (see docs/api-maps/accela-rest-probe-findings.md).
    """
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
    </table>
    <div>More Details</div>
    </body></html>
    """

    adapter = PolkCountyAdapter()
    assert adapter.inspections_on_separate_tab is True

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
    # Even though the detail page DOES have an inline inspection table,
    # the Polk adapter opts out via inspections_on_separate_tab=True.
    assert p["inspections"] == []
    # ACCELA-03: no Owner block in this fixture — regex must not spuriously match.
    assert p["raw_owner_name"] is None
    assert p["raw_owner_address"] is None


# ── Owner regex extraction (ACCELA-03) ────────────────────────────────────

def test_parse_owner_from_flat_text():
    """Exercise the owner_name / owner_address regexes against canned flat text
    slices of the Accela CapDetail Owner section.  Pins the regex shape against
    the live Polk BR-2026-2894 recon and three synthetic variants.
    """
    adapter = AccelaCitizenAccessAdapter.__new__(AccelaCitizenAccessAdapter)

    # Case 1: standard LLC with asterisk + duplicate OWNER label (live Polk shape).
    polk_text = (
        "Project Description: new construction "
        "Owner: LGI HOMES FLORIDA LLC * 1450 LAKE ROBBINS DR STE 430 "
        "THE WOODLANDS TX 77380 OWNER: LGI HOMES FLORIDA LLC More Details"
    )
    name = adapter._extract_match(AccelaCitizenAccessAdapter.owner_name_pattern, polk_text)
    addr = adapter._extract_match(AccelaCitizenAccessAdapter.owner_address_pattern, polk_text)
    assert name == "LGI HOMES FLORIDA LLC"
    assert addr == "1450 LAKE ROBBINS DR STE 430 THE WOODLANDS TX 77380"

    # Case 2: no-asterisk fallback — name captured via fallback pattern.
    no_ast_text = "Owner: JANE DOE More Details"
    name = adapter._extract_match(AccelaCitizenAccessAdapter.owner_name_pattern, no_ast_text)
    assert name is None  # primary pattern requires asterisk
    fallback_name = adapter._extract_match(
        AccelaCitizenAccessAdapter.owner_fallback_pattern, no_ast_text
    )
    assert fallback_name == "JANE DOE"

    # Case 3: Owner section entirely absent — both patterns return None.
    no_owner_text = "Project Description: NEW SFR More Details"
    assert adapter._extract_match(AccelaCitizenAccessAdapter.owner_name_pattern, no_owner_text) is None
    assert adapter._extract_match(AccelaCitizenAccessAdapter.owner_address_pattern, no_owner_text) is None
    assert adapter._extract_match(AccelaCitizenAccessAdapter.owner_fallback_pattern, no_owner_text) is None

    # Case 4: individual owner at FL address — free-form address captured as string.
    individual_text = (
        "Owner: JOHN Q PUBLIC * 123 MAIN ST LAKELAND FL 33801 "
        "OWNER: JOHN Q PUBLIC More Details"
    )
    name = adapter._extract_match(AccelaCitizenAccessAdapter.owner_name_pattern, individual_text)
    addr = adapter._extract_match(AccelaCitizenAccessAdapter.owner_address_pattern, individual_text)
    assert name == "JOHN Q PUBLIC"
    assert addr == "123 MAIN ST LAKELAND FL 33801"


# ── Contact regex extraction (ACCELA-04) ──────────────────────────────────

def test_parse_contact_fields_from_flat_text():
    """Exercise applicant/contractor sub-field regexes against flat-text slices
    of the Accela CapDetail Applicant and Licensed Professional sections.
    Pins the pattern shape against the live Polk BR-2026-2894 recon (see
    docs/api-maps/polk-county-accela.md §4).
    """
    adapter = AccelaCitizenAccessAdapter.__new__(AccelaCitizenAccessAdapter)
    A = AccelaCitizenAccessAdapter

    # Case 1: live-Polk shape — all six fields present (BR-2026-2894 extract).
    polk_text = (
        "Applicant: Jeff Cunningham LGI Homes Work Phone: 8137315791 "
        "jeff.cunningham@lgihomes.com Licensed Professional: Jason Lee James "
        "permitting@mechanicalone.com MECHANICAL ONE, LLC 307 CRANES ROOST BLVD "
        "ALTAMONTE SPRINGS, FL, 32701 Air Condition Class A CAC1820196 "
        "View Additional Licensed Professionals>> 1) Daniel A Williams "
        "trey.williams@lgihomes.com LGI HOMES - FLORIDA, LLC 989 WEDGEWOOD SE "
        "WINTER HAVEN, FL, 33880 Building CBC1258722 Project Description: new construction"
    )
    assert adapter._extract_match(A.applicant_company_pattern, polk_text) == "Jeff Cunningham LGI Homes"
    assert adapter._extract_match(A.applicant_address_pattern, polk_text) is None
    assert adapter._extract_match(A.applicant_phone_pattern, polk_text) == "8137315791"
    assert adapter._extract_match(A.applicant_email_pattern, polk_text) == "jeff.cunningham@lgihomes.com"
    # Primary LP only — must NOT bleed into subcontractor CBC1258722.
    assert adapter._extract_match(A.contractor_license_number_pattern, polk_text) == "CAC1820196"
    assert adapter._extract_match(A.contractor_license_type_pattern, polk_text) == "Air Condition Class A"

    # Case 2: partial — applicant has name+email but no phone; LP absent.
    partial_text = (
        "Applicant: JANE SMITH ACME BUILDERS jane@acme.com "
        "Licensed Professional: foo Project Description: NEW SFR"
    )
    assert adapter._extract_match(A.applicant_company_pattern, partial_text) == "JANE SMITH ACME BUILDERS"
    assert adapter._extract_match(A.applicant_phone_pattern, partial_text) is None
    assert adapter._extract_match(A.applicant_email_pattern, partial_text) == "jane@acme.com"
    assert adapter._extract_match(A.contractor_license_number_pattern, partial_text) is None
    assert adapter._extract_match(A.contractor_license_type_pattern, partial_text) is None

    # Case 3: no Applicant / LP section — all patterns return None cleanly.
    empty_text = "Parcel Number: 12-34-56 Project Description: NEW SFR More Details"
    assert adapter._extract_match(A.applicant_company_pattern, empty_text) is None
    assert adapter._extract_match(A.applicant_address_pattern, empty_text) is None
    assert adapter._extract_match(A.applicant_phone_pattern, empty_text) is None
    assert adapter._extract_match(A.applicant_email_pattern, empty_text) is None
    assert adapter._extract_match(A.contractor_license_number_pattern, empty_text) is None
    assert adapter._extract_match(A.contractor_license_type_pattern, empty_text) is None

    # Case 4: LP with "View Additional Licensed Professionals>>" terminator —
    # subcontractor license codes MUST NOT leak into the primary contractor
    # license fields.  Regression guard for the ACCELA-04 terminator anchor.
    subcontractors_text = (
        "Licensed Professional: Alice Primary alice@primary.com PRIMARY CO LLC "
        "100 MAIN ST TAMPA, FL, 33601 Building CBC9999999 "
        "View Additional Licensed Professionals>> 1) Bob Sub bob@sub.com "
        "SUB LLC 200 OAK AVE MIAMI, FL, 33101 Roofing CCC1111111 "
        "Project Description: NEW SFR"
    )
    assert adapter._extract_match(A.contractor_license_number_pattern, subcontractors_text) == "CBC9999999"
    assert adapter._extract_match(A.contractor_license_type_pattern, subcontractors_text) == "Building"


# ── Subcontractor / Additional LP parsing (ACCELA-04a) ────────────────────

def test_parse_additional_lps():
    """Exercise _parse_additional_lps against four shapes:
       1) live-Polk multi-sub format (BR-2026-2659 — 4 trade subs).
       2) single-LP segment.
       3) empty / None segment.
       4) malformed chunk (no license number — must drop it without raising).
    """
    adapter = AccelaCitizenAccessAdapter.__new__(AccelaCitizenAccessAdapter)

    # Case 1: live-Polk shape (4 subs from BR-2026-2659).
    polk_segment = (
        "1) Gonzalo Rubin permitting@level-roofing.com LEVEL ROOFING SOLUTIONS, "
        "LLC 1401 BEULAH RD WINTER GARDEN, FL, 34787 Roofing CCC1336147 "
        "2) Alexis Lopez dp@dogplumbing.com DOG PLUMBING LLC 1590 W 73 STREET "
        "MIAMI, FL, 33166 Plumbing CFC1431566 "
        "3) DANIEL PATRICK MCKEARAN danny@duckyjohnson.com DUCKY RECOVERY LLC "
        "5333 RIVER ROAD HARAHAN, LA, 70123 General CGC1526755 "
        "4) Colby Anthony Miller camiller2020@gmail.com SOUTHEASTERN ELECTRICAL "
        "CONTRACTOR LLC 9704 GALETON COURT WEST MOBILE, AL, 36695 "
        "Electric With Alarm EC13015339"
    )
    result = adapter._parse_additional_lps(polk_segment)
    assert result is not None
    parts = result.split("; ")
    assert len(parts) == 4
    # Each part is NAME|LICENSE|TYPE.
    for part in parts:
        assert part.count("|") == 2
    # Spot-check first and last entries.
    assert parts[0].startswith("Gonzalo Rubin|")
    assert "|CCC1336147|" in parts[0]
    assert parts[0].endswith("|Roofing")
    assert parts[3].startswith("Colby Anthony Miller|")
    assert "|EC13015339|" in parts[3]
    assert parts[3].endswith("|Electric With Alarm")

    # Case 2: single-LP segment.
    single_segment = (
        "1) Jane Doe jane@xyz.com XYZ CONTRACTING 100 MAIN ST OCALA, FL, 34470 "
        "Plumbing CFC9999999"
    )
    result = adapter._parse_additional_lps(single_segment)
    assert result is not None
    assert "; " not in result  # only one record
    assert result.startswith("Jane Doe|")
    assert "|CFC9999999|" in result
    assert result.endswith("|Plumbing")

    # Case 3: empty / None.
    assert adapter._parse_additional_lps(None) is None
    assert adapter._parse_additional_lps("") is None
    assert adapter._parse_additional_lps("   ") is None

    # Case 4: malformed chunk (no FL license number at end) → dropped.
    malformed_segment = "1) Bogus Name no email no company plain text"
    assert adapter._parse_additional_lps(malformed_segment) is None


# ── ACCELA-01 record-type iteration ───────────────────────────────────────

def test_fetch_permits_iterates_multiple_record_types(monkeypatch):
    """Verify the adapter loops over target_record_types and dedups by
    permit_number across types.  Mock _fetch_range to return one unique permit
    per record type and assert the final list has one entry per type.
    """
    from modules.permits.scrapers.adapters.polk_county import PolkCountyAdapter

    adapter = PolkCountyAdapter()
    # Sanity-check the override: Polk now has 9 curated record types.
    assert len(adapter._resolve_record_types()) == 9

    submitted: list[str] = []

    def fake_fetch_range(self, session, start_date, end_date, record_type=None):
        submitted.append(record_type)
        # one synthetic permit per record type, keyed by full record-type path
        # (so "Building/Residential/New" and "Building/Commercial/New" don't collide).
        return [{
            "permit_number": f"FAKE-{record_type.replace('/', '_')}",
            "address": "1 TEST DR, LAKELAND, FL 33801",
            "issue_date": "2026-04-01",
            "permit_type": record_type,
        }]

    monkeypatch.setattr(adapter, "_fetch_range", fake_fetch_range.__get__(adapter, type(adapter)))
    # Avoid 2s sleeps in unit tests.
    adapter.record_type_delay = 0
    # Avoid actually building a session.
    monkeypatch.setattr(adapter, "build_session", lambda **kwargs: object())

    permits = adapter.fetch_permits(
        start_date=date(2026, 3, 1),
        end_date=date(2026, 4, 1),
    )

    # Each record type submitted exactly once.
    assert submitted == list(adapter.target_record_types)
    # 9 unique permits emitted (one per record type).
    assert len(permits) == 9
    permit_numbers = {p["permit_number"] for p in permits}
    assert len(permit_numbers) == 9


def test_fetch_permits_back_compat_single_record_type(monkeypatch):
    """Adapters that don't set ``target_record_types`` (Citrus / Lake Alfred /
    Winter Haven) MUST keep their existing single-type behavior.  Resolve
    falls back to ``(target_record_type,)``.
    """
    from modules.permits.scrapers.adapters.citrus_county import CitrusCountyAdapter

    adapter = CitrusCountyAdapter()
    # Fallback behavior: resolves to single-element tuple.
    resolved = adapter._resolve_record_types()
    assert resolved == (adapter.target_record_type,)


def test_fetch_permits_per_record_type_exception_does_not_abort(monkeypatch):
    """One bad record type (e.g. portal returns malformed HTML or transient
    error) must NOT prevent the surviving types from yielding permits.
    """
    from modules.permits.scrapers.adapters.polk_county import PolkCountyAdapter

    adapter = PolkCountyAdapter()
    adapter.record_type_delay = 0

    def fake_fetch_range(self, session, start_date, end_date, record_type=None):
        if "Pool" in record_type:
            raise RuntimeError("simulated portal 500")
        return [{
            "permit_number": f"OK-{record_type.replace('/', '_')}",
            "address": "x", "issue_date": "2026-04-01", "permit_type": record_type,
        }]

    monkeypatch.setattr(adapter, "_fetch_range", fake_fetch_range.__get__(adapter, type(adapter)))
    monkeypatch.setattr(adapter, "build_session", lambda **kwargs: object())

    permits = adapter.fetch_permits(start_date=date(2026, 3, 1), end_date=date(2026, 4, 1))
    # 9 record types, 1 raises → 8 surviving permits.
    assert len(permits) == 8
    assert all("OK-" in p["permit_number"] for p in permits)
