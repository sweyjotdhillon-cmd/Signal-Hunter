"""
Signal Hunter JSON File Storage.

Provides non-database structured storage saving ResearchItems in clean JSON files.
"""

import logging
import os
from typing import List, Optional

from config.config_loader import MemoryConfig
from models.research_item import ResearchItem
from utils.helpers import safe_read_json, safe_write_json


class JSONMemoryStore:
    """
    Local JSON-based transactional persistence store.

    Saves individual ResearchItems as file records in `{storage_dir}/items/{item_id}.json`.
    """

    def __init__(self, config: MemoryConfig) -> None:
        """
        Initialize the JSON Memory Store and create target storage folders.

        Args:
            config (MemoryConfig): Persistence directories and backup rules.
        """
        self.config = config
        self.logger: logging.Logger = setup_logger(
            "signal_hunter.memory",
            log_level="INFO",
        )

        # Build paths
        self.base_dir = self.config.storage_dir
        self.items_dir = os.path.join(self.base_dir, "items")

        # Guarantee folder existence
        os.makedirs(self.items_dir, exist_ok=True)
        self.logger.info("Initialized JSONMemoryStore. Storage directory: %s", self.items_dir)

    def save_item(self, item: ResearchItem) -> None:
        """
        Save or overwrite a ResearchItem in the storage database.

        Args:
            item (ResearchItem): Item record containing crawled and scored data.
        """
        filepath = os.path.join(self.items_dir, f"{item.id}.json")
        try:
            # Pydantic items can dump to dictionaries safely
            data = item.model_dump()
            # Handle datetime serializations
            data["collected_at"] = item.collected_at.isoformat()

            safe_write_json(filepath, data)
            self.logger.debug("Successfully persisted ResearchItem %s to %s", item.id, filepath)
        except Exception as e:
            self.logger.error("Failed to save ResearchItem %s: %s", item.id, e)
            raise OSError(f"Could not persist record: {e}") from e

    def get_item(self, item_id: str) -> Optional[ResearchItem]:
        """
        Retrieve a single ResearchItem by its hash ID.

        Args:
            item_id (str): Hash identifier.

        Returns:
            Optional[ResearchItem]: Loaded item, or None if missing or corrupted.
        """
        filepath = os.path.join(self.items_dir, f"{item_id}.json")
        data = safe_read_json(filepath)
        if not data:
            return None

        try:
            return ResearchItem(**data)
        except Exception as e:
            self.logger.error("Corrupted record found at %s: %s", filepath, e)
            return None

    def list_items(self, verified_only: bool = False) -> List[ResearchItem]:
        """
        Load and return all saved ResearchItem records.

        Args:
            verified_only (bool): If True, filters out unverified signals.

        Returns:
            List[ResearchItem]: List of active records loaded from disk.
        """
        items: List[ResearchItem] = []
        if not os.path.exists(self.items_dir):
            return items

        for filename in os.listdir(self.items_dir):
            if not filename.endswith(".json"):
                continue

            filepath = os.path.join(self.items_dir, filename)
            data = safe_read_json(filepath)
            if not data:
                continue

            try:
                item = ResearchItem(**data)
                if verified_only and not item.is_verified:
                    continue
                items.append(item)
            except Exception as e:
                self.logger.error("Failed to parse record %s during list: %s", filename, e)

        # Sort by newest collection date
        items.sort(key=lambda x: x.collected_at, reverse=True)
        return items

    def search_items(self, query: str) -> List[ResearchItem]:
        """
        Simple text search matching against item title, summary, or raw text.

        Args:
            query (str): Search term.

        Returns:
            List[ResearchItem]: Filtered list of matching records.
        """
        term = query.lower()
        results: List[ResearchItem] = []

        for item in self.list_items():
            if (
                term in item.title.lower()
                or (item.summary and term in item.summary.lower())
                or term in item.raw_content.lower()
            ):
                results.append(item)

        return results
