# okeechobee-county-bcc — Live Validation

- **Status:** PASS
- **Adapter:** granicus (iQM2)
- **Portal:** https://okeechobeecountyfl.iqm2.com/Citizens
- **Date window:** 2025-10-01 → 2026-04-14 (6 months)
- **Timestamp (UTC):** 2026-04-14T17:21Z
- **Validated via:** `scripts/cr_live_validate.py`

## Results

- **Listings returned:** 51 (mixed board types)
- **Agenda listings:** 35
- **Minutes listings:** 16
- **First 3 listings:**
  1. `Agri-Civic Center Advisory Committee - Regular Meeting` — 2025-10-02 — agenda (pdf)
  2. `Agri-Civic Center Advisory Committee - Regular Meeting` — 2025-10-02 — minutes (pdf)
  3. `Board of County Commissioners - Regular Session` — 2025-10-09 — agenda (pdf)

## Download smoke

- **URL:** `https://okeechobeecountyfl.iqm2.com/Citizens/FileOpen.aspx?Type=14&ID=3188&Inline=True`
- **Size:** 158,525 bytes
- **Magic bytes:** `%PDF-1.7` (valid PDF)

## Warnings / notes

- Listings span multiple boards (Agri-Civic, BCC, etc.); a `meeting_group` filter is not set in the YAML so all boards surface. Downstream filtering by `detection_patterns.header_keywords` will separate BCC agendas. No fix needed for activation-level smoke.
- No duplicate-page bug observed.
