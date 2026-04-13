# UI Issues

Created: 2026-04-12. Items to address across the CountyData2 React frontend.

---

## Inventory Page

1. **Run Snapshot** needs county selector + show last successful snapshot date per county
2. Replace **"Recent Snapshots"** table with **"Most Recent Snapshot"** — show county name(s) + date, cap at 3 names then "X counties"

## Subdivisions Page

3. **Default county filter to Bay**
4. **Add "FL"** suffix to Florida counties in dropdowns
5. **Only show builder-active subdivisions** — subdivisions where builders own lots. Keep visible for 90-120 days after last builder lot transfer
6. **Subdivision Detail: Remove individual lot listing**, show builder totals instead. Lot size breakdown is a long-term stretch goal
7. **Subdivision Detail: Add map view** above data columns. Split layout 1:2 (subdivision info : map)
8. **Subdivision Detail: More detail** in the subdivision info component
9. **Subdivision Detail: Add back button**

## Transactions Page

10. **Detail panel needs review reasons + resolve actions** — currently shows "Review Flag: Yes" with no reason and no way to act. Should surface `review_reasons` from `parsed_data` and offer the same resolve actions the Review page has
11. **Bulk review actions** — checkbox selection + batch resolve
12. **Absorb current dashboard stats** as filter-context on this page. Remove duplicate stat cards from here; let Dashboard own platform-level summaries
13. **Filter-dependent context stats** — "312 unmatched in Bay" that reacts to active filters
14. **Review queue depth by reason** — breakdown of reason counts, reactive to current filters
15. **Recent activity indicators** — "47 new since last ETL", "12 resolved this week"
16. **Filter presets / saved views** — quick buttons for common review workflows ("Bay unmatched", "All flagged newest first")

## Review Queue Page

17. **"Pick subdivision" buttons in detail panel are broken** — not firing on click
18. **Column sorting** needed, at least by review reason
19. **Consider merging** Review Queue into Transactions page as a filter mode rather than a separate tab

## Permits Page

20. **"vs Last Month" metric** needs percentage and a normalized daily rate scaled to month length (on the 4th of the month, raw delta is meaningless — e.g. -90%)
21. **Increase top builders and top subdivisions** tables from 8 to 15 rows
22. **Clarify watchlist concept** — explain what it is in the UI or link to watchlist management

## Commission Page

23. **"Projects Tracked" KPI is meaningless** at 48,842 — filter to developments of meaningful size only
24. **Recent Actions → Recent Meetings** — group by meeting date, make meetings expandable to show individual actions
25. **Future meetings view** — meeting dates are set yearly in January, agendas released ~month before, can be revised
26. **Calendar view** — needed for meeting schedule; prominence TBD
27. **Entitlement progress visual** — 1 reading at Planning/Zoning board, 2 readings at City Commission, vote at 2nd CC reading
28. **Developer agreements are ancillary** — they are notes about a project (developer reimburse agreements with jurisdiction), not entitlement milestones. Track but don't surface as entitlement progress
29. **Filter project list** to developments of meaningful size only (currently showing 179K+ names)

## Dashboard

30. **Rebuild from scratch** as a cross-module command center. Current dashboard is Sales-only legacy
31. **Per-module health KPI row** — one card per module showing freshness and key count (last snapshot date + lots, this month's permits + scraper freshness, upcoming meetings + review count, new transactions since last ETL)
32. **Unified "action needed" section** — review queue items, unmatched permits, flagged commission actions, across all modules ordered by urgency
33. **Recent activity feed** — last N events across the platform ("Snapshot completed for Bay", "14 permits scraped", "ETL ran: 312 new")

## Pipeline Page

34. **UX refresh** — functions are correct but interaction design needs rework
35. **Add "last run" data points** per county and/or per module

## Global

36. **Consistent back navigation** across all detail pages — clicking browser back or re-clicking the tab you were on is not acceptable UX
