"""
Signal Hunter Pipeline Stages.

Implements modular BasePipelineStage components for each phase of the workflow.
"""

import logging
from typing import List

from models.research_item import ResearchItem
from pipeline.base import BasePipelineStage
from normalizer.normalizer import PlaceholderNormalizer
from verifier.verifier import SignalVerifier
from deduplicator.deduplicator import PlaceholderDeduplicator
from scorer.scorer import PlaceholderScorer
from knowledge_base.json_store import JSONMemoryStore
from delivery.reporter import MarkdownReporter
from utils.exceptions import (
    CollectionError,
    NormalizationError,
    VerificationError,
    DeduplicationError,
    ScoringError,
    AnalysisError,
    StorageError,
    DeliveryError,
)
from utils.logger import setup_logger


class CollectorStage(BasePipelineStage):
    """
    Stage responsible for gathering raw ResearchItem candidates.
    Uses mock/placeholder generation as real sources are not implemented yet.
    """

    def __init__(self, candidates: List[ResearchItem] = None) -> None:
        """Initialize the Collector Stage."""
        self.logger: logging.Logger = setup_logger(
            "signal_hunter.pipeline.collector",
            log_level="INFO",
        )
        self.candidates = candidates or []
        self.logger.info("Initialized CollectorStage with %d initial candidate(s)", len(self.candidates))

    def process(self, items: List[ResearchItem]) -> List[ResearchItem]:
        """
        Produce research items to begin the pipeline.

        Args:
            items (List[ResearchItem]): Optional inbound list (appended to candidates).

        Returns:
            List[ResearchItem]: The combined list of research items.
        """
        self.logger.info("CollectorStage: Producing research items")
        combined = list(items) + list(self.candidates)
        self.logger.info("CollectorStage: Gathered %d candidate(s)", len(combined))
        return combined


class NormalizerStage(BasePipelineStage):
    """
    Stage responsible for standardizing fields on ResearchItem objects.
    """

    def __init__(self, normalizer: PlaceholderNormalizer = None) -> None:
        """Initialize the Normalizer Stage."""
        self.logger: logging.Logger = setup_logger(
            "signal_hunter.pipeline.normalizer",
            log_level="INFO",
        )
        self.normalizer = normalizer or PlaceholderNormalizer()

    def process(self, items: List[ResearchItem]) -> List[ResearchItem]:
        """
        Normalize inbound research items.

        Args:
            items (List[ResearchItem]): Inbound items.

        Returns:
            List[ResearchItem]: Standardized items.
        """
        self.logger.info("NormalizerStage: Processing %d items", len(items))
        try:
            return self.normalizer.process(items)
        except Exception as e:
            self.logger.error("NormalizerStage processing failure: %s", e)
            raise NormalizationError(f"NormalizerStage failed: {e}") from e


class VerifierStage(BasePipelineStage):
    """
    Stage responsible for evaluating items against confidence filters and quality criteria.
    """

    def __init__(self, verifier: SignalVerifier = None) -> None:
        """Initialize the Verifier Stage."""
        self.logger: logging.Logger = setup_logger(
            "signal_hunter.pipeline.verifier",
            log_level="INFO",
        )
        self.verifier = verifier

    def process(self, items: List[ResearchItem]) -> List[ResearchItem]:
        """
        Verify inbound research items.

        Args:
            items (List[ResearchItem]): Standardized items.

        Returns:
            List[ResearchItem]: Verified items.
        """
        self.logger.info("VerifierStage: Processing %d items", len(items))
        if not self.verifier:
            self.logger.warning("No verifier assigned to VerifierStage. Passing items through.")
            return items
        try:
            return self.verifier.process(items)
        except Exception as e:
            self.logger.error("VerifierStage processing failure: %s", e)
            raise VerificationError(f"VerifierStage failed: {e}") from e


class DeduplicatorStage(BasePipelineStage):
    """
    Stage responsible for spotting duplicate items.
    """

    def __init__(self, deduplicator: PlaceholderDeduplicator = None) -> None:
        """Initialize the Deduplicator Stage."""
        self.logger: logging.Logger = setup_logger(
            "signal_hunter.pipeline.deduplicator",
            log_level="INFO",
        )
        self.deduplicator = deduplicator or PlaceholderDeduplicator()

    def process(self, items: List[ResearchItem]) -> List[ResearchItem]:
        """
        Identify duplicates.

        Args:
            items (List[ResearchItem]): Verified items.

        Returns:
            List[ResearchItem]: Deduplicated items (possessing filled duplicate_of properties).
        """
        self.logger.info("DeduplicatorStage: Processing %d items", len(items))
        try:
            return self.deduplicator.process(items)
        except Exception as e:
            self.logger.error("DeduplicatorStage processing failure: %s", e)
            raise DeduplicationError(f"DeduplicatorStage failed: {e}") from e


class ScorerStage(BasePipelineStage):
    """
    Stage responsible for evaluating strategic scoring vectors.
    """

    def __init__(self, scorer: PlaceholderScorer = None) -> None:
        """Initialize the Scorer Stage."""
        self.logger: logging.Logger = setup_logger(
            "signal_hunter.pipeline.scorer",
            log_level="INFO",
        )
        self.scorer = scorer or PlaceholderScorer()

    def process(self, items: List[ResearchItem]) -> List[ResearchItem]:
        """
        Score inbound research items.

        Args:
            items (List[ResearchItem]): Deduplicated items.

        Returns:
            List[ResearchItem]: Scored items.
        """
        self.logger.info("ScorerStage: Processing %d items", len(items))
        try:
            return self.scorer.process(items)
        except Exception as e:
            self.logger.error("ScorerStage processing failure: %s", e)
            raise ScoringError(f"ScorerStage failed: {e}") from e


class AIAnalyzerStage(BasePipelineStage):
    """
    Stage responsible for semantic text summarization and insight enrichment.
    """

    def __init__(self, analyzer=None) -> None:
        """Initialize the AI Analyzer Stage."""
        self.logger: logging.Logger = setup_logger(
            "signal_hunter.pipeline.analyzer",
            log_level="INFO",
        )
        self.analyzer = analyzer

    def process(self, items: List[ResearchItem]) -> List[ResearchItem]:
        """
        Enrich items using dummy analyzer logic or custom logic.

        Args:
            items (List[ResearchItem]): Scored items.

        Returns:
            List[ResearchItem]: AI enriched items.
        """
        self.logger.info("AIAnalyzerStage: Processing %d items", len(items))
        if not self.analyzer:
            self.logger.warning("No analyzer provided. Applying standard abstract updates.")
            for item in items:
                if not item.summary:
                    item.summary = f"Auto-generated summary for: {item.title}"
            return items
        try:
            enriched = []
            # Sort items by confidence_score descending to prioritize highest-signal papers
            sorted_items = sorted(items, key=lambda x: getattr(x, "confidence_score", 0.0), reverse=True)
            
            # Run AI analyzer on top 10 highest-scoring signals
            target_limit = 10
            for idx, item in enumerate(sorted_items):
                if idx < target_limit:
                    self.logger.info("AI Analyzing top candidate #%d: '%s' (Confidence: %.2f)", idx + 1, item.title, item.confidence_score)
                    try:
                        enriched.append(self.analyzer.analyze(item))
                    except Exception as exc:
                        self.logger.warning("LLM analysis failed for '%s' due to: %s. Applying local baseline fallback.", item.title, exc)
                        if not item.summary:
                            item.summary = f"Technical baseline preprint and reference covering {item.title}."
                        # Initialize empty lists if not already populated
                        if not item.signals:
                            item.signals = ["Explore general systems engineering applicability."]
                        if not item.technologies:
                            item.technologies = []
                        if not item.programming_languages:
                            item.programming_languages = []
                        if not item.build_opportunities:
                            item.build_opportunities = []
                        enriched.append(item)
                else:
                    # Lightweight fallback for lower-scoring items to bypass expensive API calls
                    if not item.summary:
                        item.summary = f"Technical baseline preprint and reference covering {item.title}."
                    # Initialize empty lists if not already populated
                    if not item.signals:
                        item.signals = ["Explore general systems engineering applicability."]
                    if not item.technologies:
                        item.technologies = []
                    if not item.programming_languages:
                        item.programming_languages = []
                    if not item.build_opportunities:
                        item.build_opportunities = []
                    enriched.append(item)
            return enriched
        except Exception as e:
            self.logger.error("AIAnalyzerStage processing failure: %s", e)
            raise AnalysisError("AIAnalyzerStage", f"Analysis failed: {e}") from e


class KnowledgeBaseStage(BasePipelineStage):
    """
    Stage responsible for persistent storage in our JSON memory store (Knowledge Base).
    """

    def __init__(self, store: JSONMemoryStore = None) -> None:
        """Initialize the Knowledge Base Stage."""
        self.logger: logging.Logger = setup_logger(
            "signal_hunter.pipeline.knowledge_base",
            log_level="INFO",
        )
        self.store = store

    def process(self, items: List[ResearchItem]) -> List[ResearchItem]:
        """
        Save items to the local file system storage.

        Args:
            items (List[ResearchItem]): Enriched items.

        Returns:
            List[ResearchItem]: Saved items.
        """
        self.logger.info("KnowledgeBaseStage: Saving %d items to store", len(items))
        if not self.store:
            self.logger.warning("No store assigned to KnowledgeBaseStage. Skipping storage step.")
            return items
        try:
            for item in items:
                self.store.save_item(item)
            return items
        except Exception as e:
            self.logger.error("KnowledgeBaseStage processing failure: %s", e)
            raise StorageError(f"KnowledgeBaseStage failed: {e}") from e


class ReporterStage(BasePipelineStage):
    """
    Stage responsible for outputting compiled markdown reports.
    """

    def __init__(self, reporter: MarkdownReporter = None) -> None:
        """Initialize the Reporter Stage."""
        self.logger: logging.Logger = setup_logger(
            "signal_hunter.pipeline.reporter",
            log_level="INFO",
        )
        self.reporter = reporter

    def process(self, items: List[ResearchItem]) -> List[ResearchItem]:
        """
        Compile and write briefing document.

        Args:
            items (List[ResearchItem]): Persisted items.

        Returns:
            List[ResearchItem]: Passed-through items.
        """
        self.logger.info("ReporterStage: Dispatching briefing report for %d items", len(items))
        if not self.reporter:
            self.logger.warning("No reporter assigned to ReporterStage. Skipping dispatch step.")
            return items
        try:
            self.reporter.deliver(items)
            return items
        except Exception as e:
            self.logger.error("ReporterStage processing failure: %s", e)
            raise DeliveryError(f"ReporterStage failed: {e}") from e
