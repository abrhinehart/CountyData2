"""Roster router — project (subdivision) tracking and lifecycle management.

Ported from the Flask ``roster`` blueprint. The original app modeled
``Project`` as a dedicated table; in CountyData2 projects are merged into
``subdivisions``. We alias ``Subdivision`` as ``Project`` for readability
and query via its ``county_id`` to reach a jurisdiction.
"""

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from shared.models import County, SubdivisionAlias
from shared.sa_database import get_db
from modules.commission.models import (
    CrEntitlementAction as EntitlementAction,
    CrSourceDocument as SourceDocument,
    Jurisdiction,
    Subdivision as Project,
)

from modules.commission.lifecycle import (
    LIFECYCLE_STAGES,
    STAGE_INDEX,
    STAGE_LABELS,
)


router = APIRouter(prefix="/roster")


@router.get("/counties")
def roster_counties(db: Session = Depends(get_db)):
    """Return distinct counties that have projects (subdivisions)."""
    rows = (
        db.query(County.name)
        .join(Project, Project.county_id == County.id)
        .distinct()
        .order_by(County.name)
        .all()
    )
    return [r[0] for r in rows if r[0]]


@router.get("")
def roster_list(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    county: str | None = Query(None),
    jurisdiction: str | None = Query(None),
    lifecycle_stage: str | None = Query(None),
    status: str | None = Query(None),
    min_acreage: float | None = Query(None),
    search: str | None = Query(None),
    sort: str = Query("last_action_date"),
    db: Session = Depends(get_db),
):
    """Paginated project roster with lifecycle tracking."""
    # Project has no jurisdiction_id. We join Project.county_id to
    # Jurisdiction.county_id so a project may map to multiple jurisdictions
    # sharing that county. When the caller filters by a specific jurisdiction
    # slug, we still use that join to scope the list.
    query = db.query(Project, Jurisdiction).outerjoin(
        Jurisdiction, Jurisdiction.county_id == Project.county_id
    )

    if county:
        counties = [c.strip() for c in county.split(",") if c.strip()]
        query = query.join(County, County.id == Project.county_id).filter(
            County.name.in_(counties)
        )

    if jurisdiction:
        slugs = [s.strip() for s in jurisdiction.split(",") if s.strip()]
        query = query.filter(Jurisdiction.slug.in_(slugs))

    if lifecycle_stage:
        stages = [s.strip() for s in lifecycle_stage.split(",") if s.strip()]
        query = query.filter(Project.lifecycle_stage.in_(stages))

    if status:
        statuses = [s.strip() for s in status.split(",") if s.strip()]
        query = query.filter(Project.entitlement_status.in_(statuses))

    if min_acreage is not None:
        query = query.filter(Project.platted_acreage >= min_acreage)

    if search:
        query = query.filter(Project.canonical_name.ilike(f"%{search}%"))

    if sort == "acreage":
        query = query.order_by(
            Project.platted_acreage.desc().nullslast(), Project.canonical_name
        )
    elif sort == "name":
        query = query.order_by(Project.canonical_name)
    else:
        query = query.order_by(
            Project.last_action_date.desc().nullslast(), Project.canonical_name
        )

    total = query.count()
    pages = max(1, (total + per_page - 1) // per_page)
    results = query.offset((page - 1) * per_page).limit(per_page).all()

    items = []
    for project, juris in results:
        action_count = (
            db.query(func.count(EntitlementAction.id))
            .filter(EntitlementAction.subdivision_id == project.id)
            .scalar()
            or 0
        )
        action_types = (
            db.query(EntitlementAction.approval_type)
            .filter(EntitlementAction.subdivision_id == project.id)
            .distinct()
            .all()
        )
        action_type_list = sorted({t[0] for t in action_types if t[0]})

        items.append(
            {
                "id": project.id,
                "name": project.canonical_name,
                "jurisdiction_name": juris.name if juris else "",
                "jurisdiction_slug": juris.slug if juris else "",
                "county": project.county or "",
                "acreage": project.platted_acreage,
                # Subdivision has no lot_count column; fall back to None.
                "lot_count": None,
                "proposed_land_use": project.proposed_land_use or "",
                "proposed_zoning": project.proposed_zoning or "",
                "entitlement_status": project.entitlement_status or "",
                "lifecycle_stage": project.lifecycle_stage or "",
                "lifecycle_stage_label": STAGE_LABELS.get(
                    project.lifecycle_stage, ""
                ),
                "last_action_date": project.last_action_date.isoformat()
                if project.last_action_date
                else "",
                "next_expected_action": project.next_expected_action or "",
                "location_description": project.location_description or "",
                "notes": project.notes or "",
                "action_count": action_count,
                "action_types": action_type_list,
                "created_at": project.created_at.isoformat()
                if project.created_at
                else "",
            }
        )

    return {
        "items": items,
        "total": total,
        "page": page,
        "pages": pages,
    }


@router.get("/{project_id}")
def roster_detail(project_id: int, db: Session = Depends(get_db)):
    """Full project detail with chronological action timeline."""
    project = db.query(Project).get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Pick the first jurisdiction sharing this county.
    juris = (
        db.query(Jurisdiction)
        .filter(Jurisdiction.county_id == project.county_id)
        .order_by(Jurisdiction.name)
        .first()
    )

    actions = (
        db.query(EntitlementAction, SourceDocument)
        .outerjoin(
            SourceDocument, EntitlementAction.source_document_id == SourceDocument.id
        )
        .filter(EntitlementAction.subdivision_id == project_id)
        .order_by(EntitlementAction.meeting_date.asc())
        .all()
    )

    action_items = []
    for action, src_doc in actions:
        ord_num = action.ordinance_number or ""
        if ord_num.lower().startswith("ord "):
            ord_num = ord_num[4:]

        action_items.append(
            {
                "id": action.id,
                "approval_type": action.approval_type or "",
                "case_number": action.case_number or "",
                "ordinance_number": ord_num,
                "ref_number": action.case_number or ord_num or "",
                "outcome": action.outcome or "",
                "vote_detail": action.vote_detail or "",
                "conditions": action.conditions or "",
                "reading_number": action.reading_number or "",
                "meeting_date": action.meeting_date.isoformat()
                if action.meeting_date
                else "",
                "action_summary": action.action_summary or "",
                "action_requested": action.action_requested or "",
                "phase_name": action.phase_name or "",
                "acreage": action.acreage,
                "lot_count": action.lot_count,
                "needs_review": bool(action.needs_review),
                "review_notes": action.review_notes or "",
                "document_type": src_doc.document_type if src_doc else "",
                "source_filename": src_doc.filename if src_doc else "",
                "source_url": src_doc.source_url if src_doc else "",
                "local_file_url": (
                    f"/api/commission/documents/{juris.slug}/{src_doc.filename}"
                    if src_doc and src_doc.filename and juris
                    else ""
                ),
            }
        )

    aliases = (
        db.query(SubdivisionAlias)
        .filter(SubdivisionAlias.subdivision_id == project_id)
        .all()
    )

    current_idx = STAGE_INDEX.get(project.lifecycle_stage, -1)
    lifecycle_progress = [
        {
            "stage": stage,
            "label": STAGE_LABELS.get(stage, stage),
            "reached": STAGE_INDEX.get(stage, -1) <= current_idx,
            "current": stage == project.lifecycle_stage,
        }
        for stage in LIFECYCLE_STAGES
    ]

    return {
        "id": project.id,
        "name": project.canonical_name,
        "jurisdiction_name": juris.name if juris else "",
        "jurisdiction_slug": juris.slug if juris else "",
        "county": project.county or "",
        "acreage": project.platted_acreage,
        "lot_count": None,  # No lot_count column on Subdivision.
        "proposed_land_use": project.proposed_land_use or "",
        "proposed_zoning": project.proposed_zoning or "",
        "entitlement_status": project.entitlement_status or "",
        "lifecycle_stage": project.lifecycle_stage or "",
        "lifecycle_stage_label": STAGE_LABELS.get(project.lifecycle_stage, ""),
        "last_action_date": project.last_action_date.isoformat()
        if project.last_action_date
        else "",
        "next_expected_action": project.next_expected_action or "",
        "location_description": project.location_description or "",
        "notes": project.notes or "",
        "lifecycle_progress": lifecycle_progress,
        "actions": action_items,
        "aliases": [{"alias": a.alias, "source": a.source} for a in aliases],
    }


@router.put("/{project_id}/notes")
def update_project_notes(
    project_id: int,
    payload: dict = Body(...),
    db: Session = Depends(get_db),
):
    """Update notes for a project."""
    project = db.query(Project).get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if not payload or "notes" not in payload:
        raise HTTPException(status_code=400, detail="Missing 'notes' field")

    project.notes = payload["notes"]
    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(exc))

    return {"id": project.id, "notes": project.notes}
