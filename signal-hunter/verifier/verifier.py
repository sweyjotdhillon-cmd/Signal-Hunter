"""
Signal Hunter Signal Verifier.

Assesses signal strength against minimum confidence thresholds and checks for structural validity.
"""

import logging

from config.config_loader import VerifierConfig
from models.research_item import ResearchItem
from utils.logger import setup_logger


class SignalVerifier:
    """
    Evaluates analyzed research items to confirm breakthrough authenticity.

    Ensures that only signals matching threshold requirements pass verification,
    thereby protecting downstream intelligence reporting from low-confidence noise.
    """

    def __init__(self, config: VerifierConfig) -> None:
        """
        Initialize the verifier.

        Args:
            config (VerifierConfig): Settings for confidence thresholds and validation mode.
        """
        self.config = config
        self.logger: logging.Logger = setup_logger(
            "signal_hunter.verifier",
            log_level="INFO",
        )
        self.logger.info(
            "Initialized SignalVerifier (Min Confidence: %s, Strict Mode: %s)",
            self.config.min_confidence_score,
            self.config.strict_mode,
        )

    def verify(self, item: ResearchItem) -> ResearchItem:
        """
        Assess if a ResearchItem's signals represent a legitimate opportunity.

        Sets `is_verified` and `verifier_notes` fields on the item.

        Args:
            item (ResearchItem): Enriched research item to check.

        Returns:
            ResearchItem: The item with populated verification decisions.
        """
        self.logger.info("Verifying signal item: %s (ID: %s)", item.title, item.id)

        # Baseline check: Confidence threshold check
        meets_confidence = item.confidence_score >= self.config.min_confidence_score

        # Rule-based validation if strict mode is active
        has_concrete_signals = len(item.signals) > 0
        has_adequate_summary = (
            item.summary is not None and len(item.summary) >= 20
        )

        is_valid = meets_confidence
        notes_list = []

        if meets_confidence:
            notes_list.append(
                f"Passed confidence threshold ({item.confidence_score} >= {self.config.min_confidence_score})."
            )
        else:
            notes_list.append(
                f"Failed confidence threshold ({item.confidence_score} < {self.config.min_confidence_score})."
            )

        if self.config.strict_mode:
            if not has_concrete_signals:
                is_valid = False
                notes_list.append("Strict validation failed: No concrete signal elements extracted.")
            if not has_adequate_summary:
                is_valid = False
                notes_list.append("Strict validation failed: Technical summary is too brief or missing.")

        item.is_verified = is_valid
        item.verifier_notes = " ".join(notes_list)

        if is_valid:
            self.logger.info("Item [%s] successfully VERIFIED as valid signal.", item.title)
        else:
            self.logger.warning("Item [%s] FAILED verification criteria.", item.title)

        return item
