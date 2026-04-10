from __future__ import annotations

from datetime import date

from modules.permits.scrapers.base import JurisdictionAdapter


class OkeechobeeAdapter(JurisdictionAdapter):
    slug = "okeechobee"
    display_name = "Okeechobee County"
    mode = "research-only"

    def fetch_permits(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[dict]:
        return self.load_fixture_records(start_date, end_date)
