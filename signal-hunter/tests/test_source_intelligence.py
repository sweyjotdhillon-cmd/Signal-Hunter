"""
Unit tests for the Source Intelligence System in Signal Hunter.
"""

import unittest
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from source_profiles.profile import SourceCategory, SourceProfile
from source_scoring.scoring import SourceWeight, SourceQuality
from source_registry.registry import SourceRegistry, SourceFilter, SourceSelector
from models.research_item import ResearchItem, Author


class TestSourceIntelligenceSystem(unittest.TestCase):
    """Test suite covering the features, scoring, filtering, and selection of Source Intelligence."""

    def setUp(self) -> None:
        self.registry = SourceRegistry()
        self.filter = SourceFilter(self.registry)
        self.selector = SourceSelector(self.registry)

    def test_registry_loading(self) -> None:
        """Verify configurations are correctly parsed and accessible via the SourceRegistry."""
        # Check categories loaded correctly
        categories = self.registry.list_categories()
        self.assertGreater(len(categories), 0)
        
        # Verify specific category is loaded
        ai_cat = self.registry.get_category("ai_ml")
        self.assertIsNotNone(ai_cat)
        self.assertEqual(ai_cat.name, "Artificial Intelligence & Machine Learning")
        self.assertEqual(ai_cat.priority, 1)

        # Verify sources loaded
        sources = self.registry.list_sources()
        self.assertGreater(len(sources), 0)
        
        arxiv_ai = self.registry.get_source("arxiv_cs_ai")
        self.assertIsNotNone(arxiv_ai)
        self.assertEqual(arxiv_ai.category, "ai_ml")
        self.assertEqual(arxiv_ai.source_type, "Preprints")

    def test_source_weights(self) -> None:
        """Verify source and parameter weights return correct defaults or configured values."""
        weights = self.registry.weights
        self.assertEqual(weights.get_source_type_weight("Preprints"), 0.85)
        self.assertEqual(weights.get_source_type_weight("Journals"), 0.95)
        self.assertEqual(weights.get_source_type_weight("Unknown Type"), 1.0)
        
        self.assertEqual(weights.get_parameter_weight("quality"), 0.35)
        self.assertEqual(weights.get_parameter_weight("reliability"), 0.30)

    def test_intelligence_scoring_and_neutralization(self) -> None:
        """Verify quality scoring rewards correct indicators and actively neutralizes famous brand bias."""
        evaluator = self.registry.quality_evaluator
        
        # Base item with good quality indicators
        clean_item = ResearchItem(
            unique_id="clean-1",
            title="Sparsely-Gated Mixture-of-Experts",
            source_name="arXiv",
            source_type="Preprints",
            url="https://arxiv.org/abs/1701.06538",
            organization="Independent University",
            novelty_score=0.90,
            engineering_score=0.85,
            scientific_score=0.90,
            startup_score=0.50,
            extra_metadata={
                "independent_confirmation": 0.80,
                "practicality": 0.80,
                "long_term_influence": 0.90
            }
        )

        score_independent = evaluator.evaluate_item_quality(clean_item)
        
        # Famous organization item with identical scores
        famous_item = ResearchItem(
            unique_id="famous-1",
            title="Sparsely-Gated Mixture-of-Experts from OpenAI",
            source_name="OpenAI Blog",
            source_type="Engineering Blogs",
            url="https://openai.com/blog",
            organization="OpenAI",
            novelty_score=0.90,
            engineering_score=0.85,
            scientific_score=0.90,
            startup_score=0.50,
            extra_metadata={
                "independent_confirmation": 0.80,
                "practicality": 0.80,
                "long_term_influence": 0.90
            }
        )

        score_famous = evaluator.evaluate_item_quality(famous_item)
        
        # Verify famous organization neutralization: famous score must be reduced/neutralized
        self.assertLess(score_famous, score_independent)

    def test_filter_by_quality_and_recency(self) -> None:
        """Verify the quality filter weeds out items below target threshold and obeys age constraints."""
        item_high_quality = ResearchItem(
            unique_id="high-q",
            title="High Quality Idea",
            source_name="arxiv_cs_ai",
            source_type="Preprints",
            url="https://arxiv.org",
            novelty_score=0.95,
            engineering_score=0.95,
            scientific_score=0.95,
            startup_score=0.80,
            publication_date=datetime.now(timezone.utc) - timedelta(days=10)
        )

        item_low_quality = ResearchItem(
            unique_id="low-q",
            title="Noise Idea",
            source_name="arxiv_cs_ai",
            source_type="Preprints",
            url="https://arxiv.org",
            novelty_score=0.10,
            engineering_score=0.10,
            scientific_score=0.10,
            startup_score=0.10,
            publication_date=datetime.now(timezone.utc) - timedelta(days=10)
        )

        item_stale = ResearchItem(
            unique_id="stale",
            title="Stale Excellent Idea",
            source_name="arxiv_cs_ai",
            source_type="Preprints",
            url="https://arxiv.org",
            novelty_score=0.95,
            engineering_score=0.95,
            scientific_score=0.95,
            startup_score=0.80,
            publication_date=datetime.now(timezone.utc) - timedelta(days=120)  # Over AI category's 90-day threshold
        )

        pool = [item_high_quality, item_low_quality, item_stale]
        
        # Quality filter
        qualified_by_quality = self.filter.filter_items_by_quality(pool)
        self.assertIn(item_high_quality, qualified_by_quality)
        self.assertNotIn(item_low_quality, qualified_by_quality)

        # Recency filter
        qualified_by_recency = self.filter.filter_items_by_recency(pool)
        self.assertIn(item_high_quality, qualified_by_recency)
        self.assertNotIn(item_stale, qualified_by_recency)

    def test_daily_capping(self) -> None:
        """Verify that category daily caps prune lower scoring surplus correctly."""
        # Create 15 items in Space category (cap is 8)
        items = []
        for i in range(15):
            items.append(
                ResearchItem(
                    unique_id=f"space-{i}",
                    title=f"Space Venture {i}",
                    source_name="nasa_technical_reports",
                    source_type="Government Labs",
                    categories=["Space & Aerospace"],
                    url="https://nasa.gov",
                    opportunity_score=0.2 + (i * 0.05)  # Quality grows with i
                )
            )

        capped = self.filter.apply_daily_caps(items)
        self.assertEqual(len(capped), 8)
        
        # Check that the highest quality ones were kept
        ids_kept = {itm.unique_id for itm in capped}
        self.assertIn("space-14", ids_kept)
        self.assertIn("space-13", ids_kept)
        self.assertNotIn("space-0", ids_kept)

    def test_selector_distribution(self) -> None:
        """Verify the Selector appropriately distributes items based on the selection strategy."""
        items = []
        # Populate a large pool representing mixed types and ages
        now = datetime.now(timezone.utc)
        
        for i in range(25):
            items.append(
                ResearchItem(
                    unique_id=f"trusted-{i}",
                    title=f"Trusted Item {i}",
                    source_name="arxiv_cs_ai",
                    source_type="Preprints",
                    url="https://arxiv.org",
                    publication_date=now - timedelta(days=i)
                )
            )
            items.append(
                ResearchItem(
                    unique_id=f"gem-{i}",
                    title=f"Hidden Gem {i}",
                    source_name="independent_blog",
                    source_type="Engineering Blogs",
                    url="https://blog.example.com",
                    publication_date=now - timedelta(days=200 + i) # timeless/stale
                )
            )

        selected = self.selector.select(items, user_interests=["ai_ml"])
        self.assertGreater(len(selected), 0)
        self.assertLessEqual(len(selected), 30)  # selector targets max 30
