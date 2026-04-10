from __future__ import annotations

import json
from datetime import UTC, date, datetime

import requests

from modules.permits.scrapers.base import JurisdictionAdapter


class PanamaCityAdapter(JurisdictionAdapter):
    slug = "panama-city"
    display_name = "Panama City"
    mode = "live"

    domain_group_id = "US-FL54700"
    municipality_number = "FL54700"
    config_url = "https://us.cloudpermit.com/api/command/public-map/config-v2"
    search_url = "https://us.cloudpermit.com/api/command/public-map/search-v2"
    referer = "https://us.cloudpermit.com/gov/map/US-FL54700"
    request_headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/123.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json",
        "Content-Type": "application/transit+json",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": referer,
    }
    tile_width = 7500.0
    tile_height = 3500.0
    tile_overlap = 0.9
    max_radius = 8
    response_cap = 1000

    residential_categories = {
        "RESIDENTIAL",
        "RESIDENTIAL PRIVATE PROVIDER",
    }
    target_work_type = "NEW"
    target_work_target = "SINGLE FAMILY DWELLING"

    def fetch_permits(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[dict]:
        session = requests.Session()
        session.headers.update(self.request_headers)

        center_x, center_y = self._fetch_municipality_center(session)
        features = self._fetch_features(session, center_x, center_y)

        permits: list[dict] = []
        seen: set[str] = set()
        for feature in features:
            permit = self._feature_to_permit(feature, start_date, end_date)
            if permit is None or permit["permit_number"] in seen:
                continue
            seen.add(permit["permit_number"])
            permits.append(permit)
        return permits

    def _fetch_municipality_center(self, session: requests.Session) -> tuple[float, float]:
        response = session.get(
            self.config_url,
            params={"domain-group-id": self.domain_group_id},
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        for municipality in payload.get("municipalities", []):
            if municipality.get("municipality/number") != self.municipality_number:
                continue
            center = municipality.get("municipality/center-location") or []
            if len(center) == 2:
                return float(center[0]), float(center[1])
        raise ValueError("Cloudpermit public-map config did not expose the Panama City center location.")

    def _fetch_features(
        self,
        session: requests.Session,
        center_x: float,
        center_y: float,
    ) -> list[dict]:
        features_by_id: dict[str, dict] = {}
        step_x = self.tile_width * self.tile_overlap
        step_y = self.tile_height * self.tile_overlap

        for radius in range(self.max_radius + 1):
            ring_total = 0
            for grid_x in range(-radius, radius + 1):
                for grid_y in range(-radius, radius + 1):
                    if max(abs(grid_x), abs(grid_y)) != radius:
                        continue

                    features = self._search_tile(
                        session,
                        center_x + (grid_x * step_x),
                        center_y + (grid_y * step_y),
                    )
                    ring_total += len(features)
                    for feature in features:
                        permit_number = feature.get("properties", {}).get("workspace/municipal-case-id")
                        if permit_number:
                            features_by_id[permit_number] = feature

            if radius >= 1 and ring_total == 0:
                break

        return list(features_by_id.values())

    def _search_tile(
        self,
        session: requests.Session,
        center_x: float,
        center_y: float,
    ) -> list[dict]:
        min_x = center_x - (self.tile_width / 2)
        max_x = center_x + (self.tile_width / 2)
        min_y = center_y - (self.tile_height / 2)
        max_y = center_y + (self.tile_height / 2)
        response = session.post(
            self.search_url,
            data=self._build_search_payload(min_x, min_y, max_x, max_y).encode("utf-8"),
            timeout=60,
        )
        response.raise_for_status()
        payload = response.json()
        features = payload.get("features", [])
        if len(features) >= self.response_cap:
            raise ValueError("Cloudpermit search tile hit the apparent 1000-record cap; reduce tile size.")
        return features

    def _build_search_payload(
        self,
        min_x: float,
        min_y: float,
        max_x: float,
        max_y: float,
    ) -> str:
        payload = [
            "^ ",
            "~:shape",
            [
                "^ ",
                "~:type",
                "Polygon",
                "~:coordinates",
                [[[min_x, min_y], [min_x, max_y], [max_x, max_y], [max_x, min_y], [min_x, min_y]]],
            ],
            "~:permit-types",
            ["~#set", ["~:permit-type/B"]],
            "~:domain-group-id",
            self.domain_group_id,
            "~:municipalities",
            ["^4", [self.municipality_number]],
        ]
        return json.dumps(payload, separators=(",", ":"))

    def _feature_to_permit(
        self,
        feature: dict,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> dict | None:
        properties = feature.get("properties") or {}
        if not self._is_target_feature(properties):
            return None

        permit_number = properties.get("workspace/municipal-case-id")
        issue_date = (
            self._parse_api_date(properties.get("issued-date"))
            or self._parse_api_date(properties.get("created"))
            or self._parse_api_date(properties.get("submitted"))
            or self._parse_api_date(properties.get("completion-date"))
        )
        if not permit_number or issue_date is None:
            return None
        if start_date and issue_date < start_date:
            return None
        if end_date and issue_date > end_date:
            return None

        longitude = None
        latitude = None
        coordinates = (feature.get("geometry") or {}).get("coordinates") or []
        if len(coordinates) == 2:
            longitude = coordinates[0]
            latitude = coordinates[1]

        address = properties.get("address/full-address") or "Address unavailable"
        applicants = properties.get("applicants") or []
        owners = properties.get("property-owners") or []

        return {
            "permit_number": permit_number,
            "address": address,
            "parcel_id": properties.get("property/id"),
            "issue_date": issue_date.isoformat(),
            "status": self._normalize_status(properties.get("domain/state")),
            "permit_type": "New Single-family dwelling",
            "valuation": None,
            "raw_subdivision_name": self._extract_subdivision_hint(address),
            "raw_contractor_name": (applicants[0] if applicants else None) or (owners[0] if owners else None),
            "latitude": latitude,
            "longitude": longitude,
        }

    def _is_target_feature(self, properties: dict) -> bool:
        categories = {self._normalize_label(value) for value in self._text_values(properties.get("category-names"))}
        if not categories.intersection(self.residential_categories):
            return False

        targets = {
            self._normalize_label(value)
            for value in self._text_values(properties.get("application/work-target-names"))
        }
        work_types = {
            self._normalize_label(value)
            for value in self._text_values(properties.get("application/work-type-names"))
        }
        return self.target_work_target in targets and self.target_work_type in work_types

    @staticmethod
    def _text_values(items: list[dict] | None) -> list[str]:
        values: list[str] = []
        for item in items or []:
            text = item.get("localized-string/text")
            if text:
                values.append(text)
        return values

    @staticmethod
    def _normalize_label(value: str) -> str:
        return " ".join(value.upper().replace("-", " ").split())

    @staticmethod
    def _parse_api_date(value: str | int | float | None) -> date | None:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(value / 1000, tz=UTC).date()

        candidate = str(value).strip()
        if not candidate:
            return None
        if candidate.endswith("Z"):
            candidate = candidate.replace("Z", "+00:00")

        try:
            return datetime.fromisoformat(candidate).date()
        except ValueError:
            pass

        try:
            return date.fromisoformat(candidate[:10])
        except ValueError:
            return None

    @staticmethod
    def _normalize_status(value: str | None) -> str:
        if not value:
            return "unknown"
        return value.split("/")[-1].replace("-", " ")

    @staticmethod
    def _extract_subdivision_hint(address: str | None) -> str | None:
        if not address or "/" not in address:
            return None
        prefix = address.split("/", 1)[0].strip()
        if not prefix or prefix[0].isdigit():
            return None
        return prefix
