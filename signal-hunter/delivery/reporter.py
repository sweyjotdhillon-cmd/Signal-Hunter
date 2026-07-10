"""
Signal Hunter Report Delivery System.

Implements reporting utilities, synthesizing verified signals into actionable briefings.
"""

from abc import ABC, abstractmethod
from datetime import datetime
import logging
import os
from typing import List

from config.config_loader import DeliveryConfig
from models.research_item import ResearchItem
from utils.logger import setup_logger


class BaseDelivery(ABC):
    """
    Abstract base class for all report delivery channels.

    Handles report generation, layout styling, and outbound transport (Console, files, webhook).
    """

    def __init__(self, config: DeliveryConfig) -> None:
        """
        Initialize the delivery service.

        Args:
            config (DeliveryConfig): Output directory and channel settings.
        """
        self.config = config
        self.logger: logging.Logger = setup_logger(
            name=f"signal_hunter.delivery.{self.name.lower()}",
            log_level="INFO",
        )

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Return the unique identifier for the delivery channel.

        Returns:
            str: Channel name (e.g., 'Console', 'MarkdownFile').
        """
        pass

    @abstractmethod
    def deliver(self, items: List[ResearchItem]) -> str:
        """
        Generate and publish the intelligence report for the active run.

        Args:
            items (List[ResearchItem]): List of verified items to include.

        Returns:
            str: The raw generated report content (typically markdown/HTML).
        """
        pass


class MarkdownReporter(BaseDelivery):
    """Generates elegant, structured, and actionable Markdown reports from verified signals."""

    @property
    def name(self) -> str:
        return "MarkdownFile"

    def deliver(self, items: List[ResearchItem]) -> str:
        """
        Synthesize verified signals, write the markdown report to file, and return the string.

        Args:
            items (List[ResearchItem]): Target verified signals list.

        Returns:
            str: Generated markdown content.
        """
        if not items:
            self.logger.warning("No verified items found to construct report. Generating empty stub.")
            return "# Signal Hunter Daily Intelligence Report\n\nNo breakthroughs verified in this pipeline run."

        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        report_lines = [
            f"# 🎯 Signal Hunter Daily Intelligence Report - {date_str}",
            "---",
            "**Mission**: *Discover early opportunities, engineering breakthroughs, and scientific discoveries before they become mainstream.*",
            "",
            "## 📊 Executive Summary Dashboard",
            f"- **Total Signals Analyzed & Verified**: {len(items)}",
            f"- **Average Confidence Score**: {sum(item.confidence_score for item in items)/len(items):.2f}",
            "",
            "## ⚡ Primary Breakthroughs",
        ]

        # Group items by source type
        categories = {}
        for item in items:
            cat = item.source_type.replace("_", " ").title()
            categories.setdefault(cat, []).append(item)

        # Build categorized list
        idx = 1
        for cat, cat_items in categories.items():
            report_lines.append(f"### 📂 Category: {cat}")
            report_lines.append("")

            # Sort within category by confidence score descending
            cat_items.sort(key=lambda x: x.confidence_score, reverse=True)

            for item in cat_items:
                indicator = "🔥 [High Signal]" if item.confidence_score >= 0.90 else "💡 [Emerging]"
                report_lines.append(f"#### {idx}. {item.title}")
                report_lines.append(f"- **Confidence Rating**: `{item.confidence_score:.2f}` {indicator}")
                report_lines.append(f"- **Canonical URL**: <{item.url}>")
                if item.authors:
                    authors_str = ", ".join(a.name for a in item.authors)
                    report_lines.append(f"- **Author/Creator**: {authors_str}")
                report_lines.append("")
                report_lines.append("**Core Technical Summary:**")
                report_lines.append(f"> {item.summary or 'No summary provided.'}")
                report_lines.append("")
                report_lines.append("**Extracted Opportunities & Future Signals:**")
                for sig in item.signals:
                    report_lines.append(f"- 🚀 {sig}")
                report_lines.append("")
                if item.verifier_notes:
                    report_lines.append(f"*Verifier Critique:* {item.verifier_notes}")
                report_lines.append("")
                report_lines.append("---")
                idx += 1

        report_lines.append("")
        report_lines.append("`Signal Hunter Pipeline v1.0.0-Beta • Executed via local scheduler`")

        markdown_content = "\n".join(report_lines)

        # Output to disk
        out_dir = self.config.output_dir
        os.makedirs(out_dir, exist_ok=True)
        report_filename = f"daily_intelligence_brief_{date_str.replace('-', '_')}.md"
        report_path = os.path.join(out_dir, report_filename)

        try:
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(markdown_content)
            # Also save as latest.md so the web app can always fetch the latest report
            latest_path = os.path.join(out_dir, "latest.md")
            with open(latest_path, "w", encoding="utf-8") as f:
                f.write(markdown_content)
            self.logger.info("Successfully published daily markdown report to: %s and %s", report_path, latest_path)
        except Exception as e:
            self.logger.error("Failed to write daily markdown report files: %s", e)

        return markdown_content
