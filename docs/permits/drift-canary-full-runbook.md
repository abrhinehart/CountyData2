# Drift Canary (Full Sweep) Runbook

Companion to `docs/permits/drift-canary-runbook.md` (which documents the
Polk-pinned monthly canary, ACCELA-14).  This runbook covers the
full-sweep canary at `scripts/drift_canary_full.py` — the broader
cross-jurisdiction drift monitor.

## What it does

`scripts/drift_canary_full.py` walks every active CR YAML under
`modules/commission/config/jurisdictions/FL/` (excluding
`_florida-defaults.yaml`, `*-boa.yaml`, `*-zba.yaml`) and every PT
adapter row in `seed_pt_jurisdiction_config.JURISDICTIONS` with
`scrape_mode="live"`, invoking each and recording per-jurisdiction
status in a uniform dated report.

Modes:

- `--dry-run` (default) — no network; enumerates configs, loads YAML,
  runs `PlatformScraper.for_platform(...)` for CR and
  `adapter_class()` for PT.  Reports `DRY-RUN` with
  `factory=OK / constructor=OK`.  Module-level offline guard installs
  `requests.get` / `requests.post` stubs that raise
  `RuntimeError("offline mode")` so any accidental network call fails
  loudly.  Safe to run under pytest.
- `--live` — imports `scripts.cr_live_validate.validate` for CR
  (30-day trailing window) and calls `fetch_permits(start, end)` per
  PT adapter (7-day trailing window).  Per-call try/except: a single
  jurisdiction failure does not abort the sweep.

Output lands in `docs/sessions/drift-canary-YYYY-MM-DD.md` with the
same sections every day (Summary, Commission Radar table, Permit
Tracker table, Regressions if any).

## Manual invocation

```sh
# Fast smoke (offline, capped at 5 per bucket). Always pass --report-dir
# to a scratch path so the committed dated report is not overwritten:
.venv/Scripts/python.exe scripts/drift_canary_full.py --dry-run --limit 5 --report-dir tmp/

# Full dry-run sweep (offline):
.venv/Scripts/python.exe scripts/drift_canary_full.py --dry-run --quiet

# Live run, CR only:
.venv/Scripts/python.exe scripts/drift_canary_full.py --live --cr-only

# Live run, append regressions to TODO.md:
.venv/Scripts/python.exe scripts/drift_canary_full.py --live --append-regressions
```

## Exit codes

- `0` — PASS, PARTIAL, or DRY-RUN.  Report written, no escalation.
- `2` — FAIL (at least one jurisdiction raised an exception).
  Investigate before the next scheduled fire.

## Scheduling — Windows Task Scheduler

The full canary is intentionally NOT auto-registered by this runbook.
Register manually when the user is ready to put it on a cadence.  The
Polk-pinned monthly canary (`scripts/drift_canary.py`) remains the
primary guardrail — the full sweep is a broader tripwire and is
appropriately scheduled weekly.

Example weekly registration (Sunday 08:00 local):

```cmd
schtasks /Create /SC WEEKLY /D SUN /ST 08:00 /TN "CountyData2-DriftCanaryFull" /TR "C:\Users\abrhi\Code\CountyData2\.venv\Scripts\python.exe C:\Users\abrhi\Code\CountyData2\scripts\drift_canary_full.py --live --append-regressions --quiet"
```

Verify:

```cmd
schtasks /Query /TN "CountyData2-DriftCanaryFull" /V /FO LIST
```

Run on demand:

```cmd
schtasks /Run /TN "CountyData2-DriftCanaryFull"
```

Deregister:

```cmd
schtasks /Delete /TN "CountyData2-DriftCanaryFull" /F
```

## Report location

Every run (dry or live) writes `docs/sessions/drift-canary-YYYY-MM-DD.md`.
A same-day second run overwrites the prior file — intentional, since
the latest snapshot is always the canonical one.  `scripts/status.py`
surfaces the most-recent report's date + status in `STATUS.md`.

## Relation to the Polk canary

`scripts/drift_canary.py` (ACCELA-14) is narrow and deep: it pins one
permit and asserts specific fields are non-null, guaranteeing Polk
Accela extraction has not regressed.  `scripts/drift_canary_full.py`
is wide and shallow: it touches every active jurisdiction to catch
structural breakage (portal 500s, adapter-class import errors, empty
listing returns).  Both are expected to coexist.
