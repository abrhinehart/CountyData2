# pasco-county-bcc — Live Validation

- **Status:** PASS
- **Adapter:** civicclerk
- **Portal:** https://pascocofl.portal.civicclerk.com (tenant: `pascocofl`, category_id=26)
- **Date window:** 2025-10-01 → 2026-04-14 (6 months)
- **Timestamp (UTC):** 2026-04-14T19:00Z
- **Validated via:** `scripts/cr_live_validate.py`

## Results

- **Listings returned:** 15
- **Agenda listings:** 11
- **Minutes listings:** 4
- **First 3 listings:**
  1. `3-10-26 FINAL Agenda` — 2026-03-10 — agenda (pdf)
  2. `2-17-26 FINAL Agenda` — 2026-02-17 — agenda (pdf)
  3. `BCC AA 02-17-2026 REVISED` — 2026-02-17 — minutes (pdf)

## Download smoke

- **URL:** Azure Blob signed URL — `https://civicclerk.blob.core.windows.net/stream/pascocofl/45176558-…pdf?<SAS params>`
- **Size:** 269,741 bytes
- **Magic bytes:** `%PDF-1.7` (valid PDF)

## Warnings / notes

- Second civicclerk jurisdiction validated on the `pascocofl` tenant — confirms BCC lives on the same tenant as the already-validated Pasco PZ (category_id=26 for BCC vs different id for PZ).
- Downloads are Azure Blob SAS-signed URLs with 7-day expiry. Scraper pulls them fresh each request — no caching.
- 11 agendas in 6 months matches expected BCC cadence (~2/month).
- Title strings are mixed: `"3-10-26 FINAL Agenda"`, `"BCC AA 02-17-2026 REVISED"` — downstream normalization will handle date parsing from filenames.
