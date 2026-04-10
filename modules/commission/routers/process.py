"""Processing router — upload and process documents via SSE pipeline."""

import os
import tempfile
from datetime import date

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from shared.sa_database import get_db, SessionLocal
from modules.commission.models import (
    CrSourceDocument as SourceDocument,
    Jurisdiction,
    SOURCE_DOCUMENT_STATUS_COMPLETED,
    SOURCE_DOCUMENT_STATUS_DETECTED,
    SOURCE_DOCUMENT_STATUS_EXTRACTION_FAILED,
    SOURCE_DOCUMENT_STATUS_FILTERED_OUT,
    Subdivision as Project,  # noqa: F401
)

from modules.commission.routers.helpers import (
    _conversion_note,
    _duplicate_error_message,
    _json_error,
    _send,
)

from modules.commission.auto_detect import (
    detect_jurisdiction_details,
    detect_meeting_date_details,
    format_detection_error,
    format_detection_success,
)
from modules.commission.config_loader import load_jurisdiction_config
from modules.commission.converters import DocumentConverter
from modules.commission.converters.base import format_conversion_detail
from modules.commission.extractor import extract_items
from modules.commission.intake import (
    _wrap_jurisdiction,
    UPLOAD_ACCEPT,
    find_source_document_duplicate,
    get_jurisdiction,
    validate_doc_type,
    validate_document_file,
    validate_iso_date,
    IntakeValidationError,
)
from modules.commission.keyword_filter import (
    check_keywords,
    format_keyword_filter_detail,
)
from modules.commission.packet_fetcher import merge_html_fields_into_items
from modules.commission.record_inserter import insert_records
from modules.commission.threshold_filter import evaluate_filters
from modules.commission.utils import append_processing_note, compute_file_hash
from modules.commission.matcher import match_agenda_to_minutes
from modules.commission.lifecycle import refresh_all_lifecycles


router = APIRouter(prefix="/process")


def _detection_note(
    jurisdiction_display,
    jurisdiction_result,
    meeting_date_result,
    *,
    jurisdiction_overridden,
    date_overridden,
):
    lines = []
    if jurisdiction_overridden:
        lines.append(f"Jurisdiction override: {jurisdiction_display}.")
    else:
        lines.append(
            f"Jurisdiction detection: {format_detection_success('Jurisdiction', jurisdiction_display, jurisdiction_result)}."
        )

    if date_overridden:
        lines.append(f"Meeting date override: {meeting_date_result['value']}.")
    else:
        lines.append(
            f"Meeting date detection: {format_detection_success('Meeting date', meeting_date_result['value'], meeting_date_result)}."
        )

    return "\n".join(lines)


def process_document(
    session,
    file_path,
    filename,
    file_format,
    jurisdiction_slug=None,
    doc_type="agenda",
    skip_filter=False,
    dry_run=False,
    override_date=None,
    label_prefix="",
    source_url=None,
    external_document_id=None,
    existing_source_document_id=None,
    collection_review_note=None,
):
    """Run the 8-step pipeline on a document, yielding SSE events.

    Yields ``_send()``-formatted strings for each progress update. The final
    yield is either an error event or a ``done`` event with results.
    """
    # Step 1: Convert
    yield _send({"step": 1, "total": 8, "label": f"{label_prefix}Converting document..."})

    needs_dedup = False
    provided_jurisdiction = None
    if jurisdiction_slug:
        provided_jurisdiction = (
            session.query(Jurisdiction)
            .filter(
                (Jurisdiction.slug == jurisdiction_slug)
                | (Jurisdiction.name == jurisdiction_slug)
            )
            .first()
        )
    detected_slug = (
        provided_jurisdiction.slug
        if provided_jurisdiction and provided_jurisdiction.slug
        else jurisdiction_slug
    )
    if detected_slug:
        juris_config = load_jurisdiction_config(detected_slug)
        if juris_config:
            needs_dedup = juris_config.get("scraping", {}).get(
                "has_duplicate_page_bug", False
            )

    converter = DocumentConverter.for_format(file_format)
    result = converter.convert(file_path, deduplicate_pages=needs_dedup)
    document_text = result.text

    step_one_payload = {
        "step": 1,
        "total": 8,
        "label": f"{label_prefix}Converting document...",
        "detail": format_conversion_detail(result),
        "status": "done",
    }
    if result.metadata.get("warnings"):
        step_one_payload["warnings"] = result.metadata["warnings"]
    yield _send(step_one_payload)

    if result.metadata.get("quality") == "empty":
        yield _send(
            {"error": f"Conversion produced too little text to continue for {filename}."}
        )
        return

    # Step 2: Detect jurisdiction and date
    yield _send(
        {
            "step": 2,
            "total": 8,
            "label": f"{label_prefix}Detecting jurisdiction and date...",
        }
    )

    jurisdiction_result = None
    if not detected_slug:
        jurisdiction_result = detect_jurisdiction_details(document_text)
        if jurisdiction_result["status"] != "ok":
            yield _send(
                {"error": format_detection_error("jurisdiction", jurisdiction_result)}
            )
            return
        detected_slug = jurisdiction_result["value"]
        juris_config = load_jurisdiction_config(detected_slug)
        if juris_config and juris_config.get("scraping", {}).get(
            "has_duplicate_page_bug", False
        ):
            if not needs_dedup:
                result = converter.convert(file_path, deduplicate_pages=True)
                document_text = result.text
                dedup_payload = {
                    "step": 1,
                    "total": 8,
                    "label": f"{label_prefix}Converting document...",
                    "detail": format_conversion_detail(result),
                    "status": "done",
                }
                if result.metadata.get("warnings"):
                    dedup_payload["warnings"] = result.metadata["warnings"]
                yield _send(dedup_payload)
                if result.metadata.get("quality") == "empty":
                    yield _send(
                        {
                            "error": f"Conversion produced too little text to continue for {filename} after duplicate-page cleanup."
                        }
                    )
                    return
    else:
        jurisdiction_result = {
            "status": "ok",
            "value": detected_slug,
            "score": None,
            "score_gap": None,
            "reason": "jurisdiction override provided",
            "warnings": [],
            "candidates": [],
        }

    meeting_date_result = None
    if override_date:
        meeting_date_result = {
            "status": "ok",
            "value": override_date,
            "score": None,
            "score_gap": None,
            "reason": "meeting date override provided",
            "warnings": [],
            "candidates": [],
        }
    else:
        meeting_date_result = detect_meeting_date_details(document_text)
        if meeting_date_result["status"] not in {"ok", "weak"}:
            yield _send(
                {"error": format_detection_error("meeting date", meeting_date_result)}
            )
            return

    juris = (
        provided_jurisdiction
        or session.query(Jurisdiction)
        .filter(
            (Jurisdiction.slug == detected_slug)
            | (Jurisdiction.name == detected_slug)
        )
        .first()
    )
    if not juris:
        yield _send({"error": f"Jurisdiction '{detected_slug}' not found in database."})
        return
    meeting_date_str = meeting_date_result["value"]

    file_hash = compute_file_hash(file_path)
    duplicate = find_source_document_duplicate(
        session,
        jurisdiction_id=juris.id,
        file_hash=file_hash,
        external_document_id=external_document_id,
        source_url=source_url,
        filename=filename,
        exclude_source_document_id=existing_source_document_id,
    )
    if duplicate:
        yield _send({"error": _duplicate_error_message(filename, duplicate)})
        return

    source_doc = None
    if not dry_run:
        if existing_source_document_id is not None:
            source_doc = session.get(SourceDocument, existing_source_document_id)
            if not source_doc:
                yield _send(
                    {
                        "error": f"Review queue item {existing_source_document_id} was not found."
                    }
                )
                return
            source_doc.jurisdiction_id = juris.id
            source_doc.filename = filename
            source_doc.file_hash = file_hash
            source_doc.source_url = source_url
            source_doc.external_document_id = external_document_id
            source_doc.file_format = file_format
            source_doc.document_type = doc_type
            source_doc.meeting_date = date.fromisoformat(meeting_date_str)
            source_doc.page_count = result.page_count
            source_doc.extracted_text_length = len(document_text)
            source_doc.keyword_filter_passed = None
            source_doc.extraction_attempted = False
            source_doc.extraction_successful = None
            source_doc.items_extracted = None
            source_doc.items_after_filtering = None
            source_doc.processing_status = SOURCE_DOCUMENT_STATUS_DETECTED
            source_doc.failure_stage = None
            source_doc.failure_reason = None
            source_doc.processing_notes = append_processing_note(
                source_doc.processing_notes,
                "Manual review approved; starting normal processing.",
            )
        else:
            source_doc = SourceDocument(
                jurisdiction_id=juris.id,
                filename=filename,
                file_hash=file_hash,
                source_url=source_url,
                external_document_id=external_document_id,
                file_format=file_format,
                document_type=doc_type,
                meeting_date=date.fromisoformat(meeting_date_str),
                page_count=result.page_count,
                extracted_text_length=len(document_text),
                processing_status=SOURCE_DOCUMENT_STATUS_DETECTED,
            )
            session.add(source_doc)
            try:
                session.flush()
            except IntegrityError:
                session.rollback()
                duplicate = find_source_document_duplicate(
                    session,
                    jurisdiction_id=juris.id,
                    file_hash=file_hash,
                    external_document_id=external_document_id,
                    source_url=source_url,
                    filename=filename,
                    exclude_source_document_id=existing_source_document_id,
                )
                reason = (
                    duplicate.reason if duplicate else "duplicate source document detected"
                )
                yield _send(
                    {
                        "error": f"{filename} has already been processed for this jurisdiction ({reason})."
                    }
                )
                return
        conversion_note = _conversion_note(result.metadata)
        if conversion_note:
            source_doc.processing_notes = append_processing_note(
                source_doc.processing_notes, conversion_note
            )
        detection_note = _detection_note(
            juris.name,
            jurisdiction_result,
            meeting_date_result,
            jurisdiction_overridden=bool(jurisdiction_slug),
            date_overridden=bool(override_date),
        )
        source_doc.processing_notes = append_processing_note(
            source_doc.processing_notes, detection_note
        )
        if collection_review_note:
            source_doc.processing_notes = append_processing_note(
                source_doc.processing_notes,
                collection_review_note,
            )

    step_two_detail = " | ".join(
        [
            (
                f"Jurisdiction override: {juris.name}"
                if jurisdiction_slug
                else format_detection_success(
                    "Jurisdiction",
                    f"{juris.name} ({detected_slug})",
                    jurisdiction_result,
                )
            ),
            (
                f"Meeting date override: {meeting_date_str}"
                if override_date
                else format_detection_success(
                    "Meeting date", meeting_date_str, meeting_date_result
                )
            ),
        ]
    )

    yield _send(
        {
            "step": 2,
            "total": 8,
            "label": f"{label_prefix}Detecting jurisdiction and date...",
            "detail": step_two_detail,
            "status": "done",
        }
    )

    # Step 3: Keyword filter
    yield _send(
        {"step": 3, "total": 8, "label": f"{label_prefix}Running keyword filter..."}
    )
    if skip_filter:
        if source_doc:
            source_doc.keyword_filter_passed = True
        kw_detail = "Keyword filter skipped."
    else:
        kw_result = check_keywords(
            document_text, load_jurisdiction_config(juris.slug) or {}
        )
        if source_doc:
            source_doc.keyword_filter_passed = kw_result["passed"]
        if not kw_result["passed"]:
            if source_doc:
                source_doc.processing_status = SOURCE_DOCUMENT_STATUS_FILTERED_OUT
                source_doc.failure_stage = None
                source_doc.failure_reason = None
                source_doc.processing_notes = append_processing_note(
                    source_doc.processing_notes,
                    f"Keyword filter blocked extraction: {kw_result['reason']}",
                )
                session.commit()
                yield _send(
                    {
                        "error": (
                            "Keyword filter did not find enough development signals. "
                            f"{kw_result['reason']} Document saved as filtered out; extraction skipped."
                        )
                    }
                )
                return
            yield _send(
                {
                    "error": (
                        "Keyword filter did not find enough development signals. "
                        f"{kw_result['reason']} Dry run stopped before extraction; nothing was saved."
                    )
                }
            )
            return
        kw_detail = format_keyword_filter_detail(kw_result)
    yield _send(
        {
            "step": 3,
            "total": 8,
            "label": f"{label_prefix}Running keyword filter...",
            "detail": kw_detail,
            "status": "done",
        }
    )

    # Step 4: Claude API extraction
    yield _send(
        {
            "step": 4,
            "total": 8,
            "label": f"{label_prefix}Extracting with Claude API (may take 30+ seconds)...",
        }
    )
    if source_doc:
        source_doc.extraction_attempted = True
    try:
        items = extract_items(document_text, detected_slug, meeting_date_str, doc_type)
        if source_doc:
            source_doc.extraction_successful = True
            source_doc.items_extracted = len(items)
    except Exception as e:
        if source_doc:
            source_doc.extraction_successful = False
            source_doc.processing_status = SOURCE_DOCUMENT_STATUS_EXTRACTION_FAILED
            source_doc.failure_stage = "extraction"
            source_doc.failure_reason = str(e)
            source_doc.processing_notes = append_processing_note(
                source_doc.processing_notes,
                f"Extraction failed: {e}",
            )
            session.commit()
        yield _send({"error": f"Claude API extraction failed: {e}"})
        return

    # Merge structured fields from CivicPlus agenda HTML (free, no API)
    juris_view = _wrap_jurisdiction(session, juris)
    html_enriched = merge_html_fields_into_items(items, source_doc, juris_view)
    html_note = f", {html_enriched} enriched from HTML" if html_enriched else ""
    yield _send(
        {
            "step": 4,
            "total": 8,
            "label": f"{label_prefix}Extracting with Claude API...",
            "detail": f"{len(items)} items extracted{html_note}",
            "status": "done",
        }
    )

    # Step 5: Threshold filtering
    yield _send(
        {
            "step": 5,
            "total": 8,
            "label": f"{label_prefix}Applying threshold filters...",
        }
    )
    filter_decisions = evaluate_filters(items)
    filtered_items = [d["item"] for d in filter_decisions if d["passed"]]
    if source_doc:
        source_doc.items_after_filtering = len(filtered_items)
    yield _send(
        {
            "step": 5,
            "total": 8,
            "label": f"{label_prefix}Applying threshold filters...",
            "detail": f"{len(filtered_items)} of {len(items)} items passed filters",
            "status": "done",
        }
    )

    # Step 6: Record insertion
    yield _send({"step": 6, "total": 8, "label": f"{label_prefix}Inserting records..."})
    if dry_run:
        session.rollback()
        counts = {"projects": 0, "phases": 0, "entitlement_actions": 0}
        insert_detail = "Dry run — no records saved."
    else:
        counts = insert_records(
            session, filtered_items, source_doc.id, juris.id, meeting_date_str
        )
        source_doc.processing_status = SOURCE_DOCUMENT_STATUS_COMPLETED
        source_doc.failure_stage = None
        source_doc.failure_reason = None
        session.commit()
        phases_msg = f", {counts['phases']} phases" if counts.get("phases") else ""
        insert_detail = (
            f"Created {counts['projects']} projects{phases_msg}, "
            f"{counts['entitlement_actions']} actions"
        )
    yield _send(
        {
            "step": 6,
            "total": 8,
            "label": f"{label_prefix}Inserting records...",
            "detail": insert_detail,
            "status": "done",
        }
    )

    match_count = 0
    lifecycle_count = 0
    if not dry_run:
        # Step 7: Agenda-minutes matching
        yield _send({"step": 7, "total": 8, "label": f"{label_prefix}Matching agenda to minutes..."})
        try:
            match_count = match_agenda_to_minutes(session, juris.id)
            session.commit()
        except Exception as e:
            session.rollback()
            source_doc.processing_notes = append_processing_note(
                source_doc.processing_notes,
                f"Matcher failed (non-fatal): {e}",
            )
            session.commit()
            yield _send({
                "step": 7,
                "total": 8,
                "label": f"{label_prefix}Matching agenda to minutes...",
                "detail": f"Matcher failed (non-fatal): {e}",
                "status": "done",
            })
        else:
            yield _send({
                "step": 7,
                "total": 8,
                "label": f"{label_prefix}Matching agenda to minutes...",
                "detail": f"Created {match_count} agenda-minutes links",
                "status": "done",
            })

        # Step 8: Lifecycle refresh (scoped to this jurisdiction)
        yield _send({"step": 8, "total": 8, "label": f"{label_prefix}Refreshing project lifecycles..."})
        try:
            lifecycle_count = refresh_all_lifecycles(session, juris.id)
            session.commit()
        except Exception as e:
            session.rollback()
            source_doc.processing_notes = append_processing_note(
                source_doc.processing_notes,
                f"Lifecycle refresh failed (non-fatal): {e}",
            )
            session.commit()
            yield _send({
                "step": 8,
                "total": 8,
                "label": f"{label_prefix}Refreshing project lifecycles...",
                "detail": f"Lifecycle refresh failed (non-fatal): {e}",
                "status": "done",
            })
        else:
            yield _send({
                "step": 8,
                "total": 8,
                "label": f"{label_prefix}Refreshing project lifecycles...",
                "detail": f"Updated lifecycle for {lifecycle_count} projects",
                "status": "done",
            })
    else:
        # Dry run: emit placeholder step 7/8 messages
        for step_no, label in ((7, "Matching agenda to minutes..."), (8, "Refreshing project lifecycles...")):
            yield _send({
                "step": step_no,
                "total": 8,
                "label": f"{label_prefix}{label}",
                "detail": "Dry run — skipped.",
                "status": "done",
            })

    removed = [d["item"] for d in filter_decisions if not d["passed"]]
    yield _send(
        {
            "done": True,
            "metrics": {
                "extracted": len(items),
                "passed": len(filtered_items),
                "projects": counts["projects"],
                "actions": counts["entitlement_actions"],
                "agenda_minutes_links": match_count,
                "lifecycles_updated": lifecycle_count,
            },
            "items": filtered_items,
            "filtered_out": removed,
        }
    )


@router.post("")
async def process(
    file: UploadFile,
    doc_type: str = Form("agenda"),
    jurisdiction: str | None = Form(None),
    skip_filter: str | None = Form(None),
    dry_run: str | None = Form(None),
    override_date: str | None = Form(None),
    db: Session = Depends(get_db),
):
    if not file or not file.filename:
        return _json_error("No file uploaded")

    try:
        doc_type_v = validate_doc_type(doc_type)
        jurisdiction_slug = jurisdiction or None
        if jurisdiction_slug == "auto":
            jurisdiction_slug = None
        skip_filter_v = skip_filter == "on"
        dry_run_v = dry_run == "on"
        override_date_v = validate_iso_date(override_date, "Override date")
    except IntakeValidationError as exc:
        return _json_error(str(exc))

    filename = file.filename
    suffix = os.path.splitext(filename)[1] or ".upload"
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    content = await file.read()
    tmp.write(content)
    tmp_path = tmp.name
    tmp.close()

    try:
        file_format = validate_document_file(tmp_path, filename)
        if jurisdiction_slug:
            get_jurisdiction(db, jurisdiction_slug)
    except IntakeValidationError as exc:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        return _json_error(str(exc))

    def generate():
        # SSE streams outlive a single request-scoped session dependency, so
        # we open a fresh session for the generator and close it at the end.
        session = SessionLocal()
        try:
            yield from process_document(
                session,
                tmp_path,
                filename,
                file_format,
                jurisdiction_slug,
                doc_type_v,
                skip_filter_v,
                dry_run_v,
                override_date_v,
            )
        except Exception as e:
            session.rollback()
            yield _send({"error": f"Unexpected error: {e}"})
        finally:
            session.close()
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
