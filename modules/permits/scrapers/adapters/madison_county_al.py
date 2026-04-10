from __future__ import annotations

from datetime import date

from modules.permits.scrapers.base import JurisdictionAdapter


class MadisonCountyAlAdapter(JurisdictionAdapter):
    slug = "madison-county-al"
    display_name = "Madison County, AL"
    mode = "live"
    bootstrap_lookback_days = 90
    rolling_overlap_days = 14

    portal_url = "https://cityview.madisoncountyal.gov/Portal"

    def fetch_permits(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[dict]:
        # TODO: Implement authenticated CityView scraper.
        # For now, fall back to fixture data so the adapter loads cleanly.
        return self.load_fixture_records(start_date, end_date)
