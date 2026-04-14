"""Unit tests for the Davenport iWorQ adapter.

Models the patterns in ``tests/test_accela_citizen_access_adapter.py``:
  1. Instantiation / attribute sanity.
  2. Row extraction against a trimmed + anonymized HTML fixture that
     mirrors the live 10-column Davenport table.
  3. ``_is_target_permit_type`` filter behavior.
"""

from __future__ import annotations

from bs4 import BeautifulSoup

from modules.permits.scrapers.adapters.davenport import DavenportAdapter
from modules.permits.scrapers.adapters.iworq import IworqAdapter


# Anonymized fixture mirroring the live Davenport search-results row
# structure (1 data row, 10 TDs after the permit-number TH). Real values
# scrubbed: permit number, contractor/applicant, address, project cost,
# and detail URL hash all replaced with synthetic stand-ins.
DAVENPORT_ROW_HTML = """
<table class="table table-sm">
  <tr>
    <th>Permit #</th>
    <th>Date</th>
    <th>Primary Contractor</th>
    <th>Applicant Name</th>
    <th>Site Address</th>
    <th>Lot</th>
    <th>Description</th>
    <th>Project Cost</th>
    <th>Permit Status</th>
    <th>Request An Inspection</th>
    <th>View</th>
  </tr>
  <tr>
    <th class="permit-open"
        data-label="Permit #"
        data-route="https://portal.iworq.net/DAVENPORT/permit/600/99999001"
        scope="row">
      <a href="https://portal.iworq.net/DAVENPORT/permit/600/99999001">PERMIT-0001</a>
    </th>
    <td data-label="Date">03/15/2026</td>
    <td data-label="Primary Contractor">SAMPLE CONTRACTOR INC</td>
    <td data-label="Applicant Name">SAMPLE APPLICANT LLC</td>
    <td data-label="Site Address">123 FAKE ST</td>
    <td data-label="Lot">42</td>
    <td data-label="Description">NEW SFR - 4BED, 2 BATH - 1 STORY</td>
    <td data-label="Project Cost">$275,000.00</td>
    <td data-label="Permit Status">Issued</td>
    <td data-label="Request An Inspection"></td>
    <td data-label="View"></td>
  </tr>
</table>
"""


# ── Instantiation ─────────────────────────────────────────────────────────

def test_davenport_instantiates_with_expected_attributes():
    adapter = DavenportAdapter()
    assert adapter.slug == "davenport"
    assert adapter.display_name == "Davenport"
    assert adapter.search_url == "https://portal.iworq.net/DAVENPORT/permits/600"
    assert adapter.mode == "live"
    assert adapter.bootstrap_lookback_days == 120
    assert adapter.rolling_overlap_days == 14
    assert isinstance(adapter, IworqAdapter)
    # Inherits residential filter vocabulary
    assert "single family" in adapter.residential_type_terms
    assert "sfr" in adapter.residential_type_terms


# ── Row extraction (10-column layout) ─────────────────────────────────────

def test_davenport_row_extraction_maps_10_column_layout():
    adapter = DavenportAdapter()
    soup = BeautifulSoup(DAVENPORT_ROW_HTML, "html.parser")
    table = soup.select_one("table.table.table-sm")
    assert table is not None

    data_row = table.find_all("tr")[1]
    permit_cell = data_row.find("th")
    cells = data_row.find_all("td")

    # Sanity: 10 TDs (Date, Primary Contractor, Applicant Name, Site Address,
    # Lot, Description, Project Cost, Permit Status, Request An Inspection,
    # View)
    assert len(cells) == 10

    fields = adapter._extract_row_fields(permit_cell, cells)
    assert fields is not None

    assert fields["permit_number"] == "PERMIT-0001"
    assert fields["issue_date_str"] == "03/15/2026"
    assert fields["permit_type"] == "NEW SFR - 4BED, 2 BATH - 1 STORY"
    assert fields["address"] == "123 FAKE ST"
    assert fields["status"] == "Issued"
    assert fields["contractor_hint"] == "SAMPLE CONTRACTOR INC"
    assert fields["valuation_hint"] == "$275,000.00"
    assert fields["detail_url"] == (
        "https://portal.iworq.net/DAVENPORT/permit/600/99999001"
    )


def test_davenport_row_extraction_skips_short_rows():
    """Rows with fewer than 8 TDs should be skipped (returns None)."""
    adapter = DavenportAdapter()
    short_html = """
    <table class="table table-sm">
      <tr>
        <th><a href="x">PERMIT-0002</a></th>
        <td>03/16/2026</td>
        <td>A</td>
        <td>B</td>
      </tr>
    </table>
    """
    soup = BeautifulSoup(short_html, "html.parser")
    data_row = soup.find_all("tr")[0]
    permit_cell = data_row.find("th")
    cells = data_row.find_all("td")
    assert adapter._extract_row_fields(permit_cell, cells) is None


# ── Permit-type filter ────────────────────────────────────────────────────

def test_davenport_permit_type_filter():
    adapter = DavenportAdapter()

    # Residential permits we care about
    assert adapter._is_target_permit_type("NEW SFR - 4BED, 2 BATH - 1 STORY")
    assert adapter._is_target_permit_type("Single Family Residence")
    assert adapter._is_target_permit_type("NEW DWELLING")

    # Non-residential / excluded
    assert not adapter._is_target_permit_type("Roof replacement")
    assert not adapter._is_target_permit_type("POOL / SPA")
    assert not adapter._is_target_permit_type("Sign Permit")
    assert not adapter._is_target_permit_type("Electrical change out")
    assert not adapter._is_target_permit_type("Fence")
    assert not adapter._is_target_permit_type("Demolition")

    # Bare/empty description: not a residential term, filtered out.
    assert not adapter._is_target_permit_type("")
    assert not adapter._is_target_permit_type("Commercial Addition")
