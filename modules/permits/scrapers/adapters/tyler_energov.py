"""
Tyler EnerGov / Civic Access permit adapter.

Generalizable adapter for jurisdictions using Tyler EnerGov Civic Access
portals.  The three-endpoint flow:

  1.  GET  /api/tenants/gettenantslist  → tenant ID + name headers
  2.  GET  /api/energov/search/criteria → criteria template (cache)
  3.  POST /api/energov/search/search   → paginated permit results

Thin per-county subclasses only need to override ``slug``, ``display_name``,
and ``base_url``.
"""

from __future__ import annotations

import copy
import json
import time
from datetime import date, timedelta

import requests

from modules.permits.scrapers.base import JurisdictionAdapter


class TylerEnerGovAdapter(JurisdictionAdapter):
    slug = "tyler-energov"
    display_name = "Tyler EnerGov"
    mode = "live"
    base_url = ""  # MUST be overridden by subclass

    bootstrap_lookback_days = 120
    rolling_overlap_days = 14
    page_size = 100
    max_pages = 200
    sleep_between_pages = 0.25

    residential_type_terms = (
        "residential",
        "new single family",
        "new construction",
        "new dwelling",
        "single family",
        "sfr",
        "sfd",
    )
    excluded_type_terms = (
        "demolition",
        "demo ",
        "sign",
        "pool",
        "solar",
        "roof",
        "reroof",
        "mechanical",
        "electrical",
        "plumbing",
        "fence",
        "dock",
        "temp",
        "temporary",
    )

    # ── public entry point ──────────────────────────────────────────────

    def fetch_permits(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[dict]:
        end_date = end_date or date.today()
        start_date = start_date or (end_date - timedelta(days=self.rolling_overlap_days))

        session = self.build_session(headers=self._request_headers())

        self._initialize_tenant(session)
        self._load_criteria_template(session)

        all_permits: list[dict] = []
        page = 1

        while True:
            permits, total_pages, saw_before_start = self._search_permits(
                session, start_date, end_date, page,
            )
            all_permits.extend(permits)

            # Stop if: all pages exhausted, safety cap hit, or results
            # have passed before our start_date (sorted desc by IssueDate).
            if page >= total_pages or page >= self.max_pages or saw_before_start:
                break

            page += 1
            time.sleep(self.sleep_between_pages)

        return all_permits

    # ── internal helpers ────────────────────────────────────────────────

    def _request_headers(self) -> dict:
        return {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/123.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": self.base_url + "/",
        }

    def _initialize_tenant(self, session: requests.Session) -> None:
        url = self._api_url("/tenants/gettenantslist")
        response = session.get(url, timeout=30)
        response.raise_for_status()
        self.record_response_trace(
            "tenant-init",
            response,
            metadata={"url": url},
        )
        data = response.json()
        tenant = data["Result"][0]
        self._tenant_id = str(tenant["TenantID"])
        self._tenant_name = tenant["TenantName"]
        session.headers["tenantId"] = self._tenant_id
        session.headers["tenantName"] = self._tenant_name

    def _load_criteria_template(self, session: requests.Session) -> None:
        url = self._api_url("/energov/search/criteria")
        response = session.get(url, timeout=30)
        response.raise_for_status()
        self.record_response_trace(
            "criteria-template",
            response,
            metadata={"url": url},
        )
        data = response.json()
        self._criteria_template = data["Result"]

    def _build_search_body(self, start_date: date, end_date: date, page: int) -> dict:
        body = copy.deepcopy(self._criteria_template)

        body["SearchModule"] = 1
        body["FilterModule"] = 2
        body["PageNumber"] = page
        body["PageSize"] = self.page_size
        body["SortBy"] = "IssueDate"
        body["SortAscending"] = False

        pc = body.get("PermitCriteria") or {}
        pc["IssueDateFrom"] = start_date.strftime("%m/%d/%Y")
        pc["IssueDateTo"] = end_date.strftime("%m/%d/%Y")
        pc["PageNumber"] = page
        pc["PageSize"] = self.page_size
        pc["SortBy"] = "IssueDate"
        pc["SortAscending"] = False
        body["PermitCriteria"] = pc

        return body

    def _search_permits(
        self,
        session: requests.Session,
        start_date: date,
        end_date: date,
        page: int,
    ) -> tuple[list[dict], int, bool]:
        url = self._api_url("/energov/search/search")
        body = self._build_search_body(start_date, end_date, page)
        response = session.post(
            url,
            json=body,
            timeout=60,
        )
        response.raise_for_status()
        self.record_response_trace(
            "permit-search",
            response,
            metadata={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "page": page,
            },
        )

        data = response.json()
        result = data.get("Result") or {}
        entities = result.get("EntityResults") or []
        total_pages = result.get("TotalPages", 1)

        permits = []
        saw_before_start = False
        start_iso = start_date.isoformat()
        end_iso = end_date.isoformat()

        for entity in entities:
            permit = self._map_entity_to_permit(entity)
            issue = permit.get("issue_date")
            # Skip permits with no issue date (submitted but not yet issued).
            if not issue:
                continue
            # Client-side date filtering — server may not honor date range.
            if issue < start_iso:
                saw_before_start = True
                continue
            if issue > end_iso:
                continue
            if self._is_target_permit_type(permit):
                permits.append(permit)

        return permits, total_pages, saw_before_start

    def _map_entity_to_permit(self, entity: dict) -> dict:
        project_name = (entity.get("ProjectName") or "").strip() or None
        return {
            "permit_number": entity.get("CaseNumber"),
            "address": entity.get("AddressDisplay"),
            "parcel_id": entity.get("MainParcel"),
            "issue_date": self._parse_api_date(entity.get("IssueDate")),
            "status": entity.get("CaseStatus"),
            "permit_type": entity.get("CaseType"),
            "valuation": None,
            "raw_subdivision_name": project_name,
            "raw_contractor_name": None,
            "raw_applicant_name": None,
            "raw_licensed_professional_name": None,
            "latitude": None,
            "longitude": None,
        }

    def _parse_api_date(self, value: str | None) -> str | None:
        if not value:
            return None
        # "2026-08-23T00:00:00" → "2026-08-23"
        return value[:10] if "T" in value else value

    def _is_target_permit_type(self, permit: dict) -> bool:
        permit_type = (permit.get("permit_type") or "").lower()
        if any(term in permit_type for term in self.excluded_type_terms):
            return False
        return any(term in permit_type for term in self.residential_type_terms)

    def _api_url(self, path: str) -> str:
        return f"{self.base_url}/api{path}"
