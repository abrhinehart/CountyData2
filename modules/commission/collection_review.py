from dataclasses import dataclass
from datetime import date

import pdfplumber

from modules.commission.converters.base import DocumentConverter
from modules.commission.constants import PRIMARY_AGENDA_MAX_PAGES, PRIMARY_DOCUMENT_PACKET_TERMS
from modules.commission.models import (
    SOURCE_DOCUMENT_STATUS_COMPLETED,
    SOURCE_DOCUMENT_STATUS_EXTRACTION_FAILED,
    SOURCE_DOCUMENT_STATUS_FILTERED_OUT,
    SOURCE_DOCUMENT_STATUS_FLAGGED_FOR_REVIEW,
    SOURCE_DOCUMENT_STATUS_REVIEW_REJECTED,
    CrSourceDocument as SourceDocument,
)
from modules.commission.utils import append_processing_note, compute_file_hash

COLLECTION_REVIEW_OUTCOME_SAFE_TO_PROCESS = "safe_to_process"
COLLECTION_REVIEW_OUTCOME_AMBIGUOUS = "ambiguous"
COLLECTION_REVIEW_OUTCOME_FLAG_FOR_REVIEW = "flag_for_review"
PRIMARY_PDF_PREVIEW_PAGES = 3
PRIMARY_PDF_PREVIEW_CHARS = 4_000
AGENDA_PREVIEW_TERMS = (
    "regular meeting",
    "special meeting",
    "work session",
    "public hearing",
    "call to order",
    "roll call",
    "planning board",
    "planning commission",
    "planning and zoning commission",
    "board of county commissioners",
    "city commission",
    "county commission",
)
MINUTES_PREVIEW_TERMS = (
    "minutes",
    "call to order",
    "roll call",
    "approval of minutes",
    "adjournment",
    "motion",
)


@dataclass(frozen=True)
class CollectionReviewInspection:
    outcome: str | None = None
    page_count: int | None = None
    review_reason: str | None = None
    audit_note: str | None = None

    @property
    def is_safe_to_process(self) -> bool:
        if self.outcome is None:
            return not bool(self.review_reason)
        return self.outcome == COLLECTION_REVIEW_OUTCOME_SAFE_TO_PROCESS

    @property
    def is_ambiguous(self) -> bool:
        return self.outcome == COLLECTION_REVIEW_OUTCOME_AMBIGUOUS

    @property
    def is_flag_for_review(self) -> bool:
        return self.outcome == COLLECTION_REVIEW_OUTCOME_FLAG_FOR_REVIEW

    @property
    def requires_review(self) -> bool:
        if self.outcome is None:
            return bool(self.review_reason)
        return self.outcome != COLLECTION_REVIEW_OUTCOME_SAFE_TO_PROCESS


def _normalize_text(value: str | None) -> str:
    if not value:
        return ""
    return " ".join(value.strip().lower().split())


def _packet_name_reason(*candidates: str | None) -> str | None:
    haystack = " ".join(_normalize_text(candidate) for candidate in candidates if candidate)
    if not haystack:
        return None

    for term in PRIMARY_DOCUMENT_PACKET_TERMS:
        if term in haystack:
            return f"Listing appears to be an agenda packet based on its title/filename ({term})."
    return None


def _pdf_page_count(file_path: str) -> int:
    with pdfplumber.open(file_path) as pdf:
        return len(pdf.pages)


def _pdf_page_count_and_preview(file_path: str) -> tuple[int, str]:
    with pdfplumber.open(file_path) as pdf:
        page_count = len(pdf.pages)
        preview_parts = []
        preview_chars = 0

        for page in pdf.pages[:PRIMARY_PDF_PREVIEW_PAGES]:
            page_text = (page.extract_text() or "").strip()
            if not page_text:
                continue
            preview_parts.append(page_text)
            preview_chars += len(page_text)
            if preview_chars >= PRIMARY_PDF_PREVIEW_CHARS:
                break

    return page_count, "\n\n".join(preview_parts)


def _primary_document_preview(file_path: str, file_format: str) -> tuple[int | None, str]:
    if file_format == "pdf":
        return _pdf_page_count_and_preview(file_path)

    if file_format in {"html", "htm", "docx"}:
        result = DocumentConverter.for_format(file_format).convert(file_path)
        return result.page_count, result.text[:PRIMARY_PDF_PREVIEW_CHARS]

    return None, ""


def _preview_lines(preview_text: str) -> list[str]:
    return [line.strip().lower() for line in preview_text.splitlines() if line.strip()]


def _preview_has_packet_cue(preview_text: str) -> bool:
    normalized = _normalize_text(preview_text)
    return any(term in normalized for term in PRIMARY_DOCUMENT_PACKET_TERMS)


def _preview_has_agenda_cue(preview_text: str) -> bool:
    lines = _preview_lines(preview_text)[:20]
    if any(line == "agenda" or line.endswith(" agenda") for line in lines):
        return True
    return any(any(term in line for term in AGENDA_PREVIEW_TERMS) for line in lines)


def _preview_has_minutes_cue(preview_text: str) -> bool:
    lines = _preview_lines(preview_text)[:20]
    if any(line == "minutes" or line.endswith(" minutes") for line in lines):
        return True
    return any(any(term in line for term in MINUTES_PREVIEW_TERMS) for line in lines)


def _doc_type_preview_has_cue(preview_text: str, doc_type: str) -> bool:
    if doc_type == "minutes":
        return _preview_has_minutes_cue(preview_text)
    return _preview_has_agenda_cue(preview_text)


def should_queue_collection_review(inspection: CollectionReviewInspection) -> bool:
    if inspection.outcome == COLLECTION_REVIEW_OUTCOME_SAFE_TO_PROCESS:
        return False
    if inspection.outcome in {
        COLLECTION_REVIEW_OUTCOME_AMBIGUOUS,
        COLLECTION_REVIEW_OUTCOME_FLAG_FOR_REVIEW,
    }:
        return True
    return bool(inspection.review_reason)


def inspect_primary_document_for_collection_review(
    file_path: str,
    file_format: str,
    doc_type: str,
    *,
    filename: str | None = None,
    listing_title: str | None = None,
) -> CollectionReviewInspection:
    """Decide whether a scraped primary document should be held for manual review."""
    name_reason = _packet_name_reason(filename, listing_title)
    page_count = None
    preview_text = ""

    if doc_type in {"agenda", "minutes"}:
        page_count, preview_text = _primary_document_preview(file_path, file_format)
        has_preview_cue = _doc_type_preview_has_cue(preview_text, doc_type)
        has_packet_cue = _preview_has_packet_cue(preview_text)
        is_oversized_agenda = (
            doc_type == "agenda"
            and page_count is not None
            and page_count >= PRIMARY_AGENDA_MAX_PAGES
        )

        if has_preview_cue and not has_packet_cue:
            note_fragments = []
            if name_reason:
                note_fragments.append("packet-like title/filename")
            if is_oversized_agenda:
                note_fragments.append(
                    f"{page_count}-page agenda exceeding the usual {PRIMARY_AGENDA_MAX_PAGES}-page limit"
                )
            audit_note = None
            if note_fragments:
                joined = " and ".join(note_fragments)
                audit_note = (
                    "Collection review allowed automatic processing after sampling the first "
                    f"{PRIMARY_PDF_PREVIEW_PAGES} pages. The document looked like a standalone {doc_type} "
                    f"despite {joined}."
                )
            return CollectionReviewInspection(
                outcome=COLLECTION_REVIEW_OUTCOME_SAFE_TO_PROCESS,
                page_count=page_count,
                audit_note=audit_note,
            )

        if has_preview_cue and has_packet_cue:
            return CollectionReviewInspection(
                outcome=COLLECTION_REVIEW_OUTCOME_AMBIGUOUS,
                page_count=page_count,
                review_reason=(
                    "Primary document preview mixes packet and agenda cues; manual review is needed."
                ),
            )

        if has_packet_cue or name_reason:
            reason_parts = []
            if name_reason:
                reason_parts.append(name_reason)
            if is_oversized_agenda:
                reason_parts.append(
                    f"Agenda has {page_count} pages, exceeding the {PRIMARY_AGENDA_MAX_PAGES}-page auto-processing limit."
                )
            reason_parts.append("Primary document preview looks packet-like.")
            return CollectionReviewInspection(
                outcome=COLLECTION_REVIEW_OUTCOME_FLAG_FOR_REVIEW,
                page_count=page_count,
                review_reason=" ".join(reason_parts),
            )

        if is_oversized_agenda:
            return CollectionReviewInspection(
                outcome=COLLECTION_REVIEW_OUTCOME_AMBIGUOUS,
                page_count=page_count,
                review_reason=(
                    f"Agenda has {page_count} pages and the first few pages were inconclusive; manual review is needed."
                ),
            )

        return CollectionReviewInspection(
            outcome=COLLECTION_REVIEW_OUTCOME_AMBIGUOUS,
            page_count=page_count,
            review_reason=(
                f"Primary {doc_type} preview is inconclusive; manual review is needed."
            ),
        )

    if name_reason:
        return CollectionReviewInspection(
            outcome=COLLECTION_REVIEW_OUTCOME_AMBIGUOUS,
            page_count=page_count,
            review_reason=name_reason,
        )

    return CollectionReviewInspection(
        outcome=COLLECTION_REVIEW_OUTCOME_SAFE_TO_PROCESS,
        page_count=page_count,
    )


def inspect_listing_for_collection_review(
    doc_type: str,
    *,
    filename: str | None = None,
    listing_title: str | None = None,
) -> CollectionReviewInspection:
    """Preview whether a listing should likely be held for review before download."""
    if doc_type not in {"agenda", "minutes"}:
        return CollectionReviewInspection(outcome=COLLECTION_REVIEW_OUTCOME_SAFE_TO_PROCESS)

    name_reason = _packet_name_reason(filename, listing_title)
    if name_reason:
        return CollectionReviewInspection(
            outcome=COLLECTION_REVIEW_OUTCOME_AMBIGUOUS,
            review_reason=(
                f"{name_reason} The downloaded document will be re-checked before it is queued for manual review."
            ),
        )

    return CollectionReviewInspection(outcome=COLLECTION_REVIEW_OUTCOME_SAFE_TO_PROCESS)


def flag_source_document_for_review(
    session,
    *,
    jurisdiction_id: int,
    file_path: str,
    filename: str,
    file_format: str,
    doc_type: str,
    meeting_date: str | None,
    source_url: str | None,
    external_document_id: str | None,
    inspection: CollectionReviewInspection,
) -> SourceDocument:
    """Persist a scraped document that was collected but held for human review."""
    source_doc = SourceDocument(
        jurisdiction_id=jurisdiction_id,
        filename=filename,
        file_hash=compute_file_hash(file_path),
        source_url=source_url,
        external_document_id=external_document_id,
        file_format=file_format,
        document_type=doc_type,
        meeting_date=date.fromisoformat(meeting_date) if meeting_date else None,
        page_count=inspection.page_count,
        extracted_text_length=None,
        processing_status=SOURCE_DOCUMENT_STATUS_FLAGGED_FOR_REVIEW,
        failure_stage="collection_review",
        failure_reason=inspection.review_reason,
        processing_notes=append_processing_note(
            None,
            f"Flagged for manual review before processing: {inspection.review_reason}",
        ),
    )
    session.add(source_doc)
    session.flush()
    return source_doc


def source_document_status_label(
    source_doc_or_status: SourceDocument | str | None,
    *,
    duplicate_reason: str | None = None,
) -> str:
    if isinstance(source_doc_or_status, SourceDocument):
        status = source_doc_or_status.processing_status
    else:
        status = source_doc_or_status

    if status is None:
        return "new"

    if status == SOURCE_DOCUMENT_STATUS_COMPLETED:
        return f"processed ({duplicate_reason or 'duplicate'})"
    if status == SOURCE_DOCUMENT_STATUS_FILTERED_OUT:
        return "filtered out"
    if status == SOURCE_DOCUMENT_STATUS_EXTRACTION_FAILED:
        return "extraction failed"
    if status == SOURCE_DOCUMENT_STATUS_FLAGGED_FOR_REVIEW:
        return "needs manual review"
    if status == SOURCE_DOCUMENT_STATUS_REVIEW_REJECTED:
        return "review rejected"
    return status or "existing"
