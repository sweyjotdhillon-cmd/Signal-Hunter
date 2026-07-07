"""
Signal Hunter Deduplicator.

Identifies and links duplicate or overlapping research items.
"""

import logging
from typing import List, Set
from models.research_item import ResearchItem
from deduplicator.base import BaseDeduplicator
from utils.exceptions import DeduplicationError
from utils.logger import setup_logger


class PlaceholderDeduplicator(BaseDeduplicator):
    """
    Deduplicates research items based on title or URL similarity, setting 'duplicate_of' properties.
    """

    def __init__(self) -> None:
        """Initialize the deduplicator with setup logging."""
        self.logger: logging.Logger = setup_logger(
            "signal_hunter.deduplicator",
            log_level="INFO",
        )
        self.logger.info("Initialized PlaceholderDeduplicator")

    def process(self, items: List[ResearchItem]) -> List[ResearchItem]:
        """
        Deduplicate research items. Matches existing titles and URLs to spot duplicates.

        Args:
            items (List[ResearchItem]): List of items to deduplicate.

        Returns:
            List[ResearchItem]: List of items with 'duplicate_of' field populated for duplicates.

        Raises:
            DeduplicationError: If processing encounters an unexpected error.
        """
        if items is None:
            raise DeduplicationError("Items list cannot be None")

        self.logger.info("Starting deduplication stage on %d items", len(items))
        processed_items: List[ResearchItem] = []
        seen_titles: Set[str] = set()
        seen_urls: Set[str] = set()

        # Map to find original unique item id by title or url
        title_to_id = {}
        url_to_id = {}

        for item in items:
            try:
                self.logger.debug("Checking duplicates for item: '%s' (ID: %s)", item.title, item.id)

                norm_title = item.title.strip().lower()
                norm_url = item.url.strip().lower()

                is_duplicate = False
                duplicate_ref_id = None

                if norm_title in seen_titles:
                    is_duplicate = True
                    duplicate_ref_id = title_to_id[norm_title]
                elif norm_url in seen_urls:
                    is_duplicate = True
                    duplicate_ref_id = url_to_id[norm_url]

                if is_duplicate:
                    self.logger.info(
                        "Found duplicate item: [%s] (ID: %s) is duplicate of (ID: %s)",
                        item.title,
                        item.id,
                        duplicate_ref_id,
                    )
                    # Never modify unrelated fields; edit only duplicate_of
                    item.duplicate_of = duplicate_ref_id
                else:
                    seen_titles.add(norm_title)
                    seen_urls.add(norm_url)
                    title_to_id[norm_title] = item.id
                    url_to_id[norm_url] = item.id
                    item.duplicate_of = None

                processed_items.append(item)
            except Exception as e:
                self.logger.error("Failed during deduplication of item %s: %s", getattr(item, "id", "Unknown"), e)
                raise DeduplicationError(f"Deduplication processing failed: {e}") from e

        self.logger.info("Completed deduplication stage. Total items processed: %d", len(processed_items))
        return processed_items
