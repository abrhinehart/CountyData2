from copy import deepcopy

from modules.commission.constants import (
    ANNEXATION_MIN_ACRES,
    ANNEXATION_MULTI_PROJECT_ACRES,
    AUTO_PASS_TYPES,
    CONDITIONAL_USE_MIN_ACRES,
    REZONING_MIN_ACRES,
    REZONING_MIN_LOTS,
)
from modules.commission.normalization import normalize_approval_type

STANDARD_REVIEW_NOTE = "No acreage or lot count available. "


def _append_review_note(item, note):
    existing = item.get("review_notes") or ""
    if note in existing:
        return existing
    return f"{existing}{note}"


def _decision(item, normalized_type, passed, rule_applied, reason, **updates):
    decided = deepcopy(item)
    decided["normalized_approval_type"] = normalized_type
    for key, value in updates.items():
        decided[key] = value

    return {
        "passed": passed,
        "rule_applied": rule_applied,
        "reason": reason,
        "item": decided,
    }


def evaluate_filters(items: list[dict]) -> list[dict]:
    """Return structured threshold-filter decisions for extracted items."""
    decisions = []

    for item in items:
        approval_type = item.get("approval_type", "")
        normalized_type = normalize_approval_type(approval_type)
        acreage = item.get("acreage")
        lot_count = item.get("lot_count")
        project_name = item.get("project_name")

        if normalized_type in AUTO_PASS_TYPES:
            decisions.append(
                _decision(
                    item,
                    normalized_type,
                    True,
                    "auto_pass_type",
                    f"{normalized_type} items auto-pass threshold filtering.",
                )
            )
            continue

        if normalized_type == "subdivision":
            if project_name:
                decisions.append(
                    _decision(
                        item,
                        normalized_type,
                        True,
                        "named_subdivision",
                        "Named subdivision/plat items pass automatically.",
                    )
                )
            else:
                note = _append_review_note(item, "Subdivision item missing project name. ")
                decisions.append(
                    _decision(
                        item,
                        normalized_type,
                        True,
                        "subdivision_needs_review",
                        "Subdivision item missing project name; passed for review.",
                        needs_review=True,
                        review_notes=note,
                    )
                )
            continue

        if normalized_type == "text_amendment":
            decisions.append(
                _decision(
                    item,
                    normalized_type,
                    True,
                    "text_amendment",
                    "Text amendments always pass threshold filtering.",
                )
            )
            continue

        if normalized_type == "conditional_use":
            if acreage is not None and acreage < CONDITIONAL_USE_MIN_ACRES:
                decisions.append(
                    _decision(
                        item,
                        normalized_type,
                        False,
                        "conditional_use_below_threshold",
                        f"Conditional use acreage {acreage} is below the {CONDITIONAL_USE_MIN_ACRES}-acre threshold.",
                    )
                )
                continue
            decisions.append(
                _decision(
                    item,
                    normalized_type,
                    True,
                    "conditional_use_pass",
                    f"Conditional use passed (acreage {acreage or 'unknown'}).",
                )
            )
            continue

        if normalized_type == "annexation":
            if acreage is None:
                note = _append_review_note(item, "Annexation acreage missing. ")
                decisions.append(
                    _decision(
                        item,
                        normalized_type,
                        True,
                        "annexation_missing_acreage",
                        "Annexation acreage missing; passed for review.",
                        needs_review=True,
                        review_notes=note,
                    )
                )
                continue
            if acreage < ANNEXATION_MIN_ACRES:
                decisions.append(
                    _decision(
                        item,
                        normalized_type,
                        False,
                        "annexation_below_threshold",
                        f"Annexation acreage {acreage} is below the {ANNEXATION_MIN_ACRES}-acre threshold.",
                    )
                )
                continue

            updates = {}
            reason = f"Annexation acreage {acreage} meets the threshold."
            if acreage >= ANNEXATION_MULTI_PROJECT_ACRES:
                updates["multi_project_flag"] = True
                reason = (
                    f"Annexation acreage {acreage} exceeds the "
                    f"{ANNEXATION_MULTI_PROJECT_ACRES}-acre multi-project threshold."
                )
            decisions.append(
                _decision(
                    item,
                    normalized_type,
                    True,
                    "annexation_threshold",
                    reason,
                    **updates,
                )
            )
            continue

        if normalized_type in {"zoning", "land_use"}:
            if lot_count is not None and lot_count >= REZONING_MIN_LOTS:
                decisions.append(
                    _decision(
                        item,
                        normalized_type,
                        True,
                        "lot_threshold",
                        f"Lot count {lot_count} meets the {REZONING_MIN_LOTS}-lot threshold.",
                    )
                )
                continue
            if acreage is not None and acreage >= REZONING_MIN_ACRES:
                decisions.append(
                    _decision(
                        item,
                        normalized_type,
                        True,
                        "acreage_threshold",
                        f"Acreage {acreage} meets the {REZONING_MIN_ACRES}-acre threshold.",
                    )
                )
                continue
            if lot_count is None and acreage is None:
                # Missing metrics is normal for agendas — pass without flagging for review
                decisions.append(
                    _decision(
                        item,
                        normalized_type,
                        True,
                        "missing_threshold_fields",
                        "Acreage and lot count are both missing; passed (missing data is common for agendas).",
                    )
                )
                continue

            decisions.append(
                _decision(
                    item,
                    normalized_type,
                    False,
                    "below_threshold",
                    (
                        f"{normalized_type} item did not meet the lot threshold "
                        f"({lot_count if lot_count is not None else 'n/a'} < {REZONING_MIN_LOTS}) "
                        f"or acreage threshold ({acreage if acreage is not None else 'n/a'} < {REZONING_MIN_ACRES})."
                    ),
                )
            )
            continue

        note = _append_review_note(item, f"Unhandled approval type '{approval_type}'. ")
        decisions.append(
            _decision(
                item,
                normalized_type,
                True,
                "unhandled_type_review",
                f"Unhandled approval type '{approval_type}' passed for review instead of silently auto-passing.",
                needs_review=True,
                review_notes=note,
            )
        )

    return decisions


def apply_filters(items: list[dict]) -> list[dict]:
    """Apply threshold filters and return only items that passed."""
    return [decision["item"] for decision in evaluate_filters(items) if decision["passed"]]
