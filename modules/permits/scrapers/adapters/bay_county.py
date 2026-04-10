from __future__ import annotations

import re
from calendar import monthrange
from datetime import date, datetime
from io import BytesIO
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader

from modules.permits.scrapers.base import JurisdictionAdapter


class BayCountyAdapter(JurisdictionAdapter):
    slug = "bay-county"
    display_name = "Bay County"
    mode = "live"

    permits_page_url = "https://www.baycountyfl.gov/155/Permits"
    request_headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/123.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    _field_starts = [
        ("application_date", 33),
        ("building_use", 63),
        ("permit_meta", 99),
        ("address", 166),
        ("owner_name", 199),
        ("contractor_name", 223),
        ("issued_date", 250),
        ("finalled_date", 280),
        ("permit_status", 310),
        ("valuation", 362),
    ]
    _date_line_pattern = re.compile(r"^\s*(\d{2}/\d{2}/\d{4})")
    _permit_number_pattern = re.compile(r"(PR[A-Z]{2,}\d{6,})")
    _token_pattern = re.compile(r"\S(?:.*?\S)?(?=(?:\s{2,}|$))")
    _monthly_report_pattern = re.compile(r"^(?P<month>[A-Za-z]+)\s+(?P<year>\d{4})\s+Permit Report$")
    _annual_report_pattern = re.compile(r"^(?P<year>\d{4})\s+Permit Report$")

    def fetch_permits(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[dict]:
        reports = self._select_reports(
            self._discover_reports(),
            start_date,
            end_date,
        )
        if not reports:
            return []

        session = requests.Session()
        session.headers.update(self.request_headers)

        permits: list[dict] = []
        seen: set[str] = set()
        for report in reports:
            for row in self._fetch_report_rows(session, report["url"]):
                permit = self._row_to_permit(row, start_date, end_date)
                if permit is None or permit["permit_number"] in seen:
                    continue
                seen.add(permit["permit_number"])
                permits.append(permit)
        return permits

    def _discover_reports(self) -> list[dict]:
        response = requests.get(
            self.permits_page_url,
            headers=self.request_headers,
            timeout=30,
        )
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        reports: list[dict] = []
        for link in soup.find_all("a", href=True):
            label = self._collapse_whitespace(link.get_text(" ", strip=True))
            if "Permit Report" not in label:
                continue
            parsed = self._parse_report_label(label)
            if parsed is None:
                continue
            reports.append(
                {
                    "label": label,
                    "url": urljoin(self.permits_page_url, link["href"]),
                    **parsed,
                }
            )

        return sorted(reports, key=lambda report: (report["start_date"], report["url"]))

    def _parse_report_label(self, label: str) -> dict | None:
        monthly = self._monthly_report_pattern.match(label)
        if monthly:
            month_start = datetime.strptime(
                f"{monthly.group('month')} {monthly.group('year')}",
                "%B %Y",
            ).date().replace(day=1)
            month_end = month_start.replace(
                day=monthrange(month_start.year, month_start.month)[1]
            )
            return {
                "kind": "month",
                "start_date": month_start,
                "end_date": month_end,
            }

        annual = self._annual_report_pattern.match(label)
        if annual:
            year = int(annual.group("year"))
            return {
                "kind": "year",
                "start_date": date(year, 1, 1),
                "end_date": date(year, 12, 31),
            }

        return None

    def _select_reports(
        self,
        reports: list[dict],
        start_date: date | None,
        end_date: date | None,
    ) -> list[dict]:
        if not reports:
            return []

        if start_date is None and end_date is None:
            latest = max(reports, key=lambda report: (report["end_date"], report["kind"]))
            return [latest]

        effective_start = start_date or min(report["start_date"] for report in reports)
        effective_end = end_date or max(report["end_date"] for report in reports)
        overlapping = [
            report
            for report in reports
            if report["start_date"] <= effective_end and report["end_date"] >= effective_start
        ]
        if not overlapping:
            return []

        monthly = {
            (report["start_date"].year, report["start_date"].month): report
            for report in overlapping
            if report["kind"] == "month"
        }
        annual = {
            report["start_date"].year: report
            for report in overlapping
            if report["kind"] == "year"
        }

        selected: list[dict] = []
        cursor = effective_start.replace(day=1)
        final_month = effective_end.replace(day=1)
        while cursor <= final_month:
            report = monthly.get((cursor.year, cursor.month)) or annual.get(cursor.year)
            if report and report not in selected:
                selected.append(report)
            if cursor.month == 12:
                cursor = cursor.replace(year=cursor.year + 1, month=1)
            else:
                cursor = cursor.replace(month=cursor.month + 1)
        return selected

    def _fetch_report_rows(self, session: requests.Session, url: str) -> list[dict]:
        response = session.get(url, timeout=60)
        response.raise_for_status()
        reader = PdfReader(BytesIO(response.content))
        rows: list[dict] = []
        for page in reader.pages:
            text = page.extract_text(extraction_mode="layout") or ""
            rows.extend(self._parse_report_text(text))
        return rows

    def _parse_report_text(self, text: str) -> list[dict]:
        rows: list[dict] = []
        current: dict[str, str] | None = None
        current_field_starts = self._field_starts

        for raw_line in text.splitlines():
            stripped = raw_line.strip()
            if not stripped:
                continue

            if self._is_footer_line(stripped):
                if current:
                    rows.append(self._finalize_row(current))
                    current = None
                    current_field_starts = self._field_starts
                continue

            if self._is_header_line(stripped):
                continue

            tokens = [
                (match.start(), self._collapse_whitespace(match.group(0)))
                for match in self._token_pattern.finditer(raw_line)
            ]
            if not tokens:
                continue

            if self._date_line_pattern.fullmatch(tokens[0][1]):
                if current:
                    rows.append(self._finalize_row(current))
                current = {key: "" for key, _ in self._field_starts}
                current_field_starts = self._infer_field_starts(tokens)

            if current is None:
                continue

            for start, piece in tokens:
                field_name = self._field_name_for_token(start, current_field_starts)
                current[field_name] = f"{current[field_name]} {piece}".strip()

        if current:
            rows.append(self._finalize_row(current))

        return rows

    def _row_to_permit(
        self,
        row: dict,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> dict | None:
        permit_number = row.get("permit_number", "")
        issued_date = self._parse_report_date(row.get("issued_date"))
        if not permit_number.startswith("PRSF") or issued_date is None:
            return None
        if start_date and issued_date < start_date:
            return None
        if end_date and issued_date > end_date:
            return None

        return {
            "permit_number": permit_number,
            "address": row["address"],
            "parcel_id": None,
            "issue_date": issued_date.isoformat(),
            "status": row["permit_status"],
            "permit_type": row["permit_type"] or "One and Two Family Dwelling",
            "valuation": self._parse_currency(row.get("valuation")),
            "raw_subdivision_name": None,
            "raw_contractor_name": row.get("contractor_name") or row.get("owner_name"),
            "latitude": None,
            "longitude": None,
        }

    def _finalize_row(self, row: dict[str, str]) -> dict[str, str]:
        finalized = {key: self._collapse_whitespace(value) for key, value in row.items()}
        permit_meta = finalized.pop("permit_meta")
        permit_match = self._permit_number_pattern.search(permit_meta)
        if permit_match:
            finalized["permit_number"] = permit_match.group(1)
            permit_type = f"{permit_meta[:permit_match.start()]} {permit_meta[permit_match.end():]}"
            finalized["permit_type"] = self._collapse_whitespace(permit_type)
        else:
            finalized["permit_number"] = ""
            finalized["permit_type"] = permit_meta
        return finalized

    def _field_name_for_token(
        self,
        start_index: int,
        field_starts: list[tuple[str, int]] | None = None,
    ) -> str:
        field_starts = field_starts or self._field_starts
        field_name = field_starts[0][0]
        for candidate_name, candidate_start in field_starts:
            if start_index >= candidate_start:
                field_name = candidate_name
            else:
                break
        return field_name

    def _infer_field_starts(self, tokens: list[tuple[int, str]]) -> list[tuple[str, int]]:
        if len(tokens) < 4:
            return self._field_starts

        permit_index = next(
            (index for index, (_, piece) in enumerate(tokens) if self._permit_number_pattern.fullmatch(piece)),
            None,
        )
        if permit_index is None or permit_index < 2:
            return self._field_starts

        inferred = {
            "application_date": tokens[0][0],
            "building_use": tokens[1][0],
            "permit_meta": tokens[2][0],
        }

        trailing_fields = ["address", "owner_name", "contractor_name"]
        for offset, field_name in enumerate(trailing_fields, start=1):
            token_index = permit_index + offset
            if token_index < len(tokens):
                inferred[field_name] = tokens[token_index][0]

        tail_tokens = tokens[permit_index + 4 :]
        date_positions = [
            start
            for start, piece in tail_tokens
            if self._date_line_pattern.fullmatch(piece)
        ]
        if date_positions:
            inferred["issued_date"] = date_positions[0]
        if len(date_positions) > 1:
            inferred["finalled_date"] = date_positions[1]

        valuation_position = next(
            (start for start, piece in tail_tokens if piece.startswith("$")),
            None,
        )
        if valuation_position is not None:
            inferred["valuation"] = valuation_position

        status_position = next(
            (
                start
                for start, piece in tail_tokens
                if not self._date_line_pattern.fullmatch(piece) and not piece.startswith("$")
            ),
            None,
        )
        if status_position is not None:
            inferred["permit_status"] = status_position

        if "finalled_date" not in inferred and "issued_date" in inferred:
            inferred["finalled_date"] = inferred["issued_date"] + 28
        if "permit_status" not in inferred and "finalled_date" in inferred:
            inferred["permit_status"] = inferred["finalled_date"] + 28
        if "valuation" not in inferred and "permit_status" in inferred:
            inferred["valuation"] = inferred["permit_status"] + 48

        return [
            (field_name, inferred.get(field_name, default_start))
            for field_name, default_start in self._field_starts
        ]

    @staticmethod
    def _is_header_line(stripped: str) -> bool:
        return (
            stripped == "January"
            or stripped.startswith("dateEntered")
            or stripped.startswith("PERMITS ISSUED BY DATE AND TYPE")
            or stripped == "Permit Type Permit Number"
            or BayCountyAdapter._date_line_pattern.fullmatch(stripped) is not None
        )

    @staticmethod
    def _is_footer_line(stripped: str) -> bool:
        return (
            stripped.startswith("=")
            or stripped.startswith("Count ")
            or stripped.startswith("Subtotal ")
            or stripped.startswith("Total ")
        )

    @staticmethod
    def _parse_report_date(value: str | None) -> date | None:
        if not value:
            return None
        candidate = value[:10]
        try:
            return datetime.strptime(candidate, "%m/%d/%Y").date()
        except ValueError:
            return None

    @staticmethod
    def _parse_currency(value: str | None) -> float | None:
        if not value:
            return None
        cleaned = value.replace("$", "").replace(",", "").strip()
        try:
            return float(cleaned)
        except ValueError:
            return None

    @staticmethod
    def _collapse_whitespace(value: str) -> str:
        return " ".join(value.split())
