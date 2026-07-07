"""
Unit Tests for NvidiaProvider and LLMAnalyzer.

Verifies the standard behavior, error handling, retries with exponential backoff,
invalid API key handling, rate-limiting behavior, and response validation.
"""

import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
import requests

from config.config_loader import AnalyzerConfig
from models.research_item import ResearchItem
from analyzers.providers import (
    NvidiaProvider,
    LLMAPIKeyError,
    LLMRateLimitError,
    LLMNetworkError,
    LLMValidationError,
)
from analyzers.llm_analyzer import LLMAnalyzer


class TestNvidiaProvider(unittest.TestCase):
    """Test suite for NvidiaProvider and LLMAnalyzer integrations."""

    def setUp(self) -> None:
        """Set up standard configurations."""
        self.config = AnalyzerConfig(
            enabled=True,
            model_name="meta/llama-3.1-70b-instruct",
            temperature=0.1,
            max_tokens=1500,
            api_key="nvapi-test-key-12345",
        )
        # Use extremely small delays in tests to keep test runs fast
        self.provider = NvidiaProvider(
            config=self.config,
            max_retries=3,
            initial_delay=0.001,
            backoff_factor=1.0,
        )

    def test_provider_initialization_reads_config(self) -> None:
        """Verify that the provider correctly extracts properties from AnalyzerConfig."""
        self.assertEqual(self.provider.api_key, "nvapi-test-key-12345")
        self.assertEqual(self.provider.model_name, "meta/llama-3.1-70b-instruct")

    @patch("requests.post")
    def test_generate_success(self, mock_post: MagicMock) -> None:
        """Verify that a successful HTTP 200 returns the generated text."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "This is a high-quality analysis summary."
                    }
                }
            ]
        }
        mock_post.return_value = mock_response

        text = self.provider.generate(prompt="Analyze this breakthrough.")
        self.assertEqual(text, "This is a high-quality analysis summary.")
        mock_post.assert_called_once()

    @patch("requests.post")
    def test_generate_unauthorized_fails_immediately(self, mock_post: MagicMock) -> None:
        """Verify that an HTTP 401/403 triggers LLMAPIKeyError immediately without retrying."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_post.return_value = mock_response

        with self.assertRaises(LLMAPIKeyError):
            self.provider.generate(prompt="Test prompt.")

        # Should fail fast and not retry
        mock_post.assert_called_once()

    @patch("requests.post")
    def test_generate_rate_limiting_retries_and_succeeds(self, mock_post: MagicMock) -> None:
        """Verify that HTTP 429 is retried with backoff and can eventually succeed."""
        mock_response_rate_limit = MagicMock()
        mock_response_rate_limit.status_code = 429

        mock_response_success = MagicMock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {
            "choices": [{"message": {"content": "Success after rate limit."}}]
        }

        # First call: 429, Second call: 200 success
        mock_post.side_effect = [mock_response_rate_limit, mock_response_success]

        text = self.provider.generate(prompt="Test prompt.")
        self.assertEqual(text, "Success after rate limit.")
        self.assertEqual(mock_post.call_count, 2)

    @patch("requests.post")
    def test_generate_rate_limit_max_retries_exceeded(self, mock_post: MagicMock) -> None:
        """Verify that persistent HTTP 429 eventually raises LLMRateLimitError."""
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_post.return_value = mock_response

        with self.assertRaises(LLMRateLimitError):
            self.provider.generate(prompt="Test prompt.")

        self.assertEqual(mock_post.call_count, 3)  # Max retries is 3

    @patch("requests.post")
    def test_generate_network_failure_retries_and_succeeds(self, mock_post: MagicMock) -> None:
        """Verify that connection/timeout exceptions are retried and can succeed."""
        mock_response_success = MagicMock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {
            "choices": [{"message": {"content": "Success after timeout."}}]
        }

        # First call raises timeout, second call succeeds
        mock_post.side_effect = [requests.exceptions.Timeout("Connection timed out"), mock_response_success]

        text = self.provider.generate(prompt="Test prompt.")
        self.assertEqual(text, "Success after timeout.")
        self.assertEqual(mock_post.call_count, 2)

    @patch("requests.post")
    def test_generate_network_failure_max_retries_exceeded(self, mock_post: MagicMock) -> None:
        """Verify that persistent network failures eventually raise LLMNetworkError."""
        mock_post.side_effect = requests.exceptions.ConnectionError("DNS failure")

        with self.assertRaises(LLMNetworkError):
            self.provider.generate(prompt="Test prompt.")

        self.assertEqual(mock_post.call_count, 3)

    @patch("requests.post")
    def test_generate_structured_success_with_json_and_markdown(self, mock_post: MagicMock) -> None:
        """Verify that JSON format is correctly parsed, even when enclosed in markdown code blocks."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        # Return response wrapped in ```json ... ``` code blocks
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": '```json\n{\n  "summary": "AI surveyed.",\n  "signals": ["quantization", "llm"]\n}\n```'
                    }
                }
            ]
        }
        mock_post.return_value = mock_response

        data = self.provider.generate_structured(
            prompt="Structured prompt",
            expected_keys=["summary", "signals"]
        )

        self.assertEqual(data["summary"], "AI surveyed.")
        self.assertEqual(data["signals"], ["quantization", "llm"])

    @patch("requests.post")
    def test_generate_structured_validation_missing_keys_raises_error(self, mock_post: MagicMock) -> None:
        """Verify that JSON missing expected keys raises LLMValidationError."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": '{"summary": "Missing signals key"}'
                    }
                }
            ]
        }
        mock_post.return_value = mock_response

        with self.assertRaises(LLMValidationError) as ctx:
            self.provider.generate_structured(
                prompt="Structured prompt",
                expected_keys=["summary", "signals"]
            )
        self.assertIn("missing required keys", str(ctx.exception))

    @patch("requests.post")
    def test_generate_structured_malformed_json_raises_error(self, mock_post: MagicMock) -> None:
        """Verify that invalid/malformed JSON string raises LLMValidationError."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "{ malformed json content"
                    }
                }
            ]
        }
        mock_post.return_value = mock_response

        with self.assertRaises(LLMValidationError) as ctx:
            self.provider.generate_structured(
                prompt="Structured prompt",
                expected_keys=["summary"]
            )
        self.assertIn("Model response is not valid JSON", str(ctx.exception))

    def test_analyzer_with_injected_provider(self) -> None:
        """Verify LLMAnalyzer correctly interacts with injected BaseLLMProvider to enrich ResearchItem."""
        # Create a mock provider that returns a valid dictionary
        mock_provider = MagicMock()
        mock_provider.generate_structured.return_value = {
            "summary": "Deep learning techniques are advancing rapidly.",
            "signals": ["Transformer architecture scaling signal", "Compute hardware breakthrough"],
            "technologies": ["PyTorch", "FlashAttention"],
            "programming_languages": ["Python", "C++"],
            "build_opportunities": ["Optimized inference engine on serverless"],
            "risks": ["VRAM footprint is high"],
        }

        analyzer = LLMAnalyzer(config=self.config, provider=mock_provider)

        item = ResearchItem(
            id="item-test-enrich",
            title="Sparsely-Gated Mixture-of-Experts",
            url="https://arxiv.org/abs/1701.06538",
            source_type="paper",
            raw_content="We introduce a MoE layer to scale neural network capacity.",
            discovered_date=datetime.now(timezone.utc),
            publication_date=datetime.now(timezone.utc),
            confidence_score=0.8,
        )

        enriched_item = analyzer.analyze(item)

        # Verify fields on the ResearchItem were populated correctly
        self.assertEqual(enriched_item.summary, "Deep learning techniques are advancing rapidly.")
        self.assertIn("Transformer architecture scaling signal", enriched_item.signals)
        self.assertIn("PyTorch", enriched_item.technologies)
        self.assertIn("Python", enriched_item.programming_languages)
        self.assertIn("Optimized inference engine on serverless", enriched_item.build_opportunities)
        self.assertIn("VRAM footprint is high", enriched_item.risks)


if __name__ == "__main__":
    unittest.main()
