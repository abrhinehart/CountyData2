# Session Journal — 2026-04-14 CR YAML category_id Audit
**Branch:** claude/cr-yaml-audit
**Baseline:** pytest 457 passed + 23 subtests (measured this session)
**Scope:** FL civicplus + civicclerk configs with `category_id` (34 total: 15 civicplus, 19 civicclerk)
**Date window:** 2025-10-01 - 2026-04-14 (6 months)

## Per-config audit table

Columns:
- **Starting cat_id** — what was in the YAML at the start of this session (pre-fix value shown for drifts that were fixed).
- **Live status** — classifier verdict on the in-window scrape. `DRIFT -> OK` means the pre-fix scrape was a drift, the post-fix scrape is OK.
- **First-3 title sample** — from the in-window run; for the 3 drift fixes the pre-fix titles are shown (they triggered classification).
- **Action / New cat_id** — `drift fix` means a category_id change was applied; `defer` means the drift/empty requires work outside this audit's scope; `no-op` means category_id is correct but 0 listings is a different root cause.

| Slug | Platform | Starting cat_id | Live status | First-3 title sample | Action | New cat_id |
|---|---|---|---|---|---|---|
| altamonte-springs-cc | civicplus | 1 | PASS | Agenda_03172026-341.pdf / Agenda_03032026-340.pdf / Agenda_02172026-339.pdf | no change | (unchanged) |
| citrus-county-bcc | civicclerk | 26 | PASS | Board of County Commissioners / Aviation Advisory Board / Beverly Hills Advisory Council | no change | (unchanged) |
| citrus-county-boa | civicclerk | 28 | PASS | Value Adjustment Board - Regular Meeting / Value Adjustment Board - Regular Meeting / Value Adjustment Board - Special Magistrate | no change | (unchanged) |
| citrus-county-pz | civicclerk | 33 | EMPTY | (none) | no-op - cat 33 correct; P&D Council inactive since 2024-12 | (unchanged) |
| collier-county-bcc | civicclerk | 26 | PASS | Agenda Index / Agenda Packet / Agenda Index | no change | (unchanged) |
| collier-county-boa | civicclerk | 32 | DRIFT | 3-26-2026 HEX INDEX / 3-13-26 HEX INDEX / 2-26-2026 HEX INDEX | defer - no Board of Adjustment in Collier civicclerk portal | (unchanged) |
| collier-county-ccpc | civicclerk | 28 | PASS | April 2, 2026 CCPC Agenda 5:05 PM / April 2, 2026 CCPC Agenda 1 pm / March 19, 2026, CCPC Agenda | no change | (unchanged) |
| collier-county-hex | civicclerk | 32 | PASS | 3-26-2026 HEX INDEX / 3-13-26 HEX INDEX / 2-26-2026 HEX INDEX | no change | (unchanged) |
| escambia-county-bcc | civicclerk | 26 | PASS | 20260401 Revised Summary Agenda (2) / 20260401 Gary Sansing Public Forum Agenda / 20260326 Revised Summary Agenda | no change | (unchanged) |
| escambia-county-pz | civicclerk | 32 | PASS | Planning Board Rezoning Meeting April 7, 2026 / Planning Board Regular Meeting April 7, 2026 / Planning Board Rezoning Meeting March 3, 2026 | no change | (unchanged) |
| fort-myers-cc | civicplus | 1 | PASS | Agenda_03172026-2198.pdf / Agenda_02102026-2181.pdf / Agenda_01132026-2150.pdf | no change | (unchanged) |
| hialeah-cc | civicplus | 2 | PASS | Agenda_03172026-1331.pdf / Agenda_02172026-1321.pdf / Agenda_01272026-1315.pdf | no change | (unchanged) |
| highlands-county-bcc | civicclerk | 26 | PASS | Agenda 040726 / 031726Reg Agenda / Board Agenda 030327 | no change | (unchanged) |
| highlands-county-pz | civicclerk | 27 | PASS | 04.14.2026 P&Z Agenda / 04.14.2026 BOA Agenda / 03.10.2026 P&Z Agenda | no change | (unchanged) |
| jackson-county-bcc | civicclerk | 27 | PASS | April 14, 2026 Agenda / March 24, 2026 Agenda / March 10, 2026 Agenda | no change | (unchanged) |
| lake-alfred-cc | civicplus | 2 | PASS | City Commission Regular Meeting Materials / City Commission Regular Meeting Materials / City Commission Regular Meeting Materials | no change | (unchanged) |
| lake-county-bcc | civicclerk | 27 | PASS | Agenda 4.14.26 / Agenda 4.7.26 / Historical Museum Funding Workshop Agenda 3.26.26 | no change | (unchanged) |
| lake-county-pz | civicclerk | 31 | EMPTY | (none) | no-op - cat 31 correct; adapter returns 0 despite API events (scraper bug, out of scope) | (unchanged) |
| lake-wales-cc | civicplus | 3 | DRIFT -> OK | Planning & Zoning Board Meeting - March 24, 2026 / Planning & Zoning Board Meeting - February 24, 2026 / Planning & Zoning Board Meeting - January 27, 2026 | drift fix | 4 |
| lee-county-bcc | civicclerk | 26 | PASS | 04/07/2026 Lee Board of County Commissioners Regular Meeting / 03/17/2026 Lee Board of County Commissioners Regular Meeting / 03/17/2026 Lee Board of County Commissioners Regular Meeting | no change | (unchanged) |
| niceville-cc | civicplus | 2 | PASS | Agenda_03022026-430.pdf / Agenda_01052026-423.pdf / Minutes_03022026-430.pdf | no change | (unchanged) |
| north-miami-beach-cc | civicplus | 3 | DRIFT | Planning and Zoning Board Meeting / Planning and Zoning Board Meeting / Planning and Zoning Board Meeting | defer - no City Commission in NMB AgendaCenter | (unchanged) |
| panama-city-cc | civicplus | 1 | PASS | City Commission Meeting of March 24, 2026. / City Commission Meeting of March 10, 2026. / City Commission Meeting of February 24, 2026. | no change | (unchanged) |
| panama-city-planning-board | civicplus | 3 | PASS | March 9, 2026 Planning Board Meeting Agenda / February 9, 2026 Planning Board Meeting Agenda / April 13, 2026 Planning Board Meeting Agenda | no change | (unchanged) |
| pasco-county-bcc | civicclerk | 26 | PASS | 3-10-26 FINAL Agenda / 2-17-26 FINAL Agenda / BCC AA 02-17-2026 REVISED | no change | (unchanged) |
| pasco-county-pz | civicclerk | 27 | PASS | 4/9/26 PC Workshop Agenda / 4/9/26 PC Agenda / 3/19/26 PC Addendum Agenda | no change | (unchanged) |
| pembroke-pines-cc | civicplus | 2 | EMPTY | (none) | defer - no City Commission in Pembroke Pines AgendaCenter (cat 2 = "Test Category") | (unchanged) |
| santa-rosa-county-bcc | civicplus | 1 | EMPTY | (none) | defer - base_url DNS fails (YAML: santarosafl.gov; real: santarosa.fl.gov) | (unchanged) |
| santa-rosa-county-zb | civicplus | 2 | EMPTY | (none) | defer - same base_url DNS issue as santa-rosa-county-bcc | (unchanged) |
| st-lucie-county-bcc | civicclerk | 26 | PASS | Second Revised Final Agenda on 4/14 / 2nd Revised Final Agenda on 4/7 / Revised Final Agenda on 3/17 | no change | (unchanged) |
| st-lucie-county-pz | civicclerk | 32 | PASS | agenda / agenda / agenda | no change | (unchanged) |
| sumter-county-bcc | civicplus | 3 | PASS | March 24, 2026 Regular Meeting Agenda / March 10, 2026 Regular Meeting Agenda / February 24, 2026 Regular Meeting Agenda | no change | (unchanged) |
| sumter-county-pz | civicplus | 2 | DRIFT -> OK | March 17, 2026 Workshop Agenda / February 17, 2026 Workshop Agenda / January 20, 2026 Workshop Meeting Agenda | drift fix | 20 |
| winter-garden-cc | civicplus | 2 | DRIFT -> OK | (0 listings in-window; cat 2 = Architectural Review — confirmed wrong via portal recon) | drift fix | 6 |

## Drifts fixed

### 1. lake-wales-cc: `category_id: 3` -> `category_id: 4`
- Portal cat 3 = Planning & Zoning Board; cat 4 = City Commission Regular Meeting.
- Pre-fix scrape: 7 listings titled "Planning & Zoning Board Meeting - ...".
- Post-fix scrape (`tmp/cr_audit/lake-wales-cc.post.json`): 13 listings, first-3 titled "City Commission Agenda for ...".
- Recon note: `docs/commission/live-validation/lake-wales-cc.md` (updated).

### 2. sumter-county-pz: `category_id: 2` -> `category_id: 20`
- Portal cat 2 = BCC Workshop; cat 20 = Planning and Zoning Special Master (PZSM).
- Sumter has no traditional Planning & Zoning Board — PZSM is their equivalent administrative body.
- Pre-fix YAML carried a `# TODO: verify category ID` comment — now resolved and stripped.
- Pre-fix scrape: 4 listings titled "... Workshop Agenda" (BCC Workshop).
- Post-fix scrape (`tmp/cr_audit/sumter-county-pz.post.json`): 5 listings, all "... Planning and Zoning Special Master Meeting Agenda".
- Recon note: `docs/commission/live-validation/sumter-county-pz.md` (new).

### 3. winter-garden-cc: `category_id: 2` -> `category_id: 6`
- Portal cat 2 = Architectural Review & Historic Preservation Board; cat 6 = City Commission.
- Pre-fix scrape: 0 listings in-window (ARB is low-volume).
- Post-fix in-window scrape: 0 listings (portal hasn't published CC agendas since March 2025 — see Follow-ups).
- Post-fix extended-window scrape (2024-01-01 .. 2026-04-14, `tmp/cr_audit/winter-garden-cc.post.json`): 59 listings, first PDF body reads "CITY COMMISSION AND COMMUNITY REDEVELOPMENT AGENCY AGENDA" — board match confirmed.
- Recon note: `docs/commission/live-validation/winter-garden-cc.md` (new).

## Follow-ups

### Out-of-scope fixes (require a separate session)

1. **santa-rosa-county-bcc & santa-rosa-county-zb** — base_url points to `www.santarosafl.gov` which has no DNS record. The correct domain is `www.santarosa.fl.gov` (verified via live HTTP 200 on AgendaCenter endpoint). Fixing this is a base_url change, not a category_id change. Both configs produce 0 listings because the scraper can't even connect. Category IDs may also need re-checking once the domain is fixed.

2. **collier-county-boa** — Collier's civicclerk portal lists these event categories: General, Board of County Commissioners, Tourist Development Council, Planning Commission, Metropolitan Planning Organization, Code Enforcement Board, Special Magistrate, Hearing Examiner, Contractors Licensing Board, Parks and Recreation Advisory Board, Advisory Boards, Infrastructure Surtax Citizen Oversight Committee. There is **no dedicated "Board of Adjustment"**. Current cat 32 returns Hearing Examiner meetings. Options: (a) point to Code Enforcement Board (cat 30) or Special Magistrate (cat 31); (b) remove the config if Collier has no BOA body; (c) research whether Collier's BOA is hosted on a different system. No fix applied — need product decision.

3. **north-miami-beach-cc** — NMB's AgendaCenter hosts only these bodies: Code Compliance Enforcement Board, Code Compliance Special Magistrate, Community Redevelopment Agency, General Employees Retirement Committee, Planning & Zoning Board, Public Utilities Commission, Retirement Boards (2), TRAD. **No City Commission category.** NMB City Commission agendas are likely on a different platform (the city's primary website or a separate granicus/legistar tenant). Cat 3 (current) returns P&Z — confirmed drift, but no corrective category exists here. Need to identify the correct portal.

4. **pembroke-pines-cc** — Pembroke Pines' AgendaCenter lists advisory/special boards only (Test Category, Youth Advisory, Affordable Housing, Arts & Culture, Board of Adjustment, Charter School boards, P&Z, etc.). **No City Commission category.** Current cat 2 ("Test Category") returns 0. Same situation as NMB — CC is likely elsewhere.

5. **winter-garden-cc portal migration** — category_id fixed to 6 (City Commission, verified by PDF inspection), but no new CC agendas have been uploaded since March 2025. Worth confirming whether Winter Garden has migrated to granicus/iQM2 or similar; if so, this config needs a new base_url + platform.

### No-op (flagged in scan, no config change needed)

6. **citrus-county-pz** — category_id 33 ("Planning and Development Council") is correct. The body's last agenda in the Citrus portal dates to 2024-12. Extended-window scrape (2024-01-01..) confirms the cat is live but infrequent. Not a drift.

7. **lake-county-pz** — category_id 31 ("Planning and Zoning Board") is correct per civicclerk EventCategories. The Events endpoint directly queried with `categoryId eq 31 and startDateTime ge 2025-10-01...` returns multiple published events (e.g. "April 1, 2026 - Planning and Zoning Board", "December 2, 2026 - Planning and Zoning Board") but the scraper adapter returns 0 listings. Likely a bug in the scraper's date-filter/visibility-filter logic. Out of scope for a category_id audit; needs an adapter-layer follow-up.

## Classifier bug discovered & fixed mid-session

The classifier harness `tmp/cr_audit_driver.py` was reading `cfg["jurisdiction"]` and `cfg["scraping"]["detection_patterns"]` — but the real YAML schema has `name`/`commission_type` at the top level and `detection_patterns` at the top level (not under `scraping`). This meant all initial classifications resolved `header_keywords = []` and every PASS bucket fell into OK regardless of actual title content. Fixed the reader and added a commission-type-family-based contradiction detector (with word-boundary matching for short acronyms like "bcc"/"boa" to avoid false positives against the word "Board"). Re-ran; lake-wales-cc, north-miami-beach-cc, sumter-county-pz, collier-county-boa surfaced as DRIFT — all confirmed via portal recon.
