"""
Signal Hunter Scorer.

Evaluates research items across various strategic score dimensions.
"""

import logging
from typing import List
from models.research_item import ResearchItem
from scorer.base import BaseScorer
from utils.exceptions import ScoringError
from utils.logger import setup_logger


class PlaceholderScorer(BaseScorer):
    """
    Evaluates research quality metrics and calculates standardized score fields.
    """

    def __init__(self) -> None:
        """Initialize the scorer with setup logging."""
        self.logger: logging.Logger = setup_logger(
            "signal_hunter.scorer",
            log_level="INFO",
        )
        self.logger.info("Initialized PlaceholderScorer")

    def process(self, items: List[ResearchItem]) -> List[ResearchItem]:
        """
        Evaluate and calculate score parameters for each item.

        Args:
            items (List[ResearchItem]): List of items to score.

        Returns:
            List[ResearchItem]: Scored items.

        Raises:
            ScoringError: If scoring math or constraints fail.
        """
        if items is None:
            raise ScoringError("Items list cannot be None")

        self.logger.info("Starting scoring stage on %d items", len(items))
        scored_items: List[ResearchItem] = []

        for item in items:
            try:
                self.logger.debug("Scoring item: '%s' (ID: %s)", item.title, item.id)

                # Safe placeholder heuristics:
                # 1. Engineering score: higher if has github repository link
                eng_score = 0.5
                if item.github_repository:
                    eng_score += 0.3
                if "python" in item.programming_languages or "rust" in item.programming_languages:
                    eng_score += 0.1

                # 2. Scientific score: higher if preprint or from arXiv source
                sci_score = 0.4
                if item.source_type == "paper" or "arxiv" in item.url.lower():
                    sci_score += 0.4

                # 3. Opportunity score: higher if there are build opportunities or tags
                opp_score = 0.3
                if item.build_opportunities:
                    opp_score += 0.4
                opp_score += min(0.2, len(item.tags) * 0.05)

                # 4. Startup score: commercial viability
                startup_score = 0.4
                if item.seller_pitch:
                    startup_score += 0.3

                # 5. Novelty score
                novelty_score = 0.5
                if item.is_verified:
                    novelty_score += 0.2

                # 6. Overall confidence score
                conf_score = (eng_score + sci_score + opp_score) / 3.0

                # Check and clamp scores to ensure strict [0.0, 1.0] pydantic constraints
                eng_score = max(0.0, min(1.0, eng_score))
                sci_score = max(0.0, min(1.0, sci_score))
                opp_score = max(0.0, min(1.0, opp_score))
                startup_score = max(0.0, min(1.0, startup_score))
                novelty_score = max(0.0, min(1.0, novelty_score))
                conf_score = max(0.0, min(1.0, conf_score))

                # Update only scoring properties to avoid modifying unrelated fields
                item.engineering_score = eng_score
                item.scientific_score = sci_score
                item.opportunity_score = opp_score
                item.startup_score = startup_score
                item.novelty_score = novelty_score
                item.confidence_score = conf_score

                scored_items.append(item)
            except Exception as e:
                self.logger.error("Failed to evaluate scores for item %s: %s", getattr(item, "id", "Unknown"), e)
                raise ScoringError(f"Scoring evaluation aborted: {e}") from e

        self.logger.info("Completed scoring stage. Scored items count: %d", len(scored_items))
        return scored_items
