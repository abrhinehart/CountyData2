"""CivicClerk scraper using the public OData API.

CivicClerk exposes a public OData v4 API at:
    https://{subdomain}.api.civicclerk.com/v1/

Flow:
    1. GET /v1/Events  — list events filtered by date range and category
    2. GET /v1/Meetings/{agendaId}  — get published files for an event
    3. GET the file URL from Meetings — returns JSON with a blobUri
    4. Download the blobUri (Azure Blob SAS URL) for the actual PDF

Some CivicClerk portals do not expose the API (404).  The scraper handles
this gracefully by logging a warning and returning an empty list.
"""

import logging
import os
import re
import time
from urllib.parse import quote

import requests

from modules.commission.constants import (
    FILE_READ_CHUNK_SIZE,
    SCRAPE_DOWNLOAD_TIMEOUT,
    SCRAPE_SEARCH_TIMEOUT,
)
from modules.commission.scrapers.base import DocumentListing, PlatformScraper

logger = logging.getLogger("commission_radar.scrapers.civicclerk")

USER_AGENT = "CommissionRadar/1.0"
REQUEST_DELAY = 1.0  # seconds between API calls

# CivicClerk's OData endpoint enforces a server-side page cap (typically 15).
# We page via @odata.nextLink. Cap the loop to bound worst-case latency.
CIVICCLERK_MAX_PAGES = 100

# Map CivicClerk file type names to our document types.
# "Agenda" is the short index with structured items — this is what we extract from.
# "Agenda Packet" is the full backup bundle (hundreds of pages) — skip it to avoid
# sending massive documents to Claude. Packet PDFs are used separately by the
# acreage enrichment pipeline.
# "Minutes" maps to "minutes". Everything else (e.g. "Change Sheet") is skipped.
FILE_TYPE_MAP = {
    "Agenda": "agenda",
    "Minutes": "minutes",
}

# Regex to extract subdomain from a CivicClerk portal URL.
SUBDOMAIN_RE = re.compile(r"https?://([^.]+)\.portal\.civicclerk\.com")


def _derive_subdomain(config: dict) -> str | None:
    """Return the CivicClerk subdomain from config, deriving it from base_url if needed."""
    subdomain = config.get("civicclerk_subdomain")
    if subdomain:
        return subdomain

    base_url = config.get("base_url", "")
    match = SUBDOMAIN_RE.match(base_url)
    if match:
        return match.group(1)

    return None


class CivicClerkScraper(PlatformScraper):
    """Scraper for CivicClerk platforms via their public OData API.

    Config fields:
        base_url: Portal URL (e.g. "https://colliercofl.portal.civicclerk.com").
        civicclerk_subdomain: Tenant subdomain (e.g. "colliercofl").
            Derived from base_url when not provided.
        category_id: Optional EventCategory ID to filter events for a
            specific board/commission.
        event_name_filter: Optional case-insensitive substring or list of
            substrings; when set, only events whose ``eventName`` contains
            one of the substrings are kept. Use this when a category is
            overloaded with multiple bodies (e.g. BCC mixed with advisory
            boards under the same categoryId).
    """

    def fetch_listings(
        self, config: dict, start_date: str, end_date: str
    ) -> list[DocumentListing]:
        """Fetch document listings from the CivicClerk OData API.

        Args:
            config: Jurisdiction scraping config with base_url and/or
                civicclerk_subdomain, plus optional category_id.
            start_date: YYYY-MM-DD inclusive start.
            end_date: YYYY-MM-DD inclusive end.

        Returns:
            List of DocumentListing objects with fully-resolved blob URLs.
        """
        subdomain = _derive_subdomain(config)
        if not subdomain:
            logger.warning(
                "CivicClerk scraper requires base_url or civicclerk_subdomain in config"
            )
            return []

        api_base = f"https://{subdomain}.api.civicclerk.com/v1"
        session = requests.Session()
        session.headers.update({"User-Agent": USER_AGENT})

        # --- Step 1: fetch events ---
        events = self._fetch_events(
            session, api_base, config.get("category_id"), start_date, end_date
        )
        if events is None:
            # API returned 404 — portal does not expose the API.
            return []

        logger.info("CivicClerk %s: found %d events in date range", subdomain, len(events))

        # --- Step 1b: optional event-name filter for overloaded categories ---
        raw_filter = config.get("event_name_filter")
        if raw_filter:
            patterns = [raw_filter] if isinstance(raw_filter, str) else list(raw_filter)
            patterns_lc = [p.strip().lower() for p in patterns if p and p.strip()]
            if patterns_lc:
                before = len(events)
                events = [
                    e for e in events
                    if any(p in (e.get("eventName") or "").lower() for p in patterns_lc)
                ]
                logger.info(
                    "CivicClerk %s: event_name_filter %r reduced %d -> %d events",
                    subdomain, patterns_lc, before, len(events),
                )

        # --- Step 2-3: for each event, get meeting files and resolve blob URIs ---
        listings: list[DocumentListing] = []
        for event in events:
            agenda_id = event.get("agendaId", 0)
            event_id = event.get("id")
            event_date_raw = event.get("eventDate", "")
            event_name = event.get("eventName", "")

            # Parse date to YYYY-MM-DD
            date_str = event_date_raw[:10] if event_date_raw else "unknown"

            if not agenda_id:
                logger.debug(
                    "Skipping event %s (%s) — no agenda published", event_id, event_name
                )
                continue

            time.sleep(REQUEST_DELAY)
            files = self._fetch_meeting_files(session, api_base, agenda_id)
            if not files:
                continue

            for f in files:
                file_type = f.get("type", "")
                doc_type = FILE_TYPE_MAP.get(file_type)
                if doc_type is None:
                    logger.debug("Skipping file type %r for event %s", file_type, event_id)
                    continue

                file_id = f.get("fileId")
                file_url = f.get("url", "")
                file_name = f.get("name", "")

                if not file_url:
                    continue

                # Resolve to blob URI so download_document is a simple GET.
                time.sleep(REQUEST_DELAY)
                blob_uri = self._resolve_blob_uri(session, file_url)
                if not blob_uri:
                    logger.warning(
                        "Could not resolve blob URI for event %s file %s", event_id, file_id
                    )
                    continue

                type_label = "Minutes" if doc_type == "minutes" else "Agenda"
                filename = f"{type_label}_{date_str}_{event_id}.pdf"

                title = file_name or f"{event_name} — {file_type}"

                listings.append(
                    DocumentListing(
                        title=title,
                        url=blob_uri,
                        date_str=date_str,
                        document_id=f"{event_id}_{file_id}",
                        document_type=doc_type,
                        file_format="pdf",
                        filename=filename,
                    )
                )

        logger.info("CivicClerk %s: resolved %d downloadable documents", subdomain, len(listings))
        return listings

    # --------------------------------------------------------------------- #
    #  API helpers                                                            #
    # --------------------------------------------------------------------- #

    def _fetch_events(
        self,
        session: requests.Session,
        api_base: str,
        category_id: int | str | None,
        start_date: str,
        end_date: str,
    ) -> list[dict] | None:
        """GET /v1/Events with OData filters, following @odata.nextLink.

        Returns None on 404 (portal has no public API). Returns the
        accumulated ``value`` arrays across all pages on success. Bounded
        by CIVICCLERK_MAX_PAGES to prevent runaway loops.
        """
        filters = [
            f"eventDate ge {start_date}T00:00:00Z",
            f"eventDate le {end_date}T23:59:59Z",
        ]
        if category_id:
            filters.append(f"categoryId eq {category_id}")

        params = {
            "$filter": " and ".join(filters),
            "$orderby": "EventDate desc",
        }

        url = f"{api_base}/Events"
        accumulated: list[dict] = []
        next_url: str | None = None
        next_params: dict | None = params

        for page_index in range(CIVICCLERK_MAX_PAGES):
            try:
                if next_url is not None:
                    resp = session.get(next_url, timeout=SCRAPE_SEARCH_TIMEOUT)
                else:
                    resp = session.get(url, params=next_params, timeout=SCRAPE_SEARCH_TIMEOUT)
            except requests.RequestException as exc:
                logger.error("CivicClerk Events request failed: %s", exc)
                return None if page_index == 0 else accumulated

            if resp.status_code == 404:
                logger.warning(
                    "CivicClerk API not available at %s (404). "
                    "This portal may not expose a public API.",
                    resp.url,
                )
                return None if page_index == 0 else accumulated

            try:
                resp.raise_for_status()
            except requests.HTTPError as exc:
                logger.error(
                    "CivicClerk Events request returned %s: %s", resp.status_code, exc
                )
                return None if page_index == 0 else accumulated

            data = resp.json()
            if not isinstance(data, dict):
                return data if page_index == 0 else accumulated

            page_values = data.get("value", [])
            if isinstance(page_values, list):
                accumulated.extend(page_values)

            next_link = data.get("@odata.nextLink")
            if not next_link:
                return accumulated

            next_url = next_link
            next_params = None
        else:
            logger.warning(
                "CivicClerk pagination hit safety cap of %d pages at %s; "
                "returning %d events accumulated so far.",
                CIVICCLERK_MAX_PAGES,
                url,
                len(accumulated),
            )
            return accumulated

    def _fetch_meeting_files(
        self, session: requests.Session, api_base: str, agenda_id: int
    ) -> list[dict]:
        """GET /v1/Meetings/{agendaId} and return its publishedFiles array."""
        url = f"{api_base}/Meetings/{agenda_id}"
        try:
            resp = session.get(url, timeout=SCRAPE_SEARCH_TIMEOUT)
            resp.raise_for_status()
        except requests.RequestException as exc:
            logger.warning("CivicClerk Meetings/%s request failed: %s", agenda_id, exc)
            return []

        data = resp.json()
        files = data.get("publishedFiles", [])
        return files if isinstance(files, list) else []

    def _resolve_blob_uri(self, session: requests.Session, file_url: str) -> str | None:
        """GET the CivicClerk file URL to obtain the Azure Blob SAS blobUri."""
        try:
            resp = session.get(file_url, timeout=SCRAPE_SEARCH_TIMEOUT)
            resp.raise_for_status()
        except requests.RequestException as exc:
            logger.warning("CivicClerk blob resolve failed for %s: %s", file_url, exc)
            return None

        data = resp.json()
        return data.get("blobUri")

    # --------------------------------------------------------------------- #
    #  Download                                                               #
    # --------------------------------------------------------------------- #

    def download_document(self, listing: DocumentListing, output_dir: str) -> str:
        """Download a resolved blob URI to output_dir.

        The listing.url should already be a direct Azure Blob SAS URL
        (resolved during fetch_listings), so this is a straightforward
        streaming download.
        """
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, listing.filename)

        resp = requests.get(
            listing.url,
            headers={"User-Agent": USER_AGENT},
            stream=True,
            timeout=SCRAPE_DOWNLOAD_TIMEOUT,
        )
        resp.raise_for_status()

        with open(filepath, "wb") as fh:
            for chunk in resp.iter_content(chunk_size=FILE_READ_CHUNK_SIZE):
                fh.write(chunk)

        return filepath
