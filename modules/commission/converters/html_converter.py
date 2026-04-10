import re

from bs4 import BeautifulSoup

from modules.commission.converters.base import (
    DocumentConverter,
    ConversionResult,
    EMPTY_TEXT_THRESHOLD,
    THIN_TEXT_WARNING_THRESHOLD,
    build_conversion_metadata,
)


# Tags to remove entirely (content and all)
REMOVE_TAGS = {"script", "style", "nav", "aside", "noscript"}


class HtmlConverter(DocumentConverter):
    """Convert HTML documents to plain text using BeautifulSoup."""

    def convert(self, file_path: str, **kwargs) -> ConversionResult:
        """Extract text from an HTML file.

        Strips scripts, styles, navigation, headers, and footers.
        Extracts readable body text with normalized whitespace.

        Args:
            file_path: Path to the HTML file.

        Returns:
            ConversionResult with extracted text.
        """
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            html_content = f.read()

        soup = BeautifulSoup(html_content, "html.parser")

        # Remove unwanted tags entirely
        for tag in soup.find_all(REMOVE_TAGS):
            tag.decompose()

        target, target_label = self._select_target(soup)

        for item in target.find_all("li"):
            if item.string and item.string.strip():
                item.string.replace_with(f"- {item.string.strip()}")

        # Get text with newlines between block elements
        text = target.get_text(separator="\n")

        # Normalize whitespace: collapse multiple blank lines, strip trailing spaces
        text = re.sub(r"[ \t]+", " ", text)  # collapse horizontal whitespace
        text = re.sub(r"\n{3,}", "\n\n", text)  # max 2 newlines in a row
        text = "\n".join(line.strip() for line in text.splitlines())
        text = text.strip()
        non_empty_lines = [line for line in text.splitlines() if line.strip()]

        warnings = []
        stripped_length = len(text.strip())
        if EMPTY_TEXT_THRESHOLD <= stripped_length < THIN_TEXT_WARNING_THRESHOLD:
            warnings.append((
                "html_thin_text",
                "HTML content was extracted, but the text is unusually thin.",
            ))

        metadata = build_conversion_metadata(
            text,
            stats={
                "target": target_label,
                "line_count": len(non_empty_lines),
            },
            warnings=warnings,
        )

        return ConversionResult(
            text=text,
            page_count=None,
            pages_after_dedup=None,
            metadata=metadata,
        )

    def _select_target(self, soup):
        """Choose the most likely main content container."""
        target = soup.find("main")
        if target:
            return target, "main"

        target = soup.find(attrs={"role": "main"})
        if target:
            return target, "role=main"

        target = soup.find("article")
        if target:
            return target, "article"

        target = soup.find("body")
        if target:
            return target, "body"

        return soup, "document"
