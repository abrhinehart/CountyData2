"""Document intake helpers (validation, duplicate detection, jurisdiction lookup).

Ported from Commission Radar. In the unified schema, commission-specific
jurisdiction fields (``agenda_source_url``, ``agenda_platform``,
``has_duplicate_page_bug``, ``config_json``) live on
``CrJurisdictionConfig`` rather than directly on ``Jurisdiction``. This
module exposes a ``JurisdictionView`` adapter that joins those tables so
downstream callers keep working with a single object.
"""

import json
import os
import re
import zipfile
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path

from modules.commission.models import (
    CrJurisdictionConfig,
    CrSourceDocument as SourceDocument,
    Jurisdiction,
)

SUPPORTED_FILE_FORMATS = ("pdf", "html", "htm", "docx")
SUPPORTED_DOC_TYPES = ("agenda", "minutes")
UPLOAD_ACCEPT = ",".join(f".{ext}" for ext in SUPPORTED_FILE_FORMATS)

_HTML_TAG_RE = re.compile(
    r"<(?:!doctype\s+html|html|head|body|meta|title|main|section|article|div|p|table|span|style|script)\b",
    re.IGNORECASE,
)


class IntakeValidationError(ValueError):
    """Raised when a document entry request fails validation."""


@dataclass(frozen=True)
class DuplicateMatch:
    field_name: str
    reason: str
    matched_value: str
    existing_id: int
    existing_filename: str
    existing_status: str | None = None
    existing_failure_reason: str | None = None


@dataclass
class JurisdictionView:
    """Convenience wrapper that exposes the old CR Jurisdiction shape.

    In the unified schema, commission-specific fields live on
    ``CrJurisdictionConfig``. Code ported from Commission Radar still expects
    a single ``jurisdiction`` object with ``agenda_source_url``,
    ``agenda_platform``, ``config``, etc. This adapter joins the two rows.
    """

    jurisdiction: Jurisdiction
    cr_config: CrJurisdictionConfig | None

    @property
    def id(self) -> int:
        return self.jurisdiction.id

    @property
    def name(self) -> str:
        return self.jurisdiction.name

    @property
    def slug(self) -> str | None:
        return self.jurisdiction.slug

    @property
    def agenda_source_url(self) -> str | None:
        return getattr(self.cr_config, "agenda_source_url", None)

    @property
    def agenda_platform(self) -> str | None:
        return getattr(self.cr_config, "agenda_platform", None)

    @property
    def commission_type(self) -> str | None:
        return getattr(self.cr_config, "commission_type", None)

    @property
    def has_duplicate_page_bug(self) -> bool:
        return bool(getattr(self.cr_config, "has_duplicate_page_bug", False))

    @property
    def pinned(self) -> bool:
        return bool(getattr(self.cr_config, "pinned", False))

    @property
    def config(self) -> dict:
        raw = getattr(self.cr_config, "config_json", None)
        if not raw:
            return {}
        try:
            loaded = json.loads(raw)
            return loaded if isinstance(loaded, dict) else {}
        except (TypeError, ValueError):
            return {}


def _wrap_jurisdiction(session, jurisdiction: Jurisdiction) -> JurisdictionView:
    cr_config = (
        session.query(CrJurisdictionConfig)
        .filter(CrJurisdictionConfig.jurisdiction_id == jurisdiction.id)
        .first()
    )
    return JurisdictionView(jurisdiction=jurisdiction, cr_config=cr_config)


def default_scrape_date_range(now: datetime | None = None) -> tuple[str, str]:
    current_time = now or datetime.now()
    end_date = current_time.date()
    start_date = end_date - timedelta(days=30)
    return start_date.isoformat(), end_date.isoformat()


def normalize_file_format(value: str) -> str:
    normalized = value.lower().lstrip(".")
    if normalized == "htm":
        return "html"
    if normalized not in {"pdf", "html", "docx"}:
        raise IntakeValidationError(
            "Unsupported file type. Supported extensions: .pdf, .html, .htm, .docx."
        )
    return normalized


def detect_file_format(filename: str) -> str:
    suffix = Path(filename).suffix
    if not suffix:
        raise IntakeValidationError(
            "Document must include a file extension: .pdf, .html, .htm, or .docx."
        )
    return normalize_file_format(suffix)


def validate_doc_type(doc_type: str | None) -> str:
    normalized = (doc_type or "agenda").strip().lower()
    if normalized not in SUPPORTED_DOC_TYPES:
        raise IntakeValidationError("Document type must be 'agenda' or 'minutes'.")
    return normalized


def validate_iso_date(value: str | None, field_name: str) -> str | None:
    if value is None or not value.strip():
        return None

    candidate = value.strip()
    try:
        return date.fromisoformat(candidate).isoformat()
    except ValueError as exc:
        raise IntakeValidationError(f"{field_name} must be in YYYY-MM-DD format.") from exc


def validate_scrape_date_range(start_date: str | None, end_date: str | None) -> tuple[str, str]:
    default_start, default_end = default_scrape_date_range()
    validated_start = validate_iso_date(start_date or default_start, "Start date")
    validated_end = validate_iso_date(end_date or default_end, "End date")

    if validated_start is None or validated_end is None:
        raise IntakeValidationError("Start date and end date are required.")
    if validated_start > validated_end:
        raise IntakeValidationError("Start date must be on or before end date.")

    return validated_start, validated_end


def validate_document_file(file_path: str, filename: str | None = None) -> str:
    resolved_filename = filename or os.path.basename(file_path)
    expected_format = detect_file_format(resolved_filename)
    sniffed_format = sniff_document_content(file_path)

    if sniffed_format != expected_format:
        raise IntakeValidationError(
            f"File content does not match the .{Path(resolved_filename).suffix.lstrip('.').lower()} extension. "
            f"Expected {expected_format.upper()} content."
        )

    return expected_format


def sniff_document_content(file_path: str) -> str:
    with open(file_path, "rb") as handle:
        sample = handle.read(8192)

    if not sample:
        raise IntakeValidationError("Uploaded file is empty.")

    if sample.startswith(b"%PDF-"):
        return "pdf"

    if zipfile.is_zipfile(file_path):
        with zipfile.ZipFile(file_path) as archive:
            names = set(archive.namelist())
        if "[Content_Types].xml" in names and "word/document.xml" in names:
            return "docx"
        raise IntakeValidationError(
            "Compressed file is not a supported DOCX document."
        )

    try:
        text_sample = sample.decode("utf-8", errors="ignore").lstrip("\ufeff\r\n\t ")
    except UnicodeDecodeError as exc:
        raise IntakeValidationError("Could not read document contents.") from exc

    if _HTML_TAG_RE.search(text_sample):
        return "html"

    raise IntakeValidationError(
        "Uploaded file is not a recognizable PDF, HTML, or DOCX document."
    )


def get_jurisdiction(session, slug_or_name: str | None, *, require_scrapable: bool = False) -> JurisdictionView | None:
    if not slug_or_name:
        return None

    jurisdiction = session.query(Jurisdiction).filter(
        (Jurisdiction.slug == slug_or_name) | (Jurisdiction.name == slug_or_name)
    ).first()
    if jurisdiction is None:
        raise IntakeValidationError(f"Jurisdiction '{slug_or_name}' was not found.")

    view = _wrap_jurisdiction(session, jurisdiction)

    if require_scrapable and not is_scrapable_jurisdiction(view):
        raise IntakeValidationError(
            f"Jurisdiction '{slug_or_name}' is not configured for scraping."
        )

    return view


def get_scrapable_jurisdictions(session, slug_or_name: str | None = None) -> list[JurisdictionView]:
    if slug_or_name:
        jurisdiction = get_jurisdiction(session, slug_or_name, require_scrapable=True)
        return [jurisdiction] if jurisdiction else []

    rows = (
        session.query(Jurisdiction, CrJurisdictionConfig)
        .join(CrJurisdictionConfig, CrJurisdictionConfig.jurisdiction_id == Jurisdiction.id)
        .filter(
            CrJurisdictionConfig.agenda_source_url.isnot(None),
            CrJurisdictionConfig.agenda_platform.isnot(None),
            CrJurisdictionConfig.agenda_platform != "manual",
        )
        .order_by(Jurisdiction.name)
        .all()
    )
    return [JurisdictionView(jurisdiction=juris, cr_config=cfg) for juris, cfg in rows]


def is_scrapable_jurisdiction(jurisdiction: JurisdictionView) -> bool:
    return bool(
        jurisdiction.agenda_source_url
        and jurisdiction.agenda_platform
        and jurisdiction.agenda_platform != "manual"
    )


def build_scrape_config(jurisdiction: JurisdictionView) -> dict:
    config = dict(jurisdiction.config) if jurisdiction.config else {}
    config["base_url"] = jurisdiction.agenda_source_url
    if "agenda_category_id" in config and "category_id" not in config:
        config["category_id"] = config["agenda_category_id"]
    return config


def normalize_external_document_id(platform: str | None, document_type: str, document_id: str | None) -> str | None:
    if document_id is None:
        return None

    normalized_document_id = str(document_id).strip()
    if not normalized_document_id:
        return None

    normalized_platform = (platform or "unknown").strip().lower() or "unknown"
    normalized_doc_type = validate_doc_type(document_type)
    return f"{normalized_platform}:{normalized_doc_type}:{normalized_document_id}"


def find_listing_duplicate(
    session,
    jurisdiction_id: int,
    *,
    platform: str | None,
    document_type: str,
    document_id: str | None,
    source_url: str | None,
    filename: str | None,
    exclude_source_document_id: int | None = None,
) -> DuplicateMatch | None:
    external_document_id = normalize_external_document_id(platform, document_type, document_id)
    return find_source_document_duplicate(
        session,
        jurisdiction_id=jurisdiction_id,
        external_document_id=external_document_id,
        source_url=source_url,
        filename=filename,
        exclude_source_document_id=exclude_source_document_id,
    )


def find_source_document_duplicate(
    session,
    *,
    jurisdiction_id: int,
    file_hash: str | None = None,
    external_document_id: str | None = None,
    source_url: str | None = None,
    filename: str | None = None,
    exclude_source_document_id: int | None = None,
) -> DuplicateMatch | None:
    checks = [
        ("file_hash", file_hash, "matching file hash"),
        ("external_document_id", external_document_id, "matching external document ID"),
        ("source_url", source_url, "matching source URL"),
        ("filename", filename, "matching filename"),
    ]

    for field_name, value, reason in checks:
        if not value:
            continue

        query = session.query(SourceDocument).filter_by(
            jurisdiction_id=jurisdiction_id,
            **{field_name: value},
        )
        if exclude_source_document_id is not None:
            query = query.filter(SourceDocument.id != exclude_source_document_id)
        existing = query.order_by(SourceDocument.id.asc()).first()
        if existing is not None:
            return DuplicateMatch(
                field_name=field_name,
                reason=reason,
                matched_value=value,
                existing_id=existing.id,
                existing_filename=existing.filename,
                existing_status=existing.processing_status,
                existing_failure_reason=existing.failure_reason,
            )

    return None
