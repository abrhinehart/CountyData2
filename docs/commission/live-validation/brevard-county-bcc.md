# brevard-county-bcc — Live Validation

- **Status:** PASS
- **Adapter:** legistar (public OData API)
- **Portal:** https://brevard.legistar.com · API: `https://webapi.legistar.com/v1/brevardfl/events`
- **Date window:** 2025-10-01 → 2026-04-14 (6 months)
- **Timestamp (UTC):** 2026-04-14T19:00Z
- **Validated via:** `scripts/cr_live_validate.py`

## Results

- **Listings returned:** 30 (filtered to body `Brevard County Board of County Commissioners`)
- **Agenda listings:** 21
- **Minutes listings:** 9
- **First 3 listings:**
  1. `Brevard County Board of County Commissioners Agenda - 2026-04-07` — 2026-04-07 — agenda (pdf)
  2. `Brevard County Board of County Commissioners Agenda - 2026-04-02` — 2026-04-02 — agenda (pdf)
  3. `Brevard County Board of County Commissioners Agenda - 2026-03-19` — 2026-03-19 — agenda (pdf)

## Download smoke

- **URL:** `https://brevardfl.legistar1.com/brevardfl/meetings/2026/4/1801_A_Brevard_County_Board_of_County_Commissioners_26-04-07_Agenda.pdf`
- **Size:** 135,829 bytes
- **Magic bytes:** `%PDF-1.7` (valid PDF)

## Warnings / notes

- Second Legistar tenant validated (after Polk). Same public OData pattern — `legistar_client=brevardfl` + `body_names` filter.
- PDFs served from sibling host `brevardfl.legistar1.com` with signed paths.
- No API key required. No DNS flakes observed on this run.
- Cadence looks healthy: 2+ meetings per month in window.
