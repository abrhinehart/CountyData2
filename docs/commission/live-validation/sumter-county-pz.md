# sumter-county-pz — Live Validation

- **Status:** PASS (after category_id drift fix)
- **Adapter:** civicplus
- **Portal:** https://sumtercountyfl.gov/AgendaCenter
- **Date window:** 2025-10-01 → 2026-04-14 (6 months)
- **Timestamp (UTC):** 2026-04-14T19:00Z
- **Validated via:** `scripts/cr_live_validate.py`

## Results (post-fix)

- **Listings returned:** 5
- **Agenda listings:** 5
- **First 3 listings:**
  1. `March 16, 2026 Planning and Zoning Special Master Meeting Agenda` — agenda (pdf)
  2. `March 2, 2026 Planning and Zoning Special Master Meeting Agenda` — agenda (pdf)
  3. `February 16, 2026 Planning and Zoning Special Master Meeting Agenda` — agenda (pdf)

## Pre-fix state

- **Previous category_id:** `2` (portal panel = "Board of County Commissioners Workshop")
- **Pre-fix scrape:** 4 listings titled "... Workshop Agenda" — all BCC Workshop, not P&Z.
- YAML carried a `# TODO: verify category ID` comment signalling the original authoring was uncertain.

## Config fix applied

- Changed `category_id: 2  # TODO: verify category ID from AgendaCenter page` to `category_id: 20  # Planning and Zoning Special Master (PZSM) (portal panel id 20; id 2 was BCC Workshop)`.
- Portal inspection (`curl -sA "CommissionRadar/1.0" https://sumtercountyfl.gov/AgendaCenter/`) produced:
  - cat 2 = Board of County Commissioners Workshop
  - cat 3 = Board of County Commissioners Regular Meeting (already used by sumter-county-bcc)
  - cat 4 = BCC Special Meeting
  - cat 5 = BCC Budget Workshop
  - cat 6 = BCC Budget Hearing
  - cat 20 = Planning and Zoning Special Master (PZSM)
  - cat 21 = Code Enforcement Hearings
  - cat 22 = Affordable Housing Advisory Committee

## Warnings / notes

- Sumter County does NOT run a traditional Planning & Zoning Board. The Planning and Zoning Special Master (PZSM) is the closest body in their portal — an administrative hearing officer that issues P&Z decisions. This is the correct target for a `commission_type: planning_board` scope.
- If downstream filtering expects "Planning Board" or "P&Z Board" verbiage in titles, note that titles here are "Planning and Zoning Special Master" — may need `header_keywords` tuning in a follow-up.
- Pre-fix scrape pulled BCC Workshop agendas which would double-count with sumter-county-bcc's BCC data.
