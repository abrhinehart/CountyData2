from __future__ import annotations

from importlib import import_module

from modules.permits.reference_data import reference_jurisdictions
from modules.permits.scrapers.base import JurisdictionAdapter


def _load_adapter_class(import_path: str) -> type[JurisdictionAdapter]:
    module_name, _, class_name = import_path.rpartition(".")
    if not module_name or not class_name:
        raise ValueError(f"Invalid adapter_class path: {import_path}")

    module = import_module(module_name)
    adapter_class = getattr(module, class_name, None)
    if adapter_class is None:
        raise ValueError(f"Adapter class not found: {import_path}")
    if not issubclass(adapter_class, JurisdictionAdapter):
        raise ValueError(f"{import_path} is not a JurisdictionAdapter")
    return adapter_class


def _build_adapters() -> dict[str, JurisdictionAdapter]:
    adapters: dict[str, JurisdictionAdapter] = {}
    seen_slugs: set[str] = set()

    for entry in reference_jurisdictions():
        adapter_class = _load_adapter_class(entry["adapter_class"])
        adapter = adapter_class()
        if adapter.slug != entry["adapter_slug"]:
            raise ValueError(
                f"Adapter slug mismatch for {entry['name']}: "
                f"expected {entry['adapter_slug']}, got {adapter.slug}"
            )
        if adapter.display_name != entry["name"]:
            raise ValueError(
                f"Adapter name mismatch for {entry['name']}: "
                f"adapter exposes {adapter.display_name}"
            )
        if adapter.slug in seen_slugs:
            raise ValueError(f"Duplicate adapter slug configured: {adapter.slug}")
        seen_slugs.add(adapter.slug)
        adapters[entry["name"]] = adapter

    return adapters


ADAPTERS = _build_adapters()
