"""Review queue router — manage flagged documents awaiting manual review."""

import os

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from shared.sa_database import get_db, SessionLocal
from modules.commission.models import (
    CrSourceDocument as SourceDocument,
    Jurisdiction,
    SOURCE_DOCUMENT_STATUS_FLAGGED_FOR_REVIEW,
    SOURCE_DOCUMENT_STATUS_REVIEW_REJECTED,
    Subdivision as Project,  # noqa: F401
)

from modules.commission.routers.helpers import (
    _document_storage_slug,
    _send,
    _source_document_file_path,
)
from modules.commission.routers.process import process_document

from modules.commission.collection_review import source_document_status_label
from modules.commission.intake import (
    IntakeValidationError,
    validate_document_file,
)
from modules.commission.utils import append_processing_note


router = APIRouter(prefix="/review")


def _review_queue_item(source_doc, jurisdiction):
    return {
        "id": source_doc.id,
        "jurisdiction": jurisdiction.name,
        "jurisdiction_slug": jurisdiction.slug,
        "filename": source_doc.filename,
        "document_type": source_doc.document_type,
        "meeting_date": source_doc.meeting_date.isoformat()
        if source_doc.meeting_date
        else "",
        "page_count": source_doc.page_count,
        "review_reason": source_doc.failure_reason or "",
        "source_url": source_doc.source_url or "",
        "local_file_url": f"/api/commission/documents/{_document_storage_slug(jurisdiction)}/{source_doc.filename}",
        "status": source_document_status_label(source_doc),
    }


@router.get("/queue")
def review_queue(db: Session = Depends(get_db)):
    rows = (
        db.query(SourceDocument, Jurisdiction)
        .join(Jurisdiction, SourceDocument.jurisdiction_id == Jurisdiction.id)
        .filter(
            SourceDocument.processing_status == SOURCE_DOCUMENT_STATUS_FLAGGED_FOR_REVIEW
        )
        .order_by(
            SourceDocument.meeting_date.desc(), SourceDocument.created_at.desc()
        )
        .all()
    )
    return [
        _review_queue_item(source_doc, jurisdiction)
        for source_doc, jurisdiction in rows
    ]


@router.post("/{source_document_id}/approve")
def approve_review_item(source_document_id: int, db: Session = Depends(get_db)):
    source_doc = db.get(SourceDocument, source_document_id)
    if not source_doc:
        raise HTTPException(status_code=404, detail="Review queue item not found.")
    if source_doc.processing_status != SOURCE_DOCUMENT_STATUS_FLAGGED_FOR_REVIEW:
        raise HTTPException(
            status_code=400, detail="Only queued review items can be approved."
        )

    jurisdiction = db.get(Jurisdiction, source_doc.jurisdiction_id)
    if not jurisdiction:
        raise HTTPException(
            status_code=404, detail="Jurisdiction for this review item was not found."
        )

    file_path = _source_document_file_path(jurisdiction, source_doc)
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=404, detail="Collected file is missing from local storage."
        )

    try:
        file_format = validate_document_file(file_path, source_doc.filename)
    except IntakeValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    filename = source_doc.filename
    jurisdiction_slug = jurisdiction.slug or jurisdiction.name
    doc_type = source_doc.document_type
    override_date = (
        source_doc.meeting_date.isoformat() if source_doc.meeting_date else None
    )
    source_url = source_doc.source_url
    external_document_id = source_doc.external_document_id

    def generate():
        # Streamed responses need their own session scope.
        session = SessionLocal()
        try:
            yield from process_document(
                session,
                file_path,
                filename,
                file_format,
                jurisdiction_slug=jurisdiction_slug,
                doc_type=doc_type,
                skip_filter=False,
                dry_run=False,
                override_date=override_date,
                label_prefix="[review] ",
                source_url=source_url,
                external_document_id=external_document_id,
                existing_source_document_id=source_document_id,
            )
        except Exception as e:
            session.rollback()
            yield _send({"error": f"Unexpected error: {e}"})
        finally:
            session.close()

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/{source_document_id}/reject")
def reject_review_item(source_document_id: int, db: Session = Depends(get_db)):
    source_doc = db.get(SourceDocument, source_document_id)
    if not source_doc:
        raise HTTPException(status_code=404, detail="Review queue item not found.")
    if source_doc.processing_status != SOURCE_DOCUMENT_STATUS_FLAGGED_FOR_REVIEW:
        raise HTTPException(
            status_code=400, detail="Only queued review items can be rejected."
        )

    source_doc.processing_status = SOURCE_DOCUMENT_STATUS_REVIEW_REJECTED
    source_doc.failure_stage = "collection_review"
    source_doc.processing_notes = append_processing_note(
        source_doc.processing_notes,
        "Manual review rejected automatic processing.",
    )
    db.commit()
    return {"ok": True, "status": source_document_status_label(source_doc)}
