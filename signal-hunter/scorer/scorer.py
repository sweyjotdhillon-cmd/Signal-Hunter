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

        # List of high-value signal keywords to boost scientific or opportunity score
        high_value_keywords = {
            "llm", "transformer", "diffusion", "rag", "agent", "multimodal",
            "quantization", "distillation", "inference", "fine-tuning",
            "reasoning", "rlhf", "dpo", "moe", "gpu", "cuda"
        }

        for item in items:
            try:
                self.logger.debug("Scoring item: '%s' (ID: %s)", item.title, item.id)

                # Initialize base score levels
                eng_score = 0.4
                sci_score = 0.4
                opp_score = 0.4
                startup_score = 0.4
                novelty_score = 0.4

                title_lower = item.title.lower()
                summary_lower = (item.summary or "").lower()

                # 1. Source-based baseline adjustment
                if item.source_type == "code_repository":
                    eng_score += 0.25
                    opp_score += 0.15
                    sci_score -= 0.10
                elif item.source_type == "engineering_blog":
                    startup_score += 0.25
                    opp_score += 0.20
                    eng_score += 0.10
                elif item.source_type in ("preprint", "paper"):
                    sci_score += 0.30
                    novelty_score += 0.15

                # 2. Richness of metadata / AI analysis contributions
                if item.github_repository:
                    eng_score += 0.15
                if item.build_opportunities:
                    opp_score += min(0.20, len(item.build_opportunities) * 0.05)
                if item.why_it_matters:
                    opp_score += 0.10
                    novelty_score += 0.05
                if item.seller_pitch:
                    startup_score += 0.15
                if item.risks:
                    eng_score += 0.05

                # 3. High-value keyword boosting
                keywords_found = 0
                for kw in high_value_keywords:
                    if kw in title_lower or kw in summary_lower or any(kw in tag.lower() for tag in item.tags):
                        keywords_found += 1

                if keywords_found > 0:
                    boost = min(0.25, keywords_found * 0.05)
                    sci_score += boost
                    opp_score += boost
                    novelty_score += boost

                # 4. Social buzz / metric boosting (stars, forks, etc.)
                if item.raw_metadata:
                    stars = int(item.raw_metadata.get("stars", 0))
                    forks = int(item.raw_metadata.get("forks", 0))
                    if stars > 0:
                        # Logarithmic scale boost
                        import math
                        star_boost = min(0.20, math.log10(stars) * 0.05)
                        eng_score += star_boost
                        opp_score += star_boost
                        startup_score += star_boost
                    if forks > 0:
                        fork_boost = min(0.10, math.log10(forks) * 0.04)
                        eng_score += fork_boost

                # 5. Temporal boost: Newer items get a subtle novelty boost
                if item.publication_date:
                    from datetime import datetime, timezone
                    age_days = (datetime.now(timezone.utc) - item.publication_date.replace(tzinfo=timezone.utc)).days
                    if age_days >= 0:
                        # Younger than 7 days gets up to +0.10 boost
                        novelty_score += max(0.0, 0.10 - (age_days * 0.01))

                # Clamp scores to [0.1, 1.0] strictly
                eng_score = max(0.1, min(1.0, eng_score))
                sci_score = max(0.1, min(1.0, sci_score))
                opp_score = max(0.1, min(1.0, opp_score))
                startup_score = max(0.1, min(1.0, startup_score))
                novelty_score = max(0.1, min(1.0, novelty_score))

                # Overall confidence/opportunity compound score
                conf_score = (eng_score * 0.25) + (sci_score * 0.25) + (opp_score * 0.25) + (startup_score * 0.15) + (novelty_score * 0.10)
                conf_score = max(0.1, min(1.0, conf_score))

                # Update the pydantic model properties directly
                item.engineering_score = round(eng_score, 2)
                item.scientific_score = round(sci_score, 2)
                item.opportunity_score = round(opp_score, 2)
                item.startup_score = round(startup_score, 2)
                item.novelty_score = round(novelty_score, 2)
                item.confidence_score = round(conf_score, 2)

                scored_items.append(item)
            except Exception as e:
                self.logger.error("Failed to evaluate scores for item %s: %s", getattr(item, "id", "Unknown"), e)
                raise ScoringError(f"Scoring evaluation aborted: {e}") from e

        self.logger.info("Completed scoring stage. Scored items count: %d", len(scored_items))
        return scored_items
