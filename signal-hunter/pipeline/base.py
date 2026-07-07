"""
Signal Hunter Base Pipeline Stage.

Defines the abstract contract for all processing steps in the pipeline.
"""

from abc import ABC, abstractmethod
from typing import List
from models.research_item import ResearchItem


class BasePipelineStage(ABC):
    """
    Abstract base class for all Signal Hunter pipeline processing stages.
    """

    @abstractmethod
    def process(self, items: List[ResearchItem]) -> List[ResearchItem]:
        """
        Process a list of ResearchItem objects and return a list of ResearchItem objects.

        Args:
            items (List[ResearchItem]): Inbound research items to process.

        Returns:
            List[ResearchItem]: Outbound processed research items.

        Raises:
            SignalHunterError: Custom exceptions on failure.
        """
        pass
