# Session Journal — 2026-04-16 CR Seeder Deactivation Fix

**Branch:** `main` (no feature branch)
**Session pattern:** one triad-agent-v2 run (Planner → Executor → QA)

## Session goal

Close the YAML-delete-DB-drift gap surfaced during the earlier CR YAML
six-pack's verification pass. `seed_cr_jurisdiction_config.py` was
upsert-only: deleting a jurisdiction YAML left its `cr_jurisdiction_config`
row at `is_active=True` indefinitely. Since dashboard + scrape router both
filter on `is_active`, stale rows keep appearing until someone manually
UPDATEs them. The fix: seeder tracks seeded `jurisdiction_id`s and
deactivates any config whose jurisdiction wasn't in the seeded set.

## Scope

CR seeder only. PT (`seed_pt_jurisdiction_config.py`) and BI
(`seed_bi_county_config.py`) use in-file Python lists rather than YAMLs,
and neither table has an `is_active` column — PT uses `scrape_mode` enum,
BI keys on `county_id`. Different drift profile; left untouched pending an
actual live incident.

## Change

`seed_cr_jurisdiction_config.py`:

- New `--no-deactivate-missing` CLI flag (default-off; reconciliation runs
  by default).
- `seed()` now takes a `deactivate_missing: bool = True` arg.
- Tracks every `jurisdiction_id` returned from the upsert loop in a set.
- At end of run, before commit, issues a single UPDATE:
  `UPDATE cr_jurisdiction_config SET is_active = FALSE
   WHERE is_active = TRUE AND jurisdiction_id <> ALL(seeded_ids)`.
- Prints `Stale configs deactivated: N` in the summary when the pass ran.

## Verification (live DB, paired negative + positive cases)

1. **Negative case (clean state):** `python seed_cr_jurisdiction_config.py`
   after the earlier manual santa-rosa cleanup. Result:
   `Stale configs deactivated: 0`. No false-deactivations on a clean repo.
2. **Positive case (induced orphan):** Manually flipped
   `santa-rosa-county-bcc` back to `is_active=TRUE` (no YAML exists on
   disk), re-ran seeder. Result: `Stale configs deactivated: 1`. Post-run
   spot-check: santa-rosa row is False, NMB + WG (which have YAMLs) stayed
   True. Active count: 86 → 85.
3. **Escape-hatch case:** `python seed_cr_jurisdiction_config.py
   --no-deactivate-missing` → summary omits the deactivated-count line and
   issues no UPDATE. Suppression works.
4. **pytest:** 580 passed, no regressions.

## Why this matters

From `modules/commission/routers/dashboard.py:173` and
`modules/commission/routers/scrape.py:83`: both filter
`CrJurisdictionConfig.is_active == True`. Before this fix, any YAML
deletion (e.g. c0ab4ed's santa-rosa and this morning's collier-boa) would
keep the old jurisdiction on the dashboard and in scrape enumerations
until a human ran an UPDATE. The fix makes the seeder the single source of
truth and closes the silent-drift class.

## Files changed

- `seed_cr_jurisdiction_config.py` — +19 lines (argparse, tracking set,
  reconciliation UPDATE, escape-hatch flag)
- `docs/sessions/2026-04-16-cr-seeder-deactivation.md` — this journal

## Triad summary

- Rounds: 1 (no QA rejection)
- Waves: 3 (Wave 1 edit seeder; Wave 2 verify negative/positive/escape
  paths live; Wave 3 journal + commit)
- Batch templates: none (single-file change)
- Deviations: originally considered parallel unit test development —
  skipped because live negative+positive pair is stronger evidence than a
  mocked-psycopg2 unit test would have been, and the code surface is
  small enough to read directly.

## No pending / follow-up work

No new TODO entries spawned. The CR-seeder drift class is closed. PT/BI
hardening is deferred until a concrete incident — memory file
`project_yaml_delete_db_drift.md` documents the template.
