# hialeah-cc — Live Validation

- **Status:** PASS
- **Adapter:** civicplus
- **Portal:** https://www.hialeahfl.gov/AgendaCenter
- **Date window:** 2025-10-01 → 2026-04-14 (6 months)
- **Timestamp (UTC):** 2026-04-14T19:00Z
- **Validated via:** `scripts/cr_live_validate.py`

## Results

- **Listings returned:** 5
- **Agenda listings:** 3
- **Minutes listings:** 2
- **First 3 listings (most-recent first):**
  1. `Agenda_03172026-1331.pdf` — 2026-03-17 — agenda (pdf)
  2. `Agenda_02172026-1321.pdf` — 2026-02-17 — agenda (pdf)
  3. `Agenda_01272026-1315.pdf` — 2026-01-27 — agenda (pdf)

## Download smoke

- **URL:** `https://www.hialeahfl.gov/AgendaCenter/ViewFile/Agenda/_03172026-1331`
- **Size:** 71,295 bytes
- **Magic bytes:** `%PDF-1.7` (valid PDF)

## Warnings / notes

- CivicPlus `category_id=2` maps to the City Council track — filtering is clean.
- Titles come back as filenames (standard CivicPlus behavior — no human title in search-result row).
- Cadence is sparse: only 3 agendas in a 6-month window for a large city. Not a scraper issue — verified via portal; matches what the portal actually publishes.
- Large-city / high-traffic domain served without rate-limit or anti-bot interference.
