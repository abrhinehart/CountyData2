"""Journal-discipline tests: new session journals must surface their pending
work through TODO.md.

This file is a pure offline filesystem read — no DB, no network, no imports of
production modules. It enforces three invariants:

1. TODO.md exists at repo root with the five canonical section headers.
2. Every ``- [ ]`` / ``- [x]`` entry carries indented ``source:`` / ``tags:`` /
   ``status:`` sub-bullets within five lines of the bullet.
3. Every session journal under ``docs/sessions/`` with a pending-work section
   is referenced by at least one line in TODO.md (so the backlog cannot quietly
   lose signal).
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
TODO_PATH = ROOT / "TODO.md"
SESSIONS_DIR = ROOT / "docs" / "sessions"
PENDING_SECTION_RE = re.compile(
    r"(?im)^##?#?\s*(Follow[- ]ups?|Items? NOT done|Deferred|Pending|"
    r"Open questions?|Risks? /?\s*open|Next session|Remaining|Outstanding)"
)
SUPERSEDED_JOURNALS = {"2026-04-16-session-g-haines-city-civicplus-calendar-plan.md"}
REQUIRED_SECTIONS = [
    "## Commission Radar (CR)",
    "## Permit Tracker (PT)",
    "## Builder Inventory (BI)",
    "## Sales / CD2",
    "## Platform / Infra",
]


def test_todo_exists_and_has_required_sections():
    assert TODO_PATH.exists(), f"TODO.md not found at {TODO_PATH}"
    body = TODO_PATH.read_text(encoding="utf-8")
    for section in REQUIRED_SECTIONS:
        assert section in body, f"Missing section: {section}"


def test_todo_entries_well_formed():
    body = TODO_PATH.read_text(encoding="utf-8")
    lines = body.splitlines()
    for i, line in enumerate(lines):
        stripped = line.lstrip()
        if stripped.startswith("- [ ]") or stripped.startswith("- [x]"):
            # Find the next lines; must contain source:, tags:, status: sub-bullets
            window = [l.strip() for l in lines[i + 1 : i + 6]]
            joined = " ".join(window)
            assert "- source:" in joined, f"entry {i} missing source: {line}"
            assert "- tags:" in joined, f"entry {i} missing tags: {line}"
            assert "- status:" in joined, f"entry {i} missing status: {line}"


def _journals_with_pending_sections() -> list[str]:
    if not SESSIONS_DIR.exists():
        return []
    results: list[str] = []
    for j in sorted(SESSIONS_DIR.glob("*.md")):
        if j.name in SUPERSEDED_JOURNALS:
            continue
        if j.name.startswith("drift-canary-"):
            # Canary reports are not session journals; they're generated.
            continue
        text = j.read_text(encoding="utf-8", errors="replace")
        if PENDING_SECTION_RE.search(text):
            results.append(j.name)
    return results


@pytest.mark.parametrize("journal_name", _journals_with_pending_sections())
def test_each_pending_section_has_matching_todo_entry(journal_name):
    body = TODO_PATH.read_text(encoding="utf-8")
    assert journal_name in body, (
        f"{journal_name} has a pending-work section but no entry in TODO.md "
        f"references it (expected a `source: docs/sessions/{journal_name}` line)."
    )
