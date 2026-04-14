"""Shared helpers used across commission FastAPI routers."""

import json
import os

from modules.commission.collection_review import source_document_status_label
from modules.commission.config import PDF_STORAGE_DIR
from modules.commission.converters.base import format_conversion_warnings


def _send(payload):
    """Format a Server-Sent Event line from a JSON-serialisable payload."""
    return f"data: {json.dumps(payload)}\n\n"


def _json_error(message, status_code=400):
    """Return a FastAPI-style JSONResponse error body.

    Flask blueprints used to return ``(jsonify(...), status)``. In FastAPI we
    build a ``JSONResponse`` directly so callers can simply ``return`` it.
    """
    from fastapi.responses import JSONResponse

    return JSONResponse(status_code=status_code, content={"error": message})


def _conversion_note(metadata):
    warning_text = format_conversion_warnings(metadata)
    if not warning_text:
        return None
    return f"Conversion warnings: {warning_text}"


def _duplicate_error_message(filename, duplicate):
    status = source_document_status_label(
        duplicate.existing_status,
        duplicate_reason=duplicate.reason,
    )
    return f"{filename} has already been collected for this jurisdiction ({status})."


def _document_storage_slug(jurisdiction):
    return jurisdiction.slug or jurisdiction.name.lower().replace(" ", "-")


def _source_document_file_path(jurisdiction, source_doc):
    return os.path.join(PDF_STORAGE_DIR, _document_storage_slug(jurisdiction), source_doc.filename)
