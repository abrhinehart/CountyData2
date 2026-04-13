# Snapshot Runner UI Improvements — Design Spec

## Purpose

Add visibility into snapshot runs: confirm before running, show progress during the run, display errors when they fail, show elapsed time, and display the queue of running/pending counties.

## Backend Changes

### New columns on `bi_snapshots` table

- `progress_current: int` (default 0) — number of builders processed so far
- `progress_total: int` (default 0) — total builders to process

### Update snapshot runner

In `snapshot_runner.py`, at the start of `run_snapshot()` after loading builder aliases, set `snapshot.progress_total = len(builder_ids)`. Inside the builder loop, after each builder is processed, increment `snapshot.progress_current` and commit.

### New endpoint: `GET /api/inventory/snapshots/active`

Returns all snapshots with `status = 'running'`, including progress fields. Used by the frontend to poll during runs.

Response: `list[SnapshotOut]` (SnapshotOut already has all the fields we need once we add progress_current/progress_total).

## Frontend Changes

### Confirm dialog

When user clicks "Run Selected" or "Run All", show a simple confirm: "Run snapshot for {county/all counties}?" with Cancel/Confirm buttons. Not a modal — inline in the Run Snapshot section.

### Active run display

When any snapshot is running:
- Poll `GET /api/inventory/snapshots/active` every 3 seconds
- For each running snapshot, show:
  - County name
  - Progress bar: `progress_current / progress_total` builders
  - Elapsed time since `started_at` (updating every second)
  - Status badge (running/completed/failed)

### Error display

When a snapshot completes with `status = 'failed'`:
- Show the `error_message` in a red alert box
- Keep it visible until dismissed or next run

### Completion

When a snapshot completes successfully:
- Invalidate inventory queries to refresh data
- Show brief success indicator with summary (new/removed/changed counts)

## Files

- Create: `migrations/018_snapshot_progress_columns.sql`
- Modify: `modules/inventory/models.py` — add progress columns to BiSnapshot
- Modify: `modules/inventory/services/snapshot_runner.py` — write progress after each builder
- Modify: `modules/inventory/routers/snapshots.py` — add active snapshots endpoint
- Modify: `modules/inventory/schemas/snapshot.py` — add progress fields to SnapshotOut
- Modify: `ui/src/pages/InventoryPage.tsx` — confirm dialog, polling, progress display, error display
