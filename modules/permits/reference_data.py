from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path


DATA_DIR = Path(__file__).parent / "data"
REGISTRY_PATH = DATA_DIR / "jurisdiction_registry.json"


@lru_cache(maxsize=1)
def load_reference_registry() -> dict:
    payload = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    jurisdictions = payload.get("jurisdictions")
    subdivisions = payload.get("subdivisions")
    if not isinstance(jurisdictions, list) or not isinstance(subdivisions, list):
        raise ValueError("jurisdiction_registry.json must contain 'jurisdictions' and 'subdivisions' lists.")

    required_jurisdiction_fields = {
        "name",
        "adapter_slug",
        "adapter_class",
        "portal_type",
        "portal_url",
        "active",
    }
    required_subdivision_fields = {
        "name",
        "jurisdiction",
        "watched",
    }

    for entry in jurisdictions:
        missing = required_jurisdiction_fields.difference(entry)
        if missing:
            raise ValueError(
                "Jurisdiction registry entry is missing fields: "
                + ", ".join(sorted(missing))
            )

    for entry in subdivisions:
        missing = required_subdivision_fields.difference(entry)
        if missing:
            raise ValueError(
                "Subdivision registry entry is missing fields: "
                + ", ".join(sorted(missing))
            )

    return payload


def reference_jurisdictions() -> list[dict]:
    return [dict(entry) for entry in load_reference_registry()["jurisdictions"]]


def reference_subdivisions() -> list[dict]:
    return [dict(entry) for entry in load_reference_registry()["subdivisions"]]


def reference_jurisdiction_by_name() -> dict[str, dict]:
    return {
        entry["name"]: dict(entry)
        for entry in load_reference_registry()["jurisdictions"]
    }


def reference_jurisdiction_by_slug() -> dict[str, dict]:
    return {
        entry["adapter_slug"]: dict(entry)
        for entry in load_reference_registry()["jurisdictions"]
        if entry.get("adapter_slug")
    }


def reference_jurisdiction_names() -> list[str]:
    return [entry["name"] for entry in reference_jurisdictions()]
