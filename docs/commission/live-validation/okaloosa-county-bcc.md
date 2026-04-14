# okaloosa-county-bcc — Live Validation

- **Status:** PASS (after one transient retry)
- **Adapter:** granicus (iQM2)
- **Portal:** https://okaloosacountyfl.iqm2.com/Citizens
- **Date window:** 2025-10-01 → 2026-04-14 (6 months)
- **Timestamp (UTC):** 2026-04-14T17:22Z
- **Validated via:** `scripts/cr_live_validate.py`

## Results

- **Listings returned:** 16 (all agenda PDFs within window)
- **Agenda listings:** 16
- **First 3 listings:**
  1. `Board of County Commissioners - Regular Meeting (North)` — 2025-10-07 — agenda (pdf)
  2. `Board of County Commissioners - Regular Meeting (South)` — 2025-10-21 — agenda (pdf)
  3. `Tourist Development Council - Regular Meeting` — 2025-10-28 — agenda (pdf)

## Download smoke

- **URL:** `https://okaloosacountyfl.iqm2.com/Citizens/FileOpen.aspx?Type=14&ID=1835&Inline=True`
- **Size:** 215,556 bytes
- **Magic bytes:** `%PDF-1.7` (valid PDF)

## Warnings / notes

- **First download attempt hit a TLS connection reset** (`WinError 10054, ConnectionResetError` during SSL handshake). The retry (immediately after) succeeded. Classic intermittent behavior from iQM2 / Akamai edge — no scraper change warranted.
- Fetch-level was stable on the first try; only the single download request flaked.
- Listings span multiple boards (BCC North/South sessions, TDC, etc.); downstream `detection_patterns` will filter to BCC.
