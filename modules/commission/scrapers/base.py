from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class DocumentListing:
    """A document available for download from a government website."""
    title: str
    url: str
    date_str: str           # YYYY-MM-DD
    document_id: str        # platform-specific ID
    document_type: str      # "agenda" or "minutes"
    file_format: str        # "pdf", "html", "docx"
    filename: str           # suggested filename for local storage


class PlatformScraper(ABC):
    """Abstract base class for government website scrapers."""

    @abstractmethod
    def fetch_listings(self, config: dict, start_date: str, end_date: str) -> list[DocumentListing]:
        """Fetch available document listings from the platform.

        Args:
            config: Jurisdiction scraping config dict (from YAML).
            start_date: Start date YYYY-MM-DD.
            end_date: End date YYYY-MM-DD.

        Returns:
            List of DocumentListing objects.
        """
        ...

    @abstractmethod
    def download_document(self, listing: DocumentListing, output_dir: str) -> str:
        """Download a document to a local directory.

        Args:
            listing: DocumentListing to download.
            output_dir: Local directory to save to.

        Returns:
            Full local file path of the downloaded document.
        """
        ...

    @staticmethod
    def for_platform(platform: str) -> "PlatformScraper":
        """Factory: return the right scraper for a platform.

        Args:
            platform: Platform name (e.g., "civicplus", "granicus", "manual").

        Returns:
            PlatformScraper instance.

        Raises:
            ValueError: If the platform is not supported.
        """
        from modules.commission.scrapers.civicclerk import CivicClerkScraper
        from modules.commission.scrapers.civicplus import CivicPlusScraper
        from modules.commission.scrapers.legistar import LegistarScraper
        from modules.commission.scrapers.manual import ManualScraper
        from modules.commission.scrapers.novusagenda import NovusAgendaScraper

        scrapers = {
            "civicclerk": CivicClerkScraper,
            "civicplus": CivicPlusScraper,
            "legistar": LegistarScraper,
            "manual": ManualScraper,
            "novusagenda": NovusAgendaScraper,
        }
        cls = scrapers.get(platform)
        if cls is None:
            raise ValueError(f"Unsupported scraper platform: {platform}. "
                             f"Supported: {', '.join(scrapers.keys())}")
        return cls()
