# Backend Issues

Created: 2026-04-12. Data quality and architectural items discovered during UI review.

---

## Builder Table Pollution

1. **PT `_ensure_builder_id()` auto-inserts false-positive builders** — `modules/permits/services.py:1482`. Every unique raw contractor name from permit scrapes (electricians, plumbers, security companies, gate installers — often with full street addresses) gets inserted as `type='builder', scope='national'` when no fuzzy match is found. Currently 1,430+ active "builders", vast majority are noise. The curated builders from `seed_reference_data.py` are diluted. Needs a cleanup pass and a strategy to prevent re-pollution (separate contractor table, or a confidence/source column, or stop auto-inserting).

## Subdivision Table Bloat

2. **48,842 subdivision rows, only 474 with builder activity.** The shared `subdivisions` table contains every subdivision name ever encountered across all four modules. For UI purposes only ~1% matter (those with active builder lots or recent builder transactions). Needs either a cleanup of dead rows or an `is_relevant` flag for UI filtering. The 90-120 day grace period after last builder lot transfer should be considered.

3. **Subdivisions table (225 MB) scales faster than transactions (79 MB).** At 10 counties the subdivisions table is already 3x the size of transactions. At 500+ counties this will be the dominant table. Not an urgent problem (PostgreSQL handles it fine) but worth monitoring and potentially partitioning or archiving inactive rows.

## Commission Radar Data Quality

4. **Deactivate BOA (Board of Adjustment) jurisdiction configs.** 26 of 98 CR jurisdiction configs are `commission_type='board_of_adjustment'`. These should be deactivated (retain data, stop processing) until their value is proven. Can be reactivated later.

5. **Developer agreements should be typed as ancillary.** Currently `approval_type='developer_agreement'` is treated the same as entitlement actions (zoning, land_use, etc.) in the actions table and UI. Developer agreements are separate reimbursement agreements between a developer and jurisdiction — they should be tracked as notes on a project, not as entitlement milestones in the progress visualization.
