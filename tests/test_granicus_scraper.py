"""Unit tests for modules.commission.scrapers.granicus (Granicus/iQM2 adapter)."""

import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from modules.commission.scrapers.base import PlatformScraper, DocumentListing
from modules.commission.scrapers.granicus import GranicusScraper


# --- Sample HTML fragments for the iQM2 Calendar list view ---

CALENDAR_HTML_TWO_MEETINGS = """
<html><body><table>
<tr>
  <td>Jan 8, 2026 9:00 AM</td>
  <td><a href="Detail_Meeting.aspx?ID=100">Board of County Commissioners</a></td>
  <td>
    <a href="FileOpen.aspx?Type=14&ID=500">Agenda</a>
    <a href="FileOpen.aspx?Type=15&ID=501">Minutes</a>
  </td>
</tr>
<tr>
  <td>Feb 12, 2026 6:00 PM</td>
  <td><a href="Detail_Meeting.aspx?ID=101">Planning and Zoning Board</a></td>
  <td>
    <a href="FileOpen.aspx?Type=14&ID=502">Agenda</a>
  </td>
</tr>
</table></body></html>
"""

CALENDAR_HTML_WITH_PACKET = """
<html><body><table>
<tr>
  <td>Mar 5, 2026 9:00 AM</td>
  <td><a href="Detail_Meeting.aspx?ID=200">Board of County Commissioners</a></td>
  <td>
    <a href="FileOpen.aspx?Type=1&ID=600">Packet</a>
    <a href="FileOpen.aspx?Type=14&ID=601">Agenda</a>
    <a href="FileOpen.aspx?Type=12&ID=602">Backup</a>
    <a href="FileOpen.aspx?Type=15&ID=603">Minutes</a>
  </td>
</tr>
</table></body></html>
"""

CALENDAR_HTML_EMPTY = """
<html><body><table></table></body></html>
"""

CALENDAR_HTML_NO_FILES = """
<html><body><table>
<tr>
  <td>Apr 1, 2026 9:00 AM</td>
  <td><a href="Detail_Meeting.aspx?ID=300">Board of County Commissioners</a></td>
  <td></td>
</tr>
</table></body></html>
"""


# --- Div-based iQM2 layout (primary parsing path) ---

CALENDAR_HTML_DIV_LAYOUT = """
<html><body>
<div class="Row MeetingRow">
  <div class="RowLink">
    <a href="Detail_Meeting.aspx?ID=400">Jan 14, 2026 9:00 AM</a>
  </div>
  <div class="RowDetails">Board of County Commissioners - Regular Meeting</div>
  <div class="RowFiles">
    <a href="FileOpen.aspx?Type=14&amp;ID=700">Agenda</a>
    <a href="FileOpen.aspx?Type=15&amp;ID=701">Minutes</a>
  </div>
</div>
<div class="Row MeetingRow">
  <div class="RowLink">
    <a href="Detail_Meeting.aspx?ID=401">Feb 3, 2026 6:30 PM</a>
  </div>
  <div class="RowDetails">Planning Board - Public Hearing</div>
  <div class="RowFiles">
    <a href="FileOpen.aspx?Type=14&amp;ID=702">Agenda</a>
  </div>
</div>
<div class="Row MeetingRow">
  <div class="RowLink">
    <a href="Detail_Meeting.aspx?ID=402">Mar 10, 2026 9:00 AM</a>
  </div>
  <div class="RowDetails">Board of County Commissioners - Workshop</div>
</div>
</body></html>
"""


def _mock_response(text="", status_code=200, content=b"fake-pdf-bytes"):
    """Build a mock requests.Response."""
    resp = MagicMock()
    resp.text = text
    resp.status_code = status_code
    resp.raise_for_status = MagicMock()
    resp.iter_content = MagicMock(return_value=[content])
    return resp


class FactoryRegistrationTests(unittest.TestCase):
    """Factory should return a GranicusScraper for 'granicus'."""

    def test_factory_returns_granicus_scraper(self):
        scraper = PlatformScraper.for_platform("granicus")
        self.assertIsInstance(scraper, GranicusScraper)

    def test_factory_type_name(self):
        scraper = PlatformScraper.for_platform("granicus")
        self.assertEqual(type(scraper).__name__, "GranicusScraper")


class CalendarParsingTests(unittest.TestCase):
    """Test HTML parsing of iQM2 calendar list views."""

    @patch("modules.commission.scrapers.granicus.requests.get")
    def test_extracts_agendas_and_minutes(self, mock_get):
        mock_get.return_value = _mock_response(text=CALENDAR_HTML_TWO_MEETINGS)

        scraper = GranicusScraper()
        config = {"base_url": "https://example.iqm2.com/Citizens"}
        listings = scraper.fetch_listings(config, "2026-01-01", "2026-03-01")

        # 2 agendas + 1 minutes = 3 total
        self.assertEqual(len(listings), 3)

        agendas = [l for l in listings if l.document_type == "agenda"]
        minutes = [l for l in listings if l.document_type == "minutes"]
        self.assertEqual(len(agendas), 2)
        self.assertEqual(len(minutes), 1)

    @patch("modules.commission.scrapers.granicus.requests.get")
    def test_skips_packet_and_backup_types(self, mock_get):
        mock_get.return_value = _mock_response(text=CALENDAR_HTML_WITH_PACKET)

        scraper = GranicusScraper()
        config = {"base_url": "https://example.iqm2.com/Citizens"}
        listings = scraper.fetch_listings(config, "2026-03-01", "2026-04-01")

        # Only agenda (Type=14) and minutes (Type=15), not packet (1) or backup (12)
        self.assertEqual(len(listings), 2)
        types = {l.document_type for l in listings}
        self.assertEqual(types, {"agenda", "minutes"})

    @patch("modules.commission.scrapers.granicus.requests.get")
    def test_empty_calendar_returns_empty(self, mock_get):
        mock_get.return_value = _mock_response(text=CALENDAR_HTML_EMPTY)

        scraper = GranicusScraper()
        config = {"base_url": "https://example.iqm2.com/Citizens"}
        listings = scraper.fetch_listings(config, "2026-01-01", "2026-03-01")
        self.assertEqual(listings, [])

    @patch("modules.commission.scrapers.granicus.requests.get")
    def test_meeting_without_files_returns_empty(self, mock_get):
        mock_get.return_value = _mock_response(text=CALENDAR_HTML_NO_FILES)

        scraper = GranicusScraper()
        config = {"base_url": "https://example.iqm2.com/Citizens"}
        listings = scraper.fetch_listings(config, "2026-04-01", "2026-04-30")
        self.assertEqual(listings, [])


class DateConversionTests(unittest.TestCase):
    """Test ISO to iQM2 date format conversion and date extraction."""

    @patch("modules.commission.scrapers.granicus.requests.get")
    def test_date_str_is_iso_format(self, mock_get):
        mock_get.return_value = _mock_response(text=CALENDAR_HTML_TWO_MEETINGS)

        scraper = GranicusScraper()
        config = {"base_url": "https://example.iqm2.com/Citizens"}
        listings = scraper.fetch_listings(config, "2026-01-01", "2026-03-01")

        dates = {l.date_str for l in listings}
        self.assertIn("2026-01-08", dates)
        self.assertIn("2026-02-12", dates)

    @patch("modules.commission.scrapers.granicus.requests.get")
    def test_iqm2_query_params_use_slash_format(self, mock_get):
        """Calendar URL should use M/D/YYYY date params."""
        mock_get.return_value = _mock_response(text=CALENDAR_HTML_EMPTY)

        scraper = GranicusScraper()
        config = {"base_url": "https://example.iqm2.com/Citizens"}
        scraper.fetch_listings(config, "2026-01-05", "2026-03-15")

        called_url = mock_get.call_args[0][0]
        self.assertIn("From=1/5/2026", called_url)
        self.assertIn("To=3/15/2026", called_url)


class MeetingGroupFilterTests(unittest.TestCase):
    """Test optional meeting_group config filter."""

    @patch("modules.commission.scrapers.granicus.requests.get")
    def test_meeting_group_filter_includes_match(self, mock_get):
        mock_get.return_value = _mock_response(text=CALENDAR_HTML_TWO_MEETINGS)

        scraper = GranicusScraper()
        config = {
            "base_url": "https://example.iqm2.com/Citizens",
            "meeting_group": "Board of County Commissioners",
        }
        listings = scraper.fetch_listings(config, "2026-01-01", "2026-03-01")

        # Only the BCC meeting (1 agenda + 1 minutes), not the P&Z meeting
        self.assertEqual(len(listings), 2)
        for listing in listings:
            self.assertIn("Board of County Commissioners", listing.title)

    @patch("modules.commission.scrapers.granicus.requests.get")
    def test_meeting_group_filter_excludes_non_match(self, mock_get):
        mock_get.return_value = _mock_response(text=CALENDAR_HTML_TWO_MEETINGS)

        scraper = GranicusScraper()
        config = {
            "base_url": "https://example.iqm2.com/Citizens",
            "meeting_group": "Nonexistent Board",
        }
        listings = scraper.fetch_listings(config, "2026-01-01", "2026-03-01")
        self.assertEqual(listings, [])


class MissingBaseUrlTests(unittest.TestCase):
    """Missing base_url should return empty list, not crash."""

    def test_missing_base_url_returns_empty(self):
        scraper = GranicusScraper()
        listings = scraper.fetch_listings({}, "2026-01-01", "2026-03-01")
        self.assertEqual(listings, [])

    def test_none_base_url_returns_empty(self):
        scraper = GranicusScraper()
        listings = scraper.fetch_listings({"base_url": None}, "2026-01-01", "2026-03-01")
        self.assertEqual(listings, [])


class DocumentListingFieldTests(unittest.TestCase):
    """Verify DocumentListing field values are populated correctly."""

    @patch("modules.commission.scrapers.granicus.requests.get")
    def test_listing_fields(self, mock_get):
        mock_get.return_value = _mock_response(text=CALENDAR_HTML_TWO_MEETINGS)

        scraper = GranicusScraper()
        config = {"base_url": "https://example.iqm2.com/Citizens"}
        listings = scraper.fetch_listings(config, "2026-01-01", "2026-03-01")

        # Find the first agenda
        agenda = next(l for l in listings if l.document_type == "agenda" and l.date_str == "2026-01-08")

        self.assertEqual(agenda.title, "Board of County Commissioners")
        self.assertIn("FileOpen.aspx", agenda.url)
        self.assertEqual(agenda.date_str, "2026-01-08")
        self.assertEqual(agenda.document_id, "500")
        self.assertEqual(agenda.document_type, "agenda")
        self.assertEqual(agenda.file_format, "pdf")
        self.assertTrue(agenda.filename.endswith(".pdf"))
        self.assertIn("Agenda", agenda.filename)


class DownloadDocumentTests(unittest.TestCase):
    """Test document download writes file correctly."""

    @patch("modules.commission.scrapers.granicus.requests.get")
    def test_download_writes_file(self, mock_get):
        fake_content = b"%PDF-1.4 fake content"
        mock_get.return_value = _mock_response(content=fake_content)

        listing = DocumentListing(
            title="Test Meeting",
            url="https://example.iqm2.com/Citizens/FileOpen.aspx?Type=14&ID=500",
            date_str="2026-01-08",
            document_id="500",
            document_type="agenda",
            file_format="pdf",
            filename="Agenda_2026-01-08_100.pdf",
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            scraper = GranicusScraper()
            filepath = scraper.download_document(listing, tmpdir)

            self.assertTrue(os.path.exists(filepath))
            self.assertEqual(os.path.basename(filepath), "Agenda_2026-01-08_100.pdf")
            with open(filepath, "rb") as f:
                self.assertEqual(f.read(), fake_content)

    @patch("modules.commission.scrapers.granicus.requests.get")
    def test_download_creates_output_dir(self, mock_get):
        mock_get.return_value = _mock_response(content=b"data")

        listing = DocumentListing(
            title="Test",
            url="https://example.iqm2.com/Citizens/FileOpen.aspx?Type=14&ID=1",
            date_str="2026-01-01",
            document_id="1",
            document_type="agenda",
            file_format="pdf",
            filename="test.pdf",
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            nested = os.path.join(tmpdir, "sub", "dir")
            scraper = GranicusScraper()
            filepath = scraper.download_document(listing, nested)
            self.assertTrue(os.path.exists(filepath))


class TestGranicusDivLayout(unittest.TestCase):
    """Test the primary div-based iQM2 parsing path (div.MeetingRow containers)."""

    @patch("modules.commission.scrapers.granicus.requests.get")
    def test_div_layout_parses_meetings(self, mock_get):
        """Meetings are extracted from MeetingRow divs, not <tr> fallback."""
        mock_get.return_value = _mock_response(text=CALENDAR_HTML_DIV_LAYOUT)

        scraper = GranicusScraper()
        config = {"base_url": "https://example.iqm2.com/Citizens"}
        listings = scraper.fetch_listings(config, "2026-01-01", "2026-04-01")

        # BCC: agenda + minutes = 2; Planning Board: agenda = 1; Workshop: 0 docs
        self.assertEqual(len(listings), 3)

        agendas = [l for l in listings if l.document_type == "agenda"]
        minutes = [l for l in listings if l.document_type == "minutes"]
        self.assertEqual(len(agendas), 2)
        self.assertEqual(len(minutes), 1)

    @patch("modules.commission.scrapers.granicus.requests.get")
    def test_div_layout_extracts_titles(self, mock_get):
        """Board names come from RowDetails div, not from the link text (which is the date)."""
        mock_get.return_value = _mock_response(text=CALENDAR_HTML_DIV_LAYOUT)

        scraper = GranicusScraper()
        config = {"base_url": "https://example.iqm2.com/Citizens"}
        listings = scraper.fetch_listings(config, "2026-01-01", "2026-04-01")

        titles = {l.title for l in listings}
        self.assertIn("Board of County Commissioners - Regular Meeting", titles)
        self.assertIn("Planning Board - Public Hearing", titles)
        # The link text is a date string — make sure it is NOT used as a title
        for listing in listings:
            self.assertNotRegex(listing.title, r"^[A-Z][a-z]{2}\s+\d+,\s*\d{4}")

    @patch("modules.commission.scrapers.granicus.requests.get")
    def test_div_layout_meeting_group_filter(self, mock_get):
        """meeting_group filter works correctly with div-based layout titles."""
        mock_get.return_value = _mock_response(text=CALENDAR_HTML_DIV_LAYOUT)

        scraper = GranicusScraper()
        config = {
            "base_url": "https://example.iqm2.com/Citizens",
            "meeting_group": "Planning Board",
        }
        listings = scraper.fetch_listings(config, "2026-01-01", "2026-04-01")

        # Only the Planning Board meeting (1 agenda)
        self.assertEqual(len(listings), 1)
        self.assertIn("Planning Board", listings[0].title)
        self.assertEqual(listings[0].document_type, "agenda")

    @patch("modules.commission.scrapers.granicus.requests.get")
    def test_div_layout_no_documents_skipped(self, mock_get):
        """Meetings without FileOpen links produce no listings (Workshop row)."""
        mock_get.return_value = _mock_response(text=CALENDAR_HTML_DIV_LAYOUT)

        scraper = GranicusScraper()
        config = {
            "base_url": "https://example.iqm2.com/Citizens",
            "meeting_group": "Workshop",
        }
        listings = scraper.fetch_listings(config, "2026-01-01", "2026-04-01")

        # The Workshop meeting has no FileOpen links, so zero listings
        self.assertEqual(listings, [])


if __name__ == "__main__":
    unittest.main()
