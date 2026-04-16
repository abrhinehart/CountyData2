"""Unit tests for modules.commission.scrapers.escribe.

Mirrors the structure of tests/test_civicweb_icompass_scraper.py and
tests/test_granicus_viewpublisher_scraper.py. All tests patch
``requests.post`` (or ``requests.get``) on the
``modules.commission.scrapers.escribe`` module namespace — no live
network.
"""

import copy
import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import requests

from modules.commission.scrapers.base import DocumentListing, PlatformScraper
from modules.commission.scrapers.escribe import EscribeScraper


# --- Fixture JSON payloads ------------------------------------------------

# Multi-body fixture spanning CC, CC Special, PC, and a non-matching
# Code Compliance meeting. Each meeting has a MeetingDocumentLink array
# that mirrors the verified live shape.
JSON_MULTI_BODY = {
    "d": [
        {
            "ID": "9c192bb8-9f27-41cb-b7cc-359e7644fa25",
            "MeetingName": "City Commission Meeting",
            "MeetingType": "City Commission Meeting",
            "StartDate": "2026/02/05 19:00:00",
            "EndDate": "2026/02/05 20:30:00",
            "MeetingDocumentLink": [
                {
                    "Type": "AgendaCover",
                    "Format": ".pdf",
                    "Title": "Agenda Cover Page (PDF)",
                    "Url": "FileStream.ashx?DocumentId=27358",
                },
                {
                    "Type": "Agenda",
                    "Format": ".pdf",
                    "Title": "Agenda (PDF)",
                    "Url": "FileStream.ashx?DocumentId=27357",
                },
                {
                    "Type": "Agenda",
                    "Format": "HTML",
                    "Title": "Agenda (HTML)",
                    "Url": "Meeting.aspx?Id=9c192bb8-9f27-41cb-b7cc-359e7644fa25&Agenda=Agenda&lang=English",
                },
                {
                    "Type": "PostMinutes",
                    "Format": ".pdf",
                    "Title": "Minutes (PDF)",
                    "Url": "FileStream.ashx?DocumentId=22976",
                },
            ],
        },
        {
            "ID": "aaaaaaaa-0000-0000-0000-000000000001",
            "MeetingName": "City Commission Special Meeting",
            "MeetingType": "City Commission Special Meeting",
            "StartDate": "2026/03/10 18:00:00",
            "EndDate": "2026/03/10 19:00:00",
            "MeetingDocumentLink": [
                {
                    "Type": "Agenda",
                    "Format": ".pdf",
                    "Title": "Agenda (PDF)",
                    "Url": "FileStream.ashx?DocumentId=28000",
                },
                {
                    "Type": "Agenda",
                    "Format": "HTML",
                    "Title": "Agenda (HTML)",
                    "Url": "Meeting.aspx?Id=aaaaaaaa-0000-0000-0000-000000000001&Agenda=Agenda&lang=English",
                },
            ],
        },
        {
            "ID": "bbbbbbbb-0000-0000-0000-000000000002",
            "MeetingName": "Planning Commission",
            "MeetingType": "Planning Commission",
            "StartDate": "2026/03/12 17:30:00",
            "EndDate": "2026/03/12 19:00:00",
            "MeetingDocumentLink": [
                {
                    "Type": "AgendaCover",
                    "Format": ".pdf",
                    "Title": "Agenda Cover Page (PDF)",
                    "Url": "FileStream.ashx?DocumentId=28100",
                },
                {
                    "Type": "Agenda",
                    "Format": ".pdf",
                    "Title": "Agenda (PDF)",
                    "Url": "FileStream.ashx?DocumentId=28101",
                },
                {
                    "Type": "Agenda",
                    "Format": "HTML",
                    "Title": "Agenda (HTML)",
                    "Url": "Meeting.aspx?Id=bbbbbbbb-0000-0000-0000-000000000002&Agenda=Agenda&lang=English",
                },
            ],
        },
        {
            "ID": "cccccccc-0000-0000-0000-000000000003",
            "MeetingName": "Code Compliance",
            "MeetingType": "Code Compliance",
            "StartDate": "2026/02/15 09:00:00",
            "EndDate": "2026/02/15 10:00:00",
            "MeetingDocumentLink": [
                {
                    "Type": "Agenda",
                    "Format": ".pdf",
                    "Title": "Agenda (PDF)",
                    "Url": "FileStream.ashx?DocumentId=28200",
                },
            ],
        },
    ]
}

JSON_NO_AGENDA_PDF = {
    "d": [
        {
            "ID": "dddddddd-0000-0000-0000-000000000004",
            "MeetingName": "City Commission Meeting",
            "MeetingType": "City Commission Meeting",
            "StartDate": "2026/05/20 19:00:00",
            "MeetingDocumentLink": [
                {
                    "Type": "Agenda",
                    "Format": "HTML",
                    "Title": "Agenda (HTML)",
                    "Url": "Meeting.aspx?Id=dddddddd-0000-0000-0000-000000000004&Agenda=Agenda&lang=English",
                },
            ],
        }
    ]
}

JSON_EMPTY_DOCS = {
    "d": [
        {
            "ID": "eeeeeeee-0000-0000-0000-000000000005",
            "MeetingName": "City Commission Meeting",
            "MeetingType": "City Commission Meeting",
            "StartDate": "2026/06/01 19:00:00",
            "MeetingDocumentLink": [],
        }
    ]
}

JSON_NULL_DOCS = {
    "d": [
        {
            "ID": "ffffffff-0000-0000-0000-000000000006",
            "MeetingName": "City Commission Meeting",
            "MeetingType": "City Commission Meeting",
            "StartDate": "2026/06/15 19:00:00",
            "MeetingDocumentLink": None,
        }
    ]
}

JSON_DUPLICATE_UUID = {
    "d": [
        {
            "ID": "11111111-1111-1111-1111-111111111111",
            "MeetingName": "City Commission Meeting",
            "MeetingType": "City Commission Meeting",
            "StartDate": "2026/07/01 19:00:00",
            "MeetingDocumentLink": [
                {
                    "Type": "Agenda",
                    "Format": ".pdf",
                    "Title": "Agenda (PDF)",
                    "Url": "FileStream.ashx?DocumentId=30000",
                }
            ],
        },
        {
            "ID": "11111111-1111-1111-1111-111111111111",
            "MeetingName": "City Commission Meeting",
            "MeetingType": "City Commission Meeting",
            "StartDate": "2026/07/01 19:00:00",
            "MeetingDocumentLink": [
                {
                    "Type": "Agenda",
                    "Format": ".pdf",
                    "Title": "Agenda (PDF)",
                    "Url": "FileStream.ashx?DocumentId=30000",
                }
            ],
        },
    ]
}

JSON_BAD_DATE = {
    "d": [
        {
            "ID": "22222222-2222-2222-2222-222222222222",
            "MeetingName": "City Commission Meeting",
            "MeetingType": "City Commission Meeting",
            "StartDate": "not a date",
            "MeetingDocumentLink": [
                {
                    "Type": "Agenda",
                    "Format": ".pdf",
                    "Title": "Agenda (PDF)",
                    "Url": "FileStream.ashx?DocumentId=30100",
                }
            ],
        }
    ]
}

JSON_DASH_DATE = {
    "d": [
        {
            "ID": "33333333-3333-3333-3333-333333333333",
            "MeetingName": "City Commission Meeting",
            "MeetingType": "City Commission Meeting",
            "StartDate": "2026-02-05 19:00:00",
            "MeetingDocumentLink": [
                {
                    "Type": "Agenda",
                    "Format": ".pdf",
                    "Title": "Agenda (PDF)",
                    "Url": "FileStream.ashx?DocumentId=30200",
                }
            ],
        }
    ]
}

JSON_EMPTY_D = {"d": []}

JSON_BAD_SHAPE = {"d": "not a list"}

JSON_MISSING_D = {}


# --- Helpers --------------------------------------------------------------

def _mock_post_response(payload, status_code=200, raise_for_status=None):
    resp = MagicMock()
    resp.status_code = status_code
    resp.json = MagicMock(return_value=payload)
    if raise_for_status is None:
        resp.raise_for_status = MagicMock()
    else:
        resp.raise_for_status = raise_for_status
    return resp


def _cfg(
    tenant_host="pub-hainescity.escribemeetings.com",
    body_filter=("City Commission Meeting", "City Commission Special Meeting"),
    body_label="City Commission",
):
    return {
        "platform": "escribe",
        "tenant_host": tenant_host,
        "body_filter": list(body_filter),
        "body_label": body_label,
    }


# --- 1. Factory registration ---------------------------------------------

class FactoryRegistrationTests(unittest.TestCase):
    def test_factory_returns_escribe_scraper(self):
        scraper = PlatformScraper.for_platform("escribe")
        self.assertIsInstance(scraper, EscribeScraper)

    def test_factory_raises_for_unknown_platform(self):
        with self.assertRaises(ValueError):
            PlatformScraper.for_platform("not_a_real_platform_xyz")


# --- 2. Missing / malformed config ---------------------------------------

class MissingConfigTests(unittest.TestCase):
    @patch("modules.commission.scrapers.escribe.requests.post")
    def test_missing_tenant_host_returns_empty(self, mock_post):
        cfg = _cfg()
        cfg.pop("tenant_host")
        scraper = EscribeScraper()
        self.assertEqual(
            scraper.fetch_listings(cfg, "2026-01-01", "2026-12-31"), []
        )
        mock_post.assert_not_called()

    @patch("modules.commission.scrapers.escribe.requests.post")
    def test_missing_body_filter_returns_empty(self, mock_post):
        cfg = _cfg()
        cfg.pop("body_filter")
        scraper = EscribeScraper()
        self.assertEqual(
            scraper.fetch_listings(cfg, "2026-01-01", "2026-12-31"), []
        )
        mock_post.assert_not_called()

    @patch("modules.commission.scrapers.escribe.requests.post")
    def test_missing_body_label_returns_empty(self, mock_post):
        cfg = _cfg()
        cfg.pop("body_label")
        scraper = EscribeScraper()
        self.assertEqual(
            scraper.fetch_listings(cfg, "2026-01-01", "2026-12-31"), []
        )
        mock_post.assert_not_called()

    @patch("modules.commission.scrapers.escribe.requests.post")
    def test_empty_body_filter_list_returns_empty(self, mock_post):
        cfg = _cfg(body_filter=())
        scraper = EscribeScraper()
        self.assertEqual(
            scraper.fetch_listings(cfg, "2026-01-01", "2026-12-31"), []
        )
        mock_post.assert_not_called()

    @patch("modules.commission.scrapers.escribe.requests.post")
    def test_bad_date_range_returns_empty(self, mock_post):
        scraper = EscribeScraper()
        self.assertEqual(
            scraper.fetch_listings(_cfg(), "nope", "2026-12-31"), []
        )
        mock_post.assert_not_called()

    @patch("modules.commission.scrapers.escribe.requests.post")
    def test_inverted_date_range_returns_empty_without_network(self, mock_post):
        scraper = EscribeScraper()
        self.assertEqual(
            scraper.fetch_listings(_cfg(), "2026-12-31", "2026-01-01"), []
        )
        mock_post.assert_not_called()


# --- 3. Body filter ------------------------------------------------------

class BodyFilterTests(unittest.TestCase):
    @patch("modules.commission.scrapers.escribe.requests.post")
    def test_cc_filter_returns_only_cc_rows(self, mock_post):
        mock_post.return_value = _mock_post_response(copy.deepcopy(JSON_MULTI_BODY))
        scraper = EscribeScraper()
        listings = scraper.fetch_listings(
            _cfg(body_filter=(
                "City Commission Meeting",
                "City Commission Special Meeting",
            )),
            "2026-01-01",
            "2026-12-31",
        )
        self.assertEqual(len(listings), 2)
        dates = sorted(l.date_str for l in listings)
        self.assertEqual(dates, ["2026-02-05", "2026-03-10"])
        for l in listings:
            self.assertEqual(l.title, "City Commission")

    @patch("modules.commission.scrapers.escribe.requests.post")
    def test_pc_filter_excludes_cc(self, mock_post):
        mock_post.return_value = _mock_post_response(copy.deepcopy(JSON_MULTI_BODY))
        scraper = EscribeScraper()
        listings = scraper.fetch_listings(
            _cfg(body_filter=("Planning Commission",),
                 body_label="Planning Commission"),
            "2026-01-01",
            "2026-12-31",
        )
        self.assertEqual(len(listings), 1)
        self.assertEqual(listings[0].date_str, "2026-03-12")
        self.assertEqual(listings[0].title, "Planning Commission")


# --- 4. Document selection ------------------------------------------------

class DocumentSelectionTests(unittest.TestCase):
    @patch("modules.commission.scrapers.escribe.requests.post")
    def test_only_agenda_pdf_doc_selected(self, mock_post):
        mock_post.return_value = _mock_post_response(copy.deepcopy(JSON_MULTI_BODY))
        scraper = EscribeScraper()
        listings = scraper.fetch_listings(
            _cfg(body_filter=("City Commission Meeting",)),
            "2026-02-01",
            "2026-02-28",
        )
        self.assertEqual(len(listings), 1)
        # Must be DocumentId=27357 (the Agenda/.pdf), not 27358 (cover),
        # not 22976 (minutes), not Meeting.aspx (HTML).
        self.assertIn("DocumentId=27357", listings[0].url)
        self.assertNotIn("Meeting.aspx", listings[0].url)
        self.assertNotIn("27358", listings[0].url)
        self.assertNotIn("22976", listings[0].url)

    @patch("modules.commission.scrapers.escribe.requests.post")
    def test_no_agenda_pdf_returns_no_listing(self, mock_post):
        mock_post.return_value = _mock_post_response(copy.deepcopy(JSON_NO_AGENDA_PDF))
        scraper = EscribeScraper()
        listings = scraper.fetch_listings(
            _cfg(body_filter=("City Commission Meeting",)),
            "2026-01-01",
            "2026-12-31",
        )
        self.assertEqual(listings, [])

    @patch("modules.commission.scrapers.escribe.requests.post")
    def test_null_or_empty_docs_list_skipped(self, mock_post):
        scraper = EscribeScraper()
        # Empty list case
        mock_post.return_value = _mock_post_response(copy.deepcopy(JSON_EMPTY_DOCS))
        self.assertEqual(
            scraper.fetch_listings(
                _cfg(body_filter=("City Commission Meeting",)),
                "2026-01-01",
                "2026-12-31",
            ),
            [],
        )
        # None case
        mock_post.return_value = _mock_post_response(copy.deepcopy(JSON_NULL_DOCS))
        self.assertEqual(
            scraper.fetch_listings(
                _cfg(body_filter=("City Commission Meeting",)),
                "2026-01-01",
                "2026-12-31",
            ),
            [],
        )

    @patch("modules.commission.scrapers.escribe.requests.post")
    def test_bad_start_date_skipped(self, mock_post):
        mock_post.return_value = _mock_post_response(copy.deepcopy(JSON_BAD_DATE))
        scraper = EscribeScraper()
        listings = scraper.fetch_listings(
            _cfg(body_filter=("City Commission Meeting",)),
            "2026-01-01",
            "2026-12-31",
        )
        self.assertEqual(listings, [])


# --- 5. Date parsing -----------------------------------------------------

class DateParsingTests(unittest.TestCase):
    @patch("modules.commission.scrapers.escribe.requests.post")
    def test_slash_format_parses(self, mock_post):
        mock_post.return_value = _mock_post_response(copy.deepcopy(JSON_MULTI_BODY))
        scraper = EscribeScraper()
        listings = scraper.fetch_listings(
            _cfg(body_filter=("City Commission Meeting",)),
            "2026-02-01",
            "2026-02-28",
        )
        self.assertEqual(len(listings), 1)
        self.assertEqual(listings[0].date_str, "2026-02-05")

    @patch("modules.commission.scrapers.escribe.requests.post")
    def test_dash_format_parses_defensively(self, mock_post):
        mock_post.return_value = _mock_post_response(copy.deepcopy(JSON_DASH_DATE))
        scraper = EscribeScraper()
        listings = scraper.fetch_listings(
            _cfg(body_filter=("City Commission Meeting",)),
            "2026-01-01",
            "2026-12-31",
        )
        self.assertEqual(len(listings), 1)
        self.assertEqual(listings[0].date_str, "2026-02-05")


# --- 6. Date windowing ---------------------------------------------------

class DateWindowingTests(unittest.TestCase):
    @patch("modules.commission.scrapers.escribe.requests.post")
    def test_rows_before_start_excluded(self, mock_post):
        mock_post.return_value = _mock_post_response(copy.deepcopy(JSON_MULTI_BODY))
        scraper = EscribeScraper()
        listings = scraper.fetch_listings(
            _cfg(body_filter=(
                "City Commission Meeting",
                "City Commission Special Meeting",
            )),
            "2026-03-01",
            "2026-12-31",
        )
        self.assertEqual(len(listings), 1)
        self.assertEqual(listings[0].date_str, "2026-03-10")

    @patch("modules.commission.scrapers.escribe.requests.post")
    def test_rows_after_end_excluded(self, mock_post):
        mock_post.return_value = _mock_post_response(copy.deepcopy(JSON_MULTI_BODY))
        scraper = EscribeScraper()
        listings = scraper.fetch_listings(
            _cfg(body_filter=(
                "City Commission Meeting",
                "City Commission Special Meeting",
            )),
            "2026-01-01",
            "2026-02-28",
        )
        self.assertEqual(len(listings), 1)
        self.assertEqual(listings[0].date_str, "2026-02-05")


# --- 7. DocumentListing field population ---------------------------------

class DocumentListingFieldTests(unittest.TestCase):
    @patch("modules.commission.scrapers.escribe.requests.post")
    def test_listing_fields_populated(self, mock_post):
        mock_post.return_value = _mock_post_response(copy.deepcopy(JSON_MULTI_BODY))
        scraper = EscribeScraper()
        listings = scraper.fetch_listings(
            _cfg(body_filter=("City Commission Meeting",)),
            "2026-02-01",
            "2026-02-28",
        )
        self.assertEqual(len(listings), 1)
        l = listings[0]
        self.assertEqual(l.title, "City Commission")
        self.assertEqual(l.document_type, "agenda")
        self.assertEqual(l.file_format, "pdf")
        self.assertEqual(l.date_str, "2026-02-05")
        self.assertEqual(
            l.url,
            "https://pub-hainescity.escribemeetings.com/FileStream.ashx?DocumentId=27357",
        )
        self.assertEqual(l.document_id, "27357")
        self.assertEqual(l.filename, "Agenda_2026-02-05_27357.pdf")


# --- 8. Deduplication ----------------------------------------------------

class DeduplicationTests(unittest.TestCase):
    @patch("modules.commission.scrapers.escribe.requests.post")
    def test_duplicate_meeting_uuids_collapsed(self, mock_post):
        mock_post.return_value = _mock_post_response(copy.deepcopy(JSON_DUPLICATE_UUID))
        scraper = EscribeScraper()
        listings = scraper.fetch_listings(
            _cfg(body_filter=("City Commission Meeting",)),
            "2026-01-01",
            "2026-12-31",
        )
        self.assertEqual(len(listings), 1)


# --- 9. Network failure --------------------------------------------------

class NetworkFailureTests(unittest.TestCase):
    @patch("modules.commission.scrapers.escribe.requests.post")
    def test_network_exception_returns_empty(self, mock_post):
        mock_post.side_effect = requests.RequestException("boom")
        scraper = EscribeScraper()
        listings = scraper.fetch_listings(
            _cfg(body_filter=("City Commission Meeting",)),
            "2026-01-01",
            "2026-12-31",
        )
        self.assertEqual(listings, [])

    @patch("modules.commission.scrapers.escribe.requests.post")
    def test_bad_json_shape_returns_empty(self, mock_post):
        scraper = EscribeScraper()
        mock_post.return_value = _mock_post_response(copy.deepcopy(JSON_BAD_SHAPE))
        self.assertEqual(
            scraper.fetch_listings(
                _cfg(body_filter=("City Commission Meeting",)),
                "2026-01-01",
                "2026-12-31",
            ),
            [],
        )
        mock_post.return_value = _mock_post_response(copy.deepcopy(JSON_MISSING_D))
        self.assertEqual(
            scraper.fetch_listings(
                _cfg(body_filter=("City Commission Meeting",)),
                "2026-01-01",
                "2026-12-31",
            ),
            [],
        )


# --- 10. download_document -----------------------------------------------

class DownloadDocumentTests(unittest.TestCase):
    def _listing(self, filename="Agenda_2026-02-05_27357.pdf"):
        return DocumentListing(
            title="City Commission",
            url="https://pub-hainescity.escribemeetings.com/FileStream.ashx?DocumentId=27357",
            date_str="2026-02-05",
            document_id="27357",
            document_type="agenda",
            file_format="pdf",
            filename=filename,
        )

    @patch("modules.commission.scrapers.escribe.requests.get")
    def test_download_writes_file(self, mock_get):
        pdf_bytes = b"%PDF-1.7\n%test\n"
        resp = MagicMock()
        resp.raise_for_status = MagicMock()
        resp.iter_content = MagicMock(return_value=iter([pdf_bytes]))
        mock_get.return_value = resp

        scraper = EscribeScraper()
        listing = self._listing()
        with tempfile.TemporaryDirectory() as tmp:
            path = scraper.download_document(listing, tmp)
            self.assertEqual(os.path.basename(path), listing.filename)
            self.assertTrue(os.path.exists(path))
            with open(path, "rb") as fh:
                self.assertEqual(fh.read(), pdf_bytes)

    @patch("modules.commission.scrapers.escribe.requests.get")
    def test_download_creates_nested_output_dir(self, mock_get):
        resp = MagicMock()
        resp.raise_for_status = MagicMock()
        resp.iter_content = MagicMock(return_value=iter([b"%PDF-1.7\n"]))
        mock_get.return_value = resp

        scraper = EscribeScraper()
        listing = self._listing()
        with tempfile.TemporaryDirectory() as tmp:
            nested = os.path.join(tmp, "a", "b", "c")
            self.assertFalse(os.path.exists(nested))
            path = scraper.download_document(listing, nested)
            self.assertTrue(os.path.exists(nested))
            self.assertTrue(os.path.exists(path))


if __name__ == "__main__":
    unittest.main()
