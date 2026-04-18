"""Journal-discipline tests: new session journals must surface their pending
work through TODO.md (or the docs/todo-archive/ tree).

This file is a pure offline filesystem read — no DB, no network, no imports of
production modules. It enforces six invariants:

1. TODO.md exists at repo root with the five canonical module headers
   (Commission Radar, Permit Tracker, Builder Inventory, Sales/CD2,
   Platform/Infra).
2. Every module section in TODO.md carries three subsections: ``### Open``,
   ``### Risks``, ``### Done``.
3. Every ``- [ ]`` / ``- [x]`` entry carries indented ``source:`` / ``tags:`` /
   ``status:`` sub-bullets within five lines of the bullet.
4. ``status:`` values are restricted to the controlled vocabulary
   ``open`` | ``risk`` | ``done`` (``done`` may carry a free-text trailer
   after `` — ``).
5. Placement: ``- [x]`` entries live only under ``### Done``; ``- [ ]`` entries
   live only under ``### Open`` or ``### Risks`` (plus the
   ``## Drift canary regressions`` machine-managed section at the bottom).
6. Every session journal under ``docs/sessions/`` with a pending-work section
   is referenced by name in TODO.md OR in any file under
   ``docs/todo-archive/`` (so moving shipped entries to the archive does
   not break the journal link).
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
TODO_PATH = ROOT / "TODO.md"
ARCHIVE_DIR = ROOT / "docs" / "todo-archive"
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
REQUIRED_SUBSECTIONS = ("### Open", "### Risks", "### Done")
STATUS_VOCAB = {"open", "risk", "done"}


def _module_blocks(body: str) -> dict[str, str]:
    """Return {module_header: text-from-that-header-to-the-next-module-header}."""
    # Split on module-level headers; keep order.
    positions: list[tuple[int, str]] = []
    for header in REQUIRED_SECTIONS + ["## Drift canary regressions"]:
        idx = body.find(header)
        if idx >= 0:
            positions.append((idx, header))
    positions.sort()
    blocks: dict[str, str] = {}
    for i, (start, header) in enumerate(positions):
        end = positions[i + 1][0] if i + 1 < len(positions) else len(body)
        blocks[header] = body[start:end]
    return blocks


def _subsection_blocks(module_text: str) -> dict[str, tuple[int, int]]:
    """Return {subsection_header: (start_line_idx, end_line_idx)} within module_text."""
    lines = module_text.splitlines()
    positions: list[tuple[int, str]] = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped in REQUIRED_SUBSECTIONS:
            positions.append((i, stripped))
    ranges: dict[str, tuple[int, int]] = {}
    for i, (start, header) in enumerate(positions):
        end = positions[i + 1][0] if i + 1 < len(positions) else len(lines)
        ranges[header] = (start, end)
    return ranges


def test_todo_exists_and_has_required_sections():
    assert TODO_PATH.exists(), f"TODO.md not found at {TODO_PATH}"
    body = TODO_PATH.read_text(encoding="utf-8")
    for section in REQUIRED_SECTIONS:
        assert section in body, f"Missing section: {section}"


def test_each_module_has_three_subsections():
    body = TODO_PATH.read_text(encoding="utf-8")
    blocks = _module_blocks(body)
    for header in REQUIRED_SECTIONS:
        module_text = blocks.get(header, "")
        for sub in REQUIRED_SUBSECTIONS:
            assert sub in module_text, (
                f"Module {header!r} is missing subsection {sub!r}"
            )


def test_todo_entries_well_formed():
    body = TODO_PATH.read_text(encoding="utf-8")
    # Skip the machine-managed canary section from structural checks —
    # it uses the same entry shape but is authored by drift_canary_full.py
    # with its own conventions (tags like [canary, fail], status: blocked).
    canary_idx = body.find("## Drift canary regressions")
    scan = body[:canary_idx] if canary_idx >= 0 else body
    lines = scan.splitlines()
    for i, line in enumerate(lines):
        stripped = line.lstrip()
        if stripped.startswith("- [ ]") or stripped.startswith("- [x]"):
            window = [l.strip() for l in lines[i + 1 : i + 6]]
            joined = " ".join(window)
            assert "- source:" in joined, f"entry line {i+1} missing source: {line}"
            assert "- tags:" in joined, f"entry line {i+1} missing tags: {line}"
            assert "- status:" in joined, f"entry line {i+1} missing status: {line}"


def test_status_values_use_controlled_vocabulary():
    """Every `status:` sub-bullet must start with open | risk | done."""
    body = TODO_PATH.read_text(encoding="utf-8")
    canary_idx = body.find("## Drift canary regressions")
    scan = body[:canary_idx] if canary_idx >= 0 else body
    for i, raw in enumerate(scan.splitlines(), start=1):
        stripped = raw.strip()
        if not stripped.startswith("- status:"):
            continue
        value = stripped[len("- status:") :].strip()
        first_token = value.split()[0] if value else ""
        # Accept "done" alone or "done <trailing free-text>"; same for the other two.
        assert first_token in STATUS_VOCAB, (
            f"line {i}: status {value!r} does not start with one of "
            f"{sorted(STATUS_VOCAB)}"
        )


def test_checkbox_placement_matches_subsection():
    """`[x]` only under ### Done; `[ ]` only under ### Open or ### Risks."""
    body = TODO_PATH.read_text(encoding="utf-8")
    blocks = _module_blocks(body)
    for header in REQUIRED_SECTIONS:
        module_text = blocks.get(header, "")
        module_lines = module_text.splitlines()
        sub_ranges = _subsection_blocks(module_text)
        for sub, (start, end) in sub_ranges.items():
            for j in range(start, end):
                s = module_lines[j].lstrip()
                if s.startswith("- [x]"):
                    assert sub == "### Done", (
                        f"{header} / {sub}: `[x]` entry at line {j} must be under ### Done"
                    )
                elif s.startswith("- [ ]"):
                    assert sub in ("### Open", "### Risks"), (
                        f"{header} / {sub}: `[ ]` entry at line {j} must be under ### Open or ### Risks"
                    )


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


def _coverage_corpus() -> str:
    parts = [TODO_PATH.read_text(encoding="utf-8")]
    if ARCHIVE_DIR.exists():
        for archive in sorted(ARCHIVE_DIR.glob("*.md")):
            parts.append(archive.read_text(encoding="utf-8", errors="replace"))
    return "\n".join(parts)


@pytest.mark.parametrize("journal_name", _journals_with_pending_sections())
def test_each_pending_section_has_matching_todo_entry(journal_name):
    body = _coverage_corpus()
    assert journal_name in body, (
        f"{journal_name} has a pending-work section but is not referenced by "
        f"TODO.md or any file under docs/todo-archive/ (expected a "
        f"`source: docs/sessions/{journal_name}` line)."
    )
