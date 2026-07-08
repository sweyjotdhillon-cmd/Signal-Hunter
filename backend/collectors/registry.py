"""
Dynamic Source Registry for Signal Hunter.
Provides decoupled registration, metadata decoration, and dynamic sorting for ingest collectors.
"""

import logging
from typing import Dict, List, Type, Any
from collectors.base import BaseCollector
from config.config_loader import AppConfig, CollectorConfig
from utils.logger import setup_logger


class SourceRegistry:
    """
    Registry for managing signal source collectors dynamically.
    """

    def __init__(self) -> None:
        self.logger: logging.Logger = setup_logger(
            name="signal_hunter.collectors.registry",
            log_level="INFO",
        )
        self._collectors: Dict[str, Dict[str, Any]] = {}

    def register(
        self,
        collector_class: Type[BaseCollector],
        priority: int = 10,
        weight: float = 1.0,
    ) -> None:
        """
        Register a new collector class in the active registry.
        """
        name = collector_class.__name__
        self._collectors[name] = {
            "class": collector_class,
            "priority": priority,
            "weight": weight,
            "enabled": True,
        }
        self.logger.info(
            "Registered collector '%s' with priority %d and weight %.2f",
            name,
            priority,
            weight,
        )

    def enable(self, name: str) -> None:
        """
        Enable a collector by name.
        """
        if name in self._collectors:
            self._collectors[name]["enabled"] = True
            self.logger.info("Enabled collector '%s'", name)

    def disable(self, name: str) -> None:
        """
        Disable a collector by name.
        """
        if name in self._collectors:
            self._collectors[name]["enabled"] = False
            self.logger.info("Disabled collector '%s'", name)

    def set_priority(self, name: str, priority: int) -> None:
        """
        Set a collector's priority.
        """
        if name in self._collectors:
            self._collectors[name]["priority"] = priority
            self.logger.info("Set priority of collector '%s' to %d", name, priority)

    def set_weight(self, name: str, weight: float) -> None:
        """
        Set a collector's weight.
        """
        if name in self._collectors:
            self._collectors[name]["weight"] = weight
            self.logger.info("Set weight of collector '%s' to %.2f", name, weight)

    def get_enabled_collectors(self, config: AppConfig) -> List[BaseCollector]:
        """
        Return instances of enabled collectors, sorted by priority.
        """
        enabled_instances: List[BaseCollector] = []
        for name, meta in self._collectors.items():
            if not meta["enabled"]:
                continue

            # Determine config key
            config_key = name.lower().replace("collector", "")
            collector_config = config.collectors.get(config_key)

            # Check config override
            if collector_config and not collector_config.enabled:
                continue

            # Instantiate collector
            col_config = collector_config or CollectorConfig(
                enabled=True, sources=[], params={}
            )
            try:
                instance = meta["class"](col_config)
            except Exception:
                try:
                    instance = meta["class"]()
                except Exception as e:
                    self.logger.error("Failed to instantiate collector '%s': %s", name, e)
                    continue

            # Set decorated attributes
            instance.priority = meta["priority"]
            instance.weight = meta["weight"]
            enabled_instances.append(instance)

        # Sort by priority ascending (lower values execute first)
        enabled_instances.sort(key=lambda x: x.priority)
        return enabled_instances
