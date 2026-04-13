from __future__ import annotations

from bs4 import Tag

from modules.permits.scrapers.adapters.iworq import IworqAdapter


class HainesCityAdapter(IworqAdapter):
    slug = "haines-city"
    display_name = "Haines City"
    search_url = "https://haines.portal.iworq.net/HAINES/permits/600"

    # Haines City iWorQ table columns:
    #   TH: Permit #
    #   0: Date
    #   1: Planning/Zoning Status
    #   2: Application Status
    #   3: Fire Marshall Review Status
    #   4: Building Plan Review Status
    #   5: Site Address
    #   6: Site City/State/Zip
    #   7: Project Name
    #   8: Request Inspection
    #   9: View
    #
    # No permit-type column — type filtering deferred to detail page Description.

    def _extract_row_fields(
        self, permit_cell: Tag, cells: list[Tag],
    ) -> dict[str, str | None] | None:
        if len(cells) < 7:
            return None
        street = cells[5].get_text(" ", strip=True)
        city_state_zip = cells[6].get_text(" ", strip=True)
        address = f"{street}, {city_state_zip}".strip(", ")
        return {
            "permit_number": permit_cell.get_text(" ", strip=True),
            "issue_date_str": cells[0].get_text(" ", strip=True),
            "permit_type": None,  # no type column — filter from detail page
            "address": address,
            "status": cells[2].get_text(" ", strip=True),
            "contractor_hint": None,  # contractor only on detail page
            "valuation_hint": None,
            "detail_url": permit_cell.get("data-route") or (permit_cell.find("a") or {}).get("href"),
        }
