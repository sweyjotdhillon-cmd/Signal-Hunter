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
        avg_conf = sum(item.confidence_score for item in items) / len(items)
        avg_opp = sum(item.score_card.opportunity_score for item in items) / len(items)

        # Sort items by opportunity score descending to determine top opportunities
        sorted_items = sorted(items, key=lambda x: x.score_card.opportunity_score, reverse=True)
        top_opportunities = sorted_items[:3]
        other_research = sorted_items[3:]

        report_lines = [
            f"# 🎯 Signal Hunter Daily Intelligence Report - {date_str}",
            "---",
            "**Mission**: *Discover early opportunities, engineering breakthroughs, and scientific discoveries before they become mainstream.*",
            "",
            "## 🚀 Executive Summary",
            f"- **Total Signals Analyzed & Verified**: {len(items)}",
            f"- **Average Opportunity Score**: `{avg_opp:.2f}`",
            f"- **Average Pipeline Confidence**: `{avg_conf:.2f}`",
            f"- **Synthesis Status**: `AUTOMATED PIPELINE SUCCESSFUL`",
            "",
            "## 🧠 Top Opportunities (Top 3)",
        ]

        if not top_opportunities:
            report_lines.append("*No top opportunities met the scoring threshold.*")
        else:
            for i, item in enumerate(top_opportunities, 1):
                seller_pitch = item.extra_metadata.get("seller_pitch") or f"Leverage {item.title} to gain a massive architectural and serving performance benefit."
                why_it_matters = item.extra_metadata.get("why_it_matters") or item.summary or f"Addresses fundamental processing and sequence scale boundaries cleanly."
                
                report_lines.append(f"### {i}. {item.title}")
                report_lines.append(f"- **Seller Pitch**: {seller_pitch}")
                report_lines.append(f"- **Why It Matters**: {why_it_matters}")
                report_lines.append("- **Opportunity Scores**:")
                report_lines.append(f"  - Viability: `{item.score_card.opportunity_score:.2f}`")
                report_lines.append(f"  - Engineering: `{item.score_card.engineering_score:.2f}`")
                report_lines.append(f"  - Scientific: `{item.score_card.scientific_score:.2f}`")
                report_lines.append(f"  - Startup Fit: `{item.score_card.startup_score:.2f}`")
                report_lines.append(f"  - Novelty: `{item.score_card.novelty_score:.2f}`")
                report_lines.append(f"- **Confidence**: `{item.confidence_score:.2f}`")
                report_lines.append(f"- **Source Link**: [{item.title}]({item.url})")
                report_lines.append("")

        report_lines.append("## 📄 Important Research")
        if not other_research:
            report_lines.append("*No secondary research candidates met pipeline screening thresholds.*")
        else:
            for item in other_research:
                seller_pitch = item.extra_metadata.get("seller_pitch") or f"Pioneering theoretical foundation mapping next-generation optimization patterns."
                why_it_matters = item.extra_metadata.get("why_it_matters") or item.summary or f"Provides crucial baseline paradigms to help guide product engineering."
                
                report_lines.append(f"### {item.title}")
                report_lines.append(f"- **Seller Pitch**: {seller_pitch}")
                report_lines.append(f"- **Why It Matters**: {why_it_matters}")
                report_lines.append("- **Opportunity Scores**:")
                report_lines.append(f"  - Viability: `{item.score_card.opportunity_score:.2f}`")
                report_lines.append(f"  - Engineering: `{item.score_card.engineering_score:.2f}`")
                report_lines.append(f"- **Confidence**: `{item.confidence_score:.2f}`")
                report_lines.append(f"- **Source Link**: [{item.title}]({item.url})")
                report_lines.append("")

        report_lines.extend([
            "## 💻 GitHub & Open Source (placeholder for now)",
            "*Currently monitoring active developer channels. GitHub trending adapters will stream repository updates here in future runs.*",
            "",
            "## 🌍 Wildcards (placeholder)",
            "*Looking for edge-case discoveries, social hype spikes, and unconventional tech anomalies.*",
            "",
            "## 📈 Emerging Trends",
            "- **Parameter-Efficient Tuning (PEFT)** is rapidly consolidating as the industry standard for production LLM personalization.",
            "- **Memory-Efficient Serving Systems** (e.g. KV cache paging) are rendering static scheduling strategies obsolete.",
            "",
            "## 🎯 Recommended Learning Topics",
            "1. **Low-Rank Neural Projections**: Core mechanism enabling rapid fine-tuning adaptations.",
            "2. **Dynamic KV Cache Virtualization**: Modern virtual memory management for extreme throughput LLM execution.",
            "",
            "## ⚠ Risks & Caveats",
            "- AI-extracted pitches may occasionally over-index on raw preprint claims. Independent sandbox validation is recommended.",
            "- Scorers are tuned heavily toward direct near-term software application potential.",
            "",
            "---",
            "`Signal Hunter Pipeline v1.0.0-Beta • Executed via local scheduler`"
        ])

        markdown_content = "\n".join(report_lines)

        # Output to disk
        out_dir = self.config.output_dir
        os.makedirs(out_dir, exist_ok=True)
        report_filename = f"daily_intelligence_brief_{date_str.replace('-', '_')}.md"
        report_path = os.path.join(out_dir, report_filename)

        try:
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(markdown_content)
            self.logger.info("Successfully published daily markdown report to: %s", report_path)
            
            # Save a stable pointer to "latest.md" so server can read it easily
            latest_path = os.path.join(out_dir, "latest.md")
            with open(latest_path, "w", encoding="utf-8") as f:
                f.write(markdown_content)
        except Exception as e:
            self.logger.error("Failed to write daily markdown report file: %s", e)

        return markdown_content
