"""Base classes for document-to-text converters.

Ported from Commission Radar. The concrete converters (PDF/HTML/DOCX) are
still stubs in the unified app, but ``collection_review`` and other early
pipeline code depend on the shared ``DocumentConverter`` / ``ConversionResult``
contract, so the base module ships first.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

EMPTY_TEXT_THRESHOLD = 50
THIN_TEXT_WARNING_THRESHOLD = 200
EMPTY_CONVERSION_CODE = "conversion_empty"
EMPTY_CONVERSION_WARNING = "Extracted text is effectively empty."


def normalize_conversion_metadata(metadata: dict | None = None) -> dict:
    """Normalize conversion metadata to the shared contract."""
    normalized = dict(metadata or {})
    return {
        "quality": normalized.get("quality", "ok"),
        "warnings": list(normalized.get("warnings", [])),
        "warning_codes": list(normalized.get("warning_codes", [])),
        "stats": dict(normalized.get("stats", {})),
    }


def build_conversion_metadata(
    text: str,
    *,
    stats: dict | None = None,
    warnings: list[tuple[str, str]] | None = None,
) -> dict:
    """Build normalized conversion metadata with shared quality defaults."""
    stats_dict = dict(stats or {})
    warning_pairs: list[tuple[str, str]] = []
    seen_pairs: set[tuple[str, str]] = set()

    for code, message in warnings or []:
        pair = (code, message)
        if pair not in seen_pairs:
            warning_pairs.append(pair)
            seen_pairs.add(pair)

    stripped_text = text.strip()
    stripped_length = len(stripped_text)
    stats_dict.setdefault("text_length", len(text))
    stats_dict.setdefault("stripped_text_length", stripped_length)

    if stripped_length < EMPTY_TEXT_THRESHOLD and (EMPTY_CONVERSION_CODE, EMPTY_CONVERSION_WARNING) not in seen_pairs:
        warning_pairs.append((EMPTY_CONVERSION_CODE, EMPTY_CONVERSION_WARNING))

    quality = "empty" if stripped_length < EMPTY_TEXT_THRESHOLD else ("weak" if warning_pairs else "ok")
    return normalize_conversion_metadata({
        "quality": quality,
        "warnings": [message for _, message in warning_pairs],
        "warning_codes": [code for code, _ in warning_pairs],
        "stats": stats_dict,
    })


def format_conversion_detail(result: "ConversionResult") -> str:
    """Return a shared human-readable Step 1 summary."""
    if result.page_count is not None:
        detail = (
            f"{result.page_count} pages, {result.pages_after_dedup} after dedup, "
            f"{len(result.text):,} characters extracted"
        )
    else:
        detail = f"{len(result.text):,} characters extracted"

    warnings = result.metadata.get("warnings", [])
    if warnings:
        detail = f"{detail}. Warnings: {'; '.join(warnings)}"
    return detail


def format_conversion_warnings(metadata: dict) -> str:
    """Return conversion warnings as a readable note string."""
    warnings = normalize_conversion_metadata(metadata).get("warnings", [])
    return "; ".join(warnings)


@dataclass
class ConversionResult:
    """Result of converting a document to plain text."""
    text: str
    page_count: int | None = None
    pages_after_dedup: int | None = None
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        self.metadata = normalize_conversion_metadata(self.metadata)


class DocumentConverter(ABC):
    """Abstract base class for document-to-text converters."""

    @abstractmethod
    def convert(self, file_path: str, **kwargs) -> ConversionResult:
        """Convert a document file to plain text.

        Args:
            file_path: Path to the document file.
            **kwargs: Converter-specific options.

        Returns:
            ConversionResult with extracted text and metadata.
        """
        ...

    @staticmethod
    def for_format(file_format: str) -> "DocumentConverter":
        """Factory: return the right converter for a file format.

        Args:
            file_format: File extension without dot (e.g., "pdf", "html", "docx").

        Returns:
            DocumentConverter instance.

        Raises:
            ValueError: If the format is not supported or its concrete
                converter hasn't been ported to the unified app yet.
        """
        # Deferred imports so the base module loads even when the concrete
        # converters are not yet available in modules.commission.
        supported = ("pdf", "html", "htm", "docx")
        fmt = (file_format or "").lower()
        if fmt not in supported:
            raise ValueError(
                f"Unsupported document format: {file_format}. "
                f"Supported: {', '.join(supported)}"
            )

        try:
            if fmt == "pdf":
                from modules.commission.converters.pdf_converter import PdfConverter
                return PdfConverter()
            if fmt in {"html", "htm"}:
                from modules.commission.converters.html_converter import HtmlConverter
                return HtmlConverter()
            if fmt == "docx":
                from modules.commission.converters.docx_converter import DocxConverter
                return DocxConverter()
        except ImportError as exc:  # pragma: no cover - stub guard
            raise NotImplementedError(
                f"The {fmt!r} converter has not been ported to modules.commission yet."
            ) from exc

        raise ValueError(f"Unsupported document format: {file_format}")
