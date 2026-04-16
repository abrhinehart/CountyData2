"""Unit tests for the Legistar scraper — event items, votes, and config flag gating."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from modules.commission.scrapers.legistar import LegistarScraper


# ── _fetch_event_items ─────────────────────────────────────────────────

def test_fetch_event_items_parses_items_and_votes():
    """Verify _fetch_event_items calls the API and normalizes response."""
    scraper = LegistarScraper()

    items_response = MagicMock()
    items_response.status_code = 200
    items_response.raise_for_status = MagicMock()
    items_response.json.return_value = [
        {
            "EventItemId": 101,
            "EventItemTitle": "Rezoning Case RZ-2026-01",
            "EventItemActionName": "Approved",
            "EventItemActionText": "Motion to approve",
            "EventItemPassedFlag": 1,
            "EventItemMover": "Commissioner Jones",
            "EventItemSeconder": "Commissioner Smith",
            "EventItemMatterId": 5001,
            "EventItemMatterFile": "RZ-2026-01",
            "EventItemMatterName": "Rezoning Request",
            "EventItemMatterType": "Ordinance",
        },
    ]

    votes_response = MagicMock()
    votes_response.status_code = 200
    votes_response.raise_for_status = MagicMock()
    votes_response.json.return_value = [
        {"VotePersonName": "Commissioner Jones", "VoteValueName": "Aye"},
        {"VotePersonName": "Commissioner Smith", "VoteValueName": "Aye"},
        {"VotePersonName": "Commissioner Brown", "VoteValueName": "Nay"},
    ]

    with patch("modules.commission.scrapers.legistar.requests.get") as mock_get, \
         patch("modules.commission.scrapers.legistar.time.sleep"):
        mock_get.side_effect = [items_response, votes_response]
        result = scraper._fetch_event_items("testclient", 999)

    assert len(result) == 1
    item = result[0]
    assert item["event_item_id"] == 101
    assert item["item_title"] == "Rezoning Case RZ-2026-01"
    assert item["item_action_name"] == "Approved"
    assert item["item_passed_flag"] == 1
    assert item["item_mover"] == "Commissioner Jones"
    assert item["item_seconder"] == "Commissioner Smith"
    assert item["matter_id"] == 5001
    assert item["matter_file"] == "RZ-2026-01"
    assert item["matter_name"] == "Rezoning Request"
    assert item["matter_type"] == "Ordinance"

    assert len(item["votes"]) == 3
    assert item["votes"][0]["person_name"] == "Commissioner Jones"
    assert item["votes"][0]["vote_value"] == "Aye"
    assert item["votes"][2]["vote_value"] == "Nay"


def test_fetch_event_items_api_error_returns_empty():
    """If the event items API call fails, return empty list."""
    import requests as req

    scraper = LegistarScraper()

    with patch("modules.commission.scrapers.legistar.requests.get") as mock_get:
        mock_get.side_effect = req.RequestException("Connection error")
        result = scraper._fetch_event_items("testclient", 999)

    assert result == []


# ── _fetch_item_votes ──────────────────────────────────────────────────

def test_fetch_item_votes_parses_votes():
    """Verify _fetch_item_votes normalizes vote records."""
    scraper = LegistarScraper()

    votes_response = MagicMock()
    votes_response.status_code = 200
    votes_response.raise_for_status = MagicMock()
    votes_response.json.return_value = [
        {"VotePersonName": "Alice", "VoteValueName": "Aye"},
        {"VotePersonName": "Bob", "VoteValueName": "Nay"},
    ]

    with patch("modules.commission.scrapers.legistar.requests.get", return_value=votes_response):
        result = scraper._fetch_item_votes("testclient", 101)

    assert len(result) == 2
    assert result[0] == {"person_name": "Alice", "vote_value": "Aye"}
    assert result[1] == {"person_name": "Bob", "vote_value": "Nay"}


def test_fetch_item_votes_api_error_returns_empty():
    """If the votes API call fails, return empty list."""
    import requests as req

    scraper = LegistarScraper()

    with patch("modules.commission.scrapers.legistar.requests.get") as mock_get:
        mock_get.side_effect = req.RequestException("Timeout")
        result = scraper._fetch_item_votes("testclient", 101)

    assert result == []


# ── Retry behavior on transient ConnectionError ───────────────────────

def test_get_json_with_retry_recovers_from_connection_error():
    """First call raises ConnectionError (RemoteDisconnected style); retry succeeds."""
    import requests as req

    scraper = LegistarScraper()

    success_response = MagicMock()
    success_response.raise_for_status = MagicMock()
    success_response.json.return_value = [{"VotePersonName": "Alice", "VoteValueName": "Aye"}]

    with patch("modules.commission.scrapers.legistar.requests.get") as mock_get, \
         patch("modules.commission.scrapers.legistar.time.sleep"):
        mock_get.side_effect = [req.ConnectionError("RemoteDisconnected"), success_response]
        result = scraper._fetch_item_votes("testclient", 101)

    # Retry produced the successful payload
    assert len(result) == 1
    assert result[0]["person_name"] == "Alice"
    # Confirm two attempts occurred
    assert mock_get.call_count == 2


def test_get_json_with_retry_gives_up_after_final_attempt():
    """Both attempts raise ConnectionError; caller receives empty list (graceful)."""
    import requests as req

    scraper = LegistarScraper()

    with patch("modules.commission.scrapers.legistar.requests.get") as mock_get, \
         patch("modules.commission.scrapers.legistar.time.sleep"):
        mock_get.side_effect = req.ConnectionError("RemoteDisconnected")
        result = scraper._fetch_item_votes("testclient", 101)

    assert result == []
    # Default retries=1, so two attempts total
    assert mock_get.call_count == 2


# ── Config flag gating ─────────────────────────────────────────────────

def test_event_items_not_fetched_without_config_flag():
    """When fetch_event_items is not set, structured_items should be None."""
    scraper = LegistarScraper()

    event = {
        "EventId": 100,
        "EventDate": "2026-03-01T00:00:00",
        "EventBodyName": "Board of County Commissioners",
        "EventAgendaFile": "https://example.com/agenda.pdf",
        "EventMinutesFile": None,
    }

    seen_ids = set()
    listings = list(scraper._event_to_listings(event, seen_ids, config={}))

    assert len(listings) == 1
    assert listings[0].structured_items is None


def test_event_items_not_fetched_when_flag_false():
    """When fetch_event_items is explicitly false, structured_items should be None."""
    scraper = LegistarScraper()

    event = {
        "EventId": 100,
        "EventDate": "2026-03-01T00:00:00",
        "EventBodyName": "Board of County Commissioners",
        "EventAgendaFile": "https://example.com/agenda.pdf",
        "EventMinutesFile": None,
    }

    seen_ids = set()
    listings = list(scraper._event_to_listings(
        event, seen_ids, config={"fetch_event_items": False, "legistar_client": "test"},
    ))

    assert len(listings) == 1
    assert listings[0].structured_items is None


def test_event_items_fetched_when_flag_true():
    """When fetch_event_items is true, structured_items should be populated."""
    scraper = LegistarScraper()

    event = {
        "EventId": 200,
        "EventDate": "2026-03-15T00:00:00",
        "EventBodyName": "Planning Commission",
        "EventAgendaFile": "https://example.com/agenda.pdf",
        "EventMinutesFile": "https://example.com/minutes.pdf",
    }

    items_response = MagicMock()
    items_response.status_code = 200
    items_response.raise_for_status = MagicMock()
    items_response.json.return_value = [
        {
            "EventItemId": 301,
            "EventItemTitle": "Site Plan SP-2026-05",
            "EventItemActionName": None,
            "EventItemActionText": None,
            "EventItemPassedFlag": None,
            "EventItemMover": None,
            "EventItemSeconder": None,
            "EventItemMatterId": None,
            "EventItemMatterFile": None,
            "EventItemMatterName": None,
            "EventItemMatterType": None,
        },
    ]

    votes_response = MagicMock()
    votes_response.status_code = 200
    votes_response.raise_for_status = MagicMock()
    votes_response.json.return_value = []

    with patch("modules.commission.scrapers.legistar.requests.get") as mock_get, \
         patch("modules.commission.scrapers.legistar.time.sleep"):
        mock_get.side_effect = [items_response, votes_response]

        seen_ids = set()
        config = {"fetch_event_items": True, "legistar_client": "testclient"}
        listings = list(scraper._event_to_listings(event, seen_ids, config=config))

    # Both agenda and minutes should have the same structured_items
    assert len(listings) == 2
    for listing in listings:
        assert listing.structured_items is not None
        assert len(listing.structured_items) == 1
        assert listing.structured_items[0]["event_item_id"] == 301
        assert listing.structured_items[0]["item_title"] == "Site Plan SP-2026-05"
        assert listing.structured_items[0]["votes"] == []


# ── DocumentListing backward compatibility ─────────────────────────────

def test_document_listing_default_structured_items():
    """DocumentListing should default structured_items to None."""
    from modules.commission.scrapers.base import DocumentListing

    listing = DocumentListing(
        title="Test Agenda",
        url="https://example.com/agenda.pdf",
        date_str="2026-03-01",
        document_id="123",
        document_type="agenda",
        file_format="pdf",
        filename="Agenda_2026-03-01_123.pdf",
    )
    assert listing.structured_items is None


def test_document_listing_with_structured_items():
    """DocumentListing can accept structured_items."""
    from modules.commission.scrapers.base import DocumentListing

    items = [{"event_item_id": 1, "item_title": "Test"}]
    listing = DocumentListing(
        title="Test Agenda",
        url="https://example.com/agenda.pdf",
        date_str="2026-03-01",
        document_id="123",
        document_type="agenda",
        file_format="pdf",
        filename="Agenda_2026-03-01_123.pdf",
        structured_items=items,
    )
    assert listing.structured_items == items


# ── LEGISTAR-08: agenda-preview emission ──────────────────────────────

def test_preview_listing_emitted_when_agenda_null_and_items_present():
    """Null agenda+minutes + structured items + InSiteURL → preview listing."""
    scraper = LegistarScraper()

    event = {
        "EventId": 500,
        "EventDate": "2026-05-15T00:00:00",
        "EventBodyName": "Board of County Commissioners",
        "EventAgendaFile": None,
        "EventMinutesFile": None,
        "EventInSiteURL": "https://polkcountyfl.legistar.com/MeetingDetail.aspx?LEGID=500",
    }

    items_response = MagicMock()
    items_response.raise_for_status = MagicMock()
    items_response.json.return_value = [{
        "EventItemId": 700, "EventItemTitle": "Rezoning RZ-2026-99",
        "EventItemActionName": None, "EventItemActionText": None,
        "EventItemPassedFlag": None, "EventItemMover": None,
        "EventItemSeconder": None, "EventItemMatterId": None,
        "EventItemMatterFile": None, "EventItemMatterName": None,
        "EventItemMatterType": None,
    }]
    votes_response = MagicMock()
    votes_response.raise_for_status = MagicMock()
    votes_response.json.return_value = []

    with patch("modules.commission.scrapers.legistar.requests.get") as mock_get, \
         patch("modules.commission.scrapers.legistar.time.sleep"):
        mock_get.side_effect = [items_response, votes_response]
        seen = set()
        listings = list(scraper._event_to_listings(
            event, seen,
            config={"fetch_event_items": True, "legistar_client": "polkcountyfl"},
        ))

    assert len(listings) == 1
    l = listings[0]
    assert l.document_type == "agenda"
    assert l.file_format == "html"
    assert l.document_id == "preview-500"
    assert l.filename == "AgendaPreview_2026-05-15_500.html"
    assert l.url == "https://polkcountyfl.legistar.com/MeetingDetail.aspx?LEGID=500"
    assert l.structured_items and l.structured_items[0]["event_item_id"] == 700


def test_preview_listing_not_emitted_when_agenda_present():
    """Published event keeps the old behavior: agenda yielded, no preview."""
    scraper = LegistarScraper()
    event = {
        "EventId": 501,
        "EventDate": "2026-05-15T00:00:00",
        "EventBodyName": "Planning Commission",
        "EventAgendaFile": "https://example.com/agenda.pdf",
        "EventMinutesFile": None,
        "EventInSiteURL": "https://polkcountyfl.legistar.com/MeetingDetail.aspx?LEGID=501",
    }
    items_response = MagicMock()
    items_response.raise_for_status = MagicMock()
    items_response.json.return_value = []

    with patch("modules.commission.scrapers.legistar.requests.get") as mock_get, \
         patch("modules.commission.scrapers.legistar.time.sleep"):
        mock_get.side_effect = [items_response]
        seen = set()
        listings = list(scraper._event_to_listings(
            event, seen,
            config={"fetch_event_items": True, "legistar_client": "polkcountyfl"},
        ))

    assert len(listings) == 1
    assert listings[0].document_type == "agenda"
    assert listings[0].document_id == "501"
    assert "preview" not in listings[0].filename.lower()


def test_preview_listing_not_emitted_when_items_empty():
    """Null agenda + empty structured_items (no EventItems returned) → no listing.

    Critical gate: must NOT emit a listing for truly empty upcoming events,
    or the review queue will flood with placeholder entries.
    """
    scraper = LegistarScraper()
    event = {
        "EventId": 502,
        "EventDate": "2026-05-15T00:00:00",
        "EventBodyName": "Board of County Commissioners",
        "EventAgendaFile": None,
        "EventMinutesFile": None,
        "EventInSiteURL": "https://polkcountyfl.legistar.com/MeetingDetail.aspx?LEGID=502",
    }
    items_response = MagicMock()
    items_response.raise_for_status = MagicMock()
    items_response.json.return_value = []

    with patch("modules.commission.scrapers.legistar.requests.get") as mock_get, \
         patch("modules.commission.scrapers.legistar.time.sleep"):
        mock_get.side_effect = [items_response]
        seen = set()
        listings = list(scraper._event_to_listings(
            event, seen,
            config={"fetch_event_items": True, "legistar_client": "polkcountyfl"},
        ))

    assert listings == []


def test_preview_listing_not_emitted_when_fetch_flag_off():
    """Null agenda + no fetch_event_items flag → no listing (never fetches items)."""
    scraper = LegistarScraper()
    event = {
        "EventId": 503,
        "EventDate": "2026-05-15T00:00:00",
        "EventBodyName": "Board of County Commissioners",
        "EventAgendaFile": None,
        "EventMinutesFile": None,
        "EventInSiteURL": "https://polkcountyfl.legistar.com/MeetingDetail.aspx?LEGID=503",
    }
    seen = set()
    listings = list(scraper._event_to_listings(
        event, seen, config={"legistar_client": "polkcountyfl"},
    ))
    assert listings == []


# ── LEGISTAR-04: per-event metadata capture ───────────────────────────

def _metadata_event_payload():
    """Shared fixture for a fully-populated event with all 7 metadata source fields."""
    return {
        "EventId": 600,
        "EventDate": "2026-04-13T00:00:00",
        "EventBodyName": "Board of County Commissioners",
        "EventAgendaFile": "https://example.com/agenda.pdf",
        "EventMinutesFile": "https://example.com/minutes.pdf",
        "EventInSiteURL": "https://polkcountyfl.legistar.com/MeetingDetail.aspx?LEGID=600",
        "EventLocation": "County Administration Building, Room 101",
        "EventTime": "9:00 AM",
        "EventComment": "Regular meeting; public hearings at 1:30 PM",
        "EventAgendaStatusName": "Final",
        "EventAgendaLastPublishedUTC": "2026-04-10T18:30:00.123",
        "EventMinutesStatusName": "Draft",
        "EventMinutesLastPublishedUTC": "2026-04-13T22:45:00.000",
    }


def _assert_all_metadata_populated(listing):
    assert listing.event_portal_url == "https://polkcountyfl.legistar.com/MeetingDetail.aspx?LEGID=600"
    assert listing.event_location == "County Administration Building, Room 101"
    assert listing.event_time == "9:00 AM"
    assert listing.event_comment == "Regular meeting; public hearings at 1:30 PM"
    assert listing.agenda_status_name == "Final"
    assert listing.agenda_last_published_utc == "2026-04-10T18:30:00.123"
    assert listing.minutes_status_name == "Draft"
    assert listing.minutes_last_published_utc == "2026-04-13T22:45:00.000"


def test_event_metadata_populated_on_agenda_listing():
    """Event with all 7 source metadata fields → agenda listing carries all 8 fields."""
    scraper = LegistarScraper()
    event = _metadata_event_payload()

    seen = set()
    listings = list(scraper._event_to_listings(event, seen, config={}))

    agenda = next(l for l in listings if l.document_type == "agenda")
    _assert_all_metadata_populated(agenda)


def test_event_metadata_populated_on_minutes_listing():
    """Same event → minutes listing also carries all 8 fields."""
    scraper = LegistarScraper()
    event = _metadata_event_payload()

    seen = set()
    listings = list(scraper._event_to_listings(event, seen, config={}))

    minutes = next(l for l in listings if l.document_type == "minutes")
    _assert_all_metadata_populated(minutes)


def test_event_metadata_populated_on_preview_listing():
    """Null agenda+minutes + structured items + metadata → preview listing carries metadata."""
    scraper = LegistarScraper()
    event = _metadata_event_payload()
    event["EventAgendaFile"] = None
    event["EventMinutesFile"] = None

    items_response = MagicMock()
    items_response.raise_for_status = MagicMock()
    items_response.json.return_value = [{
        "EventItemId": 801, "EventItemTitle": "Placeholder",
        "EventItemActionName": None, "EventItemActionText": None,
        "EventItemPassedFlag": None, "EventItemMover": None,
        "EventItemSeconder": None, "EventItemMatterId": None,
        "EventItemMatterFile": None, "EventItemMatterName": None,
        "EventItemMatterType": None,
    }]
    votes_response = MagicMock()
    votes_response.raise_for_status = MagicMock()
    votes_response.json.return_value = []

    with patch("modules.commission.scrapers.legistar.requests.get") as mock_get, \
         patch("modules.commission.scrapers.legistar.time.sleep"):
        mock_get.side_effect = [items_response, votes_response]
        seen = set()
        listings = list(scraper._event_to_listings(
            event, seen,
            config={"fetch_event_items": True, "legistar_client": "polkcountyfl"},
        ))

    assert len(listings) == 1
    preview = listings[0]
    assert preview.document_id == "preview-600"
    _assert_all_metadata_populated(preview)


def test_event_metadata_handles_missing_fields():
    """Event with only the bare minimum → all 8 metadata fields are None."""
    scraper = LegistarScraper()
    event = {
        "EventId": 700,
        "EventDate": "2026-06-01T00:00:00",
        "EventBodyName": "Planning Commission",
        "EventAgendaFile": "https://example.com/agenda.pdf",
    }

    seen = set()
    listings = list(scraper._event_to_listings(event, seen, config={}))

    assert len(listings) == 1
    l = listings[0]
    assert l.event_portal_url is None
    assert l.event_location is None
    assert l.event_time is None
    assert l.event_comment is None
    assert l.agenda_status_name is None
    assert l.agenda_last_published_utc is None
    assert l.minutes_status_name is None
    assert l.minutes_last_published_utc is None


def test_parse_event_utc_handles_legistar_format():
    """parse_event_utc: valid Legistar ISO → tz-aware UTC; None/garbage → None."""
    from datetime import datetime, timezone

    from modules.commission.scrapers.legistar import parse_event_utc

    parsed = parse_event_utc("2026-04-13T12:51:54.823")
    assert parsed == datetime(2026, 4, 13, 12, 51, 54, 823000, tzinfo=timezone.utc)
    assert parsed.tzinfo is not None

    assert parse_event_utc(None) is None
    assert parse_event_utc("") is None
    assert parse_event_utc("garbage") is None
