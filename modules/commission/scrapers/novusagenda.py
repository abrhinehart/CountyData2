import logging
import os
import re
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from modules.commission.constants import (
    SCRAPE_SEARCH_TIMEOUT,
    SCRAPE_DOWNLOAD_TIMEOUT,
    FILE_READ_CHUNK_SIZE,
)
from modules.commission.scrapers.base import PlatformScraper, DocumentListing

logger = logging.getLogger("commission_radar.scrapers.novusagenda")

USER_AGENT = "CommissionRadar/1.0"
REQUEST_DELAY = 1.0

# Pattern to extract MeetingID from links. Tenants vary: some (e.g. Bay County)
# link meetings via MeetingView.aspx; others (e.g. North Miami Beach) anchor
# directly to DisplayAgendaPDF.ashx. Both expose MeetingID and both tenants
# accept the MeetingView.aspx URL the scraper builds for download, so we
# match either href pattern here.
MEETING_LINK_RE = re.compile(
    r"(?:MeetingView\.aspx|DisplayAgendaPDF\.ashx)\?MeetingID=(\d+)",
    re.IGNORECASE,
)


class NovusAgendaScraper(PlatformScraper):
    """Scraper for NovusAgenda AgendaPublic platforms.

    Fetches agenda HTML pages by navigating the ASP.NET Meetings search form.
    """

    def fetch_listings(self, config: dict, start_date: str, end_date: str) -> list[DocumentListing]:
        """Fetch document listings from NovusAgenda.

        Args:
            config: Jurisdiction scraping config with keys:
                - base_url: NovusAgenda AgendaPublic URL
                    (e.g. https://baycounty.novusagenda.com/agendapublic)
                - meeting_type_id: (optional) NovusAgenda meeting type filter ID
            start_date: YYYY-MM-DD
            end_date: YYYY-MM-DD

        Returns:
            List of DocumentListing for agenda HTML pages.
        """
        base_url = config.get("base_url")
        if not base_url:
            logger.warning("NovusAgenda scraper requires base_url in config")
            return []

        meeting_type_id = config.get("meeting_type_id")
        session = requests.Session()
        session.headers.update({"User-Agent": USER_AGENT})

        try:
            form_state = self._get_form_state(session, base_url)
        except Exception as exc:
            logger.warning("Failed to load NovusAgenda Meetings page: %s", exc)
            return []

        time.sleep(REQUEST_DELAY)

        try:
            html = self._search_meetings(
                session, base_url, form_state,
                start_date, end_date, meeting_type_id,
            )
        except Exception as exc:
            logger.warning("NovusAgenda search request failed: %s", exc)
            return []

        rows = self._parse_meeting_rows(html, base_url)

        # Dedupe by MeetingID
        seen_ids: set[str] = set()
        listings: list[DocumentListing] = []
        for listing in rows:
            if listing.document_id not in seen_ids:
                seen_ids.add(listing.document_id)
                listings.append(listing)

        return listings

    def download_document(self, listing: DocumentListing, output_dir: str) -> str:
        """Download a NovusAgenda HTML document.

        Args:
            listing: DocumentListing to download.
            output_dir: Local directory to save to.

        Returns:
            Full local file path of the downloaded document.
        """
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, listing.filename)

        resp = requests.get(
            listing.url,
            headers={"User-Agent": USER_AGENT},
            timeout=SCRAPE_DOWNLOAD_TIMEOUT,
        )
        resp.raise_for_status()

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(resp.text)

        return filepath

    # --- Private helpers ---

    def _get_form_state(self, session: requests.Session, base_url: str) -> dict:
        """GET Meetings.aspx to obtain ASP.NET form state fields and session cookie.

        Returns:
            Dict with __VIEWSTATE, __VIEWSTATEGENERATOR, __EVENTVALIDATION.
        """
        url = f"{base_url.rstrip('/')}/Meetings.aspx"
        resp = session.get(url, timeout=SCRAPE_SEARCH_TIMEOUT)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        state: dict[str, str] = {}
        for field_name in ("__VIEWSTATE", "__VIEWSTATEGENERATOR", "__EVENTVALIDATION"):
            tag = soup.find("input", attrs={"name": field_name})
            if tag:
                state[field_name] = tag.get("value", "")
            else:
                state[field_name] = ""
        return state

    def _search_meetings(
        self,
        session: requests.Session,
        base_url: str,
        form_state: dict,
        start_date: str,
        end_date: str,
        meeting_type_id: str | None,
    ) -> str:
        """POST the Meetings.aspx search form and return response HTML."""
        url = f"{base_url.rstrip('/')}/Meetings.aspx"

        data = {
            "__VIEWSTATE": form_state.get("__VIEWSTATE", ""),
            "__VIEWSTATEGENERATOR": form_state.get("__VIEWSTATEGENERATOR", ""),
            "__EVENTVALIDATION": form_state.get("__EVENTVALIDATION", ""),
            "ctl00$ContentPlaceHolder1$txtStartDate": start_date,
            "ctl00$ContentPlaceHolder1$txtEndDate": end_date,
            "ctl00$ContentPlaceHolder1$btnSearch": "Search",
        }

        if meeting_type_id:
            data["ctl00$ContentPlaceHolder1$ddlMeetingType"] = meeting_type_id

        resp = session.post(url, data=data, timeout=SCRAPE_SEARCH_TIMEOUT)
        resp.raise_for_status()
        return resp.text

    def _parse_meeting_rows(self, html: str, base_url: str) -> list[DocumentListing]:
        """Parse search result HTML for meeting links.

        Returns:
            List of DocumentListing objects (may contain duplicates).
        """
        soup = BeautifulSoup(html, "html.parser")
        listings: list[DocumentListing] = []
        base = base_url.rstrip("/")

        for link in soup.find_all("a", href=MEETING_LINK_RE):
            href = link["href"]
            match = MEETING_LINK_RE.search(href)
            if not match:
                continue

            meeting_id = match.group(1)

            # Try to extract date and meeting type from the row
            date_str = self._extract_date_from_row(link)
            meeting_type = self._extract_type_from_row(link)
            title = meeting_type or f"Meeting {meeting_id}"

            agenda_url = (
                f"{base}/MeetingView.aspx"
                f"?MeetingID={meeting_id}&MinutesMeetingID=-1&doctype=Agenda"
            )
            filename = f"Agenda_{date_str}_{meeting_id}.html"

            listings.append(DocumentListing(
                title=title,
                url=agenda_url,
                date_str=date_str,
                document_id=meeting_id,
                document_type="agenda",
                file_format="html",
                filename=filename,
            ))

        return listings

    @staticmethod
    def _extract_date_from_row(link_tag) -> str:
        """Try to extract a YYYY-MM-DD date from the table row containing the link."""
        row = link_tag.find_parent("tr")
        if row:
            cells = row.find_all("td")
            for cell in cells:
                text = cell.get_text(strip=True)
                # Try common date formats: MM/DD/YYYY, M/D/YYYY
                date_match = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", text)
                if date_match:
                    month = int(date_match.group(1))
                    day = int(date_match.group(2))
                    year = int(date_match.group(3))
                    return f"{year:04d}-{month:02d}-{day:02d}"
        return "unknown"

    @staticmethod
    def _extract_type_from_row(link_tag) -> str:
        """Try to extract the meeting type name from the table row."""
        row = link_tag.find_parent("tr")
        if row:
            cells = row.find_all("td")
            # Meeting type is typically in the second cell after the date
            for cell in cells:
                text = cell.get_text(strip=True)
                # Skip cells that look like dates or IDs
                if re.match(r"^\d{1,2}/\d{1,2}/\d{4}$", text):
                    continue
                if text and len(text) > 3 and not text.isdigit():
                    return text
        return ""
