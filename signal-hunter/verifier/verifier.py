"""
Signal Hunter Signal Verifier.

Assesses signal strength against minimum confidence thresholds and checks for structural validity.
"""

import logging
from typing import List

from config.config_loader import VerifierConfig
from models.research_item import ResearchItem
from utils.logger import setup_logger
from utils.exceptions import VerificationError
from verifier.base import BaseVerifier


"""
Signal Hunter Signal Verifier.

Assesses signal strength against minimum confidence thresholds, checks for structural validity,
and generates comprehensive verification reports.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel, Field

from config.config_loader import VerifierConfig
from models.research_item import ResearchItem, VerificationState
from utils.logger import setup_logger
from utils.exceptions import VerificationError
from verifier.base import BaseVerifier


class VerificationReport(BaseModel):
    """
    Structured report capturing the results of the pipeline verification stage.
    """
    passed_checks: List[str] = Field(default_factory=list)
    failed_checks: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    verification_score: float = Field(default=0.0, ge=0.0, le=100.0)
    status: str = Field(default="FAILED")  # VERIFIED, PARTIALLY_VERIFIED, FAILED


class SignalVerifier(BaseVerifier):
    """
    Evaluates research items to confirm authenticity, completeness, and correctness.

    Ensures that only signals matching validation and confidence thresholds pass
    verification, protecting downstream intelligence reporting from low-confidence noise.
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

    def process(self, items: List[ResearchItem]) -> List[ResearchItem]:
        """
        Process multiple research items through verification rules.

        Args:
            items (List[ResearchItem]): List of items to verify.

        Returns:
            List[ResearchItem]: List of items with updated verification fields.

        Raises:
            VerificationError: If verification process fails unexpectedly.
        """
        self.logger.info("Starting verification stage on %d items", len(items))
        verified_list: List[ResearchItem] = []
        seen_ids: Set[str] = set()

        for item in items:
            try:
                verified_item = self.verify(item, seen_ids=seen_ids)
                if verified_item.id:
                    seen_ids.add(verified_item.id)
                verified_list.append(verified_item)
            except Exception as e:
                self.logger.error("Error verifying item %s: %s", getattr(item, "id", "Unknown"), e)
                raise VerificationError(f"Verification stage failed: {e}") from e
        return verified_list

    def verify(self, item: ResearchItem, seen_ids: Optional[Set[str]] = None) -> ResearchItem:
        """
        Assess if a ResearchItem's signals represent a legitimate opportunity.

        Sets `is_verified`, `verifier_notes`, and `verification_status` fields on the item.

        Args:
            item (ResearchItem): Enriched research item to check.
            seen_ids (Optional[Set[str]]): IDs already processed in the current batch for duplicate detection.

        Returns:
            ResearchItem: The item with populated verification decisions.
        """
        self.logger.info("Verifying signal item: %s (ID: %s)", item.title, item.id)

        passed_checks: List[str] = []
        failed_checks: List[str] = []
        warnings: List[str] = []
        score: float = 0.0

        # Check 1: Required fields exist
        required_missing = []
        if not getattr(item, "unique_id", None) or not item.unique_id.strip():
            required_missing.append("unique_id")
        if not getattr(item, "title", None) or not item.title.strip():
            required_missing.append("title")
        if not getattr(item, "url", None) or not item.url.strip():
            required_missing.append("url")
        if not getattr(item, "source_type", None) or not item.source_type.strip():
            required_missing.append("source_type")
        if not getattr(item, "discovered_date", None):
            required_missing.append("discovered_date")

        if not required_missing:
            passed_checks.append("Required fields exist")
            score += 15
        else:
            failed_checks.append(f"Required fields missing: {', '.join(required_missing)}")

        # Check 2: URL format is valid
        url = getattr(item, "url", "")
        if url and (url.startswith("http://") or url.startswith("https://")):
            passed_checks.append("URL format is valid")
            score += 15
        else:
            failed_checks.append("URL is invalid or missing scheme")

        # Check 3: Publication date is valid (past or present UTC)
        pub_date = getattr(item, "publication_date", None)
        if pub_date:
            now_utc = datetime.now(timezone.utc)
            tz_pub = pub_date.replace(tzinfo=timezone.utc) if pub_date.tzinfo is None else pub_date.astimezone(timezone.utc)
            if tz_pub <= now_utc:
                passed_checks.append("Publication date is valid")
                score += 15
            else:
                warnings.append("Publication date is in the future")
                failed_checks.append("Publication date is in the future")
        else:
            warnings.append("Publication date is missing")
            score += 5  # Give partial credit for missing but not future/invalid date

        # Check 4: Duplicate IDs check
        is_duplicate = False
        item_id = getattr(item, "id", None)
        if seen_ids is not None and item_id in seen_ids:
            is_duplicate = True

        if not is_duplicate:
            passed_checks.append("Unique ID in current batch")
            score += 15
        else:
            failed_checks.append("Duplicate ID detected in batch")

        # Check 5: Empty technical summaries
        summary = getattr(item, "summary", "")
        if summary and len(summary.strip()) >= 20:
            passed_checks.append("Non-empty technical summary")
            score += 15
        elif summary and len(summary.strip()) > 0:
            warnings.append("Technical summary is too brief")
            failed_checks.append("Technical summary is too brief")
            score += 5
        else:
            warnings.append("Technical summary is empty")
            failed_checks.append("Technical summary is empty")

        # Check 6: Title verification
        title = getattr(item, "title", "")
        if title and len(title.strip()) > 0:
            passed_checks.append("Title is valid and non-empty")
            score += 15
        else:
            failed_checks.append("Title is missing or empty")

        # Check 7: Invalid or missing metadata check
        raw_metadata = getattr(item, "raw_metadata", None)
        if isinstance(raw_metadata, dict):
            passed_checks.append("Raw metadata integrity check passed")
            score += 5
        else:
            failed_checks.append("Raw metadata is invalid or missing")

        # Check 8: Broken or malformed objects (bounds check on scores)
        scores_valid = True
        for score_field in ["opportunity_score", "engineering_score", "scientific_score", "startup_score", "confidence_score", "novelty_score"]:
            val = getattr(item, score_field, 0.0)
            if not isinstance(val, (int, float)) or not (0.0 <= val <= 1.0):
                scores_valid = False
                break

        if scores_valid:
            passed_checks.append("No score malformations detected")
            score += 5
        else:
            failed_checks.append("Object scores are malformed or out of bounds")

        # Determine overall verification status
        critical_failed = False
        if "Title is missing or empty" in failed_checks:
            critical_failed = True
        if any(f.startswith("Required fields missing") for f in failed_checks):
            critical_failed = True
        if "URL is invalid or missing scheme" in failed_checks:
            critical_failed = True
        if "Object scores are malformed or out of bounds" in failed_checks:
            critical_failed = True
        if "Publication date is in the future" in failed_checks:
            critical_failed = True

        if critical_failed:
            status = "FAILED"
        elif score >= 85:
            status = "VERIFIED"
        elif score >= 50:
            status = "PARTIALLY_VERIFIED"
        else:
            status = "FAILED"

        # Construct and log decision
        self.logger.info(
            "Verification decision for '%s' (ID: %s): Status=%s, Score=%d/100, Passed=%d, Failed=%d, Warnings=%d",
            item.title, item.id, status, score, len(passed_checks), len(failed_checks), len(warnings)
        )

        # Map to VerificationState Enum
        if status == "VERIFIED":
            state = VerificationState.VERIFIED
        elif status == "PARTIALLY_VERIFIED":
            state = VerificationState.FLAGGED
        else:
            state = VerificationState.REJECTED

        # Hydrate verification status model
        item.verification_status.state = state
        item.verification_status.verified_by = "VerificationEngine"
        item.verification_status.verified_at = datetime.utcnow()
        item.verification_status.score = score / 100.0  # ge=0.0, le=1.0

        # Construct detailed verifier notes for backward compatibility
        meets_confidence = item.confidence_score >= self.config.min_confidence_score
        notes_list = []
        if meets_confidence:
            notes_list.append(
                f"Passed confidence threshold ({item.confidence_score} >= {self.config.min_confidence_score})."
            )
        else:
            notes_list.append(
                f"Failed confidence threshold ({item.confidence_score} < {self.config.min_confidence_score})."
            )

        notes_list.append(f"Engine Status: {status} (Score: {int(score)}).")
        if failed_checks:
            notes_list.append(f"Failed: {', '.join(failed_checks)}.")
        if warnings:
            notes_list.append(f"Warnings: {', '.join(warnings)}.")

        # Determine is_verified (backward compatibility check)
        has_concrete_signals = len(item.signals) > 0
        has_adequate_summary = item.summary is not None and len(item.summary) >= 20

        is_valid = meets_confidence
        if self.config.strict_mode:
            if not has_concrete_signals:
                is_valid = False
                notes_list.append("Strict validation failed: No concrete signal elements extracted.")
            if not has_adequate_summary:
                is_valid = False
                notes_list.append("Strict validation failed: Technical summary is too brief or missing.")

        if status == "FAILED":
            is_valid = False

        # Save notes on both properties (including any strict mode additions)
        item.verification_status.notes = " ".join(notes_list)
        item.verifier_notes = item.verification_status.notes
        item.is_verified = is_valid

        # Keep structured report in extra metadata
        report = VerificationReport(
            passed_checks=passed_checks,
            failed_checks=failed_checks,
            warnings=warnings,
            verification_score=score,
            status=status
        )
        item.verification_status.extra_metadata["report"] = report.model_dump()

        if is_valid:
            self.logger.info("Item [%s] successfully VERIFIED as valid signal.", item.title)
        else:
            self.logger.warning("Item [%s] FAILED verification criteria.", item.title)

        return item

