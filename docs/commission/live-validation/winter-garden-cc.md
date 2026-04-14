# winter-garden-cc — Live Validation

- **Status:** PASS (with stale-window caveat) after category_id drift fix
- **Adapter:** civicplus
- **Portal:** https://www.cwgdn.com/AgendaCenter
- **Date window (in-window):** 2025-10-01 → 2026-04-14 (6 months) — 0 listings
- **Date window (extended):** 2024-01-01 → 2026-04-14 — 59 listings
- **Timestamp (UTC):** 2026-04-14T19:00Z
- **Validated via:** `scripts/cr_live_validate.py`

## Results (post-fix, extended window)

- **Listings returned:** 59
- **Agenda listings:** several dozen
- **First 3 listings:**
  1. `Agenda_06272024-1079.pdf` — 2024-06-27 — agenda (pdf)
  2. `Agenda_06132024-1073.pdf` — 2024-06-13 — agenda (pdf)
  3. `Agenda_05232024-1066.pdf` — 2024-05-23 — agenda (pdf)

## Download smoke

- **URL:** `https://www.cwgdn.com/AgendaCenter/ViewFile/Agenda/_06272024-1079`
- **Size:** ~91 MB
- **Magic bytes:** `%PDF-1.7` (valid PDF)
- **Content check:** PDF page 1 header reads `CITY COMMISSION AND COMMUNITY REDEVELOPMENT AGENCY AGENDA ... REGULAR MEETING June 27, 2024` — board match confirmed.

## Pre-fix state

- **Previous category_id:** `2` (portal panel = "Architectural Review & Historic Preservation Board")
- **Pre-fix scrape:** 0 listings in the 6-month window (the architectural board is low-volume).
- Titles are filename-format (`Agenda_MMDDYYYY-NNNN.pdf`), so title-level board-match detection is impossible; verification required opening the PDF.

## Config fix applied

- Changed `category_id: 2` to `category_id: 6  # City Commission (portal panel id 6; id 2 was Architectural Review & Historic Preservation Board)`.
- Portal inspection (`curl -sA "CommissionRadar/1.0" https://www.cwgdn.com/AgendaCenter/`) produced:
  - cat 2 = Architectural Review & Historic Preservation Board
  - cat 6 = City Commission
  - cat 7 = General Employees Pension Board
  - cat 8 = Planning & Zoning Board

## Warnings / notes

- **Stale portal:** no City Commission agendas uploaded after March 2025 at this tenant. Widened window confirms the fix is correct; in-window 0-listing is a portal publishing cadence issue, not a config issue.
- Recommend a follow-up: check whether Winter Garden has migrated their CC agendas to a different system (granicus / iQM2) for 2025+ meetings, or if the tenant is still operational.
- Filename-titles mean downstream `header_keywords: CITY COMMISSION` matching must rely on PDF body text, not listing title.
