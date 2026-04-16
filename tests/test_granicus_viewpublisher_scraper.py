"""Unit tests for modules.commission.scrapers.granicus_viewpublisher.

Mirrors the structure of tests/test_granicus_scraper.py. Fixtures reflect the
real Winter Haven ViewPublisher HTML shape verified live on 2026-04-16:

- <tr class="listingRow"> rows carry meeting data.
- A <td scope="row"> Name cell holds the specific meeting sub-title.
- Archived rows live inside <div class="CollapsiblePanel"> whose
  <div class="CollapsiblePanelTab"> is the authoritative body label.
- Upcoming-events rows have NO CollapsiblePanel parent.
- CloudFront PDFs live at d3n9y02raazwpg.cloudfront.net/<tenant>/<uuid>.pdf.
"""

import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from modules.commission.scrapers.base import DocumentListing, PlatformScraper
from modules.commission.scrapers.granicus_viewpublisher import ViewPublisherScraper


# --- Fixture HTML ----------------------------------------------------------

VIEWPUBLISHER_HTML_MINIMAL = """
<html><body>
<h2>Available Archives</h2>

<div class="CollapsiblePanel">
  <div class="CollapsiblePanelTab">City Commission</div>
  <div class="CollapsiblePanelContent">
    <div class="TabbedPanelsContentGroup">
      <div class="TabbedPanelsContent">
        <table class="listingTable"><tbody>
          <tr class="listingRow">
            <td scope="row" class="listItem">City Commission Meeting</td>
            <td class="listItem">Mar&nbsp;23,&nbsp;2026 - 06:00&nbsp;PM</td>
            <td class="listItem">
              <a href="//winterhaven-fl.granicus.com/AgendaViewer.php?view_id=1&amp;clip_id=347">Agenda</a>
            </td>
            <td class="listItem"></td>
            <td class="listItem">
              <a href="https://d3n9y02raazwpg.cloudfront.net/winterhaven-fl/aaaa1111-2222-3333-4444-555566667777.pdf">Agenda Packet</a>
            </td>
          </tr>
          <tr class="listingRow">
            <td scope="row" class="listItem">City Commission Agenda Review Session</td>
            <td class="listItem">Mar&nbsp;18,&nbsp;2026 - 03:00&nbsp;PM</td>
            <td class="listItem">
              <a href="//winterhaven-fl.granicus.com/AgendaViewer.php?view_id=1&amp;clip_id=337">Agenda</a>
            </td>
            <td class="listItem"></td>
            <td class="listItem"></td>
          </tr>
        </tbody></table>
      </div>
    </div>
  </div>
</div>

<div class="CollapsiblePanel">
  <div class="CollapsiblePanelTab">Planning Commission</div>
  <div class="CollapsiblePanelContent">
    <div class="TabbedPanelsContentGroup">
      <div class="TabbedPanelsContent">
        <table class="listingTable"><tbody>
          <tr class="listingRow">
            <td scope="row" class="listItem">Planning Commission Meeting</td>
            <td class="listItem">Mar&nbsp;3,&nbsp;2026 - 06:00&nbsp;PM</td>
            <td class="listItem">
              <a href="//winterhaven-fl.granicus.com/AgendaViewer.php?view_id=1&amp;clip_id=316">Agenda</a>
            </td>
            <td class="listItem"></td>
            <td class="listItem">
              <a href="https://d3n9y02raazwpg.cloudfront.net/winterhaven-fl/bbbb1111-2222-3333-4444-555566667777.pdf">Agenda Packet</a>
            </td>
          </tr>
        </tbody></table>
      </div>
    </div>
  </div>
</div>

</body></html>
"""


VIEWPUBLISHER_HTML_WITH_UPCOMING = """
<html><body>

<h2>Upcoming Events</h2>
<table class="listingTable"><tbody>
  <tr class="listingRow">
    <td scope="row" class="listItem">City Commission Meeting</td>
    <td class="listItem">Apr&nbsp;13,&nbsp;2026 - 06:00&nbsp;PM</td>
    <td class="listItem">
      <a href="AgendaViewer.php?view_id=1&amp;event_id=5500">Agenda</a>
    </td>
    <td class="listItem">
      <a href="https://d3n9y02raazwpg.cloudfront.net/winterhaven-fl/up00cc01-2222-3333-4444-555566667777.pdf">Agenda Packet</a>
    </td>
  </tr>
  <tr class="listingRow">
    <td scope="row" class="listItem">Community Redevelopment Agency (CRA) Downtown Advisory Committee Meeting</td>
    <td class="listItem">Apr&nbsp;20,&nbsp;2026 - 04:00&nbsp;PM</td>
    <td class="listItem">
      <a href="AgendaViewer.php?view_id=1&amp;event_id=5501">Agenda</a>
    </td>
    <td class="listItem">
      <a href="https://d3n9y02raazwpg.cloudfront.net/winterhaven-fl/cra00dac-2222-3333-4444-555566667777.pdf">Agenda Packet</a>
    </td>
  </tr>
</tbody></table>

</body></html>
"""


VIEWPUBLISHER_HTML_WITH_CRA_PANEL = """
<html><body>
<h2>Available Archives</h2>

<div class="CollapsiblePanel">
  <div class="CollapsiblePanelTab">Community Redevelopment Agency (CRA) Board</div>
  <div class="CollapsiblePanelContent">
    <div class="TabbedPanelsContentGroup">
      <div class="TabbedPanelsContent">
        <table class="listingTable"><tbody>
          <tr class="listingRow">
            <td scope="row" class="listItem">CRA Board Meeting</td>
            <td class="listItem">Feb&nbsp;15,&nbsp;2026 - 05:00&nbsp;PM</td>
            <td class="listItem">
              <a href="//winterhaven-fl.granicus.com/AgendaViewer.php?view_id=1&amp;clip_id=200">Agenda</a>
            </td>
            <td class="listItem"></td>
            <td class="listItem">
              <a href="https://d3n9y02raazwpg.cloudfront.net/winterhaven-fl/crapnl01-2222-3333-4444-555566667777.pdf">Agenda Packet</a>
            </td>
          </tr>
        </tbody></table>
      </div>
    </div>
  </div>
</div>

</body></html>
"""


VIEWPUBLISHER_HTML_EMPTY = "<html><body></body></html>"


# --- Helpers ---------------------------------------------------------------

def _mock_response(text="", status_code=200, content=b"fake-pdf-bytes"):
    """Build a mock requests.Response."""
    resp = MagicMock()
    resp.text = text
    resp.status_code = status_code
    resp.raise_for_status = MagicMock()
    resp.iter_content = MagicMock(return_value=[content])
    return resp


def _cfg(body_filter, base_url="https://winterhaven-fl.granicus.com/ViewPublisher.php?view_id=1"):
    return {
        "platform": "granicus_viewpublisher",
        "base_url": base_url,
        "tenant_slug": "winterhaven-fl",
        "view_id": 1,
        "body_filter": body_filter,
    }


# --- Tests -----------------------------------------------------------------

class FactoryRegistrationTests(unittest.TestCase):
    def test_factory_returns_viewpublisher_scraper(self):
        scraper = PlatformScraper.for_platform("granicus_viewpublisher")
        self.assertIsInstance(scraper, ViewPublisherScraper)

    def test_factory_raises_for_unknown_platform(self):
        with self.assertRaises(ValueError):
            PlatformScraper.for_platform("definitely-not-a-platform")


class PanelParsingTests(unittest.TestCase):
    @patch("modules.commission.scrapers.granicus_viewpublisher.requests.get")
    def test_city_commission_filter_returns_cc_rows_only(self, mock_get):
        mock_get.return_value = _mock_response(text=VIEWPUBLISHER_HTML_MINIMAL)
        scraper = ViewPublisherScraper()
        listings = scraper.fetch_listings(_cfg("City Commission"), "2026-01-01", "2026-12-31")
        # One CC row has a PDF; the Review Session row has no PDF and is skipped.
        self.assertEqual(len(listings), 1)
        self.assertEqual(listings[0].title, "City Commission")
        self.assertEqual(listings[0].document_id, "347")

    @patch("modules.commission.scrapers.granicus_viewpublisher.requests.get")
    def test_planning_commission_filter_returns_pc_rows_only(self, mock_get):
        mock_get.return_value = _mock_response(text=VIEWPUBLISHER_HTML_MINIMAL)
        scraper = ViewPublisherScraper()
        listings = scraper.fetch_listings(_cfg("Planning Commission"), "2026-01-01", "2026-12-31")
        self.assertEqual(len(listings), 1)
        self.assertEqual(listings[0].title, "Planning Commission")
        self.assertEqual(listings[0].document_id, "316")

    @patch("modules.commission.scrapers.granicus_viewpublisher.requests.get")
    def test_rows_without_pdf_are_skipped(self, mock_get):
        """The CC Review Session row has no Agenda Packet link and must be skipped."""
        mock_get.return_value = _mock_response(text=VIEWPUBLISHER_HTML_MINIMAL)
        scraper = ViewPublisherScraper()
        listings = scraper.fetch_listings(_cfg("City Commission"), "2026-01-01", "2026-12-31")
        dates = [l.date_str for l in listings]
        # Only the 2026-03-23 row (has PDF) should appear, not the 2026-03-18 Review Session.
        self.assertIn("2026-03-23", dates)
        self.assertNotIn("2026-03-18", dates)

    @patch("modules.commission.scrapers.granicus_viewpublisher.requests.get")
    def test_date_str_is_iso_format(self, mock_get):
        mock_get.return_value = _mock_response(text=VIEWPUBLISHER_HTML_MINIMAL)
        scraper = ViewPublisherScraper()
        listings = scraper.fetch_listings(_cfg("City Commission"), "2026-01-01", "2026-12-31")
        self.assertEqual(listings[0].date_str, "2026-03-23")


class UpcomingEventsTests(unittest.TestCase):
    @patch("modules.commission.scrapers.granicus_viewpublisher.requests.get")
    def test_upcoming_cc_row_picked_up_via_name_cell(self, mock_get):
        """Upcoming rows have no CollapsiblePanel parent; body match uses Name cell."""
        mock_get.return_value = _mock_response(text=VIEWPUBLISHER_HTML_WITH_UPCOMING)
        scraper = ViewPublisherScraper()
        listings = scraper.fetch_listings(_cfg("City Commission"), "2026-01-01", "2026-12-31")
        self.assertEqual(len(listings), 1)
        self.assertEqual(listings[0].date_str, "2026-04-13")
        self.assertEqual(listings[0].document_id, "5500")  # event_id

    @patch("modules.commission.scrapers.granicus_viewpublisher.requests.get")
    def test_upcoming_cra_row_excluded_under_cc_filter(self, mock_get):
        mock_get.return_value = _mock_response(text=VIEWPUBLISHER_HTML_WITH_UPCOMING)
        scraper = ViewPublisherScraper()
        listings = scraper.fetch_listings(_cfg("City Commission"), "2026-01-01", "2026-12-31")
        urls = [l.url for l in listings]
        for u in urls:
            self.assertNotIn("cra00dac", u)


class BodyFilterExclusivityTests(unittest.TestCase):
    @patch("modules.commission.scrapers.granicus_viewpublisher.requests.get")
    def test_city_commission_filter_excludes_cra_panel(self, mock_get):
        """The substring 'City Commission' must NOT match the CRA panel."""
        mock_get.return_value = _mock_response(text=VIEWPUBLISHER_HTML_WITH_CRA_PANEL)
        scraper = ViewPublisherScraper()
        listings = scraper.fetch_listings(_cfg("City Commission"), "2026-01-01", "2026-12-31")
        self.assertEqual(listings, [])


class DateWindowingTests(unittest.TestCase):
    @patch("modules.commission.scrapers.granicus_viewpublisher.requests.get")
    def test_rows_before_start_date_excluded(self, mock_get):
        mock_get.return_value = _mock_response(text=VIEWPUBLISHER_HTML_MINIMAL)
        scraper = ViewPublisherScraper()
        listings = scraper.fetch_listings(_cfg("City Commission"), "2026-06-01", "2026-12-31")
        self.assertEqual(listings, [])

    @patch("modules.commission.scrapers.granicus_viewpublisher.requests.get")
    def test_rows_after_end_date_excluded(self, mock_get):
        mock_get.return_value = _mock_response(text=VIEWPUBLISHER_HTML_MINIMAL)
        scraper = ViewPublisherScraper()
        listings = scraper.fetch_listings(_cfg("City Commission"), "2025-01-01", "2025-12-31")
        self.assertEqual(listings, [])


class DateParsingTests(unittest.TestCase):
    @patch("modules.commission.scrapers.granicus_viewpublisher.requests.get")
    def test_nbsp_dates_parse_correctly(self, mock_get):
        """NBSP-containing date cells parse to ISO."""
        mock_get.return_value = _mock_response(text=VIEWPUBLISHER_HTML_MINIMAL)
        scraper = ViewPublisherScraper()
        listings = scraper.fetch_listings(_cfg("Planning Commission"), "2026-01-01", "2026-12-31")
        self.assertEqual(listings[0].date_str, "2026-03-03")

    @patch("modules.commission.scrapers.granicus_viewpublisher.requests.get")
    def test_double_space_single_digit_day_parses(self, mock_get):
        """Date like 'Mar  9, 2026' (double-space for single-digit day) parses."""
        html = VIEWPUBLISHER_HTML_MINIMAL.replace(
            "Mar&nbsp;3,&nbsp;2026", "Mar&nbsp;&nbsp;9,&nbsp;2026"
        )
        mock_get.return_value = _mock_response(text=html)
        scraper = ViewPublisherScraper()
        listings = scraper.fetch_listings(_cfg("Planning Commission"), "2026-01-01", "2026-12-31")
        self.assertEqual(len(listings), 1)
        self.assertEqual(listings[0].date_str, "2026-03-09")


class MissingConfigTests(unittest.TestCase):
    def test_missing_base_url_returns_empty(self):
        scraper = ViewPublisherScraper()
        self.assertEqual(
            scraper.fetch_listings({"body_filter": "City Commission"}, "2026-01-01", "2026-12-31"),
            [],
        )

    def test_missing_body_filter_returns_empty(self):
        scraper = ViewPublisherScraper()
        self.assertEqual(
            scraper.fetch_listings(
                {"base_url": "https://winterhaven-fl.granicus.com/ViewPublisher.php?view_id=1"},
                "2026-01-01",
                "2026-12-31",
            ),
            [],
        )


class DocumentListingFieldTests(unittest.TestCase):
    @patch("modules.commission.scrapers.granicus_viewpublisher.requests.get")
    def test_listing_fields_populated_from_panel(self, mock_get):
        """title=panel label, document_type=agenda, file_format=pdf, doc_id=clip_id, filename shape."""
        mock_get.return_value = _mock_response(text=VIEWPUBLISHER_HTML_MINIMAL)
        scraper = ViewPublisherScraper()
        listings = scraper.fetch_listings(_cfg("City Commission"), "2026-01-01", "2026-12-31")
        self.assertEqual(len(listings), 1)
        l = listings[0]
        self.assertEqual(l.title, "City Commission")
        self.assertEqual(l.document_type, "agenda")
        self.assertEqual(l.file_format, "pdf")
        self.assertEqual(l.document_id, "347")
        self.assertEqual(l.filename, "Agenda_2026-03-23_347.pdf")


class DownloadDocumentTests(unittest.TestCase):
    @patch("modules.commission.scrapers.granicus_viewpublisher.requests.get")
    def test_download_writes_file(self, mock_get):
        fake_content = b"%PDF-1.4 fake content"
        mock_get.return_value = _mock_response(content=fake_content)

        listing = DocumentListing(
            title="City Commission",
            url="https://d3n9y02raazwpg.cloudfront.net/winterhaven-fl/aaaa.pdf",
            date_str="2026-03-23",
            document_id="347",
            document_type="agenda",
            file_format="pdf",
            filename="Agenda_2026-03-23_347.pdf",
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            scraper = ViewPublisherScraper()
            filepath = scraper.download_document(listing, tmpdir)
            self.assertTrue(os.path.exists(filepath))
            self.assertEqual(os.path.basename(filepath), "Agenda_2026-03-23_347.pdf")
            with open(filepath, "rb") as f:
                self.assertEqual(f.read(), fake_content)

    @patch("modules.commission.scrapers.granicus_viewpublisher.requests.get")
    def test_download_creates_nested_output_dir(self, mock_get):
        mock_get.return_value = _mock_response(content=b"data")

        listing = DocumentListing(
            title="Test",
            url="https://d3n9y02raazwpg.cloudfront.net/winterhaven-fl/abc.pdf",
            date_str="2026-01-01",
            document_id="1",
            document_type="agenda",
            file_format="pdf",
            filename="test.pdf",
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            nested = os.path.join(tmpdir, "sub", "dir")
            scraper = ViewPublisherScraper()
            filepath = scraper.download_document(listing, nested)
            self.assertTrue(os.path.exists(filepath))


if __name__ == "__main__":
    unittest.main()
