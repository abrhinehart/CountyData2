# polk-county-bcc — Live Validation

- **Status:** PASS (after one transient DNS-failure retry)
- **Adapter:** legistar (public OData API)
- **Portal:** https://polkcountyfl.legistar.com · API: `https://webapi.legistar.com/v1/polkcountyfl/events`
- **Date window:** 2025-10-01 → 2026-04-14 (6 months)
- **Timestamp (UTC):** 2026-04-14T17:22Z
- **Validated via:** `scripts/cr_live_validate.py`

## Results

- **Listings returned:** 24 (filtered to body `Board of County Commissioners`)
- **Agenda listings:** 13
- **Minutes listings:** 11
- **First 3 listings:**
  1. `Board of County Commissioners Agenda - 2026-04-07` — 2026-04-07 — agenda (pdf)
  2. `Board of County Commissioners Agenda - 2026-03-17` — 2026-03-17 — agenda (pdf)
  3. `Board of County Commissioners Minutes - 2026-03-17` — 2026-03-17 — minutes (pdf)

## Download smoke

- **URL:** `https://polkcountyfl.legistar1.com/polkcountyfl/meetings/2026/4/1815_A_Board_of_County_Commissioners_26-04-07_Meeting_Agenda.pdf`
- **Size:** 134,571 bytes
- **Magic bytes:** `%PDF-1.7` (valid PDF)

## Warnings / notes

- **No Legistar API key required** — `webapi.legistar.com` is the public OData endpoint; the scraper uses only `legistar_client` slug + `body_names` from YAML.
- **First attempt failed with `getaddrinfo failed` on `webapi.legistar.com`** — local DNS hiccup, not an auth/rate issue. Retry immediately succeeded.
- Cross-references the existing Polk Legistar surface map at `docs/api-maps/polk-county-legistar.md`.
- PDFs served from a sibling host (`legistar1.com`) with signed paths — followed normally by `requests`.
