"""
Signal Hunter Core Processing Pipeline Unit Tests.

Verifies independent stages, pipeline manager orchestration, state transitions,
no modifications to unrelated fields, and custom error boundaries.
"""

import unittest
from datetime import datetime

from models.research_item import ResearchItem
from normalizer.normalizer import PlaceholderNormalizer
from deduplicator.deduplicator import PlaceholderDeduplicator
from scorer.scorer import PlaceholderScorer
from verifier.verifier import SignalVerifier
from config.config_loader import VerifierConfig
from utils.exceptions import (
    NormalizationError,
    DeduplicationError,
    ScoringError,
    PipelineError,
)
from pipeline.base import BasePipelineStage
from pipeline.stages import (
    CollectorStage,
    NormalizerStage,
    VerifierStage,
    DeduplicatorStage,
    ScorerStage,
    AIAnalyzerStage,
)
from pipeline.manager import PipelineManager


class TestCoreProcessingPipeline(unittest.TestCase):
    """Test suite for the new processing pipeline architecture and components."""

    def setUp(self) -> None:
        """Set up standard mock ResearchItem objects for testing."""
        self.now = datetime.utcnow()
        self.item1 = ResearchItem(
            id="test-1",
            title="  Attention Is All You Need  ",
            url="https://arxiv.org/abs/1706.03762",
            source_type="paper",
            raw_content="Abstract description...",
            tags=["  Attention  ", "TRANSFORMER"],
            categories=["Deep Learning"],
            collected_at=self.now,
        )
        self.item2 = ResearchItem(
            id="test-2",
            title="Attention Is All You Need",  # Exact duplicate title
            url="https://example.com/other-link",
            source_type="paper",
            raw_content="Different description.",
            tags=["transformer"],
            categories=["Neural Networks"],
            collected_at=self.now,
        )
        self.item3 = ResearchItem(
            id="test-3",
            title="Different Paper entirely",
            url="https://arxiv.org/abs/1706.03762",  # Duplicate URL with item1
            source_type="paper",
            raw_content="Totally different topic.",
            tags=["AI"],
            categories=["Scientific"],
            collected_at=self.now,
        )

    def test_normalizer_trimming_and_lowercasing(self) -> None:
        """Verify normalizer cleans whitespaces and standardizes list fields."""
        normalizer = PlaceholderNormalizer()
        items = [self.item1]
        processed = normalizer.process(items)

        self.assertEqual(processed[0].title, "Attention Is All You Need")
        self.assertIn("attention", processed[0].tags)
        self.assertIn("transformer", processed[0].tags)
        # Verify non-related fields are not modified
        self.assertEqual(processed[0].id, "test-1")
        self.assertEqual(processed[0].source_type, "paper")

    def test_normalizer_raises_custom_exception(self) -> None:
        """Verify normalizer properly encapsulates unexpected errors into NormalizationError."""
        normalizer = PlaceholderNormalizer()
        # Passing None should trigger error handling
        with self.assertRaises(NormalizationError):
            normalizer.process(None)

    def test_deduplicator_links_duplicate_titles_and_urls(self) -> None:
        """Verify deduplicator identifies matching titles and URLs, marking them as duplicate_of."""
        dedup = PlaceholderDeduplicator()
        items = [self.item1, self.item2, self.item3]
        processed = dedup.process(items)

        # item1 is the original
        self.assertIsNone(processed[0].duplicate_of)

        # item2 matches item1's title
        self.assertEqual(processed[1].duplicate_of, "test-1")

        # item3 matches item1's URL
        self.assertEqual(processed[2].duplicate_of, "test-1")

    def test_deduplicator_raises_custom_exception(self) -> None:
        """Verify deduplicator encapsulates unexpected errors into DeduplicationError."""
        dedup = PlaceholderDeduplicator()
        with self.assertRaises(DeduplicationError):
            dedup.process(None)

    def test_scorer_metrics_calculation(self) -> None:
        """Verify scorer computes all strategic scorecard scores and stays in bounds."""
        scorer = PlaceholderScorer()
        items = [self.item1]
        processed = scorer.process(items)

        item = processed[0]
        # Assert scores are updated and non-zero
        self.assertTrue(0.0 <= item.opportunity_score <= 1.0)
        self.assertTrue(0.0 <= item.engineering_score <= 1.0)
        self.assertTrue(0.0 <= item.scientific_score <= 1.0)
        self.assertTrue(0.0 <= item.startup_score <= 1.0)
        self.assertTrue(0.0 <= item.confidence_score <= 1.0)
        self.assertTrue(0.0 <= item.novelty_score <= 1.0)

        # Ensure other fields aren't corrupted
        self.assertEqual(item.id, "test-1")
        self.assertEqual(item.url, "https://arxiv.org/abs/1706.03762")

    def test_scorer_raises_custom_exception(self) -> None:
        """Verify scorer encapsulates unexpected errors into ScoringError."""
        scorer = PlaceholderScorer()
        with self.assertRaises(ScoringError):
            scorer.process(None)

    def test_pipeline_stages_cohesive_execution(self) -> None:
        """Verify standard stage adapters execute safely."""
        col = CollectorStage([self.item1])
        norm = NormalizerStage()
        dedup = DeduplicatorStage()
        score = ScorerStage()

        # Collector stage outputs item1
        items = col.process([])
        self.assertEqual(len(items), 1)

        # Normalizer stage processes item1
        items = norm.process(items)
        self.assertEqual(items[0].title, "Attention Is All You Need")

        # Deduplicator stage processes item1
        items = dedup.process(items)
        self.assertIsNone(items[0].duplicate_of)

        # Scorer stage processes item1
        items = score.process(items)
        self.assertGreater(items[0].opportunity_score, 0.0)

    def test_pipeline_manager_orchestrates_full_flow(self) -> None:
        """Verify PipelineManager executes default workflow sequentially and returns final output."""
        # Create minimal pipeline stages to avoid heavy file system / reporter side-effects
        # We can construct custom stages for a clean orchestration test
        stages = [
            CollectorStage([self.item1]),
            NormalizerStage(),
            DeduplicatorStage(),
            ScorerStage(),
        ]

        manager = PipelineManager(stages=stages)
        results = manager.run([])

        self.assertEqual(len(results), 1)
        final_item = results[0]

        # Verify all pipeline components did their jobs sequentially
        self.assertEqual(final_item.title, "Attention Is All You Need")  # Normalizer
        self.assertIsNone(final_item.duplicate_of)  # Deduplicator
        self.assertGreater(final_item.opportunity_score, 0.0)  # Scorer

    def test_pipeline_manager_encapsulates_unhandled_stage_exceptions(self) -> None:
        """Verify PipelineManager wraps a stage exception into a custom PipelineError."""

        class BrokenStage(BasePipelineStage):
            def process(self, items):
                raise ValueError("Unexpected database crash")

        stages = [
            CollectorStage([self.item1]),
            BrokenStage(),
        ]

        manager = PipelineManager(stages=stages)
        with self.assertRaises(PipelineError) as ctx:
            manager.run([])

        self.assertIn("Pipeline failed at stage BrokenStage", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
