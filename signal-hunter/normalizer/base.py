"""
Signal Hunter Base Normalizer.

Standardizes fields of research items gathered from diverse collectors.
"""

from abc import abstractmethod
from typing import List
from models.research_item import ResearchItem
from pipeline.base import BasePipelineStage


class BaseNormalizer(BasePipelineStage):
    """
    Abstract base class for normalizing research items.
    """

    @abstractmethod
    def process(self, items: List[ResearchItem]) -> List[ResearchItem]:
        """
        Normalize incoming research items (e.g. standardizing URLs, dates, titles).

        Args:
            items (List[ResearchItem]): Raw collected research items.

        Returns:
            List[ResearchItem]: Standardized research items.

        Raises:
            NormalizationError: If standardizing fields fails.
        """
        pass
