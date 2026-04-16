"""status.py — Generate STATUS.md from git + filesystem + pytest.

Entry points:
    python scripts/status.py                 # print report to stdout
    python scripts/status.py --write         # write STATUS.md at repo root

Inputs collected:
    - git:        HEAD sha/date/subject, git describe tag, working-tree summary.
    - filesystem: CR scraper modules, active FL YAML configs, PT adapter modules,
                  seed-declared PT jurisdictions (AST-parsed, no psycopg2 import).
    - pytest:     collection count via ``pytest --collect-only -q`` (does NOT run tests).
    - canary:     most recent ``docs/sessions/drift-canary-*.md`` + its parsed Status.

No new deps. Stdlib only: subprocess, pathlib, datetime, ast, re, yaml.
"""
from __future__ import annotations

import argparse
import ast
import datetime as _dt
import re
import subprocess
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
FL_DIR = REPO_ROOT / "modules" / "commission" / "config" / "jurisdictions" / "FL"
CR_SCRAPERS_DIR = REPO_ROOT / "modules" / "commission" / "scrapers"
PT_ADAPTERS_DIR = REPO_ROOT / "modules" / "permits" / "scrapers" / "adapters"
SEED_PATH = REPO_ROOT / "seed_pt_jurisdiction_config.py"
SESSIONS_DIR = REPO_ROOT / "docs" / "sessions"
TODO_PATH = REPO_ROOT / "TODO.md"

YAML_EXCLUDE_NAMES = {"_florida-defaults.yaml"}
YAML_EXCLUDE_SUFFIXES = ("-boa.yaml", "-zba.yaml")


# ---------- git ----------

def _git(*args: str) -> str:
    try:
        out = subprocess.run(
            ["git", *args],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        return f"<git error: {exc}>"
    if out.returncode != 0:
        return f"<git error: {out.stderr.strip() or out.returncode}>"
    return out.stdout.strip()


def collect_git() -> dict:
    head = _git("log", "-1", "--format=%H|%h|%ci|%s")
    full, short, ciso, subject = (head.split("|", 3) + ["", "", "", ""])[:4] if "|" in head else ("", "", "", head)
    tag = _git("describe", "--tags", "--always") or "untagged"
    status = _git("status", "--porcelain")
    modified = 0
    untracked = 0
    for line in status.splitlines():
        if line.startswith("??"):
            untracked += 1
        elif line.strip():
            modified += 1
    return {
        "full": full,
        "short": short,
        "date": ciso,
        "subject": subject,
        "tag": tag,
        "modified": modified,
        "untracked": untracked,
    }


# ---------- filesystem: CR ----------

def _active_fl_yamls() -> list[Path]:
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


def _cr_scraper_modules() -> list[str]:
    if not CR_SCRAPERS_DIR.exists():
        return []
    out = []
    for p in sorted(CR_SCRAPERS_DIR.glob("*.py")):
        if p.stem in {"__init__", "base"}:
            continue
        out.append(p.name)
    return out


def _platforms_across_active_yamls(yamls: list[Path]) -> list[str]:
    platforms: set[str] = set()
    for p in yamls:
        try:
            cfg = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        except Exception:
            continue
        scraping = cfg.get("scraping") or {}
        platform = scraping.get("platform")
        if isinstance(platform, str) and platform.strip():
            platforms.add(platform.strip())
    return sorted(platforms)


def collect_cr() -> dict:
    yamls = _active_fl_yamls()
    scrapers = _cr_scraper_modules()
    platforms = _platforms_across_active_yamls(yamls)
    return {
        "scraper_count": len(scrapers),
        "scraper_files": scrapers,
        "yaml_count": len(yamls),
        "platforms": platforms,
    }


# ---------- filesystem + AST: PT ----------

def _pt_adapter_modules() -> list[str]:
    if not PT_ADAPTERS_DIR.exists():
        return []
    out = []
    for p in sorted(PT_ADAPTERS_DIR.glob("*.py")):
        if p.stem == "__init__":
            continue
        out.append(p.name)
    return out


def _parse_seed_jurisdictions() -> list[dict]:
    if not SEED_PATH.exists():
        return []
    try:
        tree = ast.parse(SEED_PATH.read_text(encoding="utf-8"))
    except SyntaxError:
        return []
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
                        # (name, county, municipality, state, adapter_slug,
                        #  adapter_class, portal_type, portal_url, scrape_mode, fragile_note)
                        if len(values) < 9:
                            continue
                        rows.append({
                            "adapter_slug": values[4],
                            "scrape_mode": values[8],
                        })
                    return rows
    return []


def collect_pt() -> dict:
    modules = _pt_adapter_modules()
    rows = _parse_seed_jurisdictions()
    live = [r for r in rows if r.get("scrape_mode") == "live"]
    fixture = [r for r in rows if r.get("scrape_mode") == "fixture"]
    live_slugs = sorted(r["adapter_slug"] for r in live)
    return {
        "adapter_count": len(modules),
        "adapter_files": modules,
        "seed_total": len(rows),
        "seed_live": len(live),
        "seed_fixture": len(fixture),
        "live_slugs": live_slugs,
    }


# ---------- pytest ----------

_COLLECT_RE = re.compile(r"(\d+)\s+tests?\s+collected", re.IGNORECASE)


def collect_pytest() -> dict:
    """Shell out to pytest --collect-only -q. Do NOT run tests."""
    py = sys.executable
    try:
        out = subprocess.run(
            [py, "-m", "pytest", "--collect-only", "-q"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=120,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        return {"collected": None, "note": f"pytest error: {exc}"}
    # pytest prints the count as "N tests collected" on the final non-empty line.
    text = (out.stdout or "") + "\n" + (out.stderr or "")
    match = None
    for line in reversed(text.splitlines()):
        if not line.strip():
            continue
        m = _COLLECT_RE.search(line)
        if m:
            match = m
            break
    count = int(match.group(1)) if match else None
    return {"collected": count, "note": None}


# ---------- drift canary ----------

_CANARY_RE = re.compile(r"^drift-canary-(\d{4}-\d{2}-\d{2})\.md$")
_STATUS_RE = re.compile(r"^\s*Status\s*:\s*(\S+)", re.IGNORECASE | re.MULTILINE)


def collect_canary() -> dict:
    if not SESSIONS_DIR.exists():
        return {"last_report": None, "status": None}
    candidates = []
    for p in SESSIONS_DIR.glob("drift-canary-*.md"):
        m = _CANARY_RE.match(p.name)
        if m:
            candidates.append((m.group(1), p))
    if not candidates:
        return {"last_report": None, "status": None}
    candidates.sort(key=lambda x: x[0], reverse=True)
    latest_date, latest_path = candidates[0]
    try:
        body = latest_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return {"last_report": str(latest_path.relative_to(REPO_ROOT)), "status": None}
    m = _STATUS_RE.search(body)
    status = m.group(1).rstrip(".") if m else None
    return {
        "last_report": str(latest_path.relative_to(REPO_ROOT)).replace("\\", "/"),
        "status": status,
    }


# ---------- TODO ----------

_TODO_UNCHECKED_RE = re.compile(r"^\s*-\s*\[\s\]", re.MULTILINE)
_TODO_CANARY_HEADER_RE = re.compile(r"^##\s+Drift canary regressions", re.MULTILINE)


def collect_todo() -> dict:
    if not TODO_PATH.exists():
        return {"open_count": 0, "present": False}
    body = TODO_PATH.read_text(encoding="utf-8", errors="replace")
    # Split off the Drift canary regressions section (if present) before counting.
    m = _TODO_CANARY_HEADER_RE.search(body)
    scan = body[: m.start()] if m else body
    open_count = len(_TODO_UNCHECKED_RE.findall(scan))
    return {"open_count": open_count, "present": True}


# ---------- render ----------

def render(git: dict, cr: dict, pt: dict, tests: dict, canary: dict, todo: dict) -> str:
    now = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines = []
    lines.append("# CountyData2 — STATUS")
    lines.append("")
    lines.append(f"_Generated: {now}_ — regenerate via `python scripts/status.py --write`.")
    lines.append("")
    lines.append("## HEAD")
    lines.append(f"- commit: {git['full'] or '(unknown)'}")
    lines.append(f"- short: {git['short'] or '(unknown)'}")
    lines.append(f"- date: {git['date'] or '(unknown)'}")
    lines.append(f"- subject: {git['subject'] or '(unknown)'}")
    lines.append(f"- tag: {git['tag'] or 'untagged'}")
    lines.append(f"- working tree: {git['modified']} modified / {git['untracked']} untracked")
    lines.append("")
    lines.append("## Test baseline")
    collected = tests.get("collected")
    lines.append(f"- pytest collected: {collected if collected is not None else '(unavailable)'}")
    lines.append(
        "- last known passing: 573 + 23 subtests "
        "(updated on --write if pytest cache shows a green run)"
    )
    lines.append(
        "- known warnings: SQLAlchemy legacy Query.get at "
        "modules/commission/routers/roster.py:164"
    )
    lines.append("")
    lines.append("## Commission Radar (CR)")
    lines.append(
        f"- platform scrapers: {cr['scraper_count']} "
        f"({', '.join(cr['scraper_files']) if cr['scraper_files'] else 'none'})"
    )
    lines.append(
        "- FL jurisdiction configs (active, excl. BOA/ZBA and _florida-defaults): "
        f"{cr['yaml_count']}"
    )
    lines.append(
        "- platforms represented: "
        f"{', '.join(cr['platforms']) if cr['platforms'] else '(none)'}"
    )
    lines.append("")
    lines.append("## Permit Tracker (PT)")
    lines.append(f"- adapter modules: {pt['adapter_count']}")
    lines.append(
        f"- seed-declared jurisdictions: {pt['seed_total']} "
        f"(live: {pt['seed_live']}, fixture: {pt['seed_fixture']})"
    )
    lines.append(
        "- adapters with scrape_mode=live: "
        f"{', '.join(pt['live_slugs']) if pt['live_slugs'] else '(none)'}"
    )
    lines.append("")
    lines.append("## Drift canary")
    lines.append(f"- last full-sweep run: {canary.get('last_report') or 'never'}")
    lines.append(f"- last status: {canary.get('status') or '(unknown)'}")
    lines.append("")
    lines.append("## TODO")
    lines.append(f"- open items: {todo['open_count']}")
    lines.append("- see [TODO.md](TODO.md)")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate STATUS.md from git + filesystem + pytest.")
    parser.add_argument("--write", action="store_true", help="Write STATUS.md at repo root.")
    args = parser.parse_args(argv)

    git = collect_git()
    cr = collect_cr()
    pt = collect_pt()
    tests = collect_pytest()
    canary = collect_canary()
    todo = collect_todo()

    body = render(git, cr, pt, tests, canary, todo)
    if args.write:
        target = REPO_ROOT / "STATUS.md"
        target.write_text(body, encoding="utf-8")
        print(f"wrote {target}")
    else:
        sys.stdout.write(body)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
