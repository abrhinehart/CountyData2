from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

import requests
from bs4 import BeautifulSoup


DATA_DIR = Path(__file__).resolve().parents[1] / "data"


@dataclass(slots=True)
class SourceResearch:
    jurisdiction: str
    portal_type: str
    portal_url: str
    public_access: str
    live_ready: bool
    status: str
    searchable_fields: list[str]
    notes: list[str]
    evidence: list[dict[str, str]]


class JurisdictionAdapter(ABC):
    slug: str
    display_name: str
    mode: str = "fixture"
    bootstrap_lookback_days: int | None = None
    rolling_overlap_days: int | None = None
    trace_excerpt_limit = 1200

    @abstractmethod
    def fetch_permits(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[dict]:
        raise NotImplementedError

    def research(self) -> SourceResearch:
        research_index = json.loads((DATA_DIR / "source_research.json").read_text(encoding="utf-8"))
        entry = research_index[self.slug]
        return SourceResearch(
            jurisdiction=entry["jurisdiction"],
            portal_type=entry["portal_type"],
            portal_url=entry["portal_url"],
            public_access=entry["public_access"],
            live_ready=entry["live_ready"],
            status=entry["status"],
            searchable_fields=entry["searchable_fields"],
            notes=entry["notes"],
            evidence=entry["evidence"],
        )

    def resolve_default_window(
        self,
        *,
        has_existing_permits: bool,
        last_success_at: datetime | None,
        today: date | None = None,
    ) -> tuple[date | None, date | None]:
        bootstrap_lookback_days = getattr(self, "bootstrap_lookback_days", None)
        rolling_overlap_days = getattr(self, "rolling_overlap_days", None)
        if bootstrap_lookback_days is None or rolling_overlap_days is None:
            return None, None

        today = today or date.today()
        if not has_existing_permits:
            return today - timedelta(days=bootstrap_lookback_days), today
        if last_success_at is None:
            return today - timedelta(days=rolling_overlap_days), today
        return last_success_at.date() - timedelta(days=rolling_overlap_days), today

    def build_session(
        self,
        *,
        headers: dict[str, str] | None = None,
        referer: str | None = None,
    ) -> requests.Session:
        self.reset_run_state()
        session = requests.Session()
        if headers:
            session.headers.update(headers)
        if referer:
            session.headers["Referer"] = referer
        return session

    def reset_run_state(self) -> None:
        self._request_cache: dict[str, str] = {}
        self._trace_artifacts: list[dict] = []

    def extract_form_fields(self, html: str) -> dict[str, str]:
        soup = BeautifulSoup(html, "html.parser")
        form = soup.find("form")
        if form is None:
            raise ValueError(f"{self.display_name} page did not expose an HTML form.")

        payload: dict[str, str] = {}
        for tag in form.find_all("input"):
            name = tag.get("name")
            if not name:
                continue
            input_type = (tag.get("type") or "").lower()
            if input_type in {"checkbox", "radio"} and not tag.has_attr("checked"):
                continue
            payload[name] = tag.get("value", "")

        for tag in form.find_all("select"):
            name = tag.get("name")
            if not name:
                continue
            selected = tag.find("option", selected=True)
            payload[name] = selected.get("value", "") if selected else ""

        return payload

    def get_cached_text(
        self,
        session: requests.Session,
        url: str,
        *,
        method: str = "get",
        cache_key: str | None = None,
        artifact_type: str | None = None,
        metadata: dict | None = None,
        **kwargs,
    ) -> str:
        cache = getattr(self, "_request_cache", None)
        if cache is None:
            cache = {}
            self._request_cache = cache

        key = cache_key or f"{method.upper()}:{url}"
        if key in cache:
            return cache[key]

        request = getattr(session, "request", None)
        if request is None:
            request = getattr(session, method.lower())
            response = request(url, **kwargs)
        else:
            response = request(method, url, **kwargs)
        response.raise_for_status()
        cache[key] = response.text
        if artifact_type:
            self.record_response_trace(
                artifact_type,
                response,
                metadata=metadata,
            )
        return response.text

    def record_response_trace(
        self,
        artifact_type: str,
        response,
        *,
        metadata: dict | None = None,
        excerpt: str | None = None,
    ) -> None:
        content_type = None
        if getattr(response, "headers", None) is not None:
            content_type = response.headers.get("Content-Type")
        self.record_trace(
            artifact_type=artifact_type,
            method=getattr(response, "request", None).method if getattr(response, "request", None) is not None else None,
            url=getattr(response, "url", None),
            status_code=getattr(response, "status_code", None),
            content_type=content_type,
            excerpt=excerpt if excerpt is not None else self._build_trace_excerpt(
                getattr(response, "text", "") or "",
                content_type=content_type,
            ),
            metadata=metadata,
        )

    def record_trace(
        self,
        *,
        artifact_type: str,
        method: str | None,
        url: str | None,
        status_code: int | None = None,
        content_type: str | None = None,
        excerpt: str | None = None,
        metadata: dict | None = None,
    ) -> None:
        trace_artifacts = getattr(self, "_trace_artifacts", None)
        if trace_artifacts is None:
            trace_artifacts = []
            self._trace_artifacts = trace_artifacts
        trace_artifacts.append(
            {
                "artifact_type": artifact_type,
                "method": method.upper() if method else None,
                "url": self._redact_url(url),
                "status_code": status_code,
                "content_type": content_type,
                "excerpt": self._truncate_text(excerpt),
                "metadata": metadata or {},
                "created_at": datetime.now(UTC).isoformat(),
            }
        )

    def consume_trace_artifacts(self) -> list[dict]:
        artifacts = [dict(item) for item in getattr(self, "_trace_artifacts", [])]
        self._trace_artifacts = []
        return artifacts

    def _build_trace_excerpt(
        self,
        text: str,
        *,
        content_type: str | None = None,
    ) -> str | None:
        if not text:
            return None
        excerpt_source = text
        if content_type and "html" in content_type.lower():
            excerpt_source = BeautifulSoup(text, "html.parser").get_text(" ", strip=True)
        excerpt_source = " ".join(excerpt_source.split())
        return self._truncate_text(excerpt_source)

    def _truncate_text(self, value: str | None) -> str | None:
        if not value:
            return None
        if len(value) <= self.trace_excerpt_limit:
            return value
        return f"{value[: self.trace_excerpt_limit - 1]}..."

    @staticmethod
    def _redact_url(url: str | None) -> str | None:
        if not url:
            return None
        parts = urlsplit(url)
        if not parts.query:
            return url
        return urlunsplit((parts.scheme, parts.netloc, parts.path, "[redacted]", parts.fragment))

    def load_fixture_records(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[dict]:
        records = json.loads((DATA_DIR / "demo_permits.json").read_text(encoding="utf-8"))
        scoped = [record for record in records if record["jurisdiction_slug"] == self.slug]
        if start_date is not None:
            scoped = [record for record in scoped if date.fromisoformat(record["issue_date"]) >= start_date]
        if end_date is not None:
            scoped = [record for record in scoped if date.fromisoformat(record["issue_date"]) <= end_date]
        return scoped
