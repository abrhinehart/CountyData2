"""Unit tests for modules.commission.scrapers.civicweb_icompass.

Mirrors the structure of tests/test_granicus_viewpublisher_scraper.py.
Fixtures reflect the real Walton County iCompass CivicWeb HTML shape
verified live on 2026-04-16:

- Folder pages at /filepro/documents/<id> list children as
  <div class="document-list-view-documents" data-id data-type
       data-title ...> rows.
- `data-type="folder"` children are subfolders (years at the body root,
  or bodies at the agendas root).
- `data-type="document"` children are leaf documents. Title shape for
  agenda PDFs: "<Body Name> - MMM dd YYYY - Pdf".
- Each document row contains <a class="document-link" href="/document/<id>">.
"""

import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from modules.commission.scrapers.base import DocumentListing, PlatformScraper
from modules.commission.scrapers.civicweb_icompass import CivicWebIcompassScraper


# --- Fixture HTML ----------------------------------------------------------

# Year-list page for the BCC body folder (id=1021). Contains year
# subfolders plus a noise non-year folder to test filtering.
YEAR_LIST_HTML = """
<html><body>
<div class="document-list-view-documents"
     data-id="519066"
     data-parentid="1021"
     data-type="folder"
     data-title="2026">
  <a class="document-link" href="/filepro/documents/519066">2026</a>
</div>
<div class="document-list-view-documents"
     data-id="419000"
     data-parentid="1021"
     data-type="folder"
     data-title="2025">
  <a class="document-link" href="/filepro/documents/419000">2025</a>
</div>
<div class="document-list-view-documents"
     data-id="319000"
     data-parentid="1021"
     data-type="folder"
     data-title="2024">
  <a class="document-link" href="/filepro/documents/319000">2024</a>
</div>
<div class="document-list-view-documents"
     data-id="900000"
     data-parentid="1021"
     data-type="folder"
     data-title="Miscellaneous">
  <a class="document-link" href="/filepro/documents/900000">Misc</a>
</div>
</body></html>
"""


# Year-docs page for BCC 2026 (id=519066). Contains:
# - Two BCC agenda PDF rows (Apr 14 + Mar 10 2026)
# - One BCC HTML row (must be skipped)
# - One PC agenda PDF (wrong body — must be skipped under BCC filter)
# - One folder row (must be skipped — data-type=folder)
YEAR_DOCS_HTML = """
<html><body>
<div class="document-list-view-documents"
     data-id="900001"
     data-parentid="519066"
     data-type="document"
     data-title="Board of County Commissioners - Apr 14 2026 - Pdf">
  <a class="document-link" href="/document/900001">PDF</a>
</div>
<div class="document-list-view-documents"
     data-id="900002"
     data-parentid="519066"
     data-type="document"
     data-title="Board of County Commissioners - Apr 14 2026 - Html">
  <a class="document-link" href="/document/900002">HTML</a>
</div>
<div class="document-list-view-documents"
     data-id="900003"
     data-parentid="519066"
     data-type="document"
     data-title="Board of County Commissioners - Mar 10 2026 - Pdf">
  <a class="document-link" href="/document/900003">PDF</a>
</div>
<div class="document-list-view-documents"
     data-id="900004"
     data-parentid="519066"
     data-type="document"
     data-title="Planning Commission - Apr 08 2026 - Pdf">
  <a class="document-link" href="/document/900004">PDF</a>
</div>
<div class="document-list-view-documents"
     data-id="900005"
     data-parentid="519066"
     data-type="folder"
     data-title="Board of County Commissioners - Apr 14 2026 - Pdf">
  <a class="document-link" href="/filepro/documents/900005">Folder</a>
</div>
</body></html>
"""


# Year-docs page with single-digit day WITHOUT zero padding (defensive parse).
YEAR_DOCS_SINGLE_DIGIT_HTML = """
<html><body>
<div class="document-list-view-documents"
     data-id="900100"
     data-parentid="519066"
     data-type="document"
     data-title="Board of County Commissioners - Apr 9 2026 - Pdf">
  <a class="document-link" href="/document/900100">PDF</a>
</div>
</body></html>
"""


# Year-docs page with an unparseable date row.
YEAR_DOCS_BAD_DATE_HTML = """
<html><body>
<div class="document-list-view-documents"
     data-id="900200"
     data-parentid="519066"
     data-type="document"
     data-title="Board of County Commissioners - Special Workshop - Pdf">
  <a class="document-link" href="/document/900200">PDF</a>
</div>
</body></html>
"""


# Year-docs page with duplicate data-id rows (e.g. identical row repeated).
YEAR_DOCS_DUP_HTML = """
<html><body>
<div class="document-list-view-documents"
     data-id="900300"
     data-parentid="519066"
     data-type="document"
     data-title="Board of County Commissioners - Apr 14 2026 - Pdf">
  <a class="document-link" href="/document/900300">PDF</a>
</div>
<div class="document-list-view-documents"
     data-id="900300"
     data-parentid="519066"
     data-type="document"
     data-title="Board of County Commissioners - Apr 14 2026 - Pdf">
  <a class="document-link" href="/document/900300">PDF</a>
</div>
</body></html>
"""


EMPTY_HTML = "<html><body></body></html>"


# --- Helpers ---------------------------------------------------------------

def _mock_response(text="", status_code=200, content=b"fake-pdf-bytes"):
    """Build a mock requests.Response."""
    resp = MagicMock()
    resp.text = text
    resp.status_code = status_code
    resp.raise_for_status = MagicMock()
    resp.iter_content = MagicMock(return_value=[content])
    return resp


def _cfg(
    tenant_host="walton.civicweb.net",
    body_folder_id=1021,
    body_label="Board of County Commissioners",
):
    return {
        "platform": "civicweb_icompass",
        "tenant_host": tenant_host,
        "body_folder_id": body_folder_id,
        "body_label": body_label,
    }


def _url_dispatcher(body_folder_id, year_list_html, docs_by_year_id):
    """Build a requests.get side_effect that dispatches by URL.

    - URL ending in /<body_folder_id> -> year_list_html
    - URL ending in /<year_id> -> docs_by_year_id[year_id]
    - Anything else -> empty HTML fixture.
    """
    def _fake_get(url, *args, **kwargs):
        if url.endswith(f"/{body_folder_id}"):
            return _mock_response(text=year_list_html)
        for yid, html in docs_by_year_id.items():
            if url.endswith(f"/{yid}"):
                return _mock_response(text=html)
        return _mock_response(text=EMPTY_HTML)
    return _fake_get


# --- Tests -----------------------------------------------------------------

class FactoryRegistrationTests(unittest.TestCase):
    def test_factory_returns_civicweb_icompass_scraper(self):
        """Factory hands back a CivicWebIcompassScraper instance."""
        scraper = PlatformScraper.for_platform("civicweb_icompass")
        self.assertIsInstance(scraper, CivicWebIcompassScraper)

    def test_factory_raises_for_unknown_platform(self):
        """Unknown platform raises ValueError."""
        with self.assertRaises(ValueError):
            PlatformScraper.for_platform("definitely-not-a-platform")


class YearFolderFilteringTests(unittest.TestCase):
    @patch("modules.commission.scrapers.civicweb_icompass.requests.get")
    def test_only_in_window_years_are_crawled(self, mock_get):
        """Year folders outside start..end year are not fetched."""
        dispatcher = _url_dispatcher(
            1021,
            YEAR_LIST_HTML,
            {"519066": YEAR_DOCS_HTML, "419000": EMPTY_HTML, "319000": EMPTY_HTML},
        )
        mock_get.side_effect = dispatcher
        scraper = CivicWebIcompassScraper()
        scraper.fetch_listings(_cfg(), "2026-01-01", "2026-12-31")

        fetched_urls = [call.args[0] for call in mock_get.call_args_list]
        # Root body folder and 2026 year folder fetched.
        self.assertTrue(any(u.endswith("/1021") for u in fetched_urls))
        self.assertTrue(any(u.endswith("/519066") for u in fetched_urls))
        # 2025 / 2024 / Misc year folders NOT fetched.
        self.assertFalse(any(u.endswith("/419000") for u in fetched_urls))
        self.assertFalse(any(u.endswith("/319000") for u in fetched_urls))
        self.assertFalse(any(u.endswith("/900000") for u in fetched_urls))

    @patch("modules.commission.scrapers.civicweb_icompass.requests.get")
    def test_non_year_folders_ignored(self, mock_get):
        """Non-year folders (e.g. 'Miscellaneous') never feed the crawler."""
        dispatcher = _url_dispatcher(1021, YEAR_LIST_HTML, {"519066": YEAR_DOCS_HTML})
        mock_get.side_effect = dispatcher
        scraper = CivicWebIcompassScraper()
        scraper.fetch_listings(_cfg(), "2026-01-01", "2026-12-31")

        fetched_urls = [call.args[0] for call in mock_get.call_args_list]
        self.assertFalse(any(u.endswith("/900000") for u in fetched_urls))


class BodyLabelFilteringTests(unittest.TestCase):
    @patch("modules.commission.scrapers.civicweb_icompass.requests.get")
    def test_wrong_body_excluded(self, mock_get):
        """Planning Commission rows are excluded under BCC body_label."""
        dispatcher = _url_dispatcher(1021, YEAR_LIST_HTML, {"519066": YEAR_DOCS_HTML})
        mock_get.side_effect = dispatcher
        scraper = CivicWebIcompassScraper()
        listings = scraper.fetch_listings(_cfg(), "2026-01-01", "2026-12-31")
        for l in listings:
            self.assertTrue(
                l.title.lower().startswith("board of county commissioners")
            )
        titles = [l.title for l in listings]
        self.assertNotIn("Planning Commission", titles)


class DocumentTypeFilteringTests(unittest.TestCase):
    @patch("modules.commission.scrapers.civicweb_icompass.requests.get")
    def test_html_rows_skipped(self, mock_get):
        """Rows whose data-title ends with '- Html' are skipped."""
        dispatcher = _url_dispatcher(1021, YEAR_LIST_HTML, {"519066": YEAR_DOCS_HTML})
        mock_get.side_effect = dispatcher
        scraper = CivicWebIcompassScraper()
        listings = scraper.fetch_listings(_cfg(), "2026-01-01", "2026-12-31")
        ids = [l.document_id for l in listings]
        # "900002" is the HTML row and must not appear.
        self.assertNotIn("900002", ids)

    @patch("modules.commission.scrapers.civicweb_icompass.requests.get")
    def test_non_document_rows_skipped(self, mock_get):
        """Rows with data-type=folder never become listings even if title matches."""
        dispatcher = _url_dispatcher(1021, YEAR_LIST_HTML, {"519066": YEAR_DOCS_HTML})
        mock_get.side_effect = dispatcher
        scraper = CivicWebIcompassScraper()
        listings = scraper.fetch_listings(_cfg(), "2026-01-01", "2026-12-31")
        ids = [l.document_id for l in listings]
        self.assertNotIn("900005", ids)


class DateParsingTests(unittest.TestCase):
    @patch("modules.commission.scrapers.civicweb_icompass.requests.get")
    def test_zero_padded_day_parses(self, mock_get):
        """'Apr 14 2026' and 'Mar 10 2026' both parse to ISO."""
        dispatcher = _url_dispatcher(1021, YEAR_LIST_HTML, {"519066": YEAR_DOCS_HTML})
        mock_get.side_effect = dispatcher
        scraper = CivicWebIcompassScraper()
        listings = scraper.fetch_listings(_cfg(), "2026-01-01", "2026-12-31")
        dates = {l.date_str for l in listings}
        self.assertIn("2026-04-14", dates)
        self.assertIn("2026-03-10", dates)

    @patch("modules.commission.scrapers.civicweb_icompass.requests.get")
    def test_single_digit_day_without_pad_parses(self, mock_get):
        """'Apr 9 2026' (no zero pad) parses defensively."""
        dispatcher = _url_dispatcher(
            1021, YEAR_LIST_HTML, {"519066": YEAR_DOCS_SINGLE_DIGIT_HTML}
        )
        mock_get.side_effect = dispatcher
        scraper = CivicWebIcompassScraper()
        listings = scraper.fetch_listings(_cfg(), "2026-01-01", "2026-12-31")
        self.assertEqual(len(listings), 1)
        self.assertEqual(listings[0].date_str, "2026-04-09")

    @patch("modules.commission.scrapers.civicweb_icompass.requests.get")
    def test_unparseable_title_skipped(self, mock_get):
        """Rows with no parseable date in the title are silently dropped."""
        dispatcher = _url_dispatcher(
            1021, YEAR_LIST_HTML, {"519066": YEAR_DOCS_BAD_DATE_HTML}
        )
        mock_get.side_effect = dispatcher
        scraper = CivicWebIcompassScraper()
        listings = scraper.fetch_listings(_cfg(), "2026-01-01", "2026-12-31")
        self.assertEqual(listings, [])


class DateWindowingTests(unittest.TestCase):
    @patch("modules.commission.scrapers.civicweb_icompass.requests.get")
    def test_rows_before_start_excluded(self, mock_get):
        """Rows dated before start_date are excluded."""
        dispatcher = _url_dispatcher(1021, YEAR_LIST_HTML, {"519066": YEAR_DOCS_HTML})
        mock_get.side_effect = dispatcher
        scraper = CivicWebIcompassScraper()
        listings = scraper.fetch_listings(_cfg(), "2026-04-01", "2026-12-31")
        # Mar 10 is before Apr 1; Apr 14 stays.
        dates = {l.date_str for l in listings}
        self.assertNotIn("2026-03-10", dates)
        self.assertIn("2026-04-14", dates)

    @patch("modules.commission.scrapers.civicweb_icompass.requests.get")
    def test_rows_after_end_excluded(self, mock_get):
        """Rows dated after end_date are excluded."""
        dispatcher = _url_dispatcher(1021, YEAR_LIST_HTML, {"519066": YEAR_DOCS_HTML})
        mock_get.side_effect = dispatcher
        scraper = CivicWebIcompassScraper()
        listings = scraper.fetch_listings(_cfg(), "2026-01-01", "2026-04-01")
        dates = {l.date_str for l in listings}
        self.assertNotIn("2026-04-14", dates)
        self.assertIn("2026-03-10", dates)


class DocumentListingFieldTests(unittest.TestCase):
    @patch("modules.commission.scrapers.civicweb_icompass.requests.get")
    def test_listing_fields_populated(self, mock_get):
        """title=body_label, document_type=agenda, file_format=pdf, url absolute, filename shape."""
        dispatcher = _url_dispatcher(1021, YEAR_LIST_HTML, {"519066": YEAR_DOCS_HTML})
        mock_get.side_effect = dispatcher
        scraper = CivicWebIcompassScraper()
        listings = scraper.fetch_listings(_cfg(), "2026-01-01", "2026-12-31")
        by_id = {l.document_id: l for l in listings}
        self.assertIn("900001", by_id)
        l = by_id["900001"]
        self.assertEqual(l.title, "Board of County Commissioners")
        self.assertEqual(l.document_type, "agenda")
        self.assertEqual(l.file_format, "pdf")
        self.assertEqual(l.date_str, "2026-04-14")
        self.assertEqual(l.url, "https://walton.civicweb.net/document/900001")
        self.assertEqual(l.filename, "Agenda_2026-04-14_900001.pdf")


class DeduplicationTests(unittest.TestCase):
    @patch("modules.commission.scrapers.civicweb_icompass.requests.get")
    def test_duplicate_data_ids_collapsed(self, mock_get):
        """A data-id appearing twice yields exactly one listing."""
        dispatcher = _url_dispatcher(1021, YEAR_LIST_HTML, {"519066": YEAR_DOCS_DUP_HTML})
        mock_get.side_effect = dispatcher
        scraper = CivicWebIcompassScraper()
        listings = scraper.fetch_listings(_cfg(), "2026-01-01", "2026-12-31")
        self.assertEqual(len(listings), 1)
        self.assertEqual(listings[0].document_id, "900300")


class MissingConfigTests(unittest.TestCase):
    def test_missing_tenant_host_returns_empty(self):
        """Absent tenant_host returns []."""
        scraper = CivicWebIcompassScraper()
        cfg = _cfg()
        cfg.pop("tenant_host")
        self.assertEqual(scraper.fetch_listings(cfg, "2026-01-01", "2026-12-31"), [])

    def test_missing_body_folder_id_returns_empty(self):
        """Absent body_folder_id returns []."""
        scraper = CivicWebIcompassScraper()
        cfg = _cfg()
        cfg.pop("body_folder_id")
        self.assertEqual(scraper.fetch_listings(cfg, "2026-01-01", "2026-12-31"), [])

    def test_missing_body_label_returns_empty(self):
        """Absent body_label returns []."""
        scraper = CivicWebIcompassScraper()
        cfg = _cfg()
        cfg.pop("body_label")
        self.assertEqual(scraper.fetch_listings(cfg, "2026-01-01", "2026-12-31"), [])

    def test_bad_date_range_returns_empty(self):
        """Malformed date strings return []."""
        scraper = CivicWebIcompassScraper()
        self.assertEqual(scraper.fetch_listings(_cfg(), "not-a-date", "2026-12-31"), [])

    def test_inverted_date_range_returns_empty(self):
        """start > end returns [] without touching the network."""
        scraper = CivicWebIcompassScraper()
        with patch(
            "modules.commission.scrapers.civicweb_icompass.requests.get"
        ) as mock_get:
            result = scraper.fetch_listings(_cfg(), "2026-12-31", "2026-01-01")
            self.assertEqual(result, [])
            self.assertEqual(mock_get.call_count, 0)


class NetworkFailureTests(unittest.TestCase):
    @patch("modules.commission.scrapers.civicweb_icompass.requests.get")
    def test_root_folder_fetch_fails_returns_empty(self, mock_get):
        """If the body-root fetch fails, return []."""
        import requests as _requests
        mock_get.side_effect = _requests.RequestException("boom")
        scraper = CivicWebIcompassScraper()
        self.assertEqual(scraper.fetch_listings(_cfg(), "2026-01-01", "2026-12-31"), [])

    @patch("modules.commission.scrapers.civicweb_icompass.requests.get")
    def test_year_folder_fetch_fails_is_skipped(self, mock_get):
        """A single year-folder fetch failure is skipped, others still parse."""
        import requests as _requests

        def _fake_get(url, *args, **kwargs):
            if url.endswith("/1021"):
                return _mock_response(text=YEAR_LIST_HTML)
            if url.endswith("/519066"):
                raise _requests.RequestException("year fetch boom")
            return _mock_response(text=EMPTY_HTML)

        mock_get.side_effect = _fake_get
        scraper = CivicWebIcompassScraper()
        listings = scraper.fetch_listings(_cfg(), "2026-01-01", "2026-12-31")
        self.assertEqual(listings, [])


class DownloadDocumentTests(unittest.TestCase):
    @patch("modules.commission.scrapers.civicweb_icompass.requests.get")
    def test_download_writes_file(self, mock_get):
        """Download streams bytes into output_dir with listing.filename."""
        fake_content = b"%PDF-1.4 fake content"
        mock_get.return_value = _mock_response(content=fake_content)

        listing = DocumentListing(
            title="Board of County Commissioners",
            url="https://walton.civicweb.net/document/900001",
            date_str="2026-04-14",
            document_id="900001",
            document_type="agenda",
            file_format="pdf",
            filename="Agenda_2026-04-14_900001.pdf",
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            scraper = CivicWebIcompassScraper()
            filepath = scraper.download_document(listing, tmpdir)
            self.assertTrue(os.path.exists(filepath))
            self.assertEqual(os.path.basename(filepath), "Agenda_2026-04-14_900001.pdf")
            with open(filepath, "rb") as f:
                self.assertEqual(f.read(), fake_content)

    @patch("modules.commission.scrapers.civicweb_icompass.requests.get")
    def test_download_creates_nested_output_dir(self, mock_get):
        """Nested output_dir is created on demand."""
        mock_get.return_value = _mock_response(content=b"data")

        listing = DocumentListing(
            title="Test",
            url="https://walton.civicweb.net/document/1",
            date_str="2026-01-01",
            document_id="1",
            document_type="agenda",
            file_format="pdf",
            filename="test.pdf",
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            nested = os.path.join(tmpdir, "sub", "dir")
            scraper = CivicWebIcompassScraper()
            filepath = scraper.download_document(listing, nested)
            self.assertTrue(os.path.exists(filepath))


if __name__ == "__main__":
    unittest.main()
