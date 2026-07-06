"""
Signal Hunter - AI-Powered Research Intelligence Pipeline.

Main entry point that orchestrates the execution flow: configuration loading,
logging setup, raw content crawling (collectors), AI extraction (analyzers),
critique validation (verifier), local JSON persistence (memory), and report output (delivery).
"""

import argparse
import logging
import sys
from datetime import datetime
from typing import List, Optional

from config.config_loader import AppConfig, load_config
from models.research_item import ResearchItem
from analyzers.base import DummyAnalyzer
from verifier.verifier import SignalVerifier
from memory.json_store import JSONMemoryStore
from delivery.reporter import MarkdownReporter
from utils.logger import setup_logger
from utils.exceptions import SignalHunterError
from utils.helpers import generate_id


def generate_mock_raw_candidates() -> List[ResearchItem]:
    """
    Generate mock candidates representing raw gathered feeds.

    Used when collectors aren't yet implemented to demonstrate the end-to-end flow.

    Returns:
        List[ResearchItem]: Array of un-analyzed research inputs.
    """
    now = datetime.utcnow()
    return [
        ResearchItem(
            id=generate_id("https://arxiv.org/abs/2106.09685"),
            title="LoRA: Low-Rank Adaptation of Large Language Models",
            url="https://arxiv.org/abs/2106.09685",
            source_type="paper",
            raw_content="We propose Low-Rank Adaptation (LoRA), which freezes the pre-trained model weights and injects trainable rank decomposition matrices into each layer of the Transformer architecture, greatly reducing the number of trainable parameters for downstream tasks.",
            author="Edward J. Hu et al.",
            published_at="2021-06-17T00:00:00Z",
            collected_at=now,
        ),
        ResearchItem(
            id=generate_id("https://github.com/vllm-project/vllm"),
            title="vLLM: Easy, Fast, and Cheap LLM Serving with PagedAttention",
            url="https://github.com/vllm-project/vllm",
            source_type="github",
            raw_content="vLLM is a fast and easy-to-use library for LLM inference and serving. It achieves state-of-the-art throughput by using PagedAttention, which manages attention key-value memory with high efficiency.",
            author="UC Berkeley team",
            published_at="2023-06-20T00:00:00Z",
            collected_at=now,
        ),
        ResearchItem(
            id=generate_id("https://openai.com/blog/frontier-risk-preparedness"),
            title="Frontier Risk Preparedness and Safety Frameworks",
            url="https://openai.com/blog/frontier-risk-preparedness",
            source_type="engineering_blog",
            raw_content="We outline our systematic preparedness safety framework designed to quantify, test, and respond to catastrophic risks in frontier models across cybersecurity, persuasion, and autonomy.",
            author="OpenAI Safety Team",
            published_at="2024-01-15T00:00:00Z",
            collected_at=now,
        ),
    ]


def run_pipeline(config_path: Optional[str] = None, dry_run: bool = False) -> None:
    """
    Load components and run the intelligence collection & analysis pipeline.

    Args:
        config_path (Optional[str]): Path to configuration YAML file.
        dry_run (bool): If True, skips external network crawls and uses pre-loaded items.

    Raises:
        SignalHunterError: If some phase of the pipeline suffers a fatal crash.
    """
    # 1. Load configuration
    try:
        config: AppConfig = load_config(config_path)
    except Exception as e:
        # Fallback console printing because logger is not configured yet
        print(f"FATAL: Failed to load system configuration: {e}", file=sys.stderr)
        sys.exit(1)

    # 2. Setup central logger
    logger: logging.Logger = setup_logger(
        name="signal_hunter",
        log_level=config.log_level,
        log_file="logs/signal_hunter.log",
    )

    logger.info("=========================================")
    logger.info("   Starting Signal Hunter Intelligence   ")
    logger.info("=========================================")
    logger.info("Application: %s", config.app_name)
    logger.info("Log Level:   %s", config.log_level)

    try:
        # 3. Instantiate memory store
        store = JSONMemoryStore(config.memory)

        # 4. Instantiate analyzers
        # We fetch the configuration for gemini_summarizer
        analyzer_cfg = config.analyzers.get("gemini_summarizer")
        if not analyzer_cfg:
            raise SignalHunterError("Configuration for 'gemini_summarizer' is missing in config.")
        analyzer = DummyAnalyzer(analyzer_cfg)

        # 5. Instantiate verifier
        verifier = SignalVerifier(config.verifier)

        # 6. Instantiate delivery system
        reporter = MarkdownReporter(config.delivery)

        # 7. Collect raw items
        raw_items: List[ResearchItem] = []
        if dry_run or not any(c.enabled for c in config.collectors.values()):
            logger.info("Running pipeline in DRY-RUN mode or with collectors disabled. Injecting base candidates...")
            raw_items = generate_mock_raw_candidates()
        else:
            logger.info("Starting active crawlers (Placeholder - no collectors registered)...")
            # In subsequent iterations, collectors will append actual results here
            raw_items = generate_mock_raw_candidates()

        logger.info("Ingested %d candidate(s) into pipeline buffers.", len(raw_items))

        # 8. Run processing loop
        verified_items: List[ResearchItem] = []

        for index, raw_item in enumerate(raw_items, 1):
            logger.info("[%d/%d] Processing signal candidate: %s", index, len(raw_items), raw_item.title)

            try:
                # Analysis
                analyzed_item = analyzer.analyze(raw_item)

                # Verification
                verified_item = verifier.verify(analyzed_item)

                # Storage
                store.save_item(verified_item)

                if verified_item.is_verified:
                    verified_items.append(verified_item)

            except Exception as e:
                logger.error("Failed to process item [%s]: %s", raw_item.title, e, exc_info=True)
                continue

        # 9. Deliver report
        logger.info("Compiling daily briefing with %d verified breakthrough(s)...", len(verified_items))
        report_content = reporter.deliver(verified_items)

        logger.info("Pipeline run successfully completed.")

    except Exception as e:
        logger.critical("Critical pipeline failure: %s", e, exc_info=True)
        raise SignalHunterError(f"Pipeline run aborted: {e}") from e


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Signal Hunter: An AI-Powered Research Intelligence Pipeline"
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to YAML configuration settings override file",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Skip active internet connection crawls and execute pipeline with mock feeds",
    )

    args = parser.parse_args()

    try:
        run_pipeline(config_path=args.config, dry_run=args.dry_run)
    except Exception as err:
        print(f"FAILED: {err}", file=sys.stderr)
        sys.exit(1)
