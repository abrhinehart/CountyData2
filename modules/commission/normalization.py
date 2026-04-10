from modules.commission.constants import APPROVAL_TYPE_ALIASES


def normalize_text(value: str | None) -> str | None:
    """Normalize a string for comparison: lowercase, collapse whitespace.

    Returns None if the value is empty, not a string, or whitespace-only.
    """
    if not value or not isinstance(value, str):
        return None
    normalized = " ".join(value.strip().lower().split())
    return normalized or None


def normalize_approval_type(approval_type: str) -> str:
    """Resolve approval type aliases to their canonical form."""
    return APPROVAL_TYPE_ALIASES.get(approval_type, approval_type)
