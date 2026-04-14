# lake-wales-cc — Live Validation

- **Status:** PASS
- **Adapter:** civicplus
- **Portal:** https://www.lakewalesfl.gov/AgendaCenter
- **Date window:** 2025-10-01 → 2026-04-14 (6 months)
- **Timestamp (UTC):** 2026-04-14T19:00Z
- **Validated via:** `scripts/cr_live_validate.py`

## Results

- **Listings returned:** 7
- **Agenda listings:** 4
- **Minutes listings:** 3
- **First 3 listings (most-recent first):**
  1. `Planning & Zoning Board Meeting - March 24, 2026` — 2026-03-24 — agenda (pdf)
  2. `Planning & Zoning Board Meeting - February 24, 2026` — 2026-02-24 — agenda (pdf)
  3. `Planning & Zoning Board Meeting - January 27, 2026` — 2026-01-27 — agenda (pdf)

## Download smoke

- **URL:** `https://www.lakewalesfl.gov/AgendaCenter/ViewFile/Agenda/_03242026-1679`
- **Size:** 56,187 bytes
- **Magic bytes:** `%PDF-1.5` (valid PDF)

## Warnings / notes

- CivicPlus `category_id=3` returns Planning & Zoning Board meetings, not strictly City Commission. Downstream `detection_patterns.header_keywords = CITY COMMISSION` will filter these out. Smoke is still PASS at activation level (fetch + download work); a separate pass may want to add a City Commission category_id.
- Titles are human-readable on this tenant (unlike Hialeah / Altamonte which return filenames) — depends on how the city tags uploads.
- Small-city breadth confirmed: civicplus parser handles low-volume portals cleanly.
