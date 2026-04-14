# lake-wales-cc — Live Validation

- **Status:** PASS (after category_id drift fix)
- **Adapter:** civicplus
- **Portal:** https://www.lakewalesfl.gov/AgendaCenter
- **Date window:** 2025-10-01 → 2026-04-14 (6 months)
- **Timestamp (UTC):** 2026-04-14T19:00Z
- **Validated via:** `scripts/cr_live_validate.py`

## Results (post-fix)

- **Listings returned:** 13
- **Agenda listings:** 7
- **First 3 listings:**
  1. `City Commission Agenda for Tuesday March 17, 2026 at 6:00 p.m.` — 2026-03-17 — agenda (pdf)
  2. `Agenda for the City Commission meeting on Tuesday March 3, 2026 at 6:00 p.m.` — 2026-03-03 — agenda (pdf)
  3. `Agenda for the City Commission Meeting on Tuesday February 17, 2026 at 6:00 p.m.` — 2026-02-17 — agenda (pdf)

## Pre-fix state

- **Previous category_id:** `3` (portal panel = "Planning & Zoning Board")
- **Pre-fix scrape:** 7 listings, all titled "Planning & Zoning Board Meeting - ..." — wrong body for a City Commission config.

## Config fix applied

- Changed `category_id: 3` to `category_id: 4  # City Commission Regular Meeting (portal panel id 4; id 3 was Planning & Zoning Board)`.
- Portal inspection (`curl -sA "CommissionRadar/1.0" https://www.lakewalesfl.gov/AgendaCenter/`) produced these relevant mappings:
  - cat 3 = Planning & Zoning Board
  - cat 4 = City Commission Regular Meeting
  - cat 9 = City Commission Workshop Meeting
  - cat 10 = City Commission Special Meeting
  - cat 14 = City Commission Budget Workshop Meeting

## Warnings / notes

- Pre-fix scrape exclusively returned P&Z agendas, which would have been dropped downstream by `header_keywords: CITY COMMISSION`. Previous note in this file acknowledged the issue but proposed adding a new config rather than fixing the id.
- After fix, all first-page listings explicitly title "City Commission Agenda" — keyword match.
- Board-level naming matches the portal's human-readable titles (unlike Altamonte/Hialeah which publish as filenames).
