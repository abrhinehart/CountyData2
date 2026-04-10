from __future__ import annotations

import re
from datetime import date, datetime, timedelta
from urllib.parse import urlparse, parse_qs

import requests
from bs4 import BeautifulSoup

from modules.permits.scrapers.base import JurisdictionAdapter


class PanamaCityBeachAdapter(JurisdictionAdapter):
    slug = "panama-city-beach"
    display_name = "Panama City Beach"
    mode = "live"
    search_url = "https://panamacitybeach.portal.iworq.net/PANAMACITYBEACH/permits/602"
    referer = "https://www.pcbfl.gov/219/Permit-Inspection-Search"
    request_headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/123.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    excluded_type_terms = (
        "plumbing",
        "mechanical",
        "electrical",
        "change out",
        "sign",
        "pool",
        "spa",
        "solar",
        "roof",
        "reroof",
        "demo",
        "demolition",
        "repair",
        "renov",
        "alter",
        "addition",
        "fence",
        "dock",
        "seawall",
        "gas",
    )
    residential_type_terms = (
        "single family",
        "residential building",
        "res new",
        "new dwelling",
        "dwelling",
        "house",
        "home",
    )
    bootstrap_lookback_days = 120
    rolling_overlap_days = 14

    def fetch_permits(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[dict]:
        end_date = end_date or date.today()
        start_date = start_date or (end_date - timedelta(days=7))

        session = self.build_session(headers=self.request_headers, referer=self.referer)

        first_page = self._fetch_search_page(session, start_date, end_date, page=1)
        permits = self._parse_search_results(first_page, session)
        max_page = self._extract_max_page(first_page)

        for page in range(2, max_page + 1):
            page_html = self._fetch_search_page(session, start_date, end_date, page=page)
            permits.extend(self._parse_search_results(page_html, session))

        return permits

    def _fetch_search_page(
        self,
        session: requests.Session,
        start_date: date,
        end_date: date,
        page: int,
    ) -> str:
        params = {
            "searchField": "permit_dt_range",
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
        }
        if page > 1:
            params["page"] = page
        response = session.get(self.search_url, params=params, timeout=30)
        response.raise_for_status()
        self.record_response_trace(
            "search-results" if page == 1 else "search-pagination",
            response,
            metadata={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "page": page,
            },
        )
        return response.text

    def _parse_search_results(self, html: str, session: requests.Session) -> list[dict]:
        soup = BeautifulSoup(html, "html.parser")
        table = soup.select_one("table.table.table-sm")
        if table is None:
            return []

        permits: list[dict] = []
        for row in table.find_all("tr")[1:]:
            cells = row.find_all("td")
            permit_cell = row.find("th")
            if permit_cell is None or len(cells) < 6:
                continue

            permit_number = permit_cell.get_text(" ", strip=True)
            issue_date = datetime.strptime(cells[0].get_text(" ", strip=True), "%m/%d/%Y").date().isoformat()
            permit_type = cells[1].get_text(" ", strip=True)
            if not self._is_target_permit_type(permit_type):
                continue

            detail_url = permit_cell.get("data-route") or permit_cell.find("a").get("href")
            detail_fields = self._fetch_detail_fields(session, detail_url)
            contractor_name = cells[5].get_text(" ", strip=True) or detail_fields.get("Applicant") or cells[3].get_text(" ", strip=True)
            permits.append(
                {
                    "permit_number": permit_number,
                    "address": cells[2].get_text(" ", strip=True),
                    "parcel_id": detail_fields.get("Parcel #"),
                    "issue_date": detail_fields.get("Issued/Paid Date") or detail_fields.get("Permit Date") or issue_date,
                    "status": detail_fields.get("Status") or cells[4].get_text(" ", strip=True),
                    "permit_type": detail_fields.get("Permit Type") or permit_type,
                    "valuation": self._parse_decimal(detail_fields.get("Valuation")),
                    "raw_subdivision_name": None,
                    "raw_contractor_name": contractor_name,
                    "latitude": None,
                    "longitude": None,
                }
            )
        return permits

    def _fetch_detail_fields(self, session: requests.Session, detail_url: str) -> dict[str, str]:
        soup = BeautifulSoup(
            self.get_cached_text(
                session,
                detail_url,
                timeout=30,
                artifact_type="detail-page",
                metadata={"detail_url": detail_url},
            ),
            "html.parser",
        )
        fields: dict[str, str] = {}

        for row in soup.select("div.row"):
            cols = row.select(":scope > div.col")
            if len(cols) != 2:
                continue
            label = cols[0].get_text(" ", strip=True).rstrip(":")
            value = cols[1].get_text(" ", strip=True)
            if label:
                fields[label] = value

        text = soup.get_text("\n", strip=True)
        parcel_match = re.search(r"Parcel #:\s*([A-Z0-9-]+)", text)
        if parcel_match:
            fields["Parcel #"] = parcel_match.group(1)

        for key in ("Permit Date", "Issued/Paid Date"):
            if key in fields and fields[key]:
                try:
                    fields[key] = datetime.strptime(fields[key], "%m/%d/%Y").date().isoformat()
                except ValueError:
                    pass

        return fields

    def _extract_max_page(self, html: str) -> int:
        soup = BeautifulSoup(html, "html.parser")
        pages = {1}
        for link in soup.select("ul.pagination a[href]"):
            query = parse_qs(urlparse(link.get("href")).query)
            if "page" in query:
                try:
                    pages.add(int(query["page"][0]))
                except (TypeError, ValueError):
                    continue
        return max(pages)

    def _is_target_permit_type(self, permit_type: str) -> bool:
        normalized = permit_type.lower()
        if any(term in normalized for term in self.excluded_type_terms):
            return False
        return any(term in normalized for term in self.residential_type_terms)

    @staticmethod
    def _parse_decimal(raw_value: str | None) -> float | None:
        if not raw_value:
            return None
        cleaned = raw_value.replace(",", "").strip()
        try:
            return float(cleaned)
        except ValueError:
            return None
