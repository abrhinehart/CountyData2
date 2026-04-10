from __future__ import annotations

import re
from datetime import date, datetime, timedelta

import requests
from bs4 import BeautifulSoup

from modules.permits.scrapers.base import JurisdictionAdapter


class PolkCountyAdapter(JurisdictionAdapter):
    slug = "polk-county"
    display_name = "Polk County"
    mode = "live"

    search_url = "https://aca-prod.accela.com/POLKCO/Cap/CapHome.aspx?module=Building&TabName=Building"
    request_headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/123.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": search_url,
    }
    target_record_type = "Building/Residential/New/NA"
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

        permits: list[dict] = []
        for row in grid.find_all("tr"):
            cells = row.find_all("td")
            if len(cells) < 10:
                continue

            record_link = row.find("a", href=lambda href: href and "CapDetail.aspx" in href)
            if record_link is None:
                continue

            issue_date = self._parse_display_date(cells[6].get_text(" ", strip=True))
            if issue_date is None or issue_date < start_date or issue_date > end_date:
                continue

            detail_fields = self._fetch_detail_fields(session, record_link["href"])
            project_name = cells[7].get_text(" ", strip=True) or None
            description = cells[8].get_text(" ", strip=True) or detail_fields.get("project_description")
            address = self._format_address(cells[3].get_text(" ", strip=True))

            permits.append(
                {
                    "permit_number": record_link.get_text(" ", strip=True),
                    "address": address,
                    "parcel_id": detail_fields.get("parcel_id"),
                    "issue_date": issue_date.isoformat(),
                    "status": cells[5].get_text(" ", strip=True),
                    "permit_type": cells[2].get_text(" ", strip=True),
                    "valuation": self._parse_money(detail_fields.get("job_value")),
                    "raw_subdivision_name": detail_fields.get("subdivision") or project_name,
                    "raw_contractor_name": detail_fields.get("licensed_professional") or detail_fields.get("applicant"),
                    "raw_applicant_name": detail_fields.get("applicant"),
                    "raw_licensed_professional_name": detail_fields.get("licensed_professional"),
                    "latitude": None,
                    "longitude": None,
                }
            )
        return permits

    def _fetch_detail_fields(self, session: requests.Session, detail_href: str) -> dict[str, str | None]:
        detail_url = self._absolute_url(detail_href)
        text = " ".join(
            BeautifulSoup(
                self.get_cached_text(
                    session,
                    detail_url,
                    timeout=30,
                    artifact_type="detail-page",
                    metadata={"detail_href": detail_url},
                ),
                "html.parser",
            ).get_text(" ", strip=True).split()
        )
        return {
            "parcel_id": self._extract_match(self.parcel_pattern, text),
            "subdivision": self._extract_match(self.subdivision_pattern, text),
            "applicant": self._extract_match(self.applicant_pattern, text),
            "licensed_professional": self._extract_match(self.licensed_professional_pattern, text),
            "project_description": self._extract_match(self.project_description_pattern, text),
            "job_value": self._extract_match(re.compile(r"Job Value\(\$\):\s*\$?[\d,]+(?:\.\d+)?"), text),
        }

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
        match = PolkCountyAdapter.money_pattern.search(value)
        if match is None:
            return None
        try:
            return float(match.group(1).replace(",", ""))
        except ValueError:
            return None
