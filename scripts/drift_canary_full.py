"""drift_canary_full.py — Full-sweep drift canary across active CR + PT configs.

Complements the Polk-pinned ``scripts/drift_canary.py`` (ACCELA-14).  This
canary walks every active CR YAML and every live PT adapter, records
per-jurisdiction PASS/PARTIAL/FAIL/SKIPPED, and writes a uniform dated
report at ``docs/sessions/drift-canary-YYYY-MM-DD.md``.

MODES
-----
* ``--dry-run`` (default for pytest) — no network.  Enumerates configs,
  ``yaml.safe_load`` each, constructs the right ``PlatformScraper`` or PT
  adapter, and reports ``factory=OK`` / ``constructor=OK`` per jurisdiction.
  As a belt-and-braces guard, patches ``requests.get`` / ``requests.post``
  to raise ``RuntimeError("offline mode")`` so any code path that tries to
  reach the network fails loud instead of silently hitting a real host.
* ``--live`` — imports ``scripts.cr_live_validate.validate`` for CR YAMLs
  (30-day trailing window) and calls each live PT adapter's
  ``fetch_permits(start, end)`` (7-day trailing window).  Per-call
  try/except so a single jurisdiction failure does not abort the sweep.

FLAGS
-----
* ``--cr-only`` / ``--pt-only`` — restrict the sweep.
* ``--limit N``                  — stop after the first N jurisdictions
  in each bucket (useful for smoke tests).
* ``--append-regressions``       — append a one-line entry for each
  PARTIAL/FAIL outcome to the Drift-canary-regressions section of
  ``TODO.md``.
* ``--report-dir DIR``           — override the default
  ``docs/sessions`` output directory.
* ``--quiet``                    — suppress per-jurisdiction stdout
  chatter; still emits a final summary line.

Register via Windows Task Scheduler — see
``docs/permits/drift-canary-full-runbook.md`` for the exact
``schtasks /Create`` command, exit-code semantics, and report location.
"""
from __future__ import annotations

import argparse
import ast
import datetime as _dt
import importlib
import os
import sys
import traceback
from pathlib import Path
from typing import Callable

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

FL_DIR = REPO_ROOT / "modules" / "commission" / "config" / "jurisdictions" / "FL"
SEED_PATH = REPO_ROOT / "seed_pt_jurisdiction_config.py"
SESSIONS_DIR = REPO_ROOT / "docs" / "sessions"
TODO_PATH = REPO_ROOT / "TODO.md"

YAML_EXCLUDE_NAMES = {"_florida-defaults.yaml"}
YAML_EXCLUDE_SUFFIXES = ("-boa.yaml", "-zba.yaml")

OFFLINE = os.environ.get("CD2_CANARY_OFFLINE") == "1"


def _offline_stub(*_args, **_kwargs):  # noqa: ARG001
    """Sentinel used in ``--dry-run``: any accidental network call blows up."""
    raise RuntimeError("offline mode")


def _install_offline_guard() -> None:
    """Monkey-patch ``requests.get`` / ``requests.post`` with the offline stub."""
    import requests  # local import; only touched when --dry-run fires

    requests.get = _offline_stub  # type: ignore[assignment]
    requests.post = _offline_stub  # type: ignore[assignment]


# ---------- CR enumeration ----------

def _iter_cr_yamls() -> list[Path]:
    if not FL_DIR.exists():
        return []
    out = []
    for p in sorted(FL_DIR.glob("*.yaml")):
        if p.name in YAML_EXCLUDE_NAMES:
            continue
        if p.name.endswith(YAML_EXCLUDE_SUFFIXES):
            continue
        out.append(p)
    return out


# ---------- PT enumeration (AST of seed_pt_jurisdiction_config.JURISDICTIONS) ----------

def _iter_pt_rows() -> list[dict]:
    if not SEED_PATH.exists():
        return []
    tree = ast.parse(SEED_PATH.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and tgt.id == "JURISDICTIONS":
                    rows: list[dict] = []
                    for tup in getattr(node.value, "elts", []):
                        if not isinstance(tup, ast.Tuple):
                            continue
                        try:
                            values = [ast.literal_eval(e) for e in tup.elts]
                        except Exception:
                            continue
                        if len(values) < 9:
                            continue
                        rows.append({
                            "name": values[0],
                            "adapter_slug": values[4],
                            "adapter_class": values[5],
                            "portal_type": values[6],
                            "scrape_mode": values[8],
                        })
                    return rows
    return []


# ---------- per-jurisdiction execution ----------

def _run_cr_dry(yaml_path: Path) -> dict:
    slug = yaml_path.stem
    try:
        cfg = yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
    except Exception as exc:
        return {"slug": slug, "platform": "?", "status": "FAIL",
                "note": f"yaml.safe_load: {exc}"}
    scraping = cfg.get("scraping") or {}
    platform = scraping.get("platform") or "?"
    try:
        from modules.commission.scrapers.base import PlatformScraper
        scraper = PlatformScraper.for_platform(platform)
    except Exception as exc:
        return {"slug": slug, "platform": platform, "status": "FAIL",
                "note": f"factory: {exc}"}
    note = f"factory=OK, constructor=OK ({scraper.__class__.__name__})"
    return {"slug": slug, "platform": platform, "status": "DRY-RUN", "note": note}


def _run_cr_live(yaml_path: Path, window_days: int = 30) -> dict:
    slug = yaml_path.stem
    try:
        cfg = yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
    except Exception as exc:
        return {"slug": slug, "platform": "?", "status": "FAIL",
                "note": f"yaml.safe_load: {exc}"}
    platform = ((cfg.get("scraping") or {}).get("platform")) or "?"
    try:
        from scripts.cr_live_validate import validate  # re-use existing harness
    except Exception as exc:
        return {"slug": slug, "platform": platform, "status": "FAIL",
                "note": f"import cr_live_validate: {exc}"}
    end = _dt.date.today()
    start = end - _dt.timedelta(days=window_days)
    try:
        result = validate(yaml_path, start.strftime("%Y-%m-%d"),
                          end.strftime("%Y-%m-%d"))
    except Exception:
        return {"slug": slug, "platform": platform, "status": "FAIL",
                "note": "validate() raised:\n" + traceback.format_exc()}
    status = result.get("status", "FAIL")
    note_bits = [f"listings={result.get('listings_count', '?')}"]
    if result.get("agenda_count") is not None:
        note_bits.append(f"agendas={result['agenda_count']}")
    if result.get("error"):
        note_bits.append(f"err={str(result['error'])[:120]}")
    return {"slug": slug, "platform": platform, "status": status,
            "note": "; ".join(note_bits)}


def _load_adapter_class(dotted: str):
    mod_name, _, cls_name = dotted.rpartition(".")
    module = importlib.import_module(mod_name)
    return getattr(module, cls_name)


def _run_pt_dry(row: dict) -> dict:
    slug = row["adapter_slug"]
    portal = row.get("portal_type") or "?"
    if row.get("scrape_mode") != "live":
        return {"slug": slug, "portal": portal, "status": "SKIPPED",
                "note": f"scrape_mode={row.get('scrape_mode')}"}
    try:
        cls = _load_adapter_class(row["adapter_class"])
    except Exception as exc:
        return {"slug": slug, "portal": portal, "status": "FAIL",
                "note": f"import: {exc}"}
    try:
        inst = cls()
    except Exception as exc:
        return {"slug": slug, "portal": portal, "status": "FAIL",
                "note": f"constructor: {exc}"}
    note = f"factory=OK, constructor=OK ({cls.__name__})"
    return {"slug": slug, "portal": portal, "status": "DRY-RUN", "note": note}


def _run_pt_live(row: dict, window_days: int = 7) -> dict:
    slug = row["adapter_slug"]
    portal = row.get("portal_type") or "?"
    if row.get("scrape_mode") != "live":
        return {"slug": slug, "portal": portal, "status": "SKIPPED",
                "note": f"scrape_mode={row.get('scrape_mode')}"}
    try:
        cls = _load_adapter_class(row["adapter_class"])
        inst = cls()
    except Exception as exc:
        return {"slug": slug, "portal": portal, "status": "FAIL",
                "note": f"load/construct: {exc}"}
    end = _dt.date.today()
    start = end - _dt.timedelta(days=window_days)
    try:
        permits = inst.fetch_permits(start_date=start, end_date=end)
    except Exception:
        return {"slug": slug, "portal": portal, "status": "FAIL",
                "note": "fetch_permits raised:\n" + traceback.format_exc()}
    count = len(permits) if permits is not None else 0
    status = "PASS" if count > 0 else "PARTIAL"
    return {"slug": slug, "portal": portal, "status": status,
            "note": f"permits={count}"}


# ---------- report writer ----------

def _classify(results: list[dict]) -> dict:
    buckets = {"PASS": 0, "PARTIAL": 0, "FAIL": 0, "SKIPPED": 0, "DRY-RUN": 0}
    for r in results:
        status = r.get("status", "FAIL")
        buckets[status] = buckets.get(status, 0) + 1
    return buckets


def _overall_status(cr: list[dict], pt: list[dict], dry_run: bool) -> str:
    if dry_run:
        return "DRY-RUN"
    all_results = cr + pt
    has_fail = any(r["status"] == "FAIL" for r in all_results)
    has_partial = any(r["status"] == "PARTIAL" for r in all_results)
    if has_fail:
        return "FAIL"
    if has_partial:
        return "PARTIAL"
    return "PASS"


def _write_report(
    report_dir: Path,
    cr: list[dict],
    pt: list[dict],
    overall: str,
) -> Path:
    today = _dt.date.today().isoformat()
    report_dir.mkdir(parents=True, exist_ok=True)
    path = report_dir / f"drift-canary-{today}.md"

    lines: list[str] = []
    lines.append(f"# Drift Canary — {today}")
    lines.append("")
    lines.append(f"Status: {overall}")
    lines.append("")
    lines.append("## Summary")
    lines.append(f"- CR configs exercised: {len(cr)}")
    lines.append(f"- PT adapters exercised: {len(pt)}")
    buckets_all = _classify(cr + pt)
    lines.append(
        "- PASS: {PASS}, PARTIAL: {PARTIAL}, FAIL: {FAIL}, SKIPPED: {SKIPPED}".format(
            **{k: buckets_all.get(k, 0) for k in ("PASS", "PARTIAL", "FAIL", "SKIPPED")}
        )
    )
    lines.append("")

    lines.append("## Commission Radar")
    lines.append("| slug | platform | status | note |")
    lines.append("|---|---|---|---|")
    for r in cr:
        note = (r.get("note") or "").replace("|", "\\|").replace("\n", " ")
        lines.append(f"| {r['slug']} | {r.get('platform', '?')} | {r['status']} | {note} |")
    lines.append("")

    lines.append("## Permit Tracker")
    lines.append("| adapter_slug | portal_type | status | note |")
    lines.append("|---|---|---|---|")
    for r in pt:
        note = (r.get("note") or "").replace("|", "\\|").replace("\n", " ")
        lines.append(f"| {r['slug']} | {r.get('portal', '?')} | {r['status']} | {note} |")
    lines.append("")

    regressions = [r for r in (cr + pt) if r["status"] in ("FAIL", "PARTIAL")]
    if regressions:
        lines.append("## Regressions")
        for r in regressions:
            lines.append(f"- {r['slug']}: {r.get('note', '')}")
        lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _append_regressions_to_todo(cr: list[dict], pt: list[dict]) -> int:
    regressions = [r for r in (cr + pt) if r["status"] in ("FAIL", "PARTIAL")]
    if not regressions or not TODO_PATH.exists():
        return 0
    body = TODO_PATH.read_text(encoding="utf-8")
    marker = "## Drift canary regressions"
    idx = body.find(marker)
    if idx < 0:
        return 0
    today = _dt.date.today().isoformat()
    stanza_lines = [""]
    for r in regressions:
        note = (r.get("note") or "").splitlines()[0][:160]
        stanza_lines.append(
            f"- [ ] {today} {r['slug']}: {note}\n"
            f"  - source: scripts/drift_canary_full.py ({today})\n"
            f"  - tags: [canary, {r['status'].lower()}]\n"
            f"  - status: {'blocked' if r['status'] == 'FAIL' else 'in-progress'}"
        )
    stanza = "\n".join(stanza_lines)
    # Insert after the section-header block (keep the HTML comment marker intact).
    after = body[idx:]
    split = after.find("\n")
    if split < 0:
        return 0
    insertion_point = idx + split + 1
    # Skip the HTML comment immediately after the header if present.
    rest = body[insertion_point:]
    if rest.startswith("<!--"):
        close = rest.find("-->")
        if close >= 0:
            insertion_point += close + 3
            if body[insertion_point:insertion_point + 1] == "\n":
                insertion_point += 1
    new_body = body[:insertion_point] + stanza + "\n" + body[insertion_point:]
    TODO_PATH.write_text(new_body, encoding="utf-8")
    return len(regressions)


# ---------- CLI ----------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Full-sweep drift canary across active CR + PT configs.",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true",
                      help="No network; enumerate + factory/constructor smoke only.")
    mode.add_argument("--live", action="store_true",
                      help="Live network calls; per-call try/except.")
    scope = parser.add_mutually_exclusive_group()
    scope.add_argument("--cr-only", action="store_true",
                       help="Skip PT adapters.")
    scope.add_argument("--pt-only", action="store_true",
                       help="Skip CR YAMLs.")
    parser.add_argument("--limit", type=int, default=0,
                        help="Cap each bucket at N jurisdictions (0=no cap).")
    parser.add_argument("--append-regressions", action="store_true",
                        help="Append PARTIAL/FAIL results to TODO.md "
                             "Drift canary regressions section.")
    parser.add_argument("--quiet", action="store_true",
                        help="Suppress per-jurisdiction stdout.")
    parser.add_argument("--report-dir", type=Path, default=SESSIONS_DIR,
                        help="Override output dir (default docs/sessions).")
    args = parser.parse_args(argv)

    # Default to dry-run when neither flag is set — safer for automation.
    dry_run = args.dry_run or not args.live
    if dry_run:
        os.environ["CD2_CANARY_OFFLINE"] = "1"
        _install_offline_guard()

    cr_yamls = [] if args.pt_only else _iter_cr_yamls()
    pt_rows = [] if args.cr_only else _iter_pt_rows()
    if args.limit and args.limit > 0:
        cr_yamls = cr_yamls[: args.limit]
        pt_rows = pt_rows[: args.limit]

    runner_cr: Callable[[Path], dict] = _run_cr_dry if dry_run else _run_cr_live
    runner_pt: Callable[[dict], dict] = _run_pt_dry if dry_run else _run_pt_live

    cr_results: list[dict] = []
    for y in cr_yamls:
        r = runner_cr(y)
        cr_results.append(r)
        if not args.quiet:
            print(f"CR  {r['slug']:<40} {r['status']:<8} {r.get('note', '')}")

    pt_results: list[dict] = []
    for row in pt_rows:
        r = runner_pt(row)
        pt_results.append(r)
        if not args.quiet:
            print(f"PT  {r['slug']:<40} {r['status']:<8} {r.get('note', '')}")

    overall = _overall_status(cr_results, pt_results, dry_run=dry_run)
    report = _write_report(args.report_dir, cr_results, pt_results, overall)
    print(f"{overall}: {report}")

    if args.append_regressions and not dry_run:
        n = _append_regressions_to_todo(cr_results, pt_results)
        if n:
            print(f"appended {n} regression(s) to TODO.md")

    if dry_run:
        return 0
    return 0 if overall in ("PASS", "PARTIAL") else 2


if __name__ == "__main__":
    raise SystemExit(main())
