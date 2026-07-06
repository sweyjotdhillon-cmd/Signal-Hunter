"""
Signal Hunter Custom Exception Hierarchy.

This module provides standard error classes to ensure distinct and
structured error handling throughout the pipeline execution.
"""


class SignalHunterError(Exception):
    """Base exception for all Signal Hunter errors."""

    def __init__(self, message: str) -> None:
        """
        Initialize the base exception.

        Args:
            message (str): Explanatory error message.
        """
        super().__init__(message)
        self.message = message


class ConfigurationError(SignalHunterError):
    """Raised when there is an issue loading or parsing configuration files or environmental variables."""

    pass


class CollectionError(SignalHunterError):
    """Raised when a collector fails to gather signals from its source."""

    def __init__(self, collector_name: str, message: str) -> None:
        """
        Initialize collection error.

        Args:
            collector_name (str): Name of the collector that failed.
            message (str): Root cause details.
        """
        super().__init__(f"Collector [{collector_name}] failed: {message}")
        self.collector_name = collector_name


class AnalysisError(SignalHunterError):
    """Raised when an analyzer fails during deep signal processing or insight extraction."""

    def __init__(self, analyzer_name: str, message: str) -> None:
        """
        Initialize analysis error.

        Args:
            analyzer_name (str): Name of the analyzer that failed.
            message (str): Root cause details.
        """
        super().__init__(f"Analyzer [{analyzer_name}] failed: {message}")
        self.analyzer_name = analyzer_name


class VerificationError(SignalHunterError):
    """Raised when the validation or verification process fails or faces unexpected states."""

    pass


class StorageError(SignalHunterError):
    """Raised when reading or writing records to persistence layer (e.g. JSON Memory store) fails."""

    pass


class DeliveryError(SignalHunterError):
    """Raised when the report generation or delivery channel (e.g. Email, Slack, Console) fails."""

    pass
