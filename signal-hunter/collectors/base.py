"""
Signal Hunter Abstract Base Collector.

Defines the required API and shared logging bootstrap for all ingestion collectors.
"""

from abc import ABC, abstractmethod
from typing import List
import logging

from config.config_loader import CollectorConfig
from models.research_item import ResearchItem
from utils.logger import setup_logger


class BaseCollector(ABC):
    """
    Abstract base class for all signal collectors.

    Every source crawler or API ingestor must implement this interface.
    """

    def __init__(self, config: CollectorConfig) -> None:
        """
        Initialize the base collector.

        Args:
            config (CollectorConfig): Source-specific configuration dictionary/model.
        """
        self.config = config
        self.logger: logging.Logger = setup_logger(
            name=f"signal_hunter.collectors.{self.name.lower()}",
            log_level="INFO",
        )
        self.logger.info(
            "Initialized collector '%s' (Enabled: %s)",
            self.name,
            config.enabled,
        )

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Return the unique descriptive name of the collector.

        Returns:
            str: Identifier (e.g. 'ArXiv', 'GitHub_Trending').
        """
        pass

    @abstractmethod
    def collect(self) -> List[ResearchItem]:
        """
        Scan external resources to gather potential breakthrough raw candidates.

        Returns:
            List[ResearchItem]: Discovered raw signals.

        Raises:
            CollectionError: If there's an issue executing the request or parsing.
        """
        pass
