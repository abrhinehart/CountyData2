"""Lifecycle stage inference for development projects.

Infers where a project sits in the entitlement pipeline based on its
EntitlementActions, and predicts the next expected action.

Lifecycle stages (typical Florida entitlement sequence):
  planning_board  -> first_reading -> second_reading -> dev_agreement -> subdivision -> construction

Not every project passes through all stages.  Some skip planning board
(city-initiated), some never need a developer agreement or subdivision.
The engine picks the *highest* stage reached.

Unified-app note: ``Project`` here is an alias for the shared
``Subdivision`` model. Subdivisions do not carry a ``jurisdiction_id``
column; we infer jurisdiction strictly via the owning SourceDocument.
"""

import logging

from modules.commission.models import (
    CrJurisdictionConfig,
    EntitlementAction,
    Project,
    SourceDocument,
)

logger = logging.getLogger("commission_radar.lifecycle")

LIFECYCLE_STAGES = [
    "planning_board",
    "first_reading",
    "second_reading",
    "subdivision",
    "complete",
]

STAGE_INDEX = {stage: i for i, stage in enumerate(LIFECYCLE_STAGES)}

STAGE_LABELS = {
    "planning_board": "Planning Board",
    "first_reading": "First Reading",
    "second_reading": "Second/Final Reading",
    "subdivision": "Subdivision/Plat",
    "complete": "Complete",
}

# What stage comes after each stage
STAGE_TRANSITIONS = {
    "planning_board": "first_reading",
    "first_reading": "second_reading",
    "second_reading": "subdivision",
    "subdivision": "complete",
}

# Approval types that map to specific lifecycle stages
_SUBDIVISION_TYPES = {"subdivision"}

# Commission types that indicate a planning board body
_PLANNING_BOARD_TYPES = {"planning_board"}


def _action_stage(action, commission_type):
    """Determine the lifecycle stage of a single EntitlementAction."""
    approval_type = action.approval_type
    reading = action.reading_number

    # Developer agreements are not lifecycle stages — skip them
    if approval_type == "developer_agreement":
        return None
    if approval_type in _SUBDIVISION_TYPES:
        return "subdivision"

    # Planning board actions
    if commission_type in _PLANNING_BOARD_TYPES:
        return "planning_board"

    # City commission / BCC actions — check reading number
    if reading == "first":
        return "first_reading"
    if reading in ("second_final", "second"):
        return "second_reading"

    # Default: if no reading number, assume it's a single-hearing item
    # which functions as a second/final reading
    if commission_type in ("city_commission", "bcc"):
        return "second_reading"

    return "planning_board"


def infer_lifecycle_stage(actions_with_commission_type: list[tuple]) -> str | None:
    """Determine the highest lifecycle stage reached by a project.

    Args:
        actions_with_commission_type: List of (EntitlementAction, commission_type_str) tuples.

    Returns:
        str lifecycle stage or None if no actions.
    """
    if not actions_with_commission_type:
        return None

    best_stage = None
    best_index = -1

    for action, commission_type in actions_with_commission_type:
        stage = _action_stage(action, commission_type)
        idx = STAGE_INDEX.get(stage, -1)
        if idx > best_index:
            best_index = idx
            best_stage = stage

    return best_stage


def infer_next_action(current_stage: str | None, actions_with_commission_type: list[tuple]) -> str | None:
    """Predict the next expected action based on current stage and completed actions.

    Args:
        current_stage: Current lifecycle stage string.
        actions_with_commission_type: List of (EntitlementAction, commission_type_str) tuples.

    Returns:
        str human-readable description or None if project appears complete.
    """
    if not current_stage:
        return None

    next_stage = STAGE_TRANSITIONS.get(current_stage)
    if not next_stage:
        return None  # At construction — nothing to predict

    # Check what approval types have been completed
    completed_types = set()
    for action, _ in actions_with_commission_type:
        if action.outcome in ("approved", "recommended_approval"):
            completed_types.add(action.approval_type)

    # For the transition from planning_board to first_reading, check if we have
    # all the needed approval types (annexation, land_use, zoning)
    if current_stage == "planning_board":
        pending_types = []
        has_types = {a.approval_type for a, _ in actions_with_commission_type}
        # If annexation is in the mix, it needs a first reading
        if "annexation" in has_types and "annexation" not in completed_types:
            pending_types.append("annexation")
        if "land_use" in has_types and "land_use" not in completed_types:
            pending_types.append("land use amendment")
        if "zoning" in has_types and "zoning" not in completed_types:
            pending_types.append("rezoning")
        if pending_types:
            return f"First reading: {', '.join(pending_types)}"
        return STAGE_LABELS.get(next_stage, next_stage)

    if current_stage == "first_reading":
        return "Second/final reading at City Commission"

    if current_stage == "second_reading":
        return "Subdivision/plat (if applicable)"

    return STAGE_LABELS.get(next_stage, next_stage)


def _get_last_action_date(actions):
    """Return the most recent meeting_date from a list of actions."""
    dates = [a.meeting_date for a in actions if a.meeting_date]
    return max(dates) if dates else None


def update_project_lifecycle(session, project: Project) -> None:
    """Refresh lifecycle fields for a single subdivision (formerly 'project').

    Queries all EntitlementActions for the subdivision, infers stage, and updates
    lifecycle_stage, next_expected_action, and last_action_date.
    """
    from sqlalchemy.orm import joinedload

    actions = (
        session.query(EntitlementAction)
        .options(joinedload(EntitlementAction.source_document))
        .filter(EntitlementAction.subdivision_id == project.id)
        .all()
    )
    if not actions:
        return

    # Batch-fetch commission_type for every jurisdiction these actions came from.
    # In the unified schema, commission_type lives on CrJurisdictionConfig.
    jurisdiction_ids = set()
    for action in actions:
        if action.source_document and action.source_document.jurisdiction_id is not None:
            jurisdiction_ids.add(action.source_document.jurisdiction_id)
    jurisdiction_ids.discard(None)

    jurisdiction_type_map = {}
    if jurisdiction_ids:
        rows = (
            session.query(
                CrJurisdictionConfig.jurisdiction_id,
                CrJurisdictionConfig.commission_type,
            )
            .filter(CrJurisdictionConfig.jurisdiction_id.in_(jurisdiction_ids))
            .all()
        )
        jurisdiction_type_map = {jid: ct for jid, ct in rows}

    actions_with_type = []
    for action in actions:
        jid = action.source_document.jurisdiction_id if action.source_document else None
        ct = jurisdiction_type_map.get(jid, "city_commission")
        actions_with_type.append((action, ct))

    stage = infer_lifecycle_stage(actions_with_type)
    next_action = infer_next_action(stage, actions_with_type)
    last_date = _get_last_action_date(actions)

    project.lifecycle_stage = stage
    project.next_expected_action = next_action
    project.last_action_date = last_date


def refresh_all_lifecycles(session, jurisdiction_id: int | None = None) -> int:
    """Recompute lifecycle stages for all subdivisions (optionally scoped by jurisdiction).

    Scoping by jurisdiction goes through CrSourceDocument ->
    CrEntitlementAction -> Subdivision in the unified schema.

    Returns:
        int count of subdivisions updated.
    """
    if jurisdiction_id is not None:
        subdivision_ids = {
            sid
            for (sid,) in session.query(EntitlementAction.subdivision_id)
            .join(SourceDocument, EntitlementAction.source_document_id == SourceDocument.id)
            .filter(
                SourceDocument.jurisdiction_id == jurisdiction_id,
                EntitlementAction.subdivision_id.isnot(None),
            )
            .distinct()
            .all()
        }
        if not subdivision_ids:
            return 0
        projects = session.query(Project).filter(Project.id.in_(subdivision_ids)).all()
    else:
        projects = session.query(Project).all()

    count = 0
    for project in projects:
        update_project_lifecycle(session, project)
        count += 1

    return count
