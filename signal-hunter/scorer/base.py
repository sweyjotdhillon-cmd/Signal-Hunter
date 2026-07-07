"""
Signal Hunter Base Scorer.

Evaluates research items across various strategic score dimensions.
"""

from abc import abstractmethod
from typing import List
from models.research_item import ResearchItem
from pipeline.base import BasePipelineStage


class BaseScorer(BasePipelineStage):
    """
    Abstract base class for scoring research items.
    """

    @abstractmethod
    def process(self, items: List[ResearchItem]) -> List[ResearchItem]:
        """
        Score incoming research items.

        Args:
            items (List[ResearchItem]): Deduplicated research items.

        Returns:
            List[ResearchItem]: Scored research items.

        Raises:
            ScoringError: If evaluation or math formulas fail.
        """
        pass
