"""Unit tests for modules.commission.scrapers.civicclerk.

Focus on the optional ``event_name_filter`` config field added to handle
overloaded CivicClerk categories (e.g. Santa Rosa County category 24, which
mixes BCC meetings with advisory boards).
"""

import unittest
from unittest.mock import Mock, patch

import requests

from modules.commission.scrapers.base import PlatformScraper
from modules.commission.scrapers.civicclerk import CivicClerkScraper


def _event(event_id: int, name: str, date_iso: str = "2026-04-09T09:00:00Z") -> dict:
    """Build a fake CivicClerk Event dict."""
    return {
        "id": event_id,
        "agendaId": 1000 + event_id,
        "eventDate": date_iso,
        "eventName": name,
    }


def _files_for(event_id: int) -> list[dict]:
    """Single Agenda file per event."""
    return [
        {
            "type": "Agenda",
            "fileId": 9000 + event_id,
            "url": f"https://santarosacofl.api.civicclerk.com/v1/Files/{9000 + event_id}",
            "name": f"Agenda {event_id}",
        }
    ]


def _cfg(**overrides) -> dict:
    base = {
        "platform": "civicclerk",
        "civicclerk_subdomain": "santarosacofl",
        "category_id": 24,
    }
    base.update(overrides)
    return base


class FactoryRegistrationTests(unittest.TestCase):
    def test_factory_returns_civicclerk_scraper(self):
        scraper = PlatformScraper.for_platform("civicclerk")
        self.assertIsInstance(scraper, CivicClerkScraper)


class EventNameFilterTests(unittest.TestCase):
    """The event_name_filter config narrows results within a category."""

    def setUp(self):
        # Patches we use across most tests.
        self._fetch_events_patcher = patch.object(
            CivicClerkScraper, "_fetch_events", autospec=True
        )
        self._fetch_files_patcher = patch.object(
            CivicClerkScraper, "_fetch_meeting_files", autospec=True
        )
        self._resolve_blob_patcher = patch.object(
            CivicClerkScraper, "_resolve_blob_uri", autospec=True
        )
        # Avoid sleeping in tests.
        self._sleep_patcher = patch(
            "modules.commission.scrapers.civicclerk.time.sleep", lambda *_a, **_k: None
        )

        self.mock_fetch_events = self._fetch_events_patcher.start()
        self.mock_fetch_files = self._fetch_files_patcher.start()
        self.mock_resolve_blob = self._resolve_blob_patcher.start()
        self._sleep_patcher.start()

        self.addCleanup(self._fetch_events_patcher.stop)
        self.addCleanup(self._fetch_files_patcher.stop)
        self.addCleanup(self._resolve_blob_patcher.stop)
        self.addCleanup(self._sleep_patcher.stop)

        # Default file/blob behaviour: every event resolves to one Agenda PDF.
        self.mock_fetch_files.side_effect = lambda self_, session, api_base, agenda_id: _files_for(
            agenda_id - 1000
        )
        self.mock_resolve_blob.side_effect = (
            lambda self_, session, file_url: file_url + "?sig=fake"
        )

    def _events(self, *names) -> list[dict]:
        return [_event(i + 1, name) for i, name in enumerate(names)]

    def test_event_name_filter_string_keeps_only_matching_events(self):
        self.mock_fetch_events.return_value = self._events(
            "Commission Regular Meeting",
            "Zoning Board",
            "Aviation Advisory Committee",
        )
        scraper = CivicClerkScraper()
        listings = scraper.fetch_listings(
            _cfg(event_name_filter="commission"), "2026-01-01", "2026-12-31"
        )
        # Only event id=1 (Commission Regular Meeting) survives the filter.
        # document_id is "{event_id}_{file_id}" = "1_9001".
        self.assertEqual(len(listings), 1)
        self.assertEqual(listings[0].document_id, "1_9001")

    def test_event_name_filter_list_unions_patterns(self):
        self.mock_fetch_events.return_value = self._events(
            "Commission Regular Meeting",
            "Commission Committee Meeting",
            "Commission Special Rezoning Meeting",
            "Zoning Board",
        )
        scraper = CivicClerkScraper()
        listings = scraper.fetch_listings(
            _cfg(
                event_name_filter=[
                    "Commission Regular",
                    "Commission Committee",
                    "Commission Special Rezoning",
                ]
            ),
            "2026-01-01",
            "2026-12-31",
        )
        # Three events kept (1, 2, 3); event 4 "Zoning Board" filtered out.
        # document_ids are "{event_id}_{file_id}" = "1_9001", "2_9002", "3_9003".
        self.assertEqual(len(listings), 3)
        kept_event_ids = sorted(int(l.document_id.split("_")[0]) for l in listings)
        self.assertEqual(kept_event_ids, [1, 2, 3])

    def test_event_name_filter_case_insensitive(self):
        self.mock_fetch_events.return_value = self._events("Commission Regular Meeting")
        scraper = CivicClerkScraper()
        listings = scraper.fetch_listings(
            _cfg(event_name_filter="COMMISSION REGULAR"),
            "2026-01-01",
            "2026-12-31",
        )
        self.assertEqual(len(listings), 1)

    def test_event_name_filter_absent_returns_all_events_in_category(self):
        self.mock_fetch_events.return_value = self._events(
            "Commission Regular Meeting",
            "Zoning Board",
            "Aviation Advisory Committee",
        )
        scraper = CivicClerkScraper()
        # No event_name_filter at all.
        listings = scraper.fetch_listings(_cfg(), "2026-01-01", "2026-12-31")
        self.assertEqual(len(listings), 3)

    def test_event_name_filter_empty_string_treated_as_unset(self):
        self.mock_fetch_events.return_value = self._events(
            "Commission Regular Meeting",
            "Zoning Board",
            "Aviation Advisory Committee",
        )
        scraper = CivicClerkScraper()
        listings = scraper.fetch_listings(
            _cfg(event_name_filter=""), "2026-01-01", "2026-12-31"
        )
        self.assertEqual(len(listings), 3)


def _make_response(
    status_code: int = 200,
    json_body: dict | None = None,
    url: str = "https://santarosacofl.api.civicclerk.com/v1/Events",
) -> Mock:
    """Build a Mock that quacks like a requests.Response."""
    resp = Mock()
    resp.status_code = status_code
    resp.url = url
    resp.json.return_value = json_body if json_body is not None else {}
    if status_code >= 400:
        resp.raise_for_status.side_effect = requests.HTTPError(
            f"{status_code} error"
        )
    else:
        resp.raise_for_status.return_value = None
    return resp


class PaginationTests(unittest.TestCase):
    """The _fetch_events helper must follow @odata.nextLink across pages."""

    API_BASE = "https://santarosacofl.api.civicclerk.com/v1"
    START = "2026-01-01"
    END = "2026-12-31"

    def test_fetch_events_follows_odata_nextlink_across_pages(self):
        evt1, evt2, evt3, evt4 = (
            _event(1, "BCC Regular"),
            _event(2, "BCC Special"),
            _event(3, "BCC Workshop"),
            _event(4, "BCC Budget"),
        )
        next1 = "https://santarosacofl.api.civicclerk.com/v1/Events?$skip=2"
        next2 = "https://santarosacofl.api.civicclerk.com/v1/Events?$skip=4"

        page1 = _make_response(
            200, {"value": [evt1, evt2], "@odata.nextLink": next1}
        )
        page2 = _make_response(
            200, {"value": [evt3], "@odata.nextLink": next2}
        )
        page3 = _make_response(200, {"value": [evt4]})

        session = Mock()
        session.get.side_effect = [page1, page2, page3]

        scraper = CivicClerkScraper()
        result = scraper._fetch_events(
            session, self.API_BASE, 24, self.START, self.END
        )

        self.assertEqual(result, [evt1, evt2, evt3, evt4])
        self.assertEqual(session.get.call_count, 3)

        # Call 1: initial GET — uses base URL with params kwarg.
        call1_args, call1_kwargs = session.get.call_args_list[0]
        self.assertEqual(call1_args[0], f"{self.API_BASE}/Events")
        self.assertIn("params", call1_kwargs)
        self.assertIsNotNone(call1_kwargs["params"])

        # Call 2: nextLink URL verbatim, no params kwarg (or params=None).
        call2_args, call2_kwargs = session.get.call_args_list[1]
        self.assertEqual(call2_args[0], next1)
        self.assertIsNone(call2_kwargs.get("params"))

        # Call 3: nextLink URL verbatim, no params kwarg.
        call3_args, call3_kwargs = session.get.call_args_list[2]
        self.assertEqual(call3_args[0], next2)
        self.assertIsNone(call3_kwargs.get("params"))

    def test_fetch_events_terminates_when_no_nextlink_on_first_page(self):
        e1, e2 = _event(1, "BCC A"), _event(2, "BCC B")
        page1 = _make_response(200, {"value": [e1, e2]})

        session = Mock()
        session.get.side_effect = [page1]

        scraper = CivicClerkScraper()
        result = scraper._fetch_events(
            session, self.API_BASE, None, self.START, self.END
        )

        self.assertEqual(session.get.call_count, 1)
        self.assertEqual(result, [e1, e2])

    def test_fetch_events_honors_safety_cap(self):
        e = _event(1, "BCC")
        # Endless responses — each one points to a next page.
        endless = lambda *a, **kw: _make_response(  # noqa: E731
            200,
            {
                "value": [e],
                "@odata.nextLink": "https://santarosacofl.api.civicclerk.com/v1/next",
            },
        )

        session = Mock()
        session.get.side_effect = endless

        scraper = CivicClerkScraper()
        with patch(
            "modules.commission.scrapers.civicclerk.CIVICCLERK_MAX_PAGES", 3
        ):
            with self.assertLogs(
                "commission_radar.scrapers.civicclerk", level="WARNING"
            ) as captured:
                result = scraper._fetch_events(
                    session, self.API_BASE, None, self.START, self.END
                )

        self.assertEqual(session.get.call_count, 3)
        self.assertEqual(len(result), 3)
        # The safety-cap warning fires.
        self.assertTrue(
            any("safety cap" in msg for msg in captured.output),
            f"Expected 'safety cap' warning in {captured.output!r}",
        )

    def test_fetch_events_returns_none_on_first_page_404(self):
        page1 = _make_response(404, {})

        session = Mock()
        session.get.side_effect = [page1]

        scraper = CivicClerkScraper()
        result = scraper._fetch_events(
            session, self.API_BASE, None, self.START, self.END
        )

        self.assertIsNone(result)
        self.assertEqual(session.get.call_count, 1)

    def test_fetch_events_returns_partial_on_midstream_404(self):
        e1 = _event(1, "BCC Page One")
        next1 = "https://santarosacofl.api.civicclerk.com/v1/p2"

        page1 = _make_response(
            200, {"value": [e1], "@odata.nextLink": next1}
        )
        page2 = _make_response(404, {})

        session = Mock()
        session.get.side_effect = [page1, page2]

        scraper = CivicClerkScraper()
        result = scraper._fetch_events(
            session, self.API_BASE, None, self.START, self.END
        )

        self.assertEqual(result, [e1])
        self.assertEqual(session.get.call_count, 2)


if __name__ == "__main__":
    unittest.main()
