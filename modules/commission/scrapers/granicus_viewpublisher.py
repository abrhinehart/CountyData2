"""Granicus ViewPublisher product scraper.

Distinct from the iQM2 scraper in granicus.py — ViewPublisher is a different
Granicus product surface that serves a single HTML page containing upcoming
events plus collapsible archive panels per body, each with per-year tabs.

Meetings are filtered to a specific body via YAML `body_filter` (case-
insensitive substring match against the panel heading + the row Name cell).

Reference portal: https://winterhaven-fl.granicus.com/ViewPublisher.php?view_id=1
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

logger = logging.getLogger("commission_radar.scrapers.granicus_viewpublisher")

USER_AGENT = "CommissionRadar/1.0"

# Agenda viewer / packet URL patterns — used to extract a stable meeting ID.
CLIP_ID_RE = re.compile(r"clip_id=(\d+)")
EVENT_ID_RE = re.compile(r"event_id=(\d+)")
CLOUDFRONT_UUID_RE = re.compile(r"cloudfront\.net/[^/]+/([0-9a-f-]+)", re.I)

# Date cell format: "Mar 23, 2026 - 06:00 PM" (NBSPs normalized to spaces first).
# Tolerate single- or multi-space separators per HTML-quirk observations.
DATE_RE = re.compile(r"([A-Z][a-z]{2})\s+(\d{1,2}),\s*(\d{4})")
VP_DATE_FMT = "%b %d, %Y"


class ViewPublisherScraper(PlatformScraper):
    """Scraper for Granicus ViewPublisher tenants.

    HTML shape (see reference portal in module docstring):
      - `<h2>Upcoming Events</h2>` + `<table class="listingTable">` at top —
        rows have NO CollapsiblePanel parent. Body identified via the
        `<td scope="row">` Name cell text.
      - `<h2>Available Archives</h2>` containing `<div class="CollapsiblePanel">`
        per body. Body label lives in `<div class="CollapsiblePanelTab">`.
      - Each panel holds per-year `<div class="TabbedPanelsContent">` tables.
      - Agenda packet PDFs are served from a CloudFront CDN
        (`d3n9y02raazwpg.cloudfront.net/<tenant>/<uuid>.pdf`). We emit one
        DocumentListing per row that has a packet PDF; rows with only the
        HTML AgendaViewer link (no PDF) or only a video clip are skipped.
    """

    def fetch_listings(
        self, config: dict, start_date: str, end_date: str
    ) -> list[DocumentListing]:
        base_url = config.get("base_url")
        if not base_url:
            logger.warning("ViewPublisher scraper: missing base_url")
            return []
        body_filter = (config.get("body_filter") or "").strip().lower()
        if not body_filter:
            logger.warning(
                "ViewPublisher scraper: missing body_filter for %s", base_url
            )
            return []
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        except (TypeError, ValueError):
            logger.warning(
                "ViewPublisher scraper: bad date range %r..%r", start_date, end_date
            )
            return []
        try:
            resp = requests.get(
                base_url,
                headers={"User-Agent": USER_AGENT},
                timeout=SCRAPE_SEARCH_TIMEOUT,
            )
            resp.raise_for_status()
        except requests.RequestException as exc:
            logger.warning(
                "ViewPublisher scraper: fetch %s failed: %s", base_url, exc
            )
            return []
        soup = BeautifulSoup(resp.text, "html.parser")
        return self._parse(soup, body_filter, start_dt, end_dt)

    def _parse(
        self,
        soup: BeautifulSoup,
        body_filter: str,
        start_dt: datetime,
        end_dt: datetime,
    ) -> list[DocumentListing]:
        listings: list[DocumentListing] = []
        seen_ids: set[str] = set()
        for row in soup.find_all("tr", class_="listingRow"):
            name_td = row.find("td", attrs={"scope": "row"})
            if not name_td:
                continue
            name_cell_text = name_td.get_text(" ", strip=True)

            # Panel label comes from the nearest ancestor CollapsiblePanel div
            # (archived rows). Upcoming rows have no such parent → "" is fine.
            panel_label = ""
            panel_div = row.find_parent(
                "div",
                class_=lambda c: c and "CollapsiblePanel" in c.split(),
            )
            if panel_div:
                tab_div = panel_div.find("div", class_="CollapsiblePanelTab")
                if tab_div:
                    panel_label = tab_div.get_text(strip=True)

            combined = f"{panel_label} {name_cell_text}".lower()
            if body_filter not in combined:
                continue

            date_iso = self._extract_date(row)
            if not date_iso:
                logger.debug(
                    "ViewPublisher: skipping row with no parseable date in %r",
                    combined[:80],
                )
                continue
            try:
                row_dt = datetime.strptime(date_iso, "%Y-%m-%d")
            except ValueError:
                continue
            if row_dt < start_dt or row_dt > end_dt:
                continue

            # Require a downloadable Agenda Packet PDF. Rows that only have
            # the HTML AgendaViewer link or video clips are skipped — we
            # intentionally do NOT synthesize HTML-preview listings here.
            pdf_a = row.find("a", href=re.compile(r"\.pdf(\?|$)", re.I))
            if not pdf_a:
                continue
            pdf_href = (pdf_a.get("href") or "").strip()
            if not pdf_href:
                continue
            if pdf_href.startswith("//"):
                pdf_href = "https:" + pdf_href

            meeting_id = self._extract_meeting_id(row, pdf_href, panel_label, date_iso)
            doc_id = f"agenda-{meeting_id}"
            if doc_id in seen_ids:
                continue
            seen_ids.add(doc_id)

            title = panel_label or name_cell_text
            filename = f"Agenda_{date_iso}_{meeting_id}.pdf"

            listings.append(
                DocumentListing(
                    title=title,
                    url=pdf_href,
                    date_str=date_iso,
                    document_id=meeting_id,
                    document_type="agenda",
                    file_format="pdf",
                    filename=filename,
                )
            )
        return listings

    @staticmethod
    def _extract_date(row) -> str | None:
        """Parse the date cell into YYYY-MM-DD. NBSPs and variable whitespace tolerated."""
        for td in row.find_all("td", class_="listItem"):
            txt = td.get_text(" ", strip=True).replace("\xa0", " ")
            m = DATE_RE.search(txt)
            if not m:
                continue
            try:
                normalized = f"{m.group(1)} {int(m.group(2))}, {m.group(3)}"
                dt = datetime.strptime(normalized, VP_DATE_FMT)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue
        return None

    @staticmethod
    def _extract_meeting_id(row, pdf_href: str, panel_label: str, date_iso: str) -> str:
        """Return a stable meeting ID: clip_id > event_id > CloudFront UUID > date-stamp."""
        viewer = row.find("a", href=re.compile(r"AgendaViewer\.php"))
        if viewer:
            viewer_href = viewer.get("href", "")
            m = CLIP_ID_RE.search(viewer_href) or EVENT_ID_RE.search(viewer_href)
            if m:
                return m.group(1)
        m = CLOUDFRONT_UUID_RE.search(pdf_href)
        if m:
            return m.group(1)
        # Fallback: date + sanitized panel label.
        slug = (panel_label or "misc")[:10].lower().replace(" ", "")
        return f"wh-{slug}-{date_iso}"

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
