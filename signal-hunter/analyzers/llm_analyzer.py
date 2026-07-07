"""
Signal Hunter LLM-Powered Analyzer.

Implements a provider-agnostic analyzer that delegates technical analysis
and structured insight extraction to an injected BaseLLMProvider.
"""

from typing import Optional, List
from analyzers.base import BaseAnalyzer
from analyzers.providers import BaseLLMProvider, NvidiaProvider
from models.research_item import ResearchItem
from config.config_loader import AnalyzerConfig
from utils.exceptions import AnalysisError


class LLMAnalyzer(BaseAnalyzer):
    """
    A unified, provider-agnostic analyzer that leverages LLMs to summarize
    and extract strategic insights from raw collected research papers/documents.

    This class adheres strictly to the dependency inversion principle: it is
    completely decoupled from specific LLM providers and accepts any instance
    implementing the BaseLLMProvider contract.
    """

    def __init__(self, config: AnalyzerConfig, provider: Optional[BaseLLMProvider] = None) -> None:
        """
        Initialize the LLM-powered analyzer.

        Args:
            config (AnalyzerConfig): Configuration settings for processing/models.
            provider (Optional[BaseLLMProvider]): Injected LLM provider.
                Defaults to NvidiaProvider(config).
        """
        super().__init__(config)
        self.provider = provider or NvidiaProvider(config)

    @property
    def name(self) -> str:
        """
        Return the unique descriptive name of the analyzer.
        """
        return "LLMAnalyzer"

    def analyze(self, item: ResearchItem) -> ResearchItem:
        """
        Process and enrich a ResearchItem with structured AI insights.

        Modifies the item in-place by extracting technical summaries, strategic signals,
        technologies, programming languages, build opportunities, and risks.

        Args:
            item (ResearchItem): Item representing the target signal source.

        Returns:
            ResearchItem: The enriched object containing summaries and opportunity lists.

        Raises:
            AnalysisError: If processing or LLM calls encounter fatal failures.
        """
        self.logger.info("Starting AI analysis for item: '%s' (ID: %s)", item.title, item.id)

        prompt = (
            f"Please analyze the following technical document and extract strategic insights:\n\n"
            f"Title: {item.title}\n"
            f"Source Type: {item.source_type}\n"
            f"Raw Content / Abstract:\n{item.raw_content or item.summary or 'No content available.'}\n"
        )

        system_instruction = (
            "You are an elite research analyst and senior software engineer at a top-tier venture firm. "
            "Your job is to thoroughly analyze raw technology preprints, blog posts, and code repositories. "
            "Isolate the true breakthrough signal from standard engineering noise.\n\n"
            "Return a clean, structured JSON response with technical summaries, concrete opportunities, and technical metrics."
        )

        expected_keys = ["summary", "signals", "technologies", "programming_languages", "build_opportunities", "risks"]

        try:
            structured_data = self.provider.generate_structured(
                prompt=prompt,
                system_instruction=system_instruction,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                expected_keys=expected_keys,
            )

            # Update the ResearchItem in-place with validated results
            item.summary = structured_data.get("summary") or item.summary or f"Technical summary for {item.title}"
            
            # Extract and update lists
            item.signals = structured_data.get("signals") or []
            item.technologies = structured_data.get("technologies") or []
            item.programming_languages = structured_data.get("programming_languages") or []
            item.build_opportunities = structured_data.get("build_opportunities") or []
            item.risks = structured_data.get("risks") or []

            self.logger.info(
                "Successfully analyzed item '%s' (Extracted %d signals, %d technologies)",
                item.title,
                len(item.signals),
                len(item.technologies),
            )
            return item

        except Exception as e:
            self.logger.error("LLM analysis failed on item '%s': %s", item.title, e)
            raise AnalysisError("LLMAnalyzer", f"Analysis failed: {e}") from e
