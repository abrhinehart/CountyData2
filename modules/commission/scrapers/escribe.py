"""eSCRIBE (Diligent) meeting portal scraper.

Distinct from Granicus, CivicPlus, CivicClerk, Legistar, NovusAgenda,
and iCompass CivicWeb. eSCRIBE tenants are hosted at
``pub-<slug>.escribemeetings.com`` and expose an ASMX-style JSON
endpoint ``POST /MeetingsCalendarView.aspx/GetCalendarMeetings`` that
returns the full meeting list for a date range with per-meeting document
links already attached. Agenda packets are served as direct PDF streams
at ``FileStream.ashx?DocumentId=<numeric>`` relative to the tenant root.

Reference portal: https://pub-hainescity.escribemeetings.com/
"""

import json
import logging
import os
from datetime import datetime

import requests

from modules.commission.constants import (
    FILE_READ_CHUNK_SIZE,
    SCRAPE_DOWNLOAD_TIMEOUT,
    SCRAPE_SEARCH_TIMEOUT,
)
from modules.commission.scrapers.base import DocumentListing, PlatformScraper

logger = logging.getLogger("commission_radar.scrapers.escribe")

USER_AGENT = "CommissionRadar/1.0"

# eSCRIBE StartDate format: "YYYY/MM/DD HH:MM:SS" (24-hour).
ESCRIBE_DT_FMT = "%Y/%m/%d %H:%M:%S"


class EscribeScraper(PlatformScraper):
    """Scraper for eSCRIBE (Diligent) tenants.

    YAML config shape:
      platform: escribe
      tenant_host: pub-hainescity.escribemeetings.com
      body_filter:                       # list of exact MeetingType strings
        - "City Commission Meeting"
        - "City Commission Special Meeting"
      body_label: "City Commission"      # canonical title on DocumentListing
    """

    def fetch_listings(
        self, config: dict, start_date: str, end_date: str
    ) -> list[DocumentListing]:
        tenant_host = (config.get("tenant_host") or "").strip().rstrip("/")
        body_filter_raw = config.get("body_filter")
        body_label = (config.get("body_label") or "").strip()
        if not tenant_host or not body_filter_raw or not body_label:
            logger.warning(
                "eSCRIBE: missing tenant_host/body_filter/body_label "
                "(got host=%r filter=%r label=%r)",
                tenant_host, body_filter_raw, body_label,
            )
            return []
        # Accept either a list or a single string for body_filter.
        if isinstance(body_filter_raw, str):
            body_filter = [body_filter_raw.strip()]
        else:
            body_filter = [str(x).strip() for x in body_filter_raw if str(x).strip()]
        if not body_filter:
            logger.warning("eSCRIBE: body_filter is empty after normalization")
            return []

        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        except (TypeError, ValueError):
            logger.warning(
                "eSCRIBE: bad date range %r..%r", start_date, end_date
            )
            return []
        if start_dt > end_dt:
            return []

        url = f"https://{tenant_host}/MeetingsCalendarView.aspx/GetCalendarMeetings"
        payload = json.dumps(
            {"calendarStartDate": start_date, "calendarEndDate": end_date}
        )
        try:
            resp = requests.post(
                url,
                headers={
                    "User-Agent": USER_AGENT,
                    "Content-Type": "application/json; charset=utf-8",
                    "Accept": "application/json",
                },
                data=payload,
                timeout=SCRAPE_SEARCH_TIMEOUT,
            )
            resp.raise_for_status()
        except requests.RequestException as exc:
            logger.warning("eSCRIBE: fetch %s failed: %s", url, exc)
            return []

        try:
            data = resp.json()
        except ValueError:
            logger.warning("eSCRIBE: %s returned non-JSON", url)
            return []

        items = data.get("d") if isinstance(data, dict) else None
        if not isinstance(items, list):
            logger.warning("eSCRIBE: unexpected JSON shape at %s", url)
            return []

        listings: list[DocumentListing] = []
        seen_ids: set[str] = set()
        allowed_types = {t for t in body_filter}
        for item in items:
            if not isinstance(item, dict):
                continue
            meeting_type = (item.get("MeetingType") or "").strip()
            if meeting_type not in allowed_types:
                continue
            date_iso = self._parse_start_date(item.get("StartDate"))
            if not date_iso:
                logger.debug(
                    "eSCRIBE: unparseable StartDate %r on meeting %r",
                    item.get("StartDate"), item.get("ID"),
                )
                continue
            try:
                row_dt = datetime.strptime(date_iso, "%Y-%m-%d")
            except ValueError:
                continue
            if row_dt < start_dt or row_dt > end_dt:
                continue

            agenda_doc = self._pick_agenda_pdf(item.get("MeetingDocumentLink"))
            if not agenda_doc:
                continue
            rel_url = (agenda_doc.get("Url") or "").strip()
            if not rel_url:
                continue
            pdf_url = f"https://{tenant_host}/{rel_url.lstrip('/')}"

            meeting_uuid = (item.get("ID") or "").strip()
            if not meeting_uuid or meeting_uuid in seen_ids:
                continue
            seen_ids.add(meeting_uuid)

            document_id = self._extract_document_id(rel_url) or meeting_uuid
            filename = f"Agenda_{date_iso}_{document_id}.pdf"

            listings.append(
                DocumentListing(
                    title=body_label,
                    url=pdf_url,
                    date_str=date_iso,
                    document_id=document_id,
                    document_type="agenda",
                    file_format="pdf",
                    filename=filename,
                )
            )
        return listings

    @staticmethod
    def _parse_start_date(raw) -> str | None:
        if not raw or not isinstance(raw, str):
            return None
        try:
            return datetime.strptime(raw.strip(), ESCRIBE_DT_FMT).strftime(
                "%Y-%m-%d"
            )
        except ValueError:
            # Tolerate dash-separated variants: "YYYY-MM-DD HH:MM:SS".
            try:
                return datetime.strptime(
                    raw.strip(), "%Y-%m-%d %H:%M:%S"
                ).strftime("%Y-%m-%d")
            except ValueError:
                return None

    @staticmethod
    def _pick_agenda_pdf(docs) -> dict | None:
        """Return the first doc dict where Type=='Agenda' AND Format=='.pdf'."""
        if not isinstance(docs, list):
            return None
        for d in docs:
            if not isinstance(d, dict):
                continue
            if (d.get("Type") or "").strip() != "Agenda":
                continue
            if (d.get("Format") or "").strip().lower() != ".pdf":
                continue
            return d
        return None

    @staticmethod
    def _extract_document_id(rel_url: str) -> str | None:
        """Pull the numeric DocumentId out of FileStream.ashx?DocumentId=<n>."""
        import re
        m = re.search(r"DocumentId=(\d+)", rel_url or "")
        return m.group(1) if m else None

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
