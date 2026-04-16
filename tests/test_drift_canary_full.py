"""Regression guard for scripts/drift_canary_full.py offline safety.

The canary runs in `--dry-run` mode under the pytest suite (directly and
transitively via any future integration test). If a future edit accidentally
removes the offline guard or makes a network call in the dry-run path, this
test fails — loud, in CI — before the change can land.
"""
from __future__ import annotations

import datetime as _dt
import importlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


@pytest.fixture
def canary_module():
    import drift_canary_full
    importlib.reload(drift_canary_full)
    return drift_canary_full


def test_offline_stub_raises_runtime_error(canary_module):
    with pytest.raises(RuntimeError, match="offline mode"):
        canary_module._offline_stub()
    with pytest.raises(RuntimeError, match="offline mode"):
        canary_module._offline_stub("https://example.com", timeout=5)


def test_install_offline_guard_replaces_requests_get_and_post(canary_module):
    import requests
    original_get = requests.get
    original_post = requests.post
    try:
        canary_module._install_offline_guard()
        with pytest.raises(RuntimeError, match="offline mode"):
            requests.get("https://example.com")
        with pytest.raises(RuntimeError, match="offline mode"):
            requests.post("https://example.com", json={})
    finally:
        requests.get = original_get
        requests.post = original_post


def test_dry_run_writes_report_and_returns_zero(canary_module, tmp_path):
    rc = canary_module.main([
        "--dry-run", "--quiet", "--limit", "1",
        "--report-dir", str(tmp_path),
    ])
    assert rc == 0
    today = _dt.date.today().isoformat()
    report = tmp_path / f"drift-canary-{today}.md"
    assert report.exists(), f"expected report at {report}"
    body = report.read_text(encoding="utf-8")
    assert "Status: DRY-RUN" in body
    assert "## Commission Radar" in body
    assert "## Permit Tracker" in body


def test_dry_run_does_not_hit_network(canary_module, tmp_path, monkeypatch):
    import requests
    calls = []

    def _trip(*a, **kw):
        calls.append((a, kw))
        raise AssertionError(
            "drift_canary_full dry-run attempted a network call — "
            f"args={a!r} kwargs={kw!r}"
        )

    monkeypatch.setattr(requests, "get", _trip)
    monkeypatch.setattr(requests, "post", _trip)
    rc = canary_module.main([
        "--dry-run", "--quiet", "--limit", "2",
        "--report-dir", str(tmp_path),
    ])
    assert rc == 0
    assert calls == [], f"unexpected network calls: {calls}"
