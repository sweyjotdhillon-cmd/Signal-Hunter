"""
Signal Hunter Pipeline Manager.

Coordinates sequential execution of normalizers, verifiers, deduplicators, scorers, and storage.
"""

import logging
from typing import List, Optional

from models.research_item import ResearchItem
from pipeline.base import BasePipelineStage
from pipeline.stages import (
    CollectorStage,
    NormalizerStage,
    VerifierStage,
    DeduplicatorStage,
    ScorerStage,
    AIAnalyzerStage,
    KnowledgeBaseStage,
    ReporterStage,
)
from utils.exceptions import PipelineError, SignalHunterError
from utils.logger import setup_logger


class PipelineManager:
    """
    Orchestrates the entire sequential data-processing pipeline.

    Defines and executes the workflow:
    Collector -> Normalizer -> Verifier -> Deduplicator -> Scorer -> AI Analyzer -> Knowledge Base -> Reporter
    """

    def __init__(
        self,
        stages: Optional[List[BasePipelineStage]] = None,
        collector_stage: Optional[CollectorStage] = None,
        normalizer_stage: Optional[NormalizerStage] = None,
        verifier_stage: Optional[VerifierStage] = None,
        deduplicator_stage: Optional[DeduplicatorStage] = None,
        scorer_stage: Optional[ScorerStage] = None,
        analyzer_stage: Optional[AIAnalyzerStage] = None,
        kb_stage: Optional[KnowledgeBaseStage] = None,
        reporter_stage: Optional[ReporterStage] = None,
    ) -> None:
        """
        Initialize the Pipeline Manager with either custom or default stages.
        """
        self.logger: logging.Logger = setup_logger(
            "signal_hunter.pipeline.manager",
            log_level="INFO",
        )

        if stages is not None:
            self.stages = stages
            self.logger.info("Initialized PipelineManager with %d custom stages", len(self.stages))
        else:
            # Construct standard sequential workflow stages
            self.stages = [
                collector_stage or CollectorStage(),
                normalizer_stage or NormalizerStage(),
                verifier_stage or VerifierStage(),
                deduplicator_stage or DeduplicatorStage(),
                scorer_stage or ScorerStage(),
                analyzer_stage or AIAnalyzerStage(),
                kb_stage or KnowledgeBaseStage(),
                reporter_stage or ReporterStage(),
            ]
            self.logger.info("Initialized PipelineManager with %d default sequential stages", len(self.stages))

    def run(self, initial_items: Optional[List[ResearchItem]] = None) -> List[ResearchItem]:
        """
        Execute every stage in the pipeline sequentially.

        Args:
            initial_items (Optional[List[ResearchItem]]): Starting research items.

        Returns:
            List[ResearchItem]: Fully processed items returned from final stage.

        Raises:
            PipelineError: If any stage execution fails.
        """
        self.logger.info("Starting pipeline execution")
        current_items = initial_items or []

        for index, stage in enumerate(self.stages, 1):
            stage_name = stage.__class__.__name__
            self.logger.info(
                "--- [Stage %d/%d] Executing: %s (Input count: %d) ---",
                index,
                len(self.stages),
                stage_name,
                len(current_items),
            )

            try:
                current_items = stage.process(current_items)
                self.logger.info(
                    "--- [Stage %d/%d] Success: %s (Output count: %d) ---",
                    index,
                    len(self.stages),
                    stage_name,
                    len(current_items),
                )
            except SignalHunterError as e:
                self.logger.error("Stage '%s' failed with SignalHunterError: %s", stage_name, e)
                raise PipelineError(f"Pipeline failed at stage {stage_name}: {e}") from e
            except Exception as e:
                self.logger.error("Stage '%s' encountered an unhandled exception: %s", stage_name, e, exc_info=True)
                raise PipelineError(f"Pipeline failed at stage {stage_name}: {e}") from e

        self.logger.info("Pipeline execution successfully completed")
        return current_items
