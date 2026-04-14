# sumter-county-bcc — Live Validation

- **Status:** PASS (after category_id typo fix)
- **Adapter:** civicplus
- **Portal:** https://sumtercountyfl.gov/AgendaCenter
- **Date window:** 2025-10-01 → 2026-04-14 (6 months)
- **Timestamp (UTC):** 2026-04-14T19:00Z
- **Validated via:** `scripts/cr_live_validate.py`

## Results

- **Listings returned:** 7
- **Agenda listings:** 7
- **Minutes listings:** 0
- **First 3 listings:**
  1. `March 24, 2026 Regular Meeting Agenda` — 2026-03-24 — agenda (pdf)
  2. `March 10, 2026 Regular Meeting Agenda` — 2026-03-10 — agenda (pdf)
  3. `February 24, 2026 Regular Meeting Agenda` — 2026-02-24 — agenda (pdf)

## Download smoke

- **URL:** `https://sumtercountyfl.gov/AgendaCenter/ViewFile/Agenda/_03242026-1009`
- **Size:** 735,985 bytes
- **Magic bytes:** `%PDF-1.5` (valid PDF)

## Warnings / notes

- **Config fix applied:** YAML originally had `category_id: 5` with comment "Board of County Commissioners Regular Meeting". Inspection of the portal HTML (`aria-controls="category-panel-3"` bound to `<h2>Board of County Commissioners Regular Meeting</h2>`) showed category 5 is actually "Budget Workshop" and category 3 is "Regular Meeting". First scrape returned 0 listings; changed to `category_id: 3` and re-ran. No adapter edits required.
- Sumter mapping (for future reference):
  - 3 = BCC Regular Meeting
  - 5 = BCC Budget Workshop
  - 6 = BCC Budget Hearing
  - 4 = BCC Special Meeting
  - 2 = BCC Workshop
- First civicplus PASS on a county-level (not city) tenant in this validation batch.
- Large download (736 KB) suggests full consent-agenda packet — healthy signal.
