"""iCompass CivicWeb (Diligent brand) product scraper.

Distinct from Granicus, CivicPlus, CivicClerk, Legistar, and NovusAgenda.
iCompass CivicWeb publishes meeting documents under a file-tree Document
Center at /filepro/documents/<folder_id>. The meeting-list surfaces
(MeetingTypeList.aspx, MeetingSchedule.aspx) are JS-rendered or
redirect-only — the Document Center is the only stable HTML-scrapable
path. Reference portal: https://walton.civicweb.net/filepro/documents/1009
"""

import logging
import os
import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from modules.commission.constants import (
    FILE_READ_CHUNK_SIZE,
    SCRAPE_DOWNLOAD_TIMEOUT,
    SCRAPE_SEARCH_TIMEOUT,
)
from modules.commission.scrapers.base import DocumentListing, PlatformScraper

logger = logging.getLogger("commission_radar.scrapers.civicweb_icompass")

USER_AGENT = "CommissionRadar/1.0"

# Title shape: "<Body Name> - MMM dd YYYY - Pdf"
TITLE_DATE_RE = re.compile(
    r"-\s+([A-Z][a-z]{2})\s+(\d{1,2})\s+(\d{4})\s+-\s+Pdf\s*$",
    re.IGNORECASE,
)
YEAR_RE = re.compile(r"^\s*(\d{4})\s*$")
TITLE_FMT = "%b %d %Y"


class CivicWebIcompassScraper(PlatformScraper):
    """Scraper for iCompass CivicWeb Document-Center-backed tenants.

    YAML config shape:
      platform: civicweb_icompass
      tenant_host: walton.civicweb.net
      body_folder_id: 1021
      body_label: "Board of County Commissioners"
    """

    def fetch_listings(
        self, config: dict, start_date: str, end_date: str
    ) -> list[DocumentListing]:
        tenant_host = (config.get("tenant_host") or "").strip().rstrip("/")
        body_folder_id = config.get("body_folder_id")
        body_label = (config.get("body_label") or "").strip()
        if not tenant_host or not body_folder_id or not body_label:
            logger.warning(
                "CivicWebIcompass: missing tenant_host/body_folder_id/body_label "
                "(got host=%r folder=%r label=%r)",
                tenant_host, body_folder_id, body_label,
            )
            return []
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        except (TypeError, ValueError):
            logger.warning(
                "CivicWebIcompass: bad date range %r..%r", start_date, end_date
            )
            return []
        if start_dt > end_dt:
            return []

        year_soup = self._fetch_folder(tenant_host, body_folder_id)
        if year_soup is None:
            return []

        year_folders = self._extract_year_folders(year_soup, start_dt.year, end_dt.year)
        listings: list[DocumentListing] = []
        seen_ids: set[str] = set()
        for year_id in year_folders:
            docs_soup = self._fetch_folder(tenant_host, year_id)
            if docs_soup is None:
                continue
            listings.extend(
                self._extract_pdfs(
                    docs_soup, body_label, tenant_host, start_dt, end_dt, seen_ids
                )
            )
        return listings

    def _fetch_folder(self, tenant_host: str, folder_id):
        url = f"https://{tenant_host}/filepro/documents/{folder_id}"
        try:
            resp = requests.get(
                url,
                headers={"User-Agent": USER_AGENT},
                timeout=SCRAPE_SEARCH_TIMEOUT,
            )
            resp.raise_for_status()
        except requests.RequestException as exc:
            logger.warning("CivicWebIcompass: fetch %s failed: %s", url, exc)
            return None
        return BeautifulSoup(resp.text, "html.parser")

    @staticmethod
    def _extract_year_folders(soup, start_year: int, end_year: int) -> list[str]:
        out: list[str] = []
        for div in soup.find_all(
            "div", class_="document-list-view-documents"
        ):
            if div.get("data-type") != "folder":
                continue
            title = (div.get("data-title") or "").strip()
            m = YEAR_RE.match(title)
            if not m:
                continue
            y = int(m.group(1))
            if start_year <= y <= end_year:
                folder_id = div.get("data-id")
                if folder_id:
                    out.append(folder_id)
        return out

    def _extract_pdfs(
        self,
        soup,
        body_label: str,
        tenant_host: str,
        start_dt: datetime,
        end_dt: datetime,
        seen_ids: set[str],
    ) -> list[DocumentListing]:
        out: list[DocumentListing] = []
        body_label_ci = body_label.lower()
        for div in soup.find_all("div", class_="document-list-view-documents"):
            if div.get("data-type") != "document":
                continue
            title = (div.get("data-title") or "").strip()
            if not title.lower().endswith("- pdf"):
                continue
            if not title.lower().startswith(body_label_ci):
                continue
            date_iso = self._parse_title_date(title)
            if not date_iso:
                logger.debug("CivicWebIcompass: unparseable date in %r", title)
                continue
            try:
                row_dt = datetime.strptime(date_iso, "%Y-%m-%d")
            except ValueError:
                continue
            if row_dt < start_dt or row_dt > end_dt:
                continue

            doc_id = (div.get("data-id") or "").strip()
            if not doc_id or doc_id in seen_ids:
                continue
            link = div.find("a", class_="document-link")
            if not link:
                continue
            href = (link.get("href") or "").strip()
            if not href:
                continue
            if href.startswith("/"):
                url = f"https://{tenant_host}{href}"
            else:
                url = href
            seen_ids.add(doc_id)

            filename = f"Agenda_{date_iso}_{doc_id}.pdf"
            out.append(
                DocumentListing(
                    title=body_label,
                    url=url,
                    date_str=date_iso,
                    document_id=doc_id,
                    document_type="agenda",
                    file_format="pdf",
                    filename=filename,
                )
            )
        return out

    @staticmethod
    def _parse_title_date(title: str) -> str | None:
        m = TITLE_DATE_RE.search(title.replace("\xa0", " "))
        if not m:
            return None
        try:
            normalized = f"{m.group(1)} {int(m.group(2))} {m.group(3)}"
            return datetime.strptime(normalized, TITLE_FMT).strftime("%Y-%m-%d")
        except ValueError:
            return None

    def download_document(self, listing: DocumentListing, output_dir: str) -> str:
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, listing.filename)
        resp = requests.get(
            listing.url,
            stream=True,
            timeout=SCRAPE_DOWNLOAD_TIMEOUT,
            headers={"User-Agent": USER_AGENT},
        )
        resp.raise_for_status()
        with open(filepath, "wb") as fh:
            for chunk in resp.iter_content(chunk_size=FILE_READ_CHUNK_SIZE):
                if chunk:
                    fh.write(chunk)
        return filepath
