import logging
import os
import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from modules.commission.constants import (
    FILE_READ_CHUNK_SIZE,
    SCRAPE_SEARCH_TIMEOUT,
    SCRAPE_DOWNLOAD_TIMEOUT,
)
from modules.commission.scrapers.base import PlatformScraper, DocumentListing

logger = logging.getLogger("commission_radar.scrapers.granicus")

# iQM2 document type codes we care about
FILE_TYPE_AGENDA = "14"
FILE_TYPE_MINUTES = "15"
FILE_TYPE_MAP = {
    FILE_TYPE_AGENDA: "agenda",
    FILE_TYPE_MINUTES: "minutes",
}

# Regex to pull Detail_Meeting links
MEETING_LINK_RE = re.compile(r"Detail_Meeting\.aspx\?ID=(\d+)")

# Regex to pull FileOpen links with Type and ID
FILE_LINK_RE = re.compile(r"FileOpen\.aspx\?.*?Type=(\d+).*?ID=(\d+)")

# iQM2 date format: "Jan 8, 2026 9:00 AM"
IQM2_DATE_FMT = "%b %d, %Y %I:%M %p"
# Fallback without time
IQM2_DATE_FMT_NO_TIME = "%b %d, %Y"

USER_AGENT = "CommissionRadar/1.0"


class GranicusScraper(PlatformScraper):
    """Scraper for Granicus iQM2 Citizens platforms.

    Fetches agenda and minutes PDFs from iQM2 meeting calendar pages.
    """

    def fetch_listings(self, config: dict, start_date: str, end_date: str) -> list[DocumentListing]:
        """Fetch document listings from a Granicus iQM2 Citizens portal.

        Args:
            config: Jurisdiction scraping config with keys:
                - base_url: iQM2 Citizens URL (e.g. https://slug.iqm2.com/Citizens)
                - meeting_group (optional): filter to a specific meeting group name
            start_date: YYYY-MM-DD
            end_date: YYYY-MM-DD

        Returns:
            List of DocumentListing for agendas and minutes.
        """
        base_url = config.get("base_url")
        if not base_url:
            logger.warning("Granicus scraper requires base_url")
            return []

        base_url = base_url.rstrip("/")
        meeting_group = config.get("meeting_group")

        # Convert YYYY-MM-DD to M/D/YYYY for iQM2 query params
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        iqm2_from = f"{start_dt.month}/{start_dt.day}/{start_dt.year}"
        iqm2_to = f"{end_dt.month}/{end_dt.day}/{end_dt.year}"

        calendar_url = (
            f"{base_url}/Calendar.aspx"
            f"?From={iqm2_from}&To={iqm2_to}&View=List"
        )

        try:
            resp = requests.get(
                calendar_url,
                headers={"User-Agent": USER_AGENT},
                timeout=SCRAPE_SEARCH_TIMEOUT,
            )
            resp.raise_for_status()
        except requests.RequestException as exc:
            logger.error("Failed to fetch iQM2 calendar: %s", exc)
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        return self._parse_calendar(soup, base_url, meeting_group)

    def _parse_calendar(self, soup: BeautifulSoup, base_url: str,
                        meeting_group: str | None) -> list[DocumentListing]:
        """Parse the iQM2 calendar list view HTML into DocumentListings."""
        listings = []
        seen_ids = set()

        # iQM2 uses div.MeetingRow containers (preferred) or <tr> rows.
        rows = soup.find_all("div", class_=re.compile(r"MeetingRow", re.I))
        if not rows:
            rows = soup.find_all("tr")

        for row in rows:
            # Find the meeting detail link
            detail_link = row.find("a", href=MEETING_LINK_RE)
            if not detail_link:
                continue

            meeting_match = MEETING_LINK_RE.search(detail_link["href"])
            if not meeting_match:
                continue
            meeting_id = meeting_match.group(1)

            # Extract meeting title / group name.
            # In div-based layouts the link text is just the date;
            # the real title lives in a RowDetails/RowBottom div or the
            # link's title attribute ("Board:\tName\nType:\tKind").
            meeting_title = self._extract_title(row, detail_link)

            # Apply meeting_group filter if configured
            if meeting_group and meeting_group.lower() not in meeting_title.lower():
                continue

            # Extract meeting date from the row text
            meeting_date = self._extract_date(row)

            # Find document links (FileOpen.aspx)
            file_links = row.find_all("a", href=FILE_LINK_RE)
            for file_link in file_links:
                file_match = FILE_LINK_RE.search(file_link["href"])
                if not file_match:
                    continue

                file_type_code = file_match.group(1)
                file_id = file_match.group(2)

                # Only process agenda and minutes
                doc_type = FILE_TYPE_MAP.get(file_type_code)
                if not doc_type:
                    continue

                doc_id = f"{doc_type}-{meeting_id}-{file_id}"
                if doc_id in seen_ids:
                    continue
                seen_ids.add(doc_id)

                href = file_link["href"]
                full_url = f"{base_url}/{href}" if not href.startswith("http") else href

                filename = f"{doc_type.capitalize()}_{meeting_date}_{meeting_id}.pdf"

                listings.append(DocumentListing(
                    title=meeting_title or filename,
                    url=full_url,
                    date_str=meeting_date,
                    document_id=file_id,
                    document_type=doc_type,
                    file_format="pdf",
                    filename=filename,
                ))

        return listings

    @staticmethod
    def _extract_title(row, detail_link) -> str:
        """Extract the meeting board/group name from the row.

        Checks (in order):
        1. A RowDetails or RowBottom div with descriptive text
        2. The title attribute of the detail link (contains Board:\tName)
        3. Falls back to the link's visible text
        """
        # 1. RowDetails div (div-based iQM2 layout)
        details_div = row.find("div", class_=re.compile(r"RowDetails", re.I))
        if details_div:
            text = details_div.get_text(strip=True)
            if text:
                return text

        # 2. title attribute of the <a> tag (e.g. "Board:\tPlanning Board")
        title_attr = detail_link.get("title", "")
        if title_attr:
            board_match = re.search(r"Board:\s*(.+?)(?:\r|\n|&#13;|$)", title_attr)
            if board_match:
                return board_match.group(1).strip()

        # 3. Visible link text (may just be the date, but better than nothing)
        return detail_link.get_text(strip=True)

    def _extract_date(self, row) -> str:
        """Extract a YYYY-MM-DD date from the row text.

        iQM2 uses formats like 'Jan 8, 2026 9:00 AM'.
        """
        text = row.get_text(" ", strip=True)
        # Try matching a date pattern in the text
        date_match = re.search(
            r"([A-Z][a-z]{2}\s+\d{1,2},\s*\d{4})\s*\d{1,2}:\d{2}\s*[AP]M",
            text,
        )
        if date_match:
            try:
                dt = datetime.strptime(
                    date_match.group(0).strip(),
                    IQM2_DATE_FMT,
                )
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                pass

        # Fallback: try without time
        date_match = re.search(r"([A-Z][a-z]{2}\s+\d{1,2},\s*\d{4})", text)
        if date_match:
            try:
                dt = datetime.strptime(
                    date_match.group(1).strip(),
                    IQM2_DATE_FMT_NO_TIME,
                )
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                pass

        return "unknown"

    def download_document(self, listing: DocumentListing, output_dir: str) -> str:
        """Download a document from iQM2."""
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
