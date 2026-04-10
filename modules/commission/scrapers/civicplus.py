import logging
import os
import re
from datetime import datetime, timedelta
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from modules.commission.constants import (
    FILE_READ_CHUNK_SIZE,
    SCRAPE_SEARCH_TIMEOUT,
    SCRAPE_DOWNLOAD_TIMEOUT,
)
from modules.commission.scrapers.base import PlatformScraper, DocumentListing

logger = logging.getLogger("commission_radar.scrapers.civicplus")

# PDF link patterns
AGENDA_PDF_RE = re.compile(r"/AgendaCenter/ViewFile/Agenda/_(\d{8})-(\d+)$")
MINUTES_PDF_RE = re.compile(r"/AgendaCenter/ViewFile/Minutes/_(\d{8})-(\d+)$")

USER_AGENT = "CommissionRadar/1.0"


class CivicPlusScraper(PlatformScraper):
    """Scraper for CivicPlus AgendaCenter platforms.

    Fetches both agenda and minutes PDFs.
    """

    # CivicPlus silently truncates results for wide date ranges.
    # Split into windows of this many days to avoid missing documents.
    MAX_WINDOW_DAYS = 180

    def fetch_listings(self, config: dict, start_date: str, end_date: str) -> list[DocumentListing]:
        """Fetch document listings from CivicPlus AgendaCenter.

        Automatically splits wide date ranges into smaller windows to avoid
        CivicPlus silently truncating results.

        Args:
            config: Jurisdiction scraping config with keys:
                - base_url: AgendaCenter URL
                - category_id: CivicPlus category ID
            start_date: YYYY-MM-DD
            end_date: YYYY-MM-DD

        Returns:
            List of DocumentListing for both agendas and minutes.
        """
        base_url = config.get("base_url")
        category_id = config.get("category_id")

        if not base_url or not category_id:
            logger.warning("CivicPlus scraper requires base_url and category_id")
            return []

        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")

        listings = []
        seen_ids = set()

        for win_start, win_end in self._date_windows(start_dt, end_dt):
            window_listings = self._fetch_window(
                base_url, category_id, win_start, win_end, seen_ids,
            )
            listings.extend(window_listings)

        return listings

    def _date_windows(self, start_dt: datetime, end_dt: datetime):
        """Yield (start, end) pairs covering the full range in MAX_WINDOW_DAYS chunks."""
        window_start = start_dt
        while window_start <= end_dt:
            window_end = min(window_start + timedelta(days=self.MAX_WINDOW_DAYS - 1), end_dt)
            yield window_start, window_end
            window_start = window_end + timedelta(days=1)

    def _fetch_window(self, base_url, category_id, start_dt, end_dt, seen_ids):
        """Fetch listings for a single date window."""
        cp_start = start_dt.strftime("%m/%d/%Y")
        cp_end = end_dt.strftime("%m/%d/%Y")

        search_url = (
            f"{base_url}/Search/?term=&CIDs={category_id}"
            f"&startDate={cp_start}&endDate={cp_end}"
            f"&dateRange=&dateSelector="
        )

        resp = requests.get(search_url, headers={"User-Agent": USER_AGENT},
                            timeout=SCRAPE_SEARCH_TIMEOUT)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        parsed_base = urlparse(base_url)
        base_domain = f"{parsed_base.scheme}://{parsed_base.netloc}"

        listings = []

        # Find agenda PDFs
        for link in soup.find_all("a", href=AGENDA_PDF_RE):
            listing = self._parse_link(link, AGENDA_PDF_RE, "agenda", base_domain, seen_ids)
            if listing:
                listings.append(listing)

        # Find minutes PDFs
        for link in soup.find_all("a", href=MINUTES_PDF_RE):
            listing = self._parse_link(link, MINUTES_PDF_RE, "minutes", base_domain, seen_ids)
            if listing:
                listings.append(listing)

        return listings

    def _parse_link(self, link, pattern, doc_type, base_domain, seen_ids):
        """Parse a single link element into a DocumentListing."""
        href = link["href"]
        match = pattern.search(href)
        if not match:
            return None

        doc_id = f"{doc_type}-{match.group(2)}"
        if doc_id in seen_ids:
            return None
        seen_ids.add(doc_id)

        date_str_raw = match.group(1)  # MMDDYYYY
        try:
            meeting_date = datetime.strptime(date_str_raw, "%m%d%Y").strftime("%Y-%m-%d")
        except ValueError:
            meeting_date = date_str_raw

        # Find meeting title from parent element
        title = ""
        parent = link.find_parent("tr") or link.find_parent("div") or link.find_parent("li")
        if parent:
            title_link = parent.find("a", href=re.compile(r"\?html=true"))
            if title_link:
                title = title_link.get_text(strip=True)

        full_url = f"{base_domain}{href}" if href.startswith("/") else href
        filename = f"{doc_type.capitalize()}_{date_str_raw}-{match.group(2)}.pdf"

        return DocumentListing(
            title=title or filename,
            url=full_url,
            date_str=meeting_date,
            document_id=match.group(2),
            document_type=doc_type,
            file_format="pdf",
            filename=filename,
        )

    def download_document(self, listing: DocumentListing, output_dir: str) -> str:
        """Download a document from CivicPlus."""
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, listing.filename)

        resp = requests.get(listing.url, headers={"User-Agent": USER_AGENT},
                            stream=True, timeout=SCRAPE_DOWNLOAD_TIMEOUT)
        resp.raise_for_status()

        with open(filepath, "wb") as f:
            for chunk in resp.iter_content(chunk_size=FILE_READ_CHUNK_SIZE):
                f.write(chunk)

        return filepath
