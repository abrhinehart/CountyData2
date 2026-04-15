"""Shared base adapter for Accela Citizen Access portals.

Subclasses override slug, display_name, and agency_code (and optionally
module_name and target_record_type) to scrape any county that runs on the
Accela Citizen Access platform.
"""

from __future__ import annotations

import re
import time
from datetime import date, datetime, timedelta

import requests
from bs4 import BeautifulSoup

from modules.permits.scrapers.base import JurisdictionAdapter


class AccelaCitizenAccessAdapter(JurisdictionAdapter):
    slug: str  # must be overridden
    display_name: str  # must be overridden
    agency_code: str  # e.g. "POLKCO", "CITRUS"
    mode = "live"

    module_name = "Building"
    target_record_type = "Building/Residential/New/NA"
    permit_type_filter: tuple[str, ...] = ()  # when non-empty, only keep rows whose permit_type matches one of these
    detail_request_delay: float = 0.0  # seconds to sleep between detail-page GETs (rate-limit courtesy)
    inspections_on_separate_tab: bool = False  # when True, skip _parse_inspections and emit []; see ACCELA-06

    bootstrap_lookback_days = 120
    rolling_overlap_days = 14
    search_result_cap = 100
    total_pattern = re.compile(r"Showing\s+\d+-\d+\s+of\s+(?P<total>\d+)", re.IGNORECASE)
    money_pattern = re.compile(r"\$?([\d,]+(?:\.\d+)?)")
    parcel_pattern = re.compile(r"Parcel Number:\s*([A-Z0-9-]+)")
    subdivision_pattern = re.compile(
        r"Subdivision:\s*(.*?)\s*(?:Fees|Inspections|Digital Projects|Processing Status|Related Records|$)",
        re.IGNORECASE,
    )
    applicant_pattern = re.compile(
        r"Applicant:\s*(.*?)\s*(?:Licensed Professional:|Project Description:|Owner:|More Details|$)",
        re.IGNORECASE,
    )
    licensed_professional_pattern = re.compile(
        r"Licensed Professional:\s*(.*?)\s*(?:View Additional Licensed Professionals>>|Project Description:|Owner:|More Details|$)",
        re.IGNORECASE,
    )
    project_description_pattern = re.compile(
        r"Project Description:\s*(.*?)\s*(?:Owner:|More Details|Additional Information|$)",
        re.IGNORECASE,
    )
    address_pattern = re.compile(
        r"^(?P<street>.+?),\s*(?P<city>[A-Za-z .'-]+)\s+FL\s+(?P<zip>\d{5}(?:-\d{4})?)$",
        re.IGNORECASE,
    )

    @property
    def search_url(self):
        return (
            f"https://aca-prod.accela.com/{self.agency_code}/Cap/CapHome.aspx"
            f"?module={self.module_name}&TabName={self.module_name}"
        )

    @property
    def request_headers(self):
        return {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/123.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": self.search_url,
        }

    def fetch_permits(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[dict]:
        end_date = end_date or date.today()
        start_date = start_date or (end_date - timedelta(days=self.rolling_overlap_days))

        session = self.build_session(headers=self.request_headers)

        permits_by_number: dict[str, dict] = {}
        for permit in self._fetch_range(session, start_date, end_date):
            permits_by_number[permit["permit_number"]] = permit
        return list(permits_by_number.values())

    def _fetch_range(
        self,
        session: requests.Session,
        start_date: date,
        end_date: date,
    ) -> list[dict]:
        page_html = self._submit_search(session, start_date, end_date)
        total = self._extract_total_results(page_html)
        if total >= self.search_result_cap and start_date < end_date:
            midpoint = start_date + timedelta(days=(end_date - start_date).days // 2)
            left = self._fetch_range(session, start_date, midpoint)
            right = self._fetch_range(session, midpoint + timedelta(days=1), end_date)
            return left + right

        permits = self._parse_search_results(page_html, session, start_date, end_date)
        next_target = self._extract_next_page_target(page_html)
        while next_target:
            page_html = self._post_back(session, page_html, next_target)
            permits.extend(self._parse_search_results(page_html, session, start_date, end_date))
            next_target = self._extract_next_page_target(page_html)
        return permits

    def _submit_search(
        self,
        session: requests.Session,
        start_date: date,
        end_date: date,
    ) -> str:
        initial_page = session.get(self.search_url, timeout=30)
        initial_page.raise_for_status()
        payload = self.extract_form_fields(initial_page.text)
        payload["ctl00$PlaceHolderMain$generalSearchForm$txtGSStartDate"] = start_date.strftime("%m/%d/%Y")
        payload["ctl00$PlaceHolderMain$generalSearchForm$txtGSEndDate"] = end_date.strftime("%m/%d/%Y")
        payload["ctl00$PlaceHolderMain$generalSearchForm$ddlGSPermitType"] = self.target_record_type
        payload["__EVENTTARGET"] = "ctl00$PlaceHolderMain$btnNewSearch"
        payload["__EVENTARGUMENT"] = ""
        response = session.post(
            self.search_url,
            data=payload,
            timeout=60,
        )
        response.raise_for_status()
        self.record_response_trace(
            "search-results",
            response,
            metadata={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "record_type": self.target_record_type,
            },
        )
        return response.text

    def _post_back(
        self,
        session: requests.Session,
        page_html: str,
        event_target: str,
    ) -> str:
        payload = self.extract_form_fields(page_html)
        payload["__EVENTTARGET"] = event_target
        payload["__EVENTARGUMENT"] = ""
        response = session.post(
            self.search_url,
            data=payload,
            timeout=60,
        )
        response.raise_for_status()
        self.record_response_trace(
            "search-pagination",
            response,
            metadata={"event_target": event_target},
        )
        return response.text

    @staticmethod
    def _build_column_map(grid) -> dict[str, int]:
        """Map normalised header text to column index from the grid's header row.

        The header row is identified as the first ``<tr>`` that contains
        ``<th>`` elements, since some agencies prepend info/pagination rows
        before the actual column headers.
        """
        for row in grid.find_all("tr"):
            headers = row.find_all("th")
            if headers:
                col_map: dict[str, int] = {}
                for idx, th in enumerate(headers):
                    label = th.get_text(strip=True).lower()
                    col_map[label] = idx
                return col_map
        return {}

    def _parse_search_results(
        self,
        html: str,
        session: requests.Session,
        start_date: date,
        end_date: date,
    ) -> list[dict]:
        soup = BeautifulSoup(html, "html.parser")
        grid = soup.find(id="ctl00_PlaceHolderMain_dgvPermitList_gdvPermitList")
        if grid is None:
            return []

        col_map = self._build_column_map(grid)
        # Accela grids use varying header names across agencies; normalise to
        # the fields we care about.  Each tuple is (canonical key, possible header labels).
        _COL_ALIASES = {
            "date": ("date",),
            "record_type": ("record type", "permit type"),
            "address": ("address",),
            "status": ("status",),
            "project_name": ("project name",),
            "description": ("description",),
        }
        idx: dict[str, int | None] = {}
        for key, aliases in _COL_ALIASES.items():
            idx[key] = next((col_map[a] for a in aliases if a in col_map), None)

        permits: list[dict] = []
        for row in grid.find_all("tr"):
            cells = row.find_all("td")
            if not cells:
                continue

            record_link = row.find("a", href=lambda href: href and "CapDetail.aspx" in href)
            if record_link is None:
                continue

            # Date column (required)
            date_idx = idx.get("date")
            if date_idx is not None and date_idx < len(cells):
                issue_date = self._parse_display_date(cells[date_idx].get_text(" ", strip=True))
            else:
                issue_date = None
            if issue_date is None or issue_date < start_date or issue_date > end_date:
                continue

            # Record/Permit type — extracted early so permit_type_filter can
            # skip non-matching rows before the expensive detail-page fetch.
            type_idx = idx.get("record_type")
            permit_type = cells[type_idx].get_text(" ", strip=True) if type_idx is not None and type_idx < len(cells) else None

            if self.permit_type_filter and (
                permit_type is None
                or not any(f.lower() in permit_type.lower() for f in self.permit_type_filter)
            ):
                continue

            if self.detail_request_delay > 0:
                time.sleep(self.detail_request_delay)

            detail_fields = self._fetch_detail_fields(session, record_link["href"])

            # Address
            addr_idx = idx.get("address")
            raw_address = cells[addr_idx].get_text(" ", strip=True) if addr_idx is not None and addr_idx < len(cells) else ""
            address = self._format_address(raw_address)

            # Status
            status_idx = idx.get("status")
            status = cells[status_idx].get_text(" ", strip=True) if status_idx is not None and status_idx < len(cells) else None

            # Project name (may not exist in all grids)
            pn_idx = idx.get("project_name")
            project_name = (cells[pn_idx].get_text(" ", strip=True) or None) if pn_idx is not None and pn_idx < len(cells) else None

            # Description (may not exist in all grids)
            desc_idx = idx.get("description")
            description = (cells[desc_idx].get_text(" ", strip=True) if desc_idx is not None and desc_idx < len(cells) else None) or detail_fields.get("project_description")

            permits.append(
                {
                    "permit_number": record_link.get_text(" ", strip=True),
                    "address": address,
                    "parcel_id": detail_fields.get("parcel_id"),
                    "issue_date": issue_date.isoformat(),
                    "status": status,
                    "permit_type": permit_type,
                    "valuation": self._parse_money(detail_fields.get("job_value")),
                    "raw_subdivision_name": detail_fields.get("subdivision") or project_name,
                    "raw_contractor_name": detail_fields.get("licensed_professional") or detail_fields.get("applicant"),
                    "raw_applicant_name": detail_fields.get("applicant"),
                    "raw_licensed_professional_name": detail_fields.get("licensed_professional"),
                    "latitude": None,
                    "longitude": None,
                    "inspections": detail_fields.get("inspections"),
                }
            )
        return permits

    def _fetch_detail_fields(self, session: requests.Session, detail_href: str) -> dict[str, str | None]:
        detail_url = self._absolute_url(detail_href)
        raw_html = self.get_cached_text(
            session,
            detail_url,
            timeout=30,
            artifact_type="detail-page",
            metadata={"detail_href": detail_url},
        )
        soup = BeautifulSoup(raw_html, "html.parser")
        text = " ".join(soup.get_text(" ", strip=True).split())

        if self.inspections_on_separate_tab:
            # Inspections render on a separate Record Info tab on this agency's
            # layout; not fetched by the HTML scrape path. Real inspection
            # capture moves to the REST API (ACCELA-06).
            inspections: list[dict] = []
        else:
            inspections = self._parse_inspections(soup) or []

        return {
            "parcel_id": self._extract_match(self.parcel_pattern, text),
            "subdivision": self._extract_match(self.subdivision_pattern, text),
            "applicant": self._extract_match(self.applicant_pattern, text),
            "licensed_professional": self._extract_match(self.licensed_professional_pattern, text),
            "project_description": self._extract_match(self.project_description_pattern, text),
            "job_value": self._extract_match(re.compile(r"Job Value\(\$\):\s*\$?[\d,]+(?:\.\d+)?"), text),
            "inspections": inspections,
        }

    def _parse_inspections(self, soup: BeautifulSoup) -> list[dict] | None:
        """Extract inspection rows from the detail page HTML.

        Accela detail pages may render inspections as:
        1. A ``<table>`` under a heading containing "Inspection"
        2. A div-based list with class patterns like ``InspectionListRow``

        Returns a list of dicts with keys: type, status, scheduled_date,
        result, inspector.  Returns None if no inspection section is found
        or no rows are parseable.
        """
        try:
            return self._parse_inspections_from_table(soup) or self._parse_inspections_from_divs(soup)
        except Exception:
            return None

    def _parse_inspections_from_table(self, soup: BeautifulSoup) -> list[dict] | None:
        """Parse inspections from a table-based layout."""
        # Look for a heading that contains "Inspection" then find the next table
        heading = soup.find(
            lambda tag: tag.name in ("h1", "h2", "h3", "h4", "h5", "h6", "span", "div", "td")
            and tag.string
            and "inspection" in tag.get_text(strip=True).lower()
            and "result" not in tag.get_text(strip=True).lower()
        )
        if heading is None:
            return None

        table = heading.find_next("table")
        if table is None:
            return None

        # Build column map from header row
        header_row = table.find("tr")
        if header_row is None:
            return None
        headers = header_row.find_all(["th", "td"])
        if not headers:
            return None

        col_map: dict[str, int] = {}
        for idx, cell in enumerate(headers):
            label = cell.get_text(strip=True).lower()
            col_map[label] = idx

        # Map known column names to our canonical keys
        _INSPECTION_ALIASES: dict[str, tuple[str, ...]] = {
            "type": ("type", "inspection type", "inspection"),
            "status": ("status", "inspection status"),
            "scheduled_date": ("scheduled date", "date", "scheduled", "request date"),
            "result": ("result", "inspection result", "result date"),
            "inspector": ("inspector", "inspector name"),
        }
        field_idx: dict[str, int | None] = {}
        for key, aliases in _INSPECTION_ALIASES.items():
            field_idx[key] = next((col_map[a] for a in aliases if a in col_map), None)

        rows: list[dict] = []
        for tr in table.find_all("tr")[1:]:
            cells = tr.find_all("td")
            if not cells:
                continue
            row: dict[str, str | None] = {}
            for key in _INSPECTION_ALIASES:
                ci = field_idx.get(key)
                if ci is not None and ci < len(cells):
                    val = cells[ci].get_text(strip=True)
                    row[key] = val if val else None
                else:
                    row[key] = None
            # Only include rows that have at least a type or status
            if row.get("type") or row.get("status"):
                rows.append(row)

        return rows if rows else None

    def _parse_inspections_from_divs(self, soup: BeautifulSoup) -> list[dict] | None:
        """Parse inspections from a div-based layout."""
        inspection_divs = soup.find_all(
            "div",
            class_=lambda c: c and "inspection" in str(c).lower(),
        )
        if not inspection_divs:
            return None

        rows: list[dict] = []
        for div in inspection_divs:
            text = div.get_text(" ", strip=True)
            if not text or len(text) < 3:
                continue
            row: dict[str, str | None] = {
                "type": None,
                "status": None,
                "scheduled_date": None,
                "result": None,
                "inspector": None,
            }
            # Try to extract key-value pairs from the text
            for field, patterns in (
                ("type", (r"(?:Inspection\s+)?Type:\s*(.+?)(?:\s*[-|]|$)",)),
                ("status", (r"Status:\s*(.+?)(?:\s*[-|]|$)",)),
                ("scheduled_date", (r"(?:Scheduled\s+)?Date:\s*(.+?)(?:\s*[-|]|$)",)),
                ("result", (r"Result:\s*(.+?)(?:\s*[-|]|$)",)),
                ("inspector", (r"Inspector:\s*(.+?)(?:\s*[-|]|$)",)),
            ):
                for pattern in patterns:
                    m = re.search(pattern, text, re.IGNORECASE)
                    if m:
                        row[field] = m.group(1).strip() or None
                        break
            if row.get("type") or row.get("status"):
                rows.append(row)

        return rows if rows else None

    def _extract_total_results(self, html: str) -> int:
        text = " ".join(BeautifulSoup(html, "html.parser").get_text(" ", strip=True).split())
        match = self.total_pattern.search(text)
        if not match:
            return 0
        return int(match.group("total"))

    def _extract_next_page_target(self, html: str) -> str | None:
        soup = BeautifulSoup(html, "html.parser")
        next_link = soup.find("a", string=lambda value: value and "Next" in value)
        if next_link is None:
            return None
        href = next_link.get("href") or ""
        match = re.search(r"__doPostBack\('([^']+)'", href)
        if match is None:
            return None
        return match.group(1)

    def _absolute_url(self, href: str) -> str:
        if href.startswith("http://") or href.startswith("https://"):
            return href
        return f"https://aca-prod.accela.com{href}"

    def _format_address(self, raw_address: str) -> str:
        cleaned = " ".join(raw_address.replace("*", " ").split())
        match = self.address_pattern.match(cleaned)
        if match is None:
            return cleaned
        return (
            f"{match.group('street').strip()}, "
            f"{match.group('city').strip()}, "
            f"FL {match.group('zip')}"
        )

    @staticmethod
    def _parse_display_date(value: str) -> date | None:
        candidate = value.strip()
        if not candidate:
            return None
        try:
            return datetime.strptime(candidate, "%m/%d/%Y").date()
        except ValueError:
            return None

    def _extract_match(self, pattern: re.Pattern[str], text: str) -> str | None:
        match = pattern.search(text)
        if match is None:
            return None
        if match.lastindex:
            value = match.group(1)
        else:
            value = match.group(0).split(":", 1)[-1]
        normalized = " ".join(value.replace("*", " ").split()).strip(" :")
        return normalized or None

    @staticmethod
    def _parse_money(value: str | None) -> float | None:
        if not value:
            return None
        match = AccelaCitizenAccessAdapter.money_pattern.search(value)
        if match is None:
            return None
        try:
            return float(match.group(1).replace(",", ""))
        except ValueError:
            return None
