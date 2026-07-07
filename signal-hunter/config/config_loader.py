"""
Signal Hunter Configuration Loader.

Parses YAML config structures into structured, verified Pydantic model configurations.
"""

import os
from typing import Any, Dict, List, Optional
import yaml
from pydantic import BaseModel, Field

from utils.exceptions import ConfigurationError


class CollectorConfig(BaseModel):
    """Configuration schema for single collector integrations."""

    enabled: bool = True
    sources: List[str] = Field(default_factory=list)
    cron: Optional[str] = None
    params: Dict[str, Any] = Field(default_factory=dict)


class AnalyzerConfig(BaseModel):
    """Configuration schema for AI processing and model settings."""

    enabled: bool = True
    model_name: str = "gemini-2.5-flash"
    temperature: float = 0.1
    max_tokens: int = 1500
    api_key: Optional[str] = Field(default=None)
    api_url: Optional[str] = Field(default=None)


class VerifierConfig(BaseModel):
    """Configuration schema for validating breakthrough signals and removing noise."""

    min_confidence_score: float = Field(default=0.75, ge=0.0, le=1.0)
    strict_mode: bool = False


class MemoryConfig(BaseModel):
    """Configuration schema for local persistent memory files."""

    storage_dir: str = "data"
    backup_enabled: bool = True


class DeliveryConfig(BaseModel):
    """Configuration schema for reporting outputs."""

    channels: List[str] = Field(default_factory=lambda: ["console"])
    output_dir: str = "reports"


class AppConfig(BaseModel):
    """Root configuration object representing the full system settings."""

    app_name: str = "Signal Hunter"
    log_level: str = "INFO"
    collectors: Dict[str, CollectorConfig] = Field(default_factory=dict)
    analyzers: Dict[str, AnalyzerConfig] = Field(default_factory=dict)
    verifier: VerifierConfig = Field(default_factory=VerifierConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    delivery: DeliveryConfig = Field(default_factory=DeliveryConfig)


def load_config(config_path: Optional[str] = None) -> AppConfig:
    """
    Search, parse, and validate configuration files into a validated AppConfig model.

    Priority:
    1. Direct file input (config_path)
    2. Local custom file `config/local_settings.yaml` (untoggled git config)
    3. Standard settings file `config/settings.yaml`

    Args:
        config_path (Optional[str]): Specified location override.

    Returns:
        AppConfig: Validated system settings configuration model.

    Raises:
        ConfigurationError: If no configuration file is found or file is invalid YAML.
    """
    candidates = []

    if config_path:
        candidates.append(config_path)

    # Resolve paths relative to where this file lives
    current_dir = os.path.dirname(os.path.abspath(__file__))
    candidates.append(os.path.join(current_dir, "local_settings.yaml"))
    candidates.append(os.path.join(current_dir, "settings.yaml"))

    selected_path = None
    for candidate in candidates:
        if os.path.exists(candidate):
            selected_path = candidate
            break

    if not selected_path:
        raise ConfigurationError(
            f"No configuration file found in candidate locations: {candidates}"
        )

    try:
        with open(selected_path, "r", encoding="utf-8") as f:
            raw_data = yaml.safe_load(f) or {}

        # Parse into Pydantic Model to guarantee correct shapes
        return AppConfig(**raw_data)
    except yaml.YAMLError as e:
        raise ConfigurationError(
            f"Config file at '{selected_path}' is not valid YAML: {e}"
        ) from e
    except Exception as e:
        raise ConfigurationError(
            f"Error parsing configuration at '{selected_path}': {e}"
        ) from e
