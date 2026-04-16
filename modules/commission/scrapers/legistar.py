import logging
import os
import time
from datetime import datetime

import requests

from modules.commission.constants import (
    FILE_READ_CHUNK_SIZE,
    SCRAPE_DOWNLOAD_TIMEOUT,
    SCRAPE_SEARCH_TIMEOUT,
)
from modules.commission.scrapers.base import PlatformScraper, DocumentListing

logger = logging.getLogger("commission_radar.scrapers.legistar")

API_BASE = "https://webapi.legistar.com/v1"
USER_AGENT = "CommissionRadar/1.0"

# Legistar OData API page size
PAGE_SIZE = 100
# Polite delay between paginated requests (seconds)
REQUEST_DELAY = 0.5


class LegistarScraper(PlatformScraper):
    """Scraper for Legistar platforms using the public OData API.

    Legistar exposes meeting events with agenda/minutes PDFs via:
        https://webapi.legistar.com/v1/{client}/events

    Config fields:
        legistar_client: Client slug (e.g., "brevardfl")
        body_names: List of EventBodyName values to filter by
    """

    def fetch_listings(self, config: dict, start_date: str, end_date: str) -> list[DocumentListing]:
        """Fetch document listings from Legistar OData API.

        Args:
            config: Jurisdiction scraping config with keys:
                - legistar_client: Legistar client identifier
                - body_names: List of body name strings to filter events
            start_date: YYYY-MM-DD
            end_date: YYYY-MM-DD

        Returns:
            List of DocumentListing for both agendas and minutes.
        """
        client = config.get("legistar_client")
        body_names = config.get("body_names", [])

        if not client:
            logger.warning("Legistar scraper requires legistar_client in config")
            return []

        if not body_names:
            logger.warning("Legistar scraper requires body_names in config")
            return []

        listings = []
        seen_ids = set()

        for body_name in body_names:
            body_listings = self._fetch_body_events(
                client, body_name, start_date, end_date, seen_ids,
                config=config,
            )
            listings.extend(body_listings)

        return listings

    def _fetch_body_events(self, client, body_name, start_date, end_date, seen_ids, *, config=None):
        """Fetch events for a single body, handling pagination."""
        listings = []
        skip = 0

        while True:
            events = self._fetch_page(client, body_name, start_date, end_date, skip)
            if events is None:
                break

            for event in events:
                for listing in self._event_to_listings(event, seen_ids, config=config):
                    listings.append(listing)

            if len(events) < PAGE_SIZE:
                break

            skip += PAGE_SIZE
            time.sleep(REQUEST_DELAY)

        return listings

    def _fetch_page(self, client, body_name, start_date, end_date, skip):
        """Fetch a single page of events from the Legistar API."""
        url = f"{API_BASE}/{client}/events"

        odata_filter = (
            f"EventDate ge datetime'{start_date}' "
            f"and EventDate le datetime'{end_date}' "
            f"and EventBodyName eq '{body_name}'"
        )
        params = {
            "$filter": odata_filter,
            "$orderby": "EventDate desc",
            "$top": PAGE_SIZE,
            "$skip": skip,
        }

        try:
            resp = requests.get(
                url, params=params,
                headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
                timeout=SCRAPE_SEARCH_TIMEOUT,
            )
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            logger.error("Legistar API error for %s/%s: %s", client, body_name, e)
            return None

    def _event_to_listings(self, event, seen_ids, *, config: dict | None = None):
        """Convert a Legistar event JSON object into DocumentListing(s)."""
        event_id = str(event.get("EventId", ""))
        if not event_id:
            return

        # Parse date from EventDate (format: "2025-01-13T00:00:00")
        raw_date = event.get("EventDate", "")
        try:
            meeting_date = datetime.strptime(raw_date[:10], "%Y-%m-%d").strftime("%Y-%m-%d")
        except (ValueError, IndexError):
            meeting_date = raw_date[:10] if len(raw_date) >= 10 else "unknown"

        body_name = event.get("EventBodyName", "Meeting")

        # Optionally fetch structured event items + votes
        structured_items = None
        if config and config.get("fetch_event_items"):
            client = config.get("legistar_client")
            if client:
                try:
                    time.sleep(REQUEST_DELAY)
                    structured_items = self._fetch_event_items(client, int(event.get("EventId", 0)))
                except Exception:
                    logger.warning(
                        "Failed to fetch event items for event %s",
                        event_id,
                        exc_info=True,
                    )
                    structured_items = None

        # Agenda PDF
        agenda_url = event.get("EventAgendaFile")
        if agenda_url:
            doc_id = f"agenda-{event_id}"
            if doc_id not in seen_ids:
                seen_ids.add(doc_id)
                yield DocumentListing(
                    title=f"{body_name} Agenda - {meeting_date}",
                    url=agenda_url,
                    date_str=meeting_date,
                    document_id=event_id,
                    document_type="agenda",
                    file_format="pdf",
                    filename=f"Agenda_{meeting_date}_{event_id}.pdf",
                    structured_items=structured_items,
                )

        # Minutes PDF
        minutes_url = event.get("EventMinutesFile")
        if minutes_url:
            doc_id = f"minutes-{event_id}"
            if doc_id not in seen_ids:
                seen_ids.add(doc_id)
                yield DocumentListing(
                    title=f"{body_name} Minutes - {meeting_date}",
                    url=minutes_url,
                    date_str=meeting_date,
                    document_id=event_id,
                    document_type="minutes",
                    file_format="pdf",
                    filename=f"Minutes_{meeting_date}_{event_id}.pdf",
                    structured_items=structured_items,
                )

        # LEGISTAR-08 preview-listing emission:
        # If fetch_event_items is enabled AND we successfully got structured_items
        # AND no agenda/minutes PDF was yielded for this event (both are null),
        # emit a "preview" listing anchored on EventInSiteURL so downstream
        # persistence has a home for the structured items.
        if (
            structured_items
            and not agenda_url
            and not minutes_url
        ):
            in_site_url = event.get("EventInSiteURL")
            if in_site_url:
                preview_doc_id = f"preview-{event_id}"
                if preview_doc_id not in seen_ids:
                    seen_ids.add(preview_doc_id)
                    yield DocumentListing(
                        title=f"{body_name} Agenda Preview - {meeting_date}",
                        url=in_site_url,
                        date_str=meeting_date,
                        document_id=preview_doc_id,
                        document_type="agenda",
                        file_format="html",
                        filename=f"AgendaPreview_{meeting_date}_{event_id}.html",
                        structured_items=structured_items,
                    )

    def _get_json_with_retry(self, url: str, *, retries: int = 1, backoff: float = 1.0):
        """GET a URL expecting JSON. Retry once on transient ConnectionError.

        Legistar occasionally closes connections mid-request (RemoteDisconnected);
        a single retry after a short backoff recovers cleanly most of the time.
        Non-connection errors (4xx/5xx, timeouts, bad JSON) are not retried.
        """
        attempts = retries + 1
        for attempt in range(attempts):
            try:
                resp = requests.get(
                    url,
                    headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
                    timeout=SCRAPE_SEARCH_TIMEOUT,
                )
                resp.raise_for_status()
                return resp.json()
            except requests.ConnectionError as e:
                if attempt + 1 < attempts:
                    logger.info(
                        "Legistar transient connection error on %s (attempt %s/%s); retrying in %ss",
                        url, attempt + 1, attempts, backoff,
                    )
                    time.sleep(backoff)
                    continue
                raise

    def _fetch_event_items(self, client: str, event_id: int) -> list[dict]:
        """Fetch event items and their votes for a Legistar event.

        GET /v1/{client}/events/{event_id}/eventitems
        For each item, fetch votes via _fetch_item_votes.

        Returns normalized list of dicts.
        """
        url = f"{API_BASE}/{client}/events/{event_id}/eventitems"
        items: list[dict] = []

        try:
            raw_items = self._get_json_with_retry(url)
        except requests.RequestException as e:
            logger.error("Legistar event items API error for %s/%s: %s", client, event_id, e)
            return []

        for raw_item in raw_items:
            event_item_id = raw_item.get("EventItemId")
            if not event_item_id:
                continue

            time.sleep(REQUEST_DELAY)
            votes = self._fetch_item_votes(client, event_item_id)

            items.append({
                "event_item_id": event_item_id,
                "item_title": raw_item.get("EventItemTitle"),
                "item_action_name": raw_item.get("EventItemActionName"),
                "item_action_text": raw_item.get("EventItemActionText"),
                "item_passed_flag": raw_item.get("EventItemPassedFlag"),
                "item_mover": raw_item.get("EventItemMover"),
                "item_seconder": raw_item.get("EventItemSeconder"),
                "matter_id": raw_item.get("EventItemMatterId"),
                "matter_file": raw_item.get("EventItemMatterFile"),
                "matter_name": raw_item.get("EventItemMatterName"),
                "matter_type": raw_item.get("EventItemMatterType"),
                "votes": votes,
            })

        return items

    def _fetch_item_votes(self, client: str, event_item_id: int) -> list[dict]:
        """Fetch votes for a single event item.

        GET /v1/{client}/eventitems/{event_item_id}/votes
        """
        url = f"{API_BASE}/{client}/eventitems/{event_item_id}/votes"

        try:
            raw_votes = self._get_json_with_retry(url)
        except requests.RequestException as e:
            logger.error("Legistar votes API error for item %s: %s", event_item_id, e)
            return []

        votes: list[dict] = []
        for raw_vote in raw_votes:
            votes.append({
                "person_name": raw_vote.get("VotePersonName"),
                "vote_value": raw_vote.get("VoteValueName"),
            })

        return votes

    def download_document(self, listing: DocumentListing, output_dir: str) -> str:
        """Download a document from Legistar."""
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, listing.filename)

        resp = requests.get(
            listing.url,
            headers={"User-Agent": USER_AGENT},
            stream=True,
            timeout=SCRAPE_DOWNLOAD_TIMEOUT,
        )
        resp.raise_for_status()

        with open(filepath, "wb") as f:
            for chunk in resp.iter_content(chunk_size=FILE_READ_CHUNK_SIZE):
                f.write(chunk)

        return filepath
