# Handoff: UI Upgrade Implementation

Created: 2026-04-12.

## Context

The CountyData2 platform was reviewed end-to-end on 2026-04-12. Three new module pages (Inventory, Permits, Commission) were added to the React frontend during that session — they are functional but rough. A full review of every tab produced two punch lists: `docs/ui-issues.md` (36 UI items) and `docs/backend-issues.md` (5 backend items).

## What was done in the prior session

- Added TypeScript types, API functions, and pages for Builder Inventory, Permit Tracker, and Commission Radar (`ui/src/pages/InventoryPage.tsx`, `PermitsPage.tsx`, `CommissionPage.tsx`)
- Updated nav (`Layout.tsx`), routes (`App.tsx`), types (`types.ts`), and API layer (`api.ts`)
- Added `start.bat` in the repo root to launch both servers
- TypeScript, Vite build, and ESLint all pass clean
- None of the review feedback has been implemented yet — the punch lists are the backlog

## What needs to happen now

Implement the items in `docs/ui-issues.md` and `docs/backend-issues.md`. Read both files first.

### Suggested approach

1. **Start with backend issues** — they affect what the UI can show. Builder table cleanup (#1) and subdivision filtering (#2) change what data the frontend receives. BOA deactivation (#4) and developer agreement typing (#5) are quick DB/config changes. Do these first so the UI work builds on clean data.

2. **Then UI by page**, roughly in dependency order:
   - **Dashboard rebuild** (#30-33) — this is the landing page, sets the tone
   - **Transactions + Review Queue merge** (#10-19) — the core workflow, biggest UX improvement
   - **Subdivisions** (#3-9) — filtering, detail page redesign with map
   - **Commission** (#23-29) — meetings view, calendar, progress visual
   - **Permits** (#20-22) — smaller fixes
   - **Inventory** (#1-2) — already partially implemented, finish it
   - **Pipeline** (#34-35) — lowest priority, cosmetic
   - **Global back navigation** (#36) — do last, touches every detail page

3. Use the **triad pattern** (Planner → Executor → QA) for the Dashboard rebuild and the Transactions/Review merge — those are the two highest-complexity items. The rest can be done directly.

### Key data points from the review

- 18,109 transactions across 10 counties, 79 MB — scaling to hundreds of counties is fine
- 48,842 subdivisions, only 474 with builder activity — 99% noise in the UI
- 1,430 "builders" in the table, vast majority are permit contractors auto-inserted by `_ensure_builder_id()`
- 26 BOA jurisdiction configs to deactivate
- Sales ETL captures all transaction types (87% House Sales) — keep capturing all, filter in the UI
- All API endpoints for all modules already exist and are validated

### Files to know

- `docs/ui-issues.md` — the 36-item UI punch list
- `docs/backend-issues.md` — the 5-item backend punch list
- `ui/src/` — all frontend code
- `modules/permits/services.py:1482` — the `_ensure_builder_id()` false-positive source
- `modules/commission/routers/` — commission API (dashboard, roster, scrape, review, process)
- `modules/inventory/routers/` — inventory API (builders, counties, inventory, parcels, snapshots, schedule)
