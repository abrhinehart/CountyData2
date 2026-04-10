import hashlib

import pdfplumber

from modules.commission.converters.base import (
    DocumentConverter,
    ConversionResult,
    build_conversion_metadata,
)


class PdfConverter(DocumentConverter):
    """Convert PDF documents to plain text using pdfplumber."""

    def convert(self, file_path: str, **kwargs) -> ConversionResult:
        """Extract text from a PDF file.

        Args:
            file_path: Path to the PDF file.
            deduplicate_pages: If True, skip pages with identical text content.
                Handles the CivicPlus duplicate-page bug. Default False.
            max_pages: If set, only extract text from the first N pages.

        Returns:
            ConversionResult with extracted text, page counts.
        """
        deduplicate_pages = kwargs.get("deduplicate_pages", False)
        max_pages = kwargs.get("max_pages")

        seen_hashes = set()
        pages_text = []
        total_pages = 0
        page_lengths = []

        with pdfplumber.open(file_path) as pdf:
            total_pages = len(pdf.pages)
            pages_to_read = pdf.pages if max_pages is None else pdf.pages[:max_pages]
            for page in pages_to_read:
                page_text = page.extract_text() or ""
                page_lengths.append(len(page_text.strip()))

                if deduplicate_pages:
                    page_hash = hashlib.sha256(page_text.encode("utf-8")).hexdigest()
                    if page_hash in seen_hashes:
                        continue
                    seen_hashes.add(page_hash)

                pages_text.append(page_text)

        full_text = "\n\n".join(pages_text)
        non_empty_pages = sum(1 for length in page_lengths if length > 0)
        blank_pages = total_pages - non_empty_pages
        dedup_removed_pages = max(total_pages - len(pages_text), 0)
        avg_chars_per_page = (sum(page_lengths) / total_pages) if total_pages else 0.0

        warnings = []
        if total_pages >= 2 and avg_chars_per_page < 80:
            warnings.append((
                "pdf_low_text",
                "PDF text is unusually thin for a multi-page document.",
            ))
        if total_pages > 0 and (blank_pages / total_pages) >= 0.5:
            warnings.append((
                "pdf_many_blank_pages",
                "PDF has many blank or unreadable pages.",
            ))
        if total_pages > 0 and dedup_removed_pages / total_pages >= 0.25:
            warnings.append((
                "pdf_heavy_dedup",
                "Duplicate-page cleanup removed a large share of pages.",
            ))

        metadata = build_conversion_metadata(
            full_text,
            stats={
                "total_pages": total_pages,
                "non_empty_pages": non_empty_pages,
                "blank_pages": blank_pages,
                "avg_chars_per_page": round(avg_chars_per_page, 1),
                "dedup_removed_pages": dedup_removed_pages,
            },
            warnings=warnings,
        )

        return ConversionResult(
            text=full_text,
            page_count=total_pages,
            pages_after_dedup=len(pages_text),
            metadata=metadata,
        )
