"""
Signal Hunter Validation & Normalization Engine Tests.

Verifies the standardizations and validation checks of the Normalizer and Verifier modules.
"""

import unittest
from datetime import datetime, timezone, timedelta

from models.research_item import ResearchItem, Author, VerificationState
from normalizer.normalizer import PlaceholderNormalizer
from verifier.verifier import SignalVerifier, VerifierConfig


class TestValidationEngine(unittest.TestCase):
    """
    Validation and normalization unit test suite.
    """

    def setUp(self) -> None:
        """Set up test instances."""
        self.normalizer = PlaceholderNormalizer()
        self.config = VerifierConfig(min_confidence_score=0.7, strict_mode=False)
        self.verifier = SignalVerifier(self.config)

    def test_valid_item_normalization_and_verification(self) -> None:
        """Verify full normalization and verification on a standard, well-formed item."""
        # Create a valid raw item with whitespace issues, lowercased names, and raw URLs
        item = ResearchItem(
            id="unique-1",
            title="  Deep learning in python and pytorch  ",
            summary="A comprehensive survey of deep learning techniques using python.",
            url="https://arxiv.org/abs/123.456/",
            source_type="arxiv",
            discovered_date=datetime(2026, 7, 7, 10, 0, tzinfo=timezone.utc),
            publication_date="2026-07-06T15:30:00Z",
            authors=[
                Author(
                    name="  john smith ",
                    email=" JOHN@Example.Com  ",
                    github_username=" @johnsmith ",
                    website="https://johnsmith.com/"
                )
            ],
            categories=["cs.ai ", " CS.LG"],
            tags=["Deep learning", "  pytorch"],
            confidence_score=0.9,
            opportunity_score=0.8,
            engineering_score=0.8,
            scientific_score=0.8,
            startup_score=0.8,
            novelty_score=0.8
        )

        # 1. Normalization Step
        normalized = self.normalizer.process([item])[0]
        self.assertEqual(normalized.title, "Deep learning in python and pytorch")
        self.assertEqual(normalized.url, "https://arxiv.org/abs/123.456")
        self.assertEqual(normalized.publication_date.tzinfo, timezone.utc)
        self.assertEqual(normalized.authors[0].name, "John Smith")
        self.assertEqual(normalized.authors[0].email, "john@example.com")
        self.assertEqual(normalized.authors[0].github_username, "johnsmith")
        self.assertEqual(normalized.authors[0].website, "https://johnsmith.com")

        # Check standardized categories and tags
        self.assertIn("cs.AI", normalized.categories)
        self.assertIn("cs.LG", normalized.categories)
        self.assertIn("deep learning", normalized.tags)
        self.assertIn("pytorch", normalized.tags)

        # Check programming languages and technologies auto-extraction & normalization
        self.assertIn("Python", normalized.programming_languages)
        self.assertIn("PyTorch", normalized.technologies)

        # 2. Verification Step
        verified = self.verifier.verify(normalized)
        report = verified.verification_status.extra_metadata.get("report", {})
        self.assertEqual(report.get("status"), "VERIFIED")
        self.assertGreaterEqual(report.get("verification_score"), 85.0)
        self.assertTrue(verified.is_verified)
        self.assertEqual(verified.verification_status.state, VerificationState.VERIFIED)

    def test_corrupted_items_raised_by_pydantic(self) -> None:
        """Verify that score fields lying outside [0.0, 1.0] raise initialization errors in Pydantic."""
        with self.assertRaises(Exception):
            ResearchItem(
                id="corrupted-uid",
                title="Malformed Scores Item",
                url="https://valid-url.com",
                source_type="arxiv",
                discovered_date=datetime.now(timezone.utc),
                publication_date=datetime.now(timezone.utc),
                startup_score=1.5,  # Out of bounds: must be <= 1.0
                confidence_score=0.8
            )

    def test_missing_metadata(self) -> None:
        """Verify that a missing raw_metadata dictionary is checked by verification."""
        item = ResearchItem(
            id="missing-meta-uid",
            title="Missing Raw Metadata Item",
            url="https://valid-url.com",
            source_type="arxiv",
            discovered_date=datetime.now(timezone.utc),
            publication_date=datetime.now(timezone.utc),
            confidence_score=0.8
        )
        item.raw_metadata = None  # Force metadata to be missing/invalid
        verified = self.verifier.verify(item)
        report = verified.verification_status.extra_metadata.get("report", {})
        self.assertIn("Raw metadata is invalid or missing", report.get("failed_checks", []))

    def test_invalid_urls_raised_by_pydantic_and_future_dates_by_verifier(self) -> None:
        """Verify that invalid URL protocols raise Pydantic errors and future dates fail Verifier checks."""
        # 1. URL scheme validation raises at instantiation
        with self.assertRaises(Exception):
            ResearchItem(
                id="invalid-url-uid",
                title="Invalid URL Scheme",
                url="ftp://arxiv.org/invalid-scheme",  # FTP scheme not supported
                source_type="arxiv",
                discovered_date=datetime.now(timezone.utc),
                publication_date=datetime.now(timezone.utc),
                confidence_score=0.8
            )

        # 2. Future publication date fails verifier validation
        future_date = datetime.now(timezone.utc) + timedelta(days=5)
        item = ResearchItem(
            id="future-date-uid",
            title="Future Date Item",
            url="https://arxiv.org/abs/future",
            source_type="arxiv",
            discovered_date=datetime.now(timezone.utc),
            publication_date=future_date,
            confidence_score=0.8
        )
        verified = self.verifier.verify(item)
        report = verified.verification_status.extra_metadata.get("report", {})
        self.assertEqual(report.get("status"), "FAILED")
        self.assertIn("Publication date is in the future", report.get("failed_checks", []))
        self.assertFalse(verified.is_verified)

    def test_duplicate_ids_in_batch(self) -> None:
        """Verify duplicate IDs in a single batch trigger warnings on successive items."""
        item_1 = ResearchItem(
            id="dup-id",
            title="First Item",
            url="https://example.com/1",
            source_type="arxiv",
            discovered_date=datetime.now(timezone.utc),
            publication_date=datetime.now(timezone.utc),
            confidence_score=0.8
        )
        item_2 = ResearchItem(
            id="dup-id",  # Duplicate ID
            title="Second Item with Duplicate ID",
            url="https://example.com/2",
            source_type="arxiv",
            discovered_date=datetime.now(timezone.utc),
            publication_date=datetime.now(timezone.utc),
            confidence_score=0.8
        )

        processed = self.verifier.process([item_1, item_2])

        # First item passes batch uniqueness
        report_1 = processed[0].verification_status.extra_metadata.get("report", {})
        self.assertIn("Unique ID in current batch", report_1.get("passed_checks", []))

        # Second item fails batch uniqueness
        report_2 = processed[1].verification_status.extra_metadata.get("report", {})
        self.assertIn("Duplicate ID detected in batch", report_2.get("failed_checks", []))


if __name__ == "__main__":
    unittest.main()
