"""Dashboard router — summary stats, action list, document serving, jurisdiction management."""

import json
import os
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy import func
from sqlalchemy.orm import Session, aliased, subqueryload

from shared.sa_database import get_db
from modules.commission.models import (
    CrCommissioner as Commissioner,
    CrCommissionerVote as CommissionerVote,
    CrEntitlementAction as EntitlementAction,
    CrJurisdictionConfig,
    CrSourceDocument as SourceDocument,
    Jurisdiction,
    Phase,
    SOURCE_DOCUMENT_STATUS_COMPLETED,
    Subdivision as Project,
)

from modules.commission.routers.helpers import PDF_STORAGE_DIR

router = APIRouter(prefix="/dashboard")

DEVELOPMENT_TYPES = {
    "annexation",
    "land_use",
    "zoning",
    "development_review",
    "subdivision",
    "conditional_use",
}
REGULATORY_TYPES = {"text_amendment"}
ANCILLARY_TYPES = {"developer_agreement"}


def _approval_type_set(category):
    if category == "development":
        return DEVELOPMENT_TYPES
    elif category == "regulatory":
        return REGULATORY_TYPES
    return None


def load_jurisdictions(db: Session):
    """Return jurisdiction data grouped for the UI.

    Commission-specific fields (``pinned``, ``agenda_platform``) live on
    ``CrJurisdictionConfig`` and must be joined in. County name comes from
    the shared ``counties`` table via ``Jurisdiction.county_id``.
    """
    from shared.models import County

    rows = (
        db.query(
            Jurisdiction.slug,
            Jurisdiction.name,
            County.name.label("county"),
            CrJurisdictionConfig.pinned,
            CrJurisdictionConfig.agenda_platform,
        )
        .outerjoin(County, County.id == Jurisdiction.county_id)
        .outerjoin(
            CrJurisdictionConfig,
            CrJurisdictionConfig.jurisdiction_id == Jurisdiction.id,
        )
        .order_by(Jurisdiction.name)
        .all()
    )

    count_rows = (
        db.query(
            Jurisdiction.slug,
            func.count(EntitlementAction.id),
        )
        .outerjoin(
            SourceDocument, SourceDocument.jurisdiction_id == Jurisdiction.id
        )
        .outerjoin(
            EntitlementAction,
            EntitlementAction.source_document_id == SourceDocument.id,
        )
        .group_by(Jurisdiction.slug)
        .all()
    )
    counts = dict(count_rows)

    pinned = []
    groups = {}
    flat = {}
    doc_count_rows = (
        db.query(
            Jurisdiction.slug,
            func.count(SourceDocument.id),
        )
        .outerjoin(
            SourceDocument, SourceDocument.jurisdiction_id == Jurisdiction.id
        )
        .group_by(Jurisdiction.slug)
        .all()
    )
    doc_counts = dict(doc_count_rows)

    for row in rows:
        flat[row.slug] = row.name
        n_docs = doc_counts.get(row.slug, 0)
        if n_docs > 0:
            scrape_status = "green"
        elif row.agenda_platform and row.agenda_platform != "manual":
            scrape_status = "yellow"
        else:
            scrape_status = "gray"
        entry = {
            "slug": row.slug,
            "name": row.name,
            "county": row.county,
            "count": counts.get(row.slug, 0),
            "scrape_status": scrape_status,
        }
        if row.pinned:
            pinned.append(entry)
        else:
            groups.setdefault(row.county or "", []).append(entry)
    sorted_groups = dict(sorted(groups.items()))
    return {"pinned": pinned, "groups": sorted_groups, "flat": flat}


@router.get("/jurisdictions")
def dashboard_jurisdictions(db: Session = Depends(get_db)):
    """Return grouped jurisdiction listing for the dashboard UI."""
    return load_jurisdictions(db)


@router.get("/summary")
def dashboard_summary(
    approval_category: str | None = Query(None),
    db: Session = Depends(get_db),
):
    type_set = _approval_type_set(approval_category)

    documents_processed = (
        db.query(func.count(SourceDocument.id))
        .filter(SourceDocument.processing_status == SOURCE_DOCUMENT_STATUS_COMPLETED)
        .scalar()
        or 0
    )

    action_q = db.query(func.count(EntitlementAction.id))
    if type_set:
        action_q = action_q.filter(EntitlementAction.approval_type.in_(type_set))
    actions_extracted = action_q.scalar() or 0

    review_q = db.query(func.count(EntitlementAction.id)).filter(
        EntitlementAction.needs_review == True  # noqa: E712
    )
    if type_set:
        review_q = review_q.filter(EntitlementAction.approval_type.in_(type_set))
    needs_review = review_q.scalar() or 0

    # Count only subdivisions that have at least one entitlement action
    projects_tracked = (
        db.query(func.count(func.distinct(EntitlementAction.subdivision_id)))
        .filter(EntitlementAction.subdivision_id.isnot(None))
        .scalar()
        or 0
    )
    jurisdictions_active = (
        db.query(func.count(CrJurisdictionConfig.id))
        .filter(CrJurisdictionConfig.is_active == True)  # noqa: E712
        .scalar()
        or 0
    )

    return {
        "documents_processed": documents_processed,
        "projects_tracked": projects_tracked,
        "actions_extracted": actions_extracted,
        "needs_review": needs_review,
        "jurisdictions_active": jurisdictions_active,
    }


@router.get("/actions")
def dashboard_actions(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    approval_category: str | None = Query(None),
    jurisdiction: str | None = Query(None),
    approval_type: str | None = Query(None),
    outcome: str | None = Query(None),
    document_type: str | None = Query(None),
    needs_review: str | None = Query(None),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    db: Session = Depends(get_db),
):
    # Project (Subdivision) has no jurisdiction_id. We approximate
    # "project jurisdiction" by joining Subdivision.county_id to
    # Jurisdiction.county_id. Because a project can map to multiple
    # jurisdictions sharing a county, we prefer the source document's
    # jurisdiction when displaying.
    SrcJurisdiction = aliased(Jurisdiction)

    query = (
        db.query(EntitlementAction, SrcJurisdiction, SourceDocument)
        .outerjoin(Project, EntitlementAction.subdivision_id == Project.id)
        .outerjoin(
            SourceDocument, EntitlementAction.source_document_id == SourceDocument.id
        )
        .outerjoin(
            SrcJurisdiction, SourceDocument.jurisdiction_id == SrcJurisdiction.id
        )
        .options(
            subqueryload(EntitlementAction.commissioner_votes).joinedload(
                CommissionerVote.commissioner
            )
        )
    )

    type_set = _approval_type_set(approval_category)
    if type_set:
        query = query.filter(EntitlementAction.approval_type.in_(type_set))

    if jurisdiction:
        slugs = [s.strip() for s in jurisdiction.split(",") if s.strip()]
        query = query.filter(SrcJurisdiction.slug.in_(slugs))

    if approval_type:
        types = [t.strip() for t in approval_type.split(",") if t.strip()]
        query = query.filter(EntitlementAction.approval_type.in_(types))

    if outcome:
        outcomes = [o.strip() for o in outcome.split(",") if o.strip()]
        query = query.filter(EntitlementAction.outcome.in_(outcomes))

    if document_type:
        doc_types = [d.strip() for d in document_type.split(",") if d.strip()]
        query = query.filter(SourceDocument.document_type.in_(doc_types))

    if needs_review == "true":
        query = query.filter(EntitlementAction.needs_review == True)  # noqa: E712

    if date_from:
        query = query.filter(
            EntitlementAction.meeting_date >= date.fromisoformat(date_from)
        )

    if date_to:
        query = query.filter(
            EntitlementAction.meeting_date <= date.fromisoformat(date_to)
        )

    total = query.count()
    pages = max(1, (total + per_page - 1) // per_page)
    page = min(page, pages)

    rows = (
        query.order_by(
            EntitlementAction.meeting_date.desc(), EntitlementAction.id.desc()
        )
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    items = []
    for a, src_juris, src_doc in rows:
        juris_name = ""
        juris_slug = ""
        if src_juris:
            juris_name = src_juris.name
            juris_slug = src_juris.slug or ""

        parcel_ids = a.parcel_ids
        if isinstance(parcel_ids, str):
            try:
                parcel_ids = json.loads(parcel_ids)
            except (json.JSONDecodeError, TypeError):
                parcel_ids = [parcel_ids] if parcel_ids else []

        ord_num = a.ordinance_number or ""
        if ord_num.lower().startswith("ord "):
            ord_num = ord_num[4:]

        ref_number = a.case_number or ord_num or ""

        doc_type = src_doc.document_type if src_doc else ""
        outcome_val = a.outcome or ""
        status = ""
        if a.reading_number == "first" and not outcome_val:
            status = "First Reading"
        elif outcome_val:
            status_map = {
                "approved": "Approved",
                "denied": "Denied",
                "tabled": "Tabled",
                "deferred": "Deferred",
                "withdrawn": "Withdrawn",
                "remanded": "Remanded",
                "modified": "Modified",
                "recommended_approval": "Rec. Approval",
                "recommended_denial": "Rec. Denial",
            }
            status = status_map.get(outcome_val, outcome_val)
        elif doc_type == "agenda":
            action_req = a.action_requested or ""
            status = f"Req: {action_req.title()}" if action_req else "Pending"

        items.append(
            {
                "id": a.id,
                "jurisdiction_name": juris_name,
                "jurisdiction_slug": juris_slug,
                "project_name": a.project_name
                or (a.subdivision.canonical_name if a.subdivision else ""),
                "phase_name": a.phase_name or "",
                "approval_type": a.approval_type or "",
                "case_number": a.case_number or "",
                "ordinance_number": ord_num,
                "ref_number": ref_number,
                "outcome": outcome_val,
                "status": status,
                "meeting_date": a.meeting_date.isoformat() if a.meeting_date else "",
                "acreage": a.acreage,
                "lot_count": a.lot_count,
                "action_summary": a.action_summary or "",
                "needs_review": bool(a.needs_review),
                "review_notes": a.review_notes or "",
                "source_filename": src_doc.filename if src_doc else "",
                "document_type": doc_type,
                "document_url": (
                    f"/api/commission/documents/{juris_slug}/{src_doc.filename}"
                    if src_doc and juris_slug
                    else ""
                ),
                "address": a.address or "",
                "parcel_ids": parcel_ids or [],
                "applicant_name": a.applicant_name or "",
                "current_land_use": a.current_land_use or "",
                "proposed_land_use": a.proposed_land_use or "",
                "current_zoning": a.current_zoning or "",
                "proposed_zoning": a.proposed_zoning or "",
                "vote_detail": a.vote_detail or "",
                "conditions": a.conditions or "",
                "reading_number": a.reading_number or "",
                "land_use_scale": a.land_use_scale or "",
                "action_requested": a.action_requested or "",
                "commissioner_votes": [
                    {
                        "commissioner_id": v.commissioner_id,
                        "name": v.commissioner.name,
                        "title": v.commissioner.title or "",
                        "vote": v.vote,
                        "made_motion": v.made_motion,
                        "seconded_motion": v.seconded_motion,
                    }
                    for v in a.commissioner_votes
                ],
            }
        )

    return {
        "items": items,
        "total": total,
        "page": page,
        "pages": pages,
    }


# NOTE: documents and jurisdictions/{slug}/pin do not live under /dashboard
# in the original Flask API. They share the /api/commission prefix but sit
# alongside /dashboard. We expose them on this router so the parent aggregator
# simply includes this file; mount paths are explicit.


docs_router = APIRouter()


@docs_router.get("/documents/{jurisdiction_slug}/{filename}")
def serve_document(jurisdiction_slug: str, filename: str):
    """Serve a downloaded agenda/minutes PDF for viewing."""
    directory = os.path.join(PDF_STORAGE_DIR, jurisdiction_slug)
    file_path = os.path.join(directory, filename)
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="Document not found")
    return FileResponse(file_path)


@docs_router.post("/jurisdictions/{slug}/pin")
def toggle_pin(slug: str, db: Session = Depends(get_db)):
    """Toggle the pinned state of a jurisdiction.

    The pinned flag lives on :class:`CrJurisdictionConfig`, not the shared
    ``Jurisdiction`` table. If no config row exists yet we create one.
    """
    juris = db.query(Jurisdiction).filter_by(slug=slug).first()
    if not juris:
        raise HTTPException(status_code=404, detail="Jurisdiction not found")

    config = (
        db.query(CrJurisdictionConfig)
        .filter(CrJurisdictionConfig.jurisdiction_id == juris.id)
        .first()
    )
    if not config:
        # commission_type is non-null on CrJurisdictionConfig, so
        # auto-creating a config row here requires a sensible default.
        # Use 'unknown' and expect operators to edit.
        config = CrJurisdictionConfig(
            jurisdiction_id=juris.id, commission_type="unknown", pinned=True
        )
        db.add(config)
    else:
        config.pinned = not bool(config.pinned)

    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(exc))

    return {"slug": slug, "pinned": bool(config.pinned)}
