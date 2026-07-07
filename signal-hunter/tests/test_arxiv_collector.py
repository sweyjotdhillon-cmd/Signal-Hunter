"""
Unit tests for the ArXivCollector.

Tests cover XML parsing, configuration values, query building,
pagination logic, error handling, retries, and date filtering.
"""

import unittest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch

import requests

from collectors.arxiv import ArXivCollector
from config.config_loader import CollectorConfig
from models.research_item import ResearchItem
from utils.exceptions import CollectionError

MOCK_XML_RESPONSE = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom">
  <entry>
    <id>http://arxiv.org/abs/1706.03762v7</id>
    <updated>2023-08-02T13:38:15Z</updated>
    <published>2017-06-12T13:38:15Z</published>
    <title>Attention Is All You Need</title>
    <summary>The dominant sequence transduction models are based on recurrent or convolutional neural networks...</summary>
    <author>
      <name>Ashish Vaswani</name>
      <arxiv:affiliation>Google Brain</arxiv:affiliation>
    </author>
    <author>
      <name>Noam Shazeer</name>
    </author>
    <arxiv:doi>10.48550/arXiv.1706.03762</arxiv:doi>
    <link href="http://arxiv.org/abs/1706.03762v7" rel="alternate" type="text/html"/>
    <link title="pdf" href="http://arxiv.org/pdf/1706.03762v7" rel="related" type="application/pdf"/>
    <arxiv:primary_category term="cs.CL" scheme="http://arxiv.org/schemas/atom"/>
    <category term="cs.CL" scheme="http://arxiv.org/schemas/atom"/>
    <category term="cs.LG" scheme="http://arxiv.org/schemas/atom"/>
  </entry>
  <entry>
    <id>http://arxiv.org/abs/2005.14165v4</id>
    <updated>2020-05-28T00:00:00Z</updated>
    <published>2020-05-28T00:00:00Z</published>
    <title>Language Models are Few-Shot Learners</title>
    <summary>We demonstrate that scaling up language models greatly improves performance...</summary>
    <author>
      <name>Tom B. Brown</name>
      <arxiv:affiliation>OpenAI</arxiv:affiliation>
    </author>
    <link href="http://arxiv.org/abs/2005.14165v4" rel="alternate" type="text/html"/>
    <link title="pdf" href="http://arxiv.org/pdf/2005.14165v4" rel="related" type="application/pdf"/>
    <arxiv:primary_category term="cs.CL" scheme="http://arxiv.org/schemas/atom"/>
    <category term="cs.CL" scheme="http://arxiv.org/schemas/atom"/>
  </entry>
</feed>
"""


class TestArXivCollector(unittest.TestCase):
    """Test suite covering the features and correctness of the ArXivCollector."""

    def setUp(self) -> None:
        """Set up standard collector config and collector instance."""
        self.config = CollectorConfig(
            enabled=True,
            sources=["cs.AI", "cs.LG"],
            params={
                "max_results": 2,
                "timeout": 5.0,
                "retry_count": 2,
                "days_back": 10000,  # Ensure our mock dates are within cutoff
            },
        )
        self.collector = ArXivCollector(self.config)

    def test_collector_metadata_properties(self) -> None:
        """Ensure collector identifies correctly."""
        self.assertEqual(self.collector.name, "ArXiv")

    def test_search_query_building(self) -> None:
        """Verify standard categories and raw text terms are formatted correctly."""
        # Standard ArXiv categories with dots or typical prefixes
        categories = ["cs.AI", "stat.ML", "physics.optics"]
        query_cats = self.collector._build_search_query(categories)
        self.assertEqual(query_cats, "(cat:cs.AI OR cat:stat.ML OR cat:physics.optics)")

        # Normal text terms (single word and multi-word with quotes)
        text_terms = ["deep learning", "transformers", "LLM"]
        query_text = self.collector._build_search_query(text_terms)
        self.assertEqual(query_text, '(all:"deep learning" OR all:transformers OR all:LLM)')

        # Empty topics edge case
        self.assertEqual(self.collector._build_search_query([]), "")

    @patch("requests.get")
    def test_successful_collect_and_parsing(self, mock_get: MagicMock) -> None:
        """Verify successful fetch and correct parsing of XML into ResearchItem fields."""
        # Mock requests Response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = MOCK_XML_RESPONSE
        mock_get.return_value = mock_response

        items = self.collector.collect()

        # Assert correct length fetched
        self.assertEqual(len(items), 2)
        
        # Test first item mappings (Attention Is All You Need)
        item1 = items[0]
        self.assertIsInstance(item1, ResearchItem)
        self.assertEqual(item1.unique_id, "1706.03762v7")
        self.assertEqual(item1.title, "Attention Is All You Need")
        self.assertEqual(item1.source_name, "arXiv")
        self.assertEqual(item1.source_type, "preprint")
        self.assertEqual(item1.url, "http://arxiv.org/abs/1706.03762v7")
        
        # Date parsing verification
        self.assertIsNotNone(item1.publication_date)
        self.assertEqual(item1.publication_date.year, 2017)
        self.assertEqual(item1.publication_date.month, 6)

        # Authors and Affiliation extraction
        self.assertEqual(len(item1.authors), 2)
        self.assertEqual(item1.authors[0].name, "Ashish Vaswani")
        self.assertEqual(item1.authors[0].affiliation, "Google Brain")
        self.assertEqual(item1.authors[1].name, "Noam Shazeer")
        self.assertIsNone(item1.authors[1].affiliation)
        self.assertEqual(item1.organization, "Google Brain")

        # Category mapping
        self.assertIn("cs.CL", item1.categories)
        self.assertIn("cs.LG", item1.categories)
        self.assertEqual(item1.version, "1.0.0+v7")

        # Abstract parsing
        self.assertTrue(item1.summary.startswith("The dominant sequence transduction"))

        # DOI extraction
        self.assertEqual(item1.raw_metadata.get("doi"), "10.48550/arXiv.1706.03762")

    @patch("requests.get")
    def test_date_filtering_with_days_back(self, mock_get: MagicMock) -> None:
        """Assert that paper's updated/published dates are filtered properly using days_back."""
        # Set days_back to only collect paper from the last 10 days
        self.collector.config.params["days_back"] = 10
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = MOCK_XML_RESPONSE
        mock_get.return_value = mock_response

        items = self.collector.collect()
        
        # Both papers in mock XML are from 2017 and 2020, so they should be filtered out
        self.assertEqual(len(items), 0)

    @patch("requests.get")
    def test_retry_on_network_failure(self, mock_get: MagicMock) -> None:
        """Verify that requests.get is retried on network exceptions and eventually recovers."""
        # First request raises timeout, second succeeds
        mock_get.side_effect = [
            requests.RequestException("Timeout!"),
            MagicMock(status_code=200, text=MOCK_XML_RESPONSE)
        ]

        # Should successfully recover and collect
        items = self.collector.collect()
        self.assertEqual(len(items), 2)
        self.assertEqual(mock_get.call_count, 2)

    @patch("requests.get")
    def test_network_failure_exhaustion(self, mock_get: MagicMock) -> None:
        """Verify that max retries raise a CollectionError."""
        mock_get.side_effect = requests.RequestException("Permanent failure")

        with self.assertRaises(CollectionError):
            self.collector.collect()

    @patch("requests.get")
    def test_rate_limit_429_recovery(self, mock_get: MagicMock) -> None:
        """Assert that 429 responses trigger a sleep and retry successfully."""
        mock_429 = MagicMock(status_code=429)
        mock_200 = MagicMock(status_code=200, text=MOCK_XML_RESPONSE)

        mock_get.side_effect = [mock_429, mock_200]

        # Use short sleep during tests
        with patch("time.sleep") as mock_sleep:
            items = self.collector.collect()
            self.assertEqual(len(items), 2)
            self.assertTrue(mock_sleep.called)

    def test_malformed_xml_handling(self) -> None:
        """Check that fully corrupted XML raises a CollectionError."""
        bad_xml = "<feed><entry><title>Incomplete XML"
        
        with self.assertRaises(CollectionError):
            self.collector._parse_xml_feed(bad_xml, None)


if __name__ == "__main__":
    unittest.main()

