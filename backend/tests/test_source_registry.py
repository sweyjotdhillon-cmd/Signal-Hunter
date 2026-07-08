"""
Unit tests for the SourceRegistry system in Signal Hunter.
"""

import unittest
from typing import List
from models.research_item import ResearchItem
from collectors.base import BaseCollector
from collectors.registry import SourceRegistry
from config.config_loader import AppConfig, CollectorConfig


class DummyCollectorA(BaseCollector):
    """Mock collector A for testing."""

    @property
    def name(self) -> str:
        return "DummyCollectorA"

    def collect(self) -> List[ResearchItem]:
        return []


class DummyCollectorB(BaseCollector):
    """Mock collector B for testing."""

    @property
    def name(self) -> str:
        return "DummyCollectorB"

    def collect(self) -> List[ResearchItem]:
        return []


class TestSourceRegistry(unittest.TestCase):
    """Test suite covering the features and correctness of the SourceRegistry."""

    def setUp(self) -> None:
        self.registry = SourceRegistry()
        self.config = AppConfig()

    def test_registration_and_get_enabled(self) -> None:
        """Verify collectors can be registered and retrieved when enabled."""
        self.registry.register(DummyCollectorA, priority=10, weight=1.5)
        self.registry.register(DummyCollectorB, priority=5, weight=2.0)

        enabled = self.registry.get_enabled_collectors(self.config)
        self.assertEqual(len(enabled), 2)
        
        # Sorted by priority (DummyCollectorB has priority 5, DummyCollectorA has priority 10)
        self.assertEqual(enabled[0].name, "DummyCollectorB")
        self.assertEqual(enabled[1].name, "DummyCollectorA")
        
        # Verify weight and priority decoration
        self.assertEqual(enabled[0].priority, 5)
        self.assertEqual(enabled[0].weight, 2.0)
        self.assertEqual(enabled[1].priority, 10)
        self.assertEqual(enabled[1].weight, 1.5)

    def test_enable_disable_state(self) -> None:
        """Verify collectors can be enabled and disabled."""
        self.registry.register(DummyCollectorA, priority=10)
        self.registry.register(DummyCollectorB, priority=20)

        # Disable Collector A
        self.registry.disable("DummyCollectorA")
        enabled = self.registry.get_enabled_collectors(self.config)
        self.assertEqual(len(enabled), 1)
        self.assertEqual(enabled[0].name, "DummyCollectorB")

        # Enable Collector A back
        self.registry.enable("DummyCollectorA")
        enabled = self.registry.get_enabled_collectors(self.config)
        self.assertEqual(len(enabled), 2)

    def test_priority_updates(self) -> None:
        """Verify priority updates change the retrieval order of collectors."""
        self.registry.register(DummyCollectorA, priority=10)
        self.registry.register(DummyCollectorB, priority=20)

        enabled = self.registry.get_enabled_collectors(self.config)
        self.assertEqual(enabled[0].name, "DummyCollectorA")

        # Set Collector B priority to lower value (higher execution order)
        self.registry.set_priority("DummyCollectorB", 5)
        enabled = self.registry.get_enabled_collectors(self.config)
        self.assertEqual(enabled[0].name, "DummyCollectorB")

    def test_weight_updates(self) -> None:
        """Verify source weight updates are reflected in active collector instances."""
        self.registry.register(DummyCollectorA, weight=1.0)
        
        self.registry.set_weight("DummyCollectorA", 4.5)
        enabled = self.registry.get_enabled_collectors(self.config)
        self.assertEqual(enabled[0].weight, 4.5)

    def test_config_override_states(self) -> None:
        """Verify application config overrides can enable/disable collectors dynamically."""
        self.registry.register(DummyCollectorA, priority=10)
        
        # Create an app config overriding "dummycollectora" (lowercase key mapping) to disabled
        override_config = AppConfig()
        override_config.collectors["dummya"] = CollectorConfig(enabled=False, sources=[], params={})
        
        # When mapped correctly using collector key:
        # get_enabled_collectors checks "config_key = name.lower().replace('collector', '')" -> "dummya"
        enabled = self.registry.get_enabled_collectors(override_config)
        self.assertEqual(len(enabled), 0)
