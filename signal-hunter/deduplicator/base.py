"""
Signal Hunter Base Deduplicator.

Identifies and links duplicates or overlapping research items.
"""

from abc import abstractmethod
from typing import List
from models.research_item import ResearchItem
from pipeline.base import BasePipelineStage


class BaseDeduplicator(BasePipelineStage):
    """
    Abstract base class for deduplicating research items.
    """

    @abstractmethod
    def process(self, items: List[ResearchItem]) -> List[ResearchItem]:
        """
        Deduplicate incoming research items.

        Args:
            items (List[ResearchItem]): Verified research items.

        Returns:
            List[ResearchItem]: Deduplicated research items.

        Raises:
            DeduplicationError: If duplicate analysis fails.
        """
        pass
