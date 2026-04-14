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
