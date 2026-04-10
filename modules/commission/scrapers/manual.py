import logging

from modules.commission.scrapers.base import PlatformScraper, DocumentListing

logger = logging.getLogger("commission_radar.scrapers.manual")


class ManualScraper(PlatformScraper):
    """No-op scraper for jurisdictions that require manual document upload.

    Returns empty listings. Documents are processed via the CLI `process` command.
    """

    def fetch_listings(self, config: dict, start_date: str, end_date: str) -> list[DocumentListing]:
        """Returns empty list — manual jurisdictions don't support scraping."""
        logger.info("Manual scraper: no automated listings available. Use 'process' command.")
        return []

    def download_document(self, listing: DocumentListing, output_dir: str) -> str:
        """Not supported for manual scraper."""
        raise NotImplementedError("Manual scraper does not support downloading. "
                                  "Use the 'process' command to process local files.")
