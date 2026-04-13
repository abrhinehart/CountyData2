from __future__ import annotations

from bs4 import Tag

from modules.permits.scrapers.adapters.iworq import IworqAdapter


class DavenportAdapter(IworqAdapter):
    slug = "davenport"
    display_name = "Davenport"
    search_url = "https://portal.iworq.net/DAVENPORT/permits/600"

    # Davenport iWorQ table columns:
    #   TH: Permit #
    #   0: Date
    #   1: Primary Contractor
    #   2: Applicant Name
    #   3: Site Address
    #   4: Lot
    #   5: Description (permit type / scope)
    #   6: Project Cost
    #   7: Permit Status
    #   8: Request An Inspection
    #   9: View

    def _extract_row_fields(
        self, permit_cell: Tag, cells: list[Tag],
    ) -> dict[str, str | None] | None:
        if len(cells) < 8:
            return None
        return {
            "permit_number": permit_cell.get_text(" ", strip=True),
            "issue_date_str": cells[0].get_text(" ", strip=True),
            "permit_type": cells[5].get_text(" ", strip=True),
            "address": cells[3].get_text(" ", strip=True),
            "status": cells[7].get_text(" ", strip=True),
            "contractor_hint": cells[1].get_text(" ", strip=True),
            "valuation_hint": cells[6].get_text(" ", strip=True),
            "detail_url": permit_cell.get("data-route") or (permit_cell.find("a") or {}).get("href"),
        }
