"""Compare GIS query results against current DB state to detect changes."""

from decimal import Decimal

from modules.inventory.models import Parcel
from modules.inventory.services.gis_query import ParsedParcel


def _normalize(val) -> str | None:
    """Normalize a value for comparison. Handles Decimal/float trailing zeros."""
    if val is None:
        return None
    if isinstance(val, (Decimal, float)):
        # Normalize to float string without trailing zeros
        return f"{float(val):g}"
    return str(val).strip()


def compare_parcel(existing: Parcel, incoming: ParsedParcel, builder_id: int | None) -> dict | None:
    """Compare an existing DB parcel against incoming GIS data.

    Returns None if unchanged, or a dict with 'old_values' and 'new_values' keys.
    """
    changes_old = {}
    changes_new = {}

    field_pairs = [
        ("owner_name", incoming.owner_name),
        ("site_address", incoming.site_address),
        ("use_type", incoming.use_type),
        ("acreage", incoming.acreage),
    ]

    for field_name, new_val in field_pairs:
        old_val = getattr(existing, field_name)
        if _normalize(old_val) != _normalize(new_val):
            changes_old[field_name] = old_val if old_val is None else str(old_val)
            changes_new[field_name] = new_val if new_val is None else str(new_val)

    # Check builder assignment change
    if existing.builder_id != builder_id:
        changes_old["builder_id"] = existing.builder_id
        changes_new["builder_id"] = builder_id

    if changes_old:
        return {"old_values": changes_old, "new_values": changes_new}
    return None
