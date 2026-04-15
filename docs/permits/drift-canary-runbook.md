# Drift Canary Runbook (ACCELA-14)

Monthly fixture-drift guardrail for the Polk Accela adapter, plus full
api-map drift audit.  Closes ACCELA-14 from the Polk improvement report.

## What it does

`scripts/drift_canary.py` runs three checks:

1. `audit_api_maps.py --fail-on-drift` (every documented map matches code).
2. Live Polk Accela fetch over a 30-day window — anchors on the validated
   `BR-2026-2894` (LGI HOMES FLORIDA LLC, 7118 CANOPY LN LAKELAND), falls
   back to the most-recent permit with `raw_owner_name` non-null when the
   pinned permit ages out of the window.
3. NotNull asserts on `raw_owner_name`, `raw_applicant_company`,
   `raw_contractor_license_number`, `parcel_id`, `valuation`.

On pass the script writes `docs/sessions/drift-canary-<YYYY-MM-DD>.md` and
exits 0.  On fail it writes a loud `DRIFT_CANARY_FAILED_<YYYY-MM-DD>.md`
marker at the repo root and exits 2.

## Manual invocation

```sh
.venv/Scripts/python.exe scripts/drift_canary.py
.venv/Scripts/python.exe scripts/drift_canary.py --skip-audit
.venv/Scripts/python.exe scripts/drift_canary.py --quiet
```

## Scheduling — Windows Task Scheduler

Register a monthly run on day 1 at 09:00 local.  Run from an elevated
PowerShell or `cmd` (the task runs under your user; `/RU SYSTEM` is also
supported but loses access to the project venv).

```cmd
schtasks /Create /SC MONTHLY /D 1 /ST 09:00 /TN "CountyData2-DriftCanary" /TR "C:\Users\abrhi\Code\CountyData2\.venv\Scripts\python.exe C:\Users\abrhi\Code\CountyData2\scripts\drift_canary.py"
```

Verify:

```cmd
schtasks /Query /TN "CountyData2-DriftCanary" /V /FO LIST
```

Run on demand (sanity-check before the next scheduled fire):

```cmd
schtasks /Run /TN "CountyData2-DriftCanary"
```

Deregister:

```cmd
schtasks /Delete /TN "CountyData2-DriftCanary" /F
```

## Fallback — manual cron

If `schtasks /Create` is blocked by permissions or policy, run the canary
manually on the first Monday of each month:

```sh
cd C:\Users\abrhi\Code\CountyData2
.venv/Scripts/python.exe scripts/drift_canary.py
```

Commit the resulting `docs/sessions/drift-canary-<YYYY-MM-DD>.md` so future
sessions can see the most recent pass.  If a `DRIFT_CANARY_FAILED_*.md`
marker appears at the repo root, treat it as a P0 — investigate before any
new Accela work, and delete the marker once the underlying drift is fixed
(or knowingly accepted).

## Why monthly

ACA HTML markup tends to drift on Accela platform releases (~quarterly).
Monthly catches a single release window with margin; weekly burns API budget
and rate-limit headroom for no marginal coverage gain.  See
`docs/api-maps/polk-county-improvement-report.md` row ACCELA-14.
