"""Unit tests for the Haines City iWorQ adapter.

Models ``tests/test_davenport_adapter.py``:
  1. Instantiation / attribute sanity.
  2. Row extraction against a trimmed + fully-anonymized HTML fixture that
     mirrors the live 10-column Haines City grid.
  3. Filter behavior — Haines has no permit-type column, so the base-class
     residential/excluded vocabulary still governs the *detail-page*
     Description filter.
"""

from __future__ import annotations

from bs4 import BeautifulSoup

from modules.permits.scrapers.adapters.haines_city import HainesCityAdapter
from modules.permits.scrapers.adapters.iworq import IworqAdapter


# Anonymized fixture mirroring the live Haines City grid row structure
# (1 TH for the permit # plus 10 TDs).  Every real-world value has been
# replaced: permit #, detail-URL hash, addresses, and project names are all
# synthetic stand-ins.
HAINES_CITY_ROW_HTML = """
<table class="table table-sm">
  <tr>
    <th>Permit #</th>
    <th>Date</th>
    <th>Planning/Zoning Status</th>
    <th>Application Status</th>
    <th>Fire Marshall Review Status</th>
    <th>Building Plan Review Status</th>
    <th>Site Address</th>
    <th>Site City, State Zip Code</th>
    <th>Project Name</th>
    <th>Request An Inspection</th>
    <th>View</th>
  </tr>
  <tr>
    <th class="permit-open"
        data-label="Permit #"
        data-route="https://haines.portal.iworq.net/HAINES/permit/600/99999001"
        scope="row">
      <a href="https://haines.portal.iworq.net/HAINES/permit/600/99999001">PERMIT-0001</a>
    </th>
    <td data-label="Date">03/15/2026</td>
    <td>Not Required</td>
    <td data-label="Application Status">Issued</td>
    <td>Not Required</td>
    <td data-label="Building Plan Review Status">Approved</td>
    <td data-label="Site Address">123 FAKE ST</td>
    <td data-label="Site City, State Zip Code">HAINES CITY, FL 33844</td>
    <td data-label="Project Name">SAMPLE SUBDIVISION LOT 42</td>
    <td data-label="Inspection"></td>
    <td></td>
  </tr>
</table>
"""


# ── Instantiation ─────────────────────────────────────────────────────────

def test_haines_city_instantiates_with_expected_attributes():
    adapter = HainesCityAdapter()
    assert adapter.slug == "haines-city"
    assert adapter.display_name == "Haines City"
    assert adapter.search_url == "https://haines.portal.iworq.net/HAINES/permits/600"
    assert adapter.mode == "live"
    assert adapter.bootstrap_lookback_days == 120
    assert adapter.rolling_overlap_days == 14
    assert isinstance(adapter, IworqAdapter)
    # Inherits residential filter vocabulary from IworqAdapter
    assert "single family" in adapter.residential_type_terms
    assert "sfr" in adapter.residential_type_terms


# ── Row extraction (10-column layout, no type column) ────────────────────

def test_haines_city_row_extraction_maps_10_column_layout():
    adapter = HainesCityAdapter()
    soup = BeautifulSoup(HAINES_CITY_ROW_HTML, "html.parser")
    table = soup.select_one("table.table.table-sm")
    assert table is not None

    data_row = table.find_all("tr")[1]
    permit_cell = data_row.find("th")
    cells = data_row.find_all("td")

    # Haines grid: 10 TDs after the permit-# TH (Date, Planning/Zoning Status,
    # Application Status, Fire Marshall, Building Plan Review, Site Address,
    # Site City/State/Zip, Project Name, Request An Inspection, View).
    assert len(cells) == 10

    fields = adapter._extract_row_fields(permit_cell, cells)
    assert fields is not None

    assert fields["permit_number"] == "PERMIT-0001"
    assert fields["issue_date_str"] == "03/15/2026"
    # No type column on Haines — permit_type must be None so the
    # IworqAdapter base class knows to defer to the detail page.
    assert fields["permit_type"] is None
    # Address concatenated: street + ", " + city/state/zip
    assert fields["address"] == "123 FAKE ST, HAINES CITY, FL 33844"
    # Status pulled from Application Status column
    assert fields["status"] == "Issued"
    # Contractor/valuation are detail-page-only on Haines
    assert fields["contractor_hint"] is None
    assert fields["valuation_hint"] is None
    assert fields["detail_url"] == (
        "https://haines.portal.iworq.net/HAINES/permit/600/99999001"
    )


def test_haines_city_row_extraction_skips_short_rows():
    """Rows with fewer than 7 TDs should be skipped (returns None)."""
    adapter = HainesCityAdapter()
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


# ── Deferred type filter (description from detail page) ───────────────────

def test_haines_city_type_filter_delegates_to_base_vocabulary():
    """Haines has no type column; verify the inherited filter still works
    against the kind of Description text the detail page returns."""
    adapter = HainesCityAdapter()

    # Residential descriptions we expect to keep.
    assert adapter._is_target_permit_type("NEW SFR")
    assert adapter._is_target_permit_type("Single Family Residence")
    assert adapter._is_target_permit_type("New Dwelling")

    # Non-residential descriptions should be excluded.
    assert not adapter._is_target_permit_type("Roof replacement")
    assert not adapter._is_target_permit_type("POOL")
    assert not adapter._is_target_permit_type("Sign")
    assert not adapter._is_target_permit_type("Fence")
    assert not adapter._is_target_permit_type("")
