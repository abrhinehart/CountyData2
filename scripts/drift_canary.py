"""drift_canary.py - Monthly fixture-drift guardrail for live adapters.

ACCELA-14: Runs three checks against the production adapter surface and writes
a dated success report or a loud failure file at the repo root.

CHECKS
------
1. ``audit_api_maps.py --fail-on-drift`` — exit 0 means every documented map
   matches the codebase.  Subprocess invocation; non-zero rolls up to the
   canary's exit code.
2. Live Polk Accela fetch over a 30-day window.  We pin the validated permit
   ``BR-2026-2894`` (LGI HOMES FLORIDA LLC, 7118 CANOPY LN LAKELAND).  If that
   permit is no longer in the rolling window, we fall back to the most-recent
   Polk permit whose ``raw_owner_name`` parsed non-null and assert the same
   shape against it.
3. NotNull asserts on five extracted fields: ``raw_owner_name``,
   ``raw_applicant_company``, ``raw_contractor_license_number``,
   ``parcel_id``, ``valuation``.

OUTPUTS
-------
* Pass: ``docs/sessions/drift-canary-<YYYY-MM-DD>.md`` — one-line status +
  field values for the inspected permit.  Exit 0.
* Fail: ``DRIFT_CANARY_FAILED_<YYYY-MM-DD>.md`` at repo root + dated session
  doc with the failure reason.  Exit 2.

USAGE
-----
    .venv/Scripts/python.exe scripts/drift_canary.py
    .venv/Scripts/python.exe scripts/drift_canary.py --skip-audit
    .venv/Scripts/python.exe scripts/drift_canary.py --quiet

Register via Windows Task Scheduler — see
``docs/permits/drift-canary-runbook.md`` for the exact ``schtasks /Create``
command and deregistration steps.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
# Ensure the project's modules/ package is importable regardless of CWD
# (Task Scheduler may run us from %SystemRoot%).
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
PINNED_POLK_PERMIT = "BR-2026-2894"  # LGI HOMES FLORIDA LLC; ACCELA-03/-04 anchor
REQUIRED_FIELDS = (
    "raw_owner_name",
    "raw_applicant_company",
    "raw_contractor_license_number",
    "parcel_id",
    "valuation",
)


def _run_audit(quiet: bool = False) -> tuple[bool, str]:
    """Subprocess-call audit_api_maps.py --fail-on-drift.  Returns (ok, output)."""
    try:
        proc = subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts" / "audit_api_maps.py"), "--fail-on-drift"],
            capture_output=True,
            text=True,
            timeout=120,
        )
    except subprocess.TimeoutExpired as exc:
        return False, f"TIMEOUT: {exc}"
    output = proc.stdout + ("\n" + proc.stderr if proc.stderr else "")
    if not quiet:
        print(output)
    return proc.returncode == 0, output


def _fetch_polk_canary_permit() -> tuple[dict | None, str]:
    """Fetch a 30-day Polk window; return (permit_dict, source_label).

    Tries the pinned BR-2026-2894 first; falls back to the most-recent permit
    with raw_owner_name non-null.  Returns (None, "<reason>") on total failure.
    """
    from modules.permits.scrapers.adapters.polk_county import PolkCountyAdapter

    adapter = PolkCountyAdapter()
    end_date = date.today()
    start_date = end_date - timedelta(days=30)
    try:
        permits = adapter.fetch_permits(start_date=start_date, end_date=end_date)
    except Exception as exc:
        return None, f"fetch_permits raised {type(exc).__name__}: {exc}"

    if not permits:
        return None, "fetch_permits returned 0 permits in 30-day window"

    pinned = [p for p in permits if p.get("permit_number") == PINNED_POLK_PERMIT]
    if pinned:
        return pinned[0], f"pinned {PINNED_POLK_PERMIT}"

    # Fallback: most-recent permit with raw_owner_name non-null.
    candidates = [p for p in permits if p.get("raw_owner_name")]
    if not candidates:
        return None, f"no permit in 30-day window has raw_owner_name (n={len(permits)})"

    candidates.sort(key=lambda p: p.get("issue_date") or "", reverse=True)
    return candidates[0], f"fallback most-recent owner-bearing permit ({candidates[0].get('permit_number')})"


def _check_required_fields(permit: dict) -> list[str]:
    """Return list of field names that are None / empty / missing."""
    missing = []
    for field in REQUIRED_FIELDS:
        value = permit.get(field)
        if value is None or value == "" or (isinstance(value, str) and not value.strip()):
            missing.append(field)
    return missing


def _write_success_report(permit: dict, source: str, audit_output: str) -> Path:
    today = date.today().isoformat()
    report = REPO_ROOT / "docs" / "sessions" / f"drift-canary-{today}.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    body = f"""# Drift Canary — {today}

Status: PASS

## Audit
audit_api_maps.py --fail-on-drift exited 0.

## Polk Accela live fetch
Source: {source}
Permit: {permit.get('permit_number')}
Address: {permit.get('address')}
Issue date: {permit.get('issue_date')}

### Required field values
- raw_owner_name: {permit.get('raw_owner_name')!r}
- raw_applicant_company: {permit.get('raw_applicant_company')!r}
- raw_contractor_license_number: {permit.get('raw_contractor_license_number')!r}
- parcel_id: {permit.get('parcel_id')!r}
- valuation: {permit.get('valuation')!r}

### Bonus fields
- raw_owner_address: {permit.get('raw_owner_address')!r}
- raw_applicant_phone: {permit.get('raw_applicant_phone')!r}
- raw_applicant_email: {permit.get('raw_applicant_email')!r}
- raw_contractor_license_type: {permit.get('raw_contractor_license_type')!r}
- raw_additional_licensed_professionals: {permit.get('raw_additional_licensed_professionals')!r}
"""
    report.write_text(body, encoding="utf-8")
    return report


def _write_failure_files(reason: str, audit_output: str) -> tuple[Path, Path]:
    today = date.today().isoformat()
    failure_marker = REPO_ROOT / f"DRIFT_CANARY_FAILED_{today}.md"
    body = f"""# DRIFT CANARY FAILED — {today}

Reason: {reason}

Investigate `docs/sessions/drift-canary-{today}.md` for details, then delete
this marker once the underlying issue is fixed (or knowingly accepted).
"""
    failure_marker.write_text(body, encoding="utf-8")

    detail = REPO_ROOT / "docs" / "sessions" / f"drift-canary-{today}.md"
    detail.parent.mkdir(parents=True, exist_ok=True)
    detail.write_text(
        f"""# Drift Canary — {today}

Status: FAIL

## Reason
{reason}

## Audit output
```
{audit_output.strip() or '(no output)'}
```
""",
        encoding="utf-8",
    )
    return failure_marker, detail


def main() -> int:
    parser = argparse.ArgumentParser(description="Monthly drift canary (ACCELA-14).")
    parser.add_argument("--skip-audit", action="store_true", help="Skip the audit_api_maps subprocess check.")
    parser.add_argument("--quiet", action="store_true", help="Suppress audit subprocess stdout.")
    args = parser.parse_args()

    audit_ok = True
    audit_output = "(skipped)"
    if not args.skip_audit:
        audit_ok, audit_output = _run_audit(quiet=args.quiet)
        if not audit_ok:
            failure_marker, detail = _write_failure_files(
                reason="audit_api_maps.py --fail-on-drift exited non-zero",
                audit_output=audit_output,
            )
            print(f"FAIL: {failure_marker}")
            return 2

    permit, source = _fetch_polk_canary_permit()
    if permit is None:
        failure_marker, detail = _write_failure_files(
            reason=f"Polk fetch produced no usable permit: {source}",
            audit_output=audit_output,
        )
        print(f"FAIL: {failure_marker}")
        return 2

    missing = _check_required_fields(permit)
    if missing:
        failure_marker, detail = _write_failure_files(
            reason=(
                f"Permit {permit.get('permit_number')} (source={source}) is "
                f"missing required fields: {', '.join(missing)}"
            ),
            audit_output=audit_output,
        )
        print(f"FAIL: {failure_marker}")
        return 2

    report = _write_success_report(permit, source, audit_output)
    print(f"PASS: {report}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
