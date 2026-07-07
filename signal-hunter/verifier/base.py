"""
Signal Hunter Base Verifier.

Filters research items against quality rules and minimum confidence score thresholds.
"""

from abc import abstractmethod
from typing import List
from models.research_item import ResearchItem
from pipeline.base import BasePipelineStage


class BaseVerifier(BasePipelineStage):
    """
    Abstract base class for verifying research items.
    """

    @abstractmethod
    def process(self, items: List[ResearchItem]) -> List[ResearchItem]:
        """
        Verify incoming research items.

        Args:
            items (List[ResearchItem]): Normalized research items.

        Returns:
            List[ResearchItem]: Verified research items.

        Raises:
            VerificationError: If verification checks fail.
        """
        pass
