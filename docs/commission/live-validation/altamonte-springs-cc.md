# altamonte-springs-cc — Live Validation

- **Status:** PASS
- **Adapter:** civicplus
- **Portal:** https://fl-altamontesprings.civicplus.com/agendacenter
- **Date window:** 2025-10-01 → 2026-04-14 (6 months)
- **Timestamp (UTC):** 2026-04-14T17:21Z
- **Validated via:** `scripts/cr_live_validate.py`

## Results

- **Listings returned:** 12
- **Agenda listings:** 7
- **Minutes listings:** 5
- **First 3 listings (most-recent first):**
  1. `Agenda_03172026-341.pdf` — 2026-03-17 — agenda (pdf)
  2. `Agenda_03032026-340.pdf` — 2026-03-03 — agenda (pdf)
  3. `Agenda_02172026-339.pdf` — 2026-02-17 — agenda (pdf)

## Download smoke

- **URL:** `https://fl-altamontesprings.civicplus.com/AgendaCenter/ViewFile/Agenda/_03172026-341`
- **Size:** 183,648 bytes
- **Magic bytes:** `%PDF-1.6` (valid PDF)

## Warnings / notes

- CivicPlus category_id=1 picks up only the City Commission category — good.
- Titles come back as filenames because CivicPlus doesn't expose a human title in the search-result row; acceptable for fetch-level validation.
- No duplicate-page bug observed.
