"""
Signal Hunter Unit Test Suite.

Executes baseline assertions verifying configurations, ResearchItem properties,
and SignalVerifier threshold filters.
"""

import unittest
from datetime import datetime

from config.config_loader import AppConfig, load_config, VerifierConfig
from models.research_item import ResearchItem
from verifier.verifier import SignalVerifier


class TestSignalHunterPipeline(unittest.TestCase):
    """Test suite targeting the main pipeline components and validation rules."""

    def test_config_loading_and_pydantic_parsing(self) -> None:
        """Verify settings.yaml loads correctly and hydrates into structured AppConfig."""
        config = load_config()
        self.assertIsInstance(config, AppConfig)
        self.assertEqual(config.app_name, "Signal Hunter")
        self.assertTrue("arxiv" in config.collectors)
        self.assertTrue(config.verifier.min_confidence_score > 0.0)

    def test_research_item_pydantic_constraints(self) -> None:
        """Assert ResearchItem field constraints, serialization, and default values work."""
        now = datetime.utcnow()
        item = ResearchItem(
            id="test-id-123",
            title="Breakthrough Quantum Computing Model",
            url="https://example.com/quantum",
            source_type="paper",
            raw_content="Abstract detailing high room-temperature superconductor breakthrough details...",
            collected_at=now,
        )
        self.assertEqual(item.id, "test-id-123")
        self.assertEqual(item.confidence_score, 0.0)
        self.assertFalse(item.is_verified)
        self.assertEqual(len(item.signals), 0)

    def test_signal_verifier_confidence_filter(self) -> None:
        """Verify SignalVerifier correctly triggers is_verified flags depending on confidence score."""
        verifier_config = VerifierConfig(min_confidence_score=0.80, strict_mode=False)
        verifier = SignalVerifier(verifier_config)

        now = datetime.utcnow()
        item = ResearchItem(
            id="test-id",
            title="Sparsely-Gated Mixture-of-Experts",
            url="https://arxiv.org/abs/1701.06538",
            source_type="paper",
            raw_content="We introduce a Sparsely-Gated Mixture-of-Experts layer to scale neural models...",
            collected_at=now,
            confidence_score=0.92,  # Greater than 0.80
        )

        verified_item = verifier.verify(item)
        self.assertTrue(verified_item.is_verified)
        self.assertIn("Passed confidence threshold", verified_item.verifier_notes or "")

        # Test failure scenario
        item.confidence_score = 0.50  # Less than 0.80
        failed_item = verifier.verify(item)
        self.assertFalse(failed_item.is_verified)
        self.assertIn("Failed confidence threshold", failed_item.verifier_notes or "")

    def test_signal_verifier_strict_mode(self) -> None:
        """Verify strict mode raises validation alarms if signals or summaries are empty."""
        verifier_config = VerifierConfig(min_confidence_score=0.70, strict_mode=True)
        verifier = SignalVerifier(verifier_config)

        now = datetime.utcnow()
        item = ResearchItem(
            id="test-id-strict",
            title="Prompt Tuning Breakthrough",
            url="https://arxiv.org/abs/2104.08691",
            source_type="paper",
            raw_content="Abstract...",
            collected_at=now,
            confidence_score=0.85,
            summary=None,  # Missing summary (strict violation)
            signals=[],  # Missing signals list (strict violation)
        )

        verified_item = verifier.verify(item)
        self.assertFalse(verified_item.is_verified)
        self.assertIn("Strict validation failed", verified_item.verifier_notes or "")


if __name__ == "__main__":
    unittest.main()
