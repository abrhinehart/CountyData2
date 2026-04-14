"""Drift-prevention tests: keep seed_pt_jurisdiction_config.JURISDICTIONS,
modules/permits/data/jurisdiction_registry.json, and adapter classes aligned.

All checks are pure offline -- no DB, no network.

Six parametrized checks:
 1. Each JURISDICTIONS row's adapter_class is importable.
 2. Adapter instance's slug + display_name agree with the seed row.
 3. Adapter class-level ``mode`` is consistent with the seed row's scrape_mode
    (directional: if seed says "live", the class must also declare ``mode="live"``;
    the reverse is allowed -- a class can be coded live but administratively
    disabled via seed "fixture" mode).
 4. Instantiation doesn't crash (`adapter_class()` returns an instance).
 5. Set-equality of (slug, scrape_mode) across seed vs registry JSON (registry's
    scrape_mode is derived from ``active``: True->"live", False->"fixture").
 6. For seed rows with scrape_mode="live": fetch_permits is overridden from
    the abstract base (not the unimplemented JurisdictionAdapter.fetch_permits).
"""

from __future__ import annotations

import ast
import json
import sys
from importlib import import_module
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SEED_PATH = ROOT / "seed_pt_jurisdiction_config.py"
REGISTRY_PATH = ROOT / "modules" / "permits" / "data" / "jurisdiction_registry.json"


def _parse_seed_rows() -> list[dict]:
    """Parse JURISDICTIONS from seed_pt_jurisdiction_config.py via AST
    (no psycopg2 import required)."""
    tree = ast.parse(SEED_PATH.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and tgt.id == "JURISDICTIONS":
                    rows = []
                    for tup in node.value.elts:
                        assert isinstance(tup, ast.Tuple), "JURISDICTIONS entry must be tuple"
                        values = [ast.literal_eval(e) for e in tup.elts]
                        # (name, county, municipality, state, adapter_slug,
                        #  adapter_class, portal_type, portal_url, scrape_mode, fragile_note)
                        rows.append({
                            "name": values[0],
                            "county": values[1],
                            "municipality": values[2],
                            "state": values[3],
                            "adapter_slug": values[4],
                            "adapter_class": values[5],
                            "portal_type": values[6],
                            "portal_url": values[7],
                            "scrape_mode": values[8],
                            "fragile_note": values[9],
                        })
                    return rows
    raise RuntimeError("JURISDICTIONS not found in seed_pt_jurisdiction_config.py")


def _load_registry() -> list[dict]:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))["jurisdictions"]


SEED_ROWS = _parse_seed_rows()
SEED_IDS = [r["adapter_slug"] for r in SEED_ROWS]


@pytest.mark.parametrize("row", SEED_ROWS, ids=SEED_IDS)
def test_adapter_class_importable(row):
    """Check #1: adapter_class dotted path resolves to a class."""
    mod_name, _, cls_name = row["adapter_class"].rpartition(".")
    module = import_module(mod_name)
    adapter_cls = getattr(module, cls_name, None)
    assert adapter_cls is not None, (
        f"{row['adapter_slug']}: adapter class not found at {row['adapter_class']}"
    )
    assert isinstance(adapter_cls, type)


@pytest.mark.parametrize("row", SEED_ROWS, ids=SEED_IDS)
def test_adapter_slug_and_display_name_match(row):
    """Check #2: instance.slug == seed adapter_slug; instance.display_name == seed name."""
    mod_name, _, cls_name = row["adapter_class"].rpartition(".")
    adapter_cls = getattr(import_module(mod_name), cls_name)
    adapter = adapter_cls()
    assert adapter.slug == row["adapter_slug"], (
        f"{row['adapter_slug']}: instance.slug={adapter.slug!r}"
    )
    assert adapter.display_name == row["name"], (
        f"{row['adapter_slug']}: instance.display_name={adapter.display_name!r}"
    )


@pytest.mark.parametrize("row", SEED_ROWS, ids=SEED_IDS)
def test_mode_matches_scrape_mode(row):
    """Check #3: adapter class-level ``mode`` agrees with seed ``scrape_mode``
    in the direction that matters -- seed ``live`` requires class ``mode="live"``.

    The reverse (class ``mode="live"`` while seed says ``fixture``) is allowed:
    Winter Haven (Accela) and Lake Hamilton (iWorQ) inherit ``mode="live"``
    from their base class but are administratively disabled via the seed.
    """
    mod_name, _, cls_name = row["adapter_class"].rpartition(".")
    adapter_cls = getattr(import_module(mod_name), cls_name)
    if row["scrape_mode"] == "live":
        assert adapter_cls.mode == "live", (
            f"{row['adapter_slug']}: seed says scrape_mode='live' but "
            f"adapter.mode={adapter_cls.mode!r}"
        )
    else:
        # seed scrape_mode="fixture": class may be live-capable but disabled
        assert adapter_cls.mode in ("live", "fixture"), (
            f"{row['adapter_slug']}: unknown adapter.mode={adapter_cls.mode!r}"
        )


@pytest.mark.parametrize("row", SEED_ROWS, ids=SEED_IDS)
def test_adapter_instantiates_without_crash(row):
    """Check #4: ``adapter_class()`` returns an instance (no arg-less crash)."""
    mod_name, _, cls_name = row["adapter_class"].rpartition(".")
    adapter_cls = getattr(import_module(mod_name), cls_name)
    instance = adapter_cls()
    assert instance is not None


def test_seed_and_registry_have_set_equality_on_slug_mode():
    """Check #5: set-equality of (adapter_slug, scrape_mode) between seed and registry.

    Registry's scrape_mode is derived: active=True -> "live", active=False -> "fixture".

    PRE-CHECK: seed JURISDICTIONS and registry JSON jurisdictions have exact 1:1
    parity (both 16 rows, same slugs) at test-authoring time, so we keep the
    strict set-equality check. If a future divergence is introduced, this test
    will name both the missing-in-seed and missing-in-registry rows.
    """
    seed_set = {(r["adapter_slug"], r["scrape_mode"]) for r in SEED_ROWS}
    registry_set = {
        (r["adapter_slug"], "live" if r["active"] else "fixture")
        for r in _load_registry()
    }
    missing_in_registry = seed_set - registry_set
    missing_in_seed = registry_set - seed_set
    assert not missing_in_registry and not missing_in_seed, (
        f"seed - registry = {missing_in_registry}; "
        f"registry - seed = {missing_in_seed}"
    )


_LIVE_ROWS = [r for r in SEED_ROWS if r["scrape_mode"] == "live"]
_LIVE_IDS = [r["adapter_slug"] for r in _LIVE_ROWS]


@pytest.mark.parametrize("row", _LIVE_ROWS, ids=_LIVE_IDS)
def test_live_adapter_overrides_fetch_permits(row):
    """Check #6: live adapters must override fetch_permits from the abstract base."""
    from modules.permits.scrapers.base import JurisdictionAdapter

    mod_name, _, cls_name = row["adapter_class"].rpartition(".")
    adapter_cls = getattr(import_module(mod_name), cls_name)
    # fetch_permits must not be the abstract base-class method
    assert adapter_cls.fetch_permits is not JurisdictionAdapter.fetch_permits, (
        f"{row['adapter_slug']}: fetch_permits is still the abstract base method"
    )
    # And we can check it isn't an abstract method placeholder
    assert not getattr(adapter_cls.fetch_permits, "__isabstractmethod__", False), (
        f"{row['adapter_slug']}: fetch_permits still has __isabstractmethod__=True"
    )
