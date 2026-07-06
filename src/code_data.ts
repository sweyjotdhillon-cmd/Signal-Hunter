export interface ProjectFile {
  path: string;
  name: string;
  description: string;
  content: string;
}

export const PYTHON_PROJECT_FILES: ProjectFile[] = [
  {
    path: "requirements.txt",
    name: "requirements.txt",
    description: "Defines the essential Python packages for the pipeline, prioritizing minimal lightweight libraries suitable for local or Termux environments.",
    content: `# Core dependencies for Signal Hunter pipeline
pydantic>=2.6.0
PyYAML>=6.0.1
requests>=2.31.0
typing-extensions>=4.9.0
`
  },
  {
    path: ".gitignore",
    name: ".gitignore",
    description: "Specifies git-ignore paths to avoid checking in virtual environments, caches, compiled files, and downloaded JSON dataset items.",
    content: `# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# C extensions
*.so

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# Testing / coverage
.cache
.pytest_cache/
.coverage
htmlcov/

# Local data storage for Signal Hunter
data/*.json
logs/*.log
config/local_settings.yaml
`
  },
  {
    path: "models/research_item.py",
    name: "research_item.py",
    description: "Defines the primary Pydantic models for unified collector outputs, evaluation scores, verifications, and trend metadata.",
    content: `"""
Signal Hunter Core Data Models.

Defines the Pydantic schemas for unified collector outputs, scoring, verification, and trends.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator, AliasChoices


class VerificationState(str, Enum):
    """Enumeration of possible verification states."""
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"
    FLAGGED = "flagged"


class Author(BaseModel):
    """
    Represents an author, creator, or key contributor of a research item.
    """
    model_config = ConfigDict(
        extra="ignore",
        populate_by_name=True,
    )

    name: str = Field(
        ...,
        description="Full name of the author, creator, or team member."
    )
    email: Optional[str] = Field(
        None,
        description="Contact email address of the author."
    )
    affiliation: Optional[str] = Field(
        None,
        description="Academic institution or corporate organization the author is affiliated with."
    )
    github_username: Optional[str] = Field(
        None,
        description="GitHub username of the author if applicable."
    )
    website: Optional[str] = Field(
        None,
        description="URL of the author's personal or academic homepage."
    )
    extra_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Flexible container for future field additions or custom collector metadata."
    )


class Source(BaseModel):
    """
    Represents the source platform or publisher of a research item.
    """
    model_config = ConfigDict(
        extra="ignore",
        populate_by_name=True,
    )

    name: str = Field(
        ...,
        description="Name of the source platform or publisher (e.g., 'arXiv', 'GitHub', 'IEEE', 'OpenAI Blog')."
    )
    type: str = Field(
        ...,
        description="Classification category of the source platform (e.g., 'preprint', 'code_repository', 'engineering_blog', 'documentation')."
    )
    url: Optional[str] = Field(
        None,
        description="Base canonical URL of the source platform itself."
    )
    collector_version: Optional[str] = Field(
        None,
        description="Version string of the collector used to parse this source."
    )
    extra_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Flexible container for future field additions or custom collector metadata."
    )


class ScoreCard(BaseModel):
    """
    Represents the complete breakdown of evaluation scores for a research item.
    """
    model_config = ConfigDict(
        extra="ignore",
        populate_by_name=True,
    )

    opportunity_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Evaluated potential for building software/products on top of this item (0.0 to 1.0)."
    )
    engineering_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Evaluated technical, implementation, or architectural quality (0.0 to 1.0)."
    )
    scientific_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Evaluated scientific novelty, rigorous methodology, or theoretical contribution (0.0 to 1.0)."
    )
    startup_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Evaluated product-market fit, commercial viability, or spin-off potential (0.0 to 1.0)."
    )
    confidence_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="The overall level of trust/validation in the pipeline's analysis (0.0 to 1.0)."
    )
    novelty_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Evaluation of how groundbreaking or non-obvious this item is compared to standard state-of-the-art (0.0 to 1.0)."
    )
    extra_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Flexible container for future field additions or custom scoring metadata."
    )


class VerificationStatus(BaseModel):
    """
    Represents the quality validation lifecycle status of a research item.
    """
    model_config = ConfigDict(
        extra="ignore",
        populate_by_name=True,
    )

    state: VerificationState = Field(
        default=VerificationState.PENDING,
        description="The current verification state of the item (e.g., 'pending', 'verified', 'rejected', 'flagged')."
    )
    verified_by: Optional[str] = Field(
        None,
        description="Identifier of the verifier module, system model, or human auditor."
    )
    verified_at: Optional[datetime] = Field(
        None,
        description="UTC timestamp when the verification was performed."
    )
    score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Numerical confidence/accuracy score generated by the verifier (0.0 to 1.0)."
    )
    notes: Optional[str] = Field(
        None,
        description="Detailed verification feedback, critiques, or justification for the state."
    )
    is_breakthrough: bool = Field(
        default=False,
        description="Flag indicating if this item represents an exceptional major breakthrough."
    )
    extra_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Flexible container for future field additions or custom verification metadata."
    )


class TrendMetadata(BaseModel):
    """
    Represents social buzz, citation growth, and traction metrics for a research item.
    """
    model_config = ConfigDict(
        extra="ignore",
        populate_by_name=True,
    )

    velocity: float = Field(
        default=0.0,
        description="Rate of signal adoption or engagement change (e.g., stars/day, citations/month)."
    )
    sentiment_score: float = Field(
        default=0.0,
        ge=-1.0,
        le=1.0,
        description="Sentiment evaluation score of public discussions ranging from -1.0 (extremely negative) to 1.0 (extremely positive)."
    )
    interest_level: str = Field(
        default="low",
        description="Categorical indicator of general interest (e.g., 'low', 'medium', 'high', 'breakout')."
    )
    growth_percentage: Optional[float] = Field(
        None,
        description="Relative interest growth percentage calculated over a rolling time window."
    )
    mentions_count: int = Field(
        default=0,
        ge=0,
        description="Count of parsed mentions or discussions across tracked social/developer channels."
    )
    sources_count: int = Field(
        default=0,
        ge=0,
        description="Number of unique tracking sources discussing or citing this item."
    )
    extra_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Flexible container for future field additions or custom trend tracking metadata."
    )


class ResearchItem(BaseModel):
    """
    The unified data model representing an ingested, analyzed, and validated signal.
    
    This schema acts as the standard interchange contract across all collectors
    and pipeline processing steps.
    """
    model_config = ConfigDict(
        extra="ignore",
        populate_by_name=True,
    )

    unique_id: str = Field(
        ...,
        validation_alias=AliasChoices("unique_id", "id"),
        description="Globally unique identifier for this research item (typically a SHA-256 hash or canonical URI string)."
    )
    title: str = Field(
        ...,
        description="Official title of the research paper, article, software repository, or document."
    )
    source_name: str = Field(
        default="Unknown",
        description="The specific name of the source/publisher platform (e.g., 'arXiv', 'GitHub', 'IEEE', 'OpenAI Blog')."
    )
    source_type: str = Field(
        ...,
        description="Classification category of the source platform (e.g., 'preprint', 'code_repository', 'engineering_blog', 'documentation')."
    )
    url: str = Field(
        ...,
        description="The canonical, public URL linking directly to the source resource."
    )
    publication_date: Optional[datetime] = Field(
        None,
        description="The official date when this item was first published or made public."
    )
    discovered_date: datetime = Field(
        default_factory=datetime.utcnow,
        validation_alias=AliasChoices("discovered_date", "collected_at"),
        description="The timestamp when this item was discovered and ingested into the pipeline."
    )
    authors: List[Author] = Field(
        default_factory=list,
        description="A structured list of authors, creators, or contributors who produced this item."
    )
    organization: Optional[str] = Field(
        None,
        description="The primary company, university, or institution associated with the work."
    )
    summary: Optional[str] = Field(
        None,
        description="A comprehensive, high-quality technical summary detailing the main ideas and takeaways."
    )
    tags: List[str] = Field(
        default_factory=list,
        description="A list of descriptive keywords or keyword tags associated with this item."
    )
    categories: List[str] = Field(
        default_factory=list,
        description="Unified thematic categories (e.g., 'Large Language Models', 'Optimization', 'Hardware Acceleration')."
    )
    technologies: List[str] = Field(
        default_factory=list,
        description="Key technologies, frameworks, or methodologies utilized (e.g., 'PyTorch', 'Quantization', 'CUDA')."
    )
    programming_languages: List[str] = Field(
        default_factory=list,
        description="Programming languages prominently used in this item (e.g., 'Python', 'Rust', 'C++')."
    )
    paper_type: Optional[str] = Field(
        None,
        description="Detailed format type if applicable (e.g., 'Preprint', 'Peer-Reviewed Conference Paper', 'Whitepaper', 'Technical Report')."
    )
    github_repository: Optional[str] = Field(
        None,
        description="Associated official GitHub repository URL if applicable."
    )
    documentation_links: List[str] = Field(
        default_factory=list,
        description="URLs linking to official documentation, APIs, or developer guides."
    )
    related_links: List[str] = Field(
        default_factory=list,
        description="Other relevant URLs (e.g., community discussions, demo sites, YouTube presentations)."
    )
    seller_pitch: Optional[str] = Field(
        None,
        description="A persuasive summary highlighting how the authors position their work and its commercial/adoption appeal."
    )
    why_it_matters: Optional[str] = Field(
        None,
        description="A clear justification of the breakthrough's strategic significance and operational relevance."
    )
    build_opportunities: List[str] = Field(
        default_factory=list,
        description="Concrete ideas, architectures, or prototypes that can be built on top of this research."
    )
    risks: List[str] = Field(
        default_factory=list,
        description="Potential challenges, limitations, negative social impacts, or implementation hurdles."
    )

    # Scoring fields (top-level for direct access)
    opportunity_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Evaluated potential for building software/products on top of this item (0.0 to 1.0)."
    )
    engineering_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Evaluated technical, implementation, or architectural quality (0.0 to 1.0)."
    )
    scientific_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Evaluated scientific novelty, rigorous methodology, or theoretical contribution (0.0 to 1.0)."
    )
    startup_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Evaluated product-market fit, commercial viability, or spin-off potential (0.0 to 1.0)."
    )
    confidence_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="The overall level of trust/validation in the pipeline's analysis (0.0 to 1.0)."
    )
    novelty_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Evaluation of how groundbreaking or non-obvious this item is compared to standard state-of-the-art (0.0 to 1.0)."
    )

    # Verification and Trend aggregates
    verification_status: VerificationStatus = Field(
        default_factory=VerificationStatus,
        description="Structured verification lifecycle metadata populated by Verifier gates."
    )
    trend_metadata: TrendMetadata = Field(
        default_factory=TrendMetadata,
        description="Structured trend, social, and popularity metrics parsed from community chatter."
    )

    # Deduplication and versioning
    duplicate_of: Optional[str] = Field(
        None,
        description="Unique ID of another ResearchItem if this item is marked as a duplicate."
    )
    version: str = Field(
        default="1.0.0",
        description="Schema model version to assist with forward and backward compatibility."
    )
    raw_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Arbitrary nested raw collector-specific metadata payload to protect original data."
    )

    # Backward compatibility attributes (required by original pipeline verifier, tests, and logger)
    raw_content: str = Field(
        default="",
        description="Raw fetched text content, abstract, or description (retained for backward compatibility)."
    )
    signals: List[str] = Field(
        default_factory=list,
        description="Extracted early opportunities or signals (retained for backward compatibility)."
    )
    is_verified: bool = Field(
        default=False,
        description="Flag indicating whether this signal has been verified (backward compatibility field)."
    )
    verifier_notes: Optional[str] = Field(
        None,
        description="Explanation or critique regarding signal authenticity (backward compatibility field)."
    )

    @property
    def id(self) -> str:
        """Alias for unique_id to support legacy property-based accesses."""
        return self.unique_id

    @id.setter
    def id(self, value: str) -> None:
        """Setter for legacy unique ID updates."""
        self.unique_id = value

    @property
    def score_card(self) -> ScoreCard:
        """Returns a composite ScoreCard compiled from the top-level scores."""
        return ScoreCard(
            opportunity_score=self.opportunity_score,
            engineering_score=self.engineering_score,
            scientific_score=self.scientific_score,
            startup_score=self.startup_score,
            confidence_score=self.confidence_score,
            novelty_score=self.novelty_score,
        )

    @field_validator("unique_id")
    @classmethod
    def validate_unique_id(cls, v: str) -> str:
        """Ensure unique_id is non-empty and well-formed."""
        if not v.strip():
            raise ValueError("unique_id cannot be empty or whitespace-only")
        return v

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Ensure the canonical URL starts with a valid web scheme."""
        if not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError("URL must start with 'http://' or 'https://'")
        return v

    @field_validator(
        "opportunity_score",
        "engineering_score",
        "scientific_score",
        "startup_score",
        "confidence_score",
        "novelty_score"
    )
    @classmethod
    def validate_scores(cls, v: float) -> float:
        """Ensure all scoring fields are constrained strictly between 0.0 and 1.0."""
        if not (0.0 <= v <= 1.0):
            raise ValueError("Scores must be between 0.0 and 1.0 inclusive")
        return v
`
  },
  {
    path: "models/__init__.py",
    name: "__init__.py",
    description: "Initializes the models package and exposes the full suite of Pydantic models cleanly.",
    content: `"""
Signal Hunter models package.

Contains core data transfer and domain models.
"""

from models.research_item import (
    ResearchItem,
    Author,
    Source,
    ScoreCard,
    VerificationStatus,
    TrendMetadata,
    VerificationState,
)

__all__ = [
    "ResearchItem",
    "Author",
    "Source",
    "ScoreCard",
    "VerificationStatus",
    "TrendMetadata",
    "VerificationState",
]
`
  },
  {
    path: "utils/exceptions.py",
    name: "exceptions.py",
    description: "Custom pipeline exception hierarchy separating collector, analyzer, verifier, memory, and delivery failures.",
    content: `"""
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
`
  },
  {
    path: "utils/logger.py",
    name: "logger.py",
    description: "Sets up standard pipeline logger configuring multiple handlers, timestamps, formatting levels, and optional log files.",
    content: `"""
Signal Hunter Logger Utility.

Provides standard logger configuration with support for console formatting and file output.
"""

import logging
import os
import sys
from typing import Optional


def setup_logger(
    name: str = "signal_hunter",
    log_level: str = "INFO",
    log_file: Optional[str] = None,
) -> logging.Logger:
    """
    Configure and retrieve a custom logger with standardized formatting.

    Args:
        name (str): Name of the logger, typically __name__ of calling module.
        log_level (str): String logging level (DEBUG, INFO, WARNING, ERROR).
        log_file (Optional[str]): Optional file path to stream logs.

    Returns:
        logging.Logger: Preconfigured logging instance.
    """
    logger = logging.getLogger(name)

    # If the logger is already configured, return it to prevent duplicate handlers
    if logger.handlers:
        return logger

    # Resolve level
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    logger.setLevel(numeric_level)

    # Formatter configuration
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console stdout handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Optional file handler
    if log_file:
        # Create directories if they do not exist
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
`
  },
  {
    path: "utils/helpers.py",
    name: "helpers.py",
    description: "Utility tools for cleaning textual whitespace, generating deterministic SHA-256 IDs, and performing transactional atomic JSON operations.",
    content: `"""
Signal Hunter General Utility Helpers.

Common functional routines for filesystem operations, string sanitization,
and cryptographic hashing for ID consistency.
"""

import hashlib
import json
import os
import re
from typing import Any, Dict, Optional


def generate_id(url: str) -> str:
    """
    Generate a deterministic SHA-256 identifier based on a canonical URL.

    Args:
        url (str): Canonical source URL.

    Returns:
        str: 64-character hexadecimal SHA-256 hash.
    """
    cleaned_url = url.strip().lower()
    return hashlib.sha256(cleaned_url.encode("utf-8")).hexdigest()


def safe_write_json(filepath: str, data: Any, indent: int = 4) -> None:
    """
    Safely write data structure to a JSON file, creating parent directories if missing.

    Args:
        filepath (str): Absolute or relative filesystem destination path.
        data (Any): JSON-serializable dictionary or list.
        indent (int): Visual spacing indentation size.
    """
    dir_path = os.path.dirname(filepath)
    if dir_path:
        os.makedirs(dir_path, exist_ok=True)

    # Write to a temporary file first, then rename (atomic write)
    temp_filepath = f"{filepath}.tmp"
    try:
        with open(temp_filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=indent)
        os.replace(temp_filepath, filepath)
    except Exception as e:
        if os.path.exists(temp_filepath):
            os.remove(temp_filepath)
        raise OSError(f"Failed to write JSON securely to {filepath}: {e}") from e


def safe_read_json(filepath: str) -> Optional[Any]:
    """
    Safely load data structure from a JSON file. Returns None if the file is absent.

    Args:
        filepath (str): Filesystem path to read from.

    Returns:
        Optional[Any]: Loaded Python structure or None if not found/invalid.
    """
    if not os.path.exists(filepath):
        return None

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        # Gracefully handle corrupted files or locked reads
        return None


def sanitize_text(text: str) -> str:
    """
    Sanitize and clean raw text by collapsing consecutive whitespaces.

    Args:
        text (str): Raw string.

    Returns:
        str: Trimmed, formatted string.
    """
    if not text:
        return ""
    # Collapse multiple spaces and newlines into single spaces/newlines
    cleaned = re.sub(r"\s+", " ", text)
    return cleaned.strip()
`
  },
  {
    path: "utils/__init__.py",
    name: "__init__.py",
    description: "Registers and exposes exceptions, loggers, and functional helpers.",
    content: `"""
Signal Hunter utilities package.

Houses core exception types, logging infrastructure, and basic helpers.
"""

from utils.exceptions import (
    AnalysisError,
    CollectionError,
    ConfigurationError,
    DeliveryError,
    SignalHunterError,
    StorageError,
    VerificationError,
)
from utils.helpers import (
    generate_id,
    safe_read_json,
    safe_write_json,
    sanitize_text,
)
from utils.logger import setup_logger

__all__ = [
    "SignalHunterError",
    "ConfigurationError",
    "CollectionError",
    "AnalysisError",
    "VerificationError",
    "StorageError",
    "DeliveryError",
    "generate_id",
    "safe_read_json",
    "safe_write_json",
    "sanitize_text",
    "setup_logger",
]
`
  },
  {
    path: "config/settings.yaml",
    name: "settings.yaml",
    description: "System central YAML settings containing crawler configurations, active pipelines, scoring policies, and report delivery parameters.",
    content: `# Signal Hunter Default Pipeline Configuration

app_name: "Signal Hunter"
log_level: "INFO"

collectors:
  arxiv:
    enabled: true
    sources:
      - "cs.AI"
      - "cs.LG"
      - "cs.CL"
    cron: "0 8 * * *"
    params:
      max_results: 50
  tech_blogs:
    enabled: true
    sources:
      - "https://openai.com/blog"
      - "https://deepmind.google/discover"
      - "https://netflixtechblog.com"
    cron: "0 9 * * *"
    params:
      request_timeout: 10
  github_trending:
    enabled: true
    sources:
      - "python"
      - "typescript"
      - "go"
    cron: "0 10 * * *"
    params:
      min_stars: 100

analyzers:
  gemini_summarizer:
    enabled: true
    model_name: "gemini-2.5-flash"
    temperature: 0.1
    max_tokens: 1500
  opportunity_scout:
    enabled: true
    model_name: "gemini-2.5-pro"
    temperature: 0.3
    max_tokens: 2000

verifier:
  min_confidence_score: 0.75
  strict_mode: true

memory:
  storage_dir: "data"
  backup_enabled: true

delivery:
  channels:
    - "console"
    - "markdown_file"
  output_dir: "reports"
`
  },
  {
    path: "config/config_loader.py",
    name: "config_loader.py",
    description: "ConfigLoader module, reading active local override files and parsing values recursively into strict validation schemas.",
    content: `"""
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
    2. Local custom file \`config/local_settings.yaml\` (untoggled git config)
    3. Standard settings file \`config/settings.yaml\`

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
`
  },
  {
    path: "config/__init__.py",
    name: "__init__.py",
    description: "Initializes the config package, exposing loaders and data-validation model structures.",
    content: `"""
Signal Hunter configuration package.

Initializes settings loaders and validated schema models.
"""

from config.config_loader import (
    AnalyzerConfig,
    AppConfig,
    CollectorConfig,
    DeliveryConfig,
    MemoryConfig,
    VerifierConfig,
    load_config,
)

__all__ = [
    "AppConfig",
    "CollectorConfig",
    "AnalyzerConfig",
    "VerifierConfig",
    "MemoryConfig",
    "DeliveryConfig",
    "load_config",
]
`
  },
  {
    path: "collectors/base.py",
    name: "base.py",
    description: "Defines the Abstract BaseCollector class, establishing common logging setups and data pipelines for crawl modules.",
    content: `"""
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
`
  },
  {
    path: "collectors/__init__.py",
    name: "__init__.py",
    description: "Exposes the base class representing target collection strategies.",
    content: `"""
Signal Hunter collectors package.

Houses all source integrations (papers, blogs, github, etc.) inheriting from BaseCollector.
"""

from collectors.base import BaseCollector

__all__ = ["BaseCollector"]
`
  },
  {
    path: "analyzers/base.py",
    name: "base.py",
    description: "Defines the Abstract BaseAnalyzer interface, alongside a DummyAnalyzer performing baseline keyword scoring and abstract extractions.",
    content: `"""
Signal Hunter Abstract Base Analyzer.

Defines the core pipeline contract for modifying, scoring, and summarizing ResearchItems.
"""

from abc import ABC, abstractmethod
import logging

from config.config_loader import AnalyzerConfig
from models.research_item import ResearchItem
from utils.logger import setup_logger


class BaseAnalyzer(ABC):
    """
    Abstract base class for all signal intelligence processors.

    Analyzers process raw collected items and enrich them with summaries,
    signals, and initial evaluations.
    """

    def __init__(self, config: AnalyzerConfig) -> None:
        """
        Initialize the base analyzer.

        Args:
            config (AnalyzerConfig): Specific settings for processing/models.
        """
        self.config = config
        self.logger: logging.Logger = setup_logger(
            name=f"signal_hunter.analyzers.{self.name.lower()}",
            log_level="INFO",
        )
        self.logger.info(
            "Initialized analyzer '%s' (Enabled: %s)",
            self.name,
            config.enabled,
        )

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Return the unique descriptive name of the analyzer.

        Returns:
            str: Identifier (e.g. 'GeminiSummarizer', 'OpportunityScout').
        """
        pass

    @abstractmethod
    def analyze(self, item: ResearchItem) -> ResearchItem:
        """
        Process and enrich a ResearchItem with structured AI insights.

        Modifies the item in-place or returns a newly enriched instance.

        Args:
            item (ResearchItem): Item representing the target signal source.

        Returns:
            ResearchItem: The enriched object containing summaries or opportunity lists.

        Raises:
            AnalysisError: If processing or LLM calls encounter fatal failures.
        """
        pass


class DummyAnalyzer(BaseAnalyzer):
    """A simple placeholder analyzer used to satisfy initial skeleton execution."""

    @property
    def name(self) -> str:
        return "DummyAnalyzer"

    def analyze(self, item: ResearchItem) -> ResearchItem:
        """Mock analysis simulating keyword discovery and scoring."""
        self.logger.debug("Running mock analyzer on item: %s", item.title)
        
        # Simple simulated extraction
        signals = []
        if "attention" in item.title.lower() or "transformer" in item.raw_content.lower():
            signals.append("Highly parallelized neural architecture signal")
            signals.append("Foundation model emergence opportunity")
            item.confidence_score = 0.95
        else:
            signals.append("Standard technical advancement signal")
            item.confidence_score = 0.65
            
        item.summary = f"Simulated abstract summary: {item.title}. Concluded that content revolves around tech advancements."
        item.signals = signals
        return item
`
  },
  {
    path: "analyzers/__init__.py",
    name: "__init__.py",
    description: "Initializes the analyzers package and exposes BaseAnalyzer.",
    content: `"""
Signal Hunter analyzers package.

Contains intelligence models and semantic parsers to isolate and analyze breakthroughs.
"""

from analyzers.base import BaseAnalyzer, DummyAnalyzer

__all__ = ["BaseAnalyzer", "DummyAnalyzer"]
`
  },
  {
    path: "verifier/verifier.py",
    name: "verifier.py",
    description: "Applies rule parameters and minimum threshold gates onto incoming scored records to confirm signal quality.",
    content: `"""
Signal Hunter Signal Verifier.

Assesses signal strength against minimum confidence thresholds and checks for structural validity.
"""

import logging

from config.config_loader import VerifierConfig
from models.research_item import ResearchItem
from utils.logger import setup_logger


class SignalVerifier:
    """
    Evaluates analyzed research items to confirm breakthrough authenticity.

    Ensures that only signals matching threshold requirements pass verification,
    thereby protecting downstream intelligence reporting from low-confidence noise.
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

    def verify(self, item: ResearchItem) -> ResearchItem:
        """
        Assess if a ResearchItem's signals represent a legitimate opportunity.

        Sets \`is_verified\` and \`verifier_notes\` fields on the item.

        Args:
            item (ResearchItem): Enriched research item to check.

        Returns:
            ResearchItem: The item with populated verification decisions.
        """
        self.logger.info("Verifying signal item: %s (ID: %s)", item.title, item.id)

        # Baseline check: Confidence threshold check
        meets_confidence = item.confidence_score >= self.config.min_confidence_score

        # Rule-based validation if strict mode is active
        has_concrete_signals = len(item.signals) > 0
        has_adequate_summary = (
            item.summary is not None and len(item.summary) >= 20
        )

        is_valid = meets_confidence
        notes_list = []

        if meets_confidence:
            notes_list.append(
                f"Passed confidence threshold ({item.confidence_score} >= {self.config.min_confidence_score})."
            )
        else:
            notes_list.append(
                f"Failed confidence threshold ({item.confidence_score} < {self.config.min_confidence_score})."
            )

        if self.config.strict_mode:
            if not has_concrete_signals:
                is_valid = False
                notes_list.append("Strict validation failed: No concrete signal elements extracted.")
            if not has_adequate_summary:
                is_valid = False
                notes_list.append("Strict validation failed: Technical summary is too brief or missing.")

        item.is_verified = is_valid
        item.verifier_notes = " ".join(notes_list)

        if is_valid:
            self.logger.info("Item [%s] successfully VERIFIED as valid signal.", item.title)
        else:
            self.logger.warning("Item [%s] FAILED verification criteria.", item.title)

        return item
`
  },
  {
    path: "verifier/__init__.py",
    name: "__init__.py",
    description: "Exposes the SignalVerifier package components.",
    content: `"""
Signal Hunter verifier package.

Ensures collected insights meet strict confidence thresholds before reporting.
"""

from verifier.verifier import SignalVerifier

__all__ = ["SignalVerifier"]
`
  },
  {
    path: "memory/json_store.py",
    name: "json_store.py",
    description: "An atomic, thread-safe persistence layer writing files directly under data/items/item_id.json to ensure offline storage without complex relational DBs.",
    content: `"""
Signal Hunter JSON File Storage.

Provides non-database structured storage saving ResearchItems in clean JSON files.
"""

import logging
import os
from typing import List, Optional

from config.config_loader import MemoryConfig
from models.research_item import ResearchItem
from utils.helpers import safe_read_json, safe_write_json


class JSONMemoryStore:
    """
    Local JSON-based transactional persistence store.

    Saves individual ResearchItems as file records in \`{storage_dir}/items/{item_id}.json\`.
    """

    def __init__(self, config: MemoryConfig) -> None:
        """
        Initialize the JSON Memory Store and create target storage folders.

        Args:
            config (MemoryConfig): Persistence directories and backup rules.
        """
        self.config = config
        self.logger: logging.Logger = setup_logger(
            "signal_hunter.memory",
            log_level="INFO",
        )

        # Build paths
        self.base_dir = self.config.storage_dir
        self.items_dir = os.path.join(self.base_dir, "items")

        # Guarantee folder existence
        os.makedirs(self.items_dir, exist_ok=True)
        self.logger.info("Initialized JSONMemoryStore. Storage directory: %s", self.items_dir)

    def save_item(self, item: ResearchItem) -> None:
        """
        Save or overwrite a ResearchItem in the storage database.

        Args:
            item (ResearchItem): Item record containing crawled and scored data.
        """
        filepath = os.path.join(self.items_dir, f"{item.id}.json")
        try:
            # Pydantic items can dump to dictionaries safely
            data = item.model_dump()
            # Handle datetime serializations
            data["collected_at"] = item.collected_at.isoformat()

            safe_write_json(filepath, data)
            self.logger.debug("Successfully persisted ResearchItem %s to %s", item.id, filepath)
        except Exception as e:
            self.logger.error("Failed to save ResearchItem %s: %s", item.id, e)
            raise OSError(f"Could not persist record: {e}") from e

    def get_item(self, item_id: str) -> Optional[ResearchItem]:
        """
        Retrieve a single ResearchItem by its hash ID.

        Args:
            item_id (str): Hash identifier.

        Returns:
            Optional[ResearchItem]: Loaded item, or None if missing or corrupted.
        """
        filepath = os.path.join(self.items_dir, f"{item_id}.json")
        data = safe_read_json(filepath)
        if not data:
            return None

        try:
            return ResearchItem(**data)
        except Exception as e:
            self.logger.error("Corrupted record found at %s: %s", filepath, e)
            return None

    def list_items(self, verified_only: bool = False) -> List[ResearchItem]:
        """
        Load and return all saved ResearchItem records.

        Args:
            verified_only (bool): If True, filters out unverified signals.

        Returns:
            List[ResearchItem]: List of active records loaded from disk.
        """
        items: List[ResearchItem] = []
        if not os.path.exists(self.items_dir):
            return items

        for filename in os.listdir(self.items_dir):
            if not filename.endswith(".json"):
                continue

            filepath = os.path.join(self.items_dir, filename)
            data = safe_read_json(filepath)
            if not data:
                continue

            try:
                item = ResearchItem(**data)
                if verified_only and not item.is_verified:
                    continue
                items.append(item)
            except Exception as e:
                self.logger.error("Failed to parse record %s during list: %s", filename, e)

        # Sort by newest collection date
        items.sort(key=lambda x: x.collected_at, reverse=True)
        return items

    def search_items(self, query: str) -> List[ResearchItem]:
        """
        Simple text search matching against item title, summary, or raw text.

        Args:
            query (str): Search term.

        Returns:
            List[ResearchItem]: Filtered list of matching records.
        """
        term = query.lower()
        results: List[ResearchItem] = []

        for item in self.list_items():
            if (
                term in item.title.lower()
                or (item.summary and term in item.summary.lower())
                or term in item.raw_content.lower()
            ):
                results.append(item)

        return results
`
  },
  {
    path: "memory/__init__.py",
    name: "__init__.py",
    description: "Initializes local file storage services, preventing bloated SQL processes.",
    content: `"""
Signal Hunter memory storage package.

Manages persistent items, states, and cached vectors using simple JSON formats.
"""

from memory.json_store import JSONMemoryStore

__all__ = ["JSONMemoryStore"]
`
  },
  {
    path: "delivery/reporter.py",
    name: "reporter.py",
    description: "Constructs the Daily Intelligence Report inside reports/ from verified, high-confidence breakthrough items.",
    content: `"""
Signal Hunter Report Delivery System.

Implements reporting utilities, synthesizing verified signals into actionable briefings.
"""

from abc import ABC, abstractmethod
from datetime import datetime
import logging
import os
from typing import List

from config.config_loader import DeliveryConfig
from models.research_item import ResearchItem
from utils.logger import setup_logger


class BaseDelivery(ABC):
    """
    Abstract base class for all report delivery channels.

    Handles report generation, layout styling, and outbound transport (Console, files, webhook).
    """

    def __init__(self, config: DeliveryConfig) -> None:
        """
        Initialize the delivery service.

        Args:
            config (DeliveryConfig): Output directory and channel settings.
        """
        self.config = config
        self.logger: logging.Logger = setup_logger(
            name=f"signal_hunter.delivery.{self.name.lower()}",
            log_level="INFO",
        )

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Return the unique identifier for the delivery channel.

        Returns:
            str: Channel name (e.g., 'Console', 'MarkdownFile').
        """
        pass

    @abstractmethod
    def deliver(self, items: List[ResearchItem]) -> str:
        """
        Generate and publish the intelligence report for the active run.

        Args:
            items (List[ResearchItem]): List of verified items to include.

        Returns:
            str: The raw generated report content (typically markdown/HTML).
        """
        pass


class MarkdownReporter(BaseDelivery):
    """Generates elegant, structured, and actionable Markdown reports from verified signals."""

    @property
    def name(self) -> str:
        return "MarkdownFile"

    def deliver(self, items: List[ResearchItem]) -> str:
        """
        Synthesize verified signals, write the markdown report to file, and return the string.

        Args:
            items (List[ResearchItem]): Target verified signals list.

        Returns:
            str: Generated markdown content.
        """
        if not items:
            self.logger.warning("No verified items found to construct report. Generating empty stub.")
            return "# Signal Hunter Daily Intelligence Report\\n\\nNo breakthroughs verified in this pipeline run."

        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        report_lines = [
            f"# 🎯 Signal Hunter Daily Intelligence Report - {date_str}",
            "---",
            "**Mission**: *Discover early opportunities, engineering breakthroughs, and scientific discoveries before they become mainstream.*",
            "",
            "## 📊 Executive Summary Dashboard",
            f"- **Total Signals Analyzed & Verified**: {len(items)}",
            f"- **Average Confidence Score**: {sum(item.confidence_score for item in items)/len(items):.2f}",
            "",
            "## ⚡ Primary Breakthroughs",
        ]

        # Group items by source type
        categories = {}
        for item in items:
            cat = item.source_type.replace("_", " ").title()
            categories.setdefault(cat, []).append(item)

        # Build categorized list
        idx = 1
        for cat, cat_items in categories.items():
            report_lines.append(f"### 📂 Category: {cat}")
            report_lines.append("")

            # Sort within category by confidence score descending
            cat_items.sort(key=lambda x: x.confidence_score, reverse=True)

            for item in cat_items:
                indicator = "🔥 [High Signal]" if item.confidence_score >= 0.90 else "💡 [Emerging]"
                report_lines.append(f"#### {idx}. {item.title}")
                report_lines.append(f"- **Confidence Rating**: \`{item.confidence_score:.2f}\` {indicator}")
                report_lines.append(f"- **Canonical URL**: <{item.url}>")
                if item.author:
                    report_lines.append(f"- **Author/Creator**: {item.author}")
                report_lines.append("")
                report_lines.append("**Core Technical Summary:**")
                report_lines.append(f"> {item.summary or 'No summary provided.'}")
                report_lines.append("")
                report_lines.append("**Extracted Opportunities & Future Signals:**")
                for sig in item.signals:
                    report_lines.append(f"- 🚀 {sig}")
                report_lines.append("")
                if item.verifier_notes:
                    report_lines.append(f"*Verifier Critique:* {item.verifier_notes}")
                report_lines.append("")
                report_lines.append("---")
                idx += 1

        report_lines.append("")
        report_lines.append("\`Signal Hunter Pipeline v1.0.0-Beta • Executed via local scheduler\`")

        markdown_content = "\\n".join(report_lines)

        # Output to disk
        out_dir = self.config.output_dir
        os.makedirs(out_dir, exist_ok=True)
        report_filename = f"daily_intelligence_brief_{date_str.replace('-', '_')}.md"
        report_path = os.path.join(out_dir, report_filename)

        try:
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(markdown_content)
            self.logger.info("Successfully published daily markdown report to: %s", report_path)
        except Exception as e:
            self.logger.error("Failed to write daily markdown report file: %s", e)

        return markdown_content
`
  },
  {
    path: "delivery/__init__.py",
    name: "__init__.py",
    description: "Initializes the delivery package containing base and markdown reporters.",
    content: `"""
Signal Hunter delivery package.

Synthesizes findings into actionable daily research intelligence reports.
"""

from delivery.reporter import BaseDelivery, MarkdownReporter

__all__ = ["BaseDelivery", "MarkdownReporter"]
`
  },
  {
    path: "tests/test_pipeline.py",
    name: "test_pipeline.py",
    description: "Comprehensive unit regression assertions ensuring configuration hydration, constraint properties, and confidence triggers.",
    content: `"""
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
`
  },
  {
    path: "tests/__init__.py",
    name: "__init__.py",
    description: "Initializes the test suite package.",
    content: `"""
Signal Hunter unit tests package.
"""
`
  },
  {
    path: "main.py",
    name: "main.py",
    description: "Pipeline orchestrator bootstrapping central setups, logging configurations, collection dry-runs, scoring enriches, and verifications.",
    content: `"""
Signal Hunter - AI-Powered Research Intelligence Pipeline.

Main entry point that orchestrates the execution flow: configuration loading,
logging setup, raw content crawling (collectors), AI extraction (analyzers),
critique validation (verifier), local JSON persistence (memory), and report output (delivery).
"""

import argparse
import logging
import sys
from datetime import datetime
from typing import List, Optional

from config.config_loader import AppConfig, load_config
from models.research_item import ResearchItem
from analyzers.base import DummyAnalyzer
from verifier.verifier import SignalVerifier
from memory.json_store import JSONMemoryStore
from delivery.reporter import MarkdownReporter
from utils.logger import setup_logger
from utils.exceptions import SignalHunterError
from utils.helpers import generate_id


def generate_mock_raw_candidates() -> List[ResearchItem]:
    """
    Generate mock candidates representing raw gathered feeds.

    Used when collectors aren't yet implemented to demonstrate the end-to-end flow.

    Returns:
        List[ResearchItem]: Array of un-analyzed research inputs.
    """
    now = datetime.utcnow()
    return [
        ResearchItem(
            id=generate_id("https://arxiv.org/abs/2106.09685"),
            title="LoRA: Low-Rank Adaptation of Large Language Models",
            url="https://arxiv.org/abs/2106.09685",
            source_type="paper",
            raw_content="We propose Low-Rank Adaptation (LoRA), which freezes the pre-trained model weights and injects trainable rank decomposition matrices into each layer of the Transformer architecture, greatly reducing the number of trainable parameters for downstream tasks.",
            author="Edward J. Hu et al.",
            published_at="2021-06-17T00:00:00Z",
            collected_at=now,
        ),
        ResearchItem(
            id=generate_id("https://github.com/vllm-project/vllm"),
            title="vLLM: Easy, Fast, and Cheap LLM Serving with PagedAttention",
            url="https://github.com/vllm-project/vllm",
            source_type="github",
            raw_content="vLLM is a fast and easy-to-use library for LLM inference and serving. It achieves state-of-the-art throughput by using PagedAttention, which manages attention key-value memory with high efficiency.",
            author="UC Berkeley team",
            published_at="2023-06-20T00:00:00Z",
            collected_at=now,
        ),
        ResearchItem(
            id=generate_id("https://openai.com/blog/frontier-risk-preparedness"),
            title="Frontier Risk Preparedness and Safety Frameworks",
            url="https://openai.com/blog/frontier-risk-preparedness",
            source_type="engineering_blog",
            raw_content="We outline our systematic preparedness safety framework designed to quantify, test, and respond to catastrophic risks in frontier models across cybersecurity, persuasion, and autonomy.",
            author="OpenAI Safety Team",
            published_at="2024-01-15T00:00:00Z",
            collected_at=now,
        ),
    ]


def run_pipeline(config_path: Optional[str] = None, dry_run: bool = False) -> None:
    """
    Load components and run the intelligence collection & analysis pipeline.

    Args:
        config_path (Optional[str]): Path to configuration YAML file.
        dry_run (bool): If True, skips external network crawls and uses pre-loaded items.

    Raises:
        SignalHunterError: If some phase of the pipeline suffers a fatal crash.
    """
    # 1. Load configuration
    try:
        config: AppConfig = load_config(config_path)
    except Exception as e:
        # Fallback console printing because logger is not configured yet
        print(f"FATAL: Failed to load system configuration: {e}", file=sys.stderr)
        sys.exit(1)

    # 2. Setup central logger
    logger: logging.Logger = setup_logger(
        name="signal_hunter",
        log_level=config.log_level,
        log_file="logs/signal_hunter.log",
    )

    logger.info("=========================================")
    logger.info("   Starting Signal Hunter Intelligence   ")
    logger.info("=========================================")
    logger.info("Application: %s", config.app_name)
    logger.info("Log Level:   %s", config.log_level)

    try:
        # 3. Instantiate memory store
        store = JSONMemoryStore(config.memory)

        # 4. Instantiate analyzers
        # We fetch the configuration for gemini_summarizer
        analyzer_cfg = config.analyzers.get("gemini_summarizer")
        if not analyzer_cfg:
            raise SignalHunterError("Configuration for 'gemini_summarizer' is missing in config.")
        analyzer = DummyAnalyzer(analyzer_cfg)

        # 5. Instantiate verifier
        verifier = SignalVerifier(config.verifier)

        # 6. Instantiate delivery system
        reporter = MarkdownReporter(config.delivery)

        # 7. Collect raw items
        raw_items: List[ResearchItem] = []
        if dry_run or not any(c.enabled for c in config.collectors.values()):
            logger.info("Running pipeline in DRY-RUN mode or with collectors disabled. Injecting base candidates...")
            raw_items = generate_mock_raw_candidates()
        else:
            logger.info("Starting active crawlers (Placeholder - no collectors registered)...")
            # In subsequent iterations, collectors will append actual results here
            raw_items = generate_mock_raw_candidates()

        logger.info("Ingested %d candidate(s) into pipeline buffers.", len(raw_items))

        # 8. Run processing loop
        verified_items: List[ResearchItem] = []

        for index, raw_item in enumerate(raw_items, 1):
            logger.info("[%d/%d] Processing signal candidate: %s", index, len(raw_items), raw_item.title)

            try:
                # Analysis
                analyzed_item = analyzer.analyze(raw_item)

                # Verification
                verified_item = verifier.verify(analyzed_item)

                # Storage
                store.save_item(verified_item)

                if verified_item.is_verified:
                    verified_items.append(verified_item)

            except Exception as e:
                logger.error("Failed to process item [%s]: %s", raw_item.title, e, exc_info=True)
                continue

        # 9. Deliver report
        logger.info("Compiling daily briefing with %d verified breakthrough(s)...", len(verified_items))
        report_content = reporter.deliver(verified_items)

        logger.info("Pipeline run successfully completed.")

    except Exception as e:
        logger.critical("Critical pipeline failure: %s", e, exc_info=True)
        raise SignalHunterError(f"Pipeline run aborted: {e}") from e


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Signal Hunter: An AI-Powered Research Intelligence Pipeline"
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to YAML configuration settings override file",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Skip active internet connection crawls and execute pipeline with mock feeds",
    )

    args = parser.parse_args()

    try:
        run_pipeline(config_path=args.config, dry_run=args.dry_run)
    except Exception as err:
        print(f"FAILED: {err}", file=sys.stderr)
        sys.exit(1)
`
  },
  {
    path: "README.md",
    name: "README.md",
    description: "Primary project documentation outlining the mission, design topologies, system structure, Termux installs, and usage settings.",
    content: `# 🎯 Signal Hunter

An AI-powered research intelligence pipeline designed to discover early tech opportunities, emerging engineering breakthroughs, startup concepts, and hidden scientific discoveries before they become mainstream.

---

## 📌 Mission

Most research summarization tools focus on condensing information. **Signal Hunter** is different. Its mission is to **detect signals of breakthrough potential**. 

It systematically monitors, crawls, and filters technical feeds to extract actionable insights, early-stage opportunities, and scientific breakthroughs. The output is a highly structured, prioritized **Daily Intelligence Report** curated for software engineers, research scientists, founders, and investors.

---

## 🧩 System Architecture

Signal Hunter is built on a clean, decoupled, event-ready modular pipeline. Below is the data flow topology:

\`\`\`
[ External Sources ] (arXiv, Engineering Blogs, GitHub Trending)
        │
        ▼
┌────────────────────────┐
│  Collectors            │ (BaseCollector: Fetches raw Candidates)
└──────────┬─────────────┘
           │ (ResearchItem - raw)
           ▼
┌────────────────────────┐
│  Analyzers             │ (BaseAnalyzer: Cognitive AI Summary & Opportunity Extraction)
└──────────┬─────────────┘
           │ (ResearchItem - analyzed)
           ▼
┌────────────────────────┐
│  Signal Verifier       │ (SignalVerifier: Confirms thresholds, applies filters)
└──────────┬─────────────┘
           ├─────────────────────────┐
           │ (Verified)              │ (Unverified Noise)
           ▼                         ▼
┌────────────────────────┐     ┌───────────┐
│  Memory Storage        │     │  Filtered │ (Discarded or logged)
│  (JSON Store database) │     └───────────┘
└──────────┬─────────────┘
           │
           ▼
┌────────────────────────┐
│  Delivery Reporter     │ (BaseDelivery: Markdown briefings, notifications)
└────────────────────────┘
\`\`\`

---

## 📂 Project Structure

\`\`\`
signal-hunter/
├── config/                  # Configuration Schema and Loaders
│   ├── __init__.py
│   ├── config_loader.py     # Pydantic Configuration Model
│   └── settings.yaml        # Default pipeline settings
├── collectors/              # Raw data crawlers and feeds ingestors
│   ├── __init__.py
│   └── base.py              # BaseCollector abstract base class
├── analyzers/               # Cognitive processors and LLM extractors
│   ├── __init__.py
│   └── base.py              # BaseAnalyzer abstract base class
├── verifier/                # Validation and signal grading rules
│   ├── __init__.py
│   └── verifier.py          # SignalVerifier core class
├── memory/                  # Persistence and historic caches
│   ├── __init__.py
│   └── json_store.py        # JSON-based transactional persistence
├── delivery/                # Report compiles and publishers
│   ├── __init__.py
│   └── reporter.py          # MarkdownReporter delivery service
├── models/                  # Shared structured objects
│   ├── __init__.py
│   └── research_item.py     # ResearchItem data model (Pydantic)
├── utils/                   # Shared utility helpers
│   ├── __init__.py
│   ├── exceptions.py        # Pipeline custom error hierachy
│   ├── helpers.py           # Atomic JSON, hashing, text cleaners
│   └── logger.py            # Central logging config
├── tests/                   # Regression and unit test suite
│   ├── __init__.py
│   └── test_pipeline.py     # Component test assertions
├── main.py                  # Pipeline central entrypoint
├── requirements.txt         # Minimum external dependencies
└── README.md                # System documentation
\`\`\`

---

## 🚀 Installation & Setup

### Requirements
- **Python 3.12+**
- No external heavy databases required (persistence is fully JSON-based out-of-the-box).

### 1. Clone & Environment Set Up
\`\`\`bash
git clone https://github.com/yourusername/signal-hunter.git
cd signal-hunter
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
\`\`\`

### 2. Local Configuration Override (Optional)
If you wish to override standard settings without altering tracked files, create a file named \`config/local_settings.yaml\`. It is automatically prioritized and merged by the loader:
\`\`\`yaml
# config/local_settings.yaml
log_level: "DEBUG"
verifier:
  min_confidence_score: 0.85
\`\`\`

---

## 📱 Running on Android (via Termux)

Signal Hunter is fully optimized to run efficiently inside **Termux** on Android devices, making it perfect for off-grid edge execution or daily mobile briefings.

### Termux Setup Instructions:
1. **Install Termux** from F-Droid (avoid Google Play as it's outdated).
2. **Bootstrap Packages & Python**:
   \`\`\`bash
   pkg update && pkg upgrade -y
   pkg install python python-pip git libyaml -y
   \`\`\`
3. **Setup Filesystem Storage**:
   \`\`\`bash
   termux-setup-storage
   \`\`\`
4. **Install Signal Hunter**:
   \`\`\`bash
   git clone https://github.com/yourusername/signal-hunter.git
   cd signal-hunter
   pip install -r requirements.txt
   \`\`\`
5. **Run the Pipeline**:
   \`\`\`bash
   python main.py --dry-run
   \`\`\`

---

## ⚙️ Usage & CLI Arguments

Execute the central coordinator using the standard Python interpreter:

\`\`\`bash
# Execute standard run with mock/demo feed crawlers
python main.py --dry-run

# Run using a custom configuration file path
python main.py --config config/local_settings.yaml
\`\`\`

The run triggers a full cycle:
1. Loads settings from \`config/settings.yaml\`.
2. Sets up logging in console stdout and writes records to \`logs/signal_hunter.log\`.
3. Simulates/gathers breakthrough indicators.
4. enriches records with summaries and opportunities using active Analyzers.
5. Filters results against confidence scores inside \`SignalVerifier\`.
6. Commits verified results to \`data/items/{item_id}.json\`.
7. Compiles and publishes the Markdown Briefing under \`reports/daily_intelligence_brief_{date}.md\`.

---

## 🧪 Testing

Execute the test suite using Python's standard discovery runner:

\`\`\`bash
python -m unittest discover -s tests
\`\`\`

---

## 🔌 Extensibility: How to Add a Collector

Adding a new collector (e.g. Substack, HackerNews, or custom API) is extremely straightforward:

1. Create a file inside \`collectors/\` (e.g., \`collectors/hn_collector.py\`).
2. Implement a class inheriting from \`BaseCollector\`:
   \`\`\`python
   from typing import List
   from collectors.base import BaseCollector
   from models.research_item import ResearchItem
   from utils.helpers import generate_id
   from utils.exceptions import CollectionError

   class HackerNewsCollector(BaseCollector):
       @property
       def name(self) -> str:
           return "HackerNews"

       def collect(self) -> List[ResearchItem]:
           self.logger.info("Starting HackerNews crawl...")
           results = []
           try:
               # Fetch API content...
               # Parse and instantiate ResearchItems
               item = ResearchItem(
                   id=generate_id("https://news.ycombinator.com/item?id=123"),
                   title="Show HN: A new compiler in Rust",
                   url="https://news.ycombinator.com/item?id=123",
                   source_type="engineering_blog",
                   raw_content="Show HN description text...",
               )
               results.append(item)
           except Exception as e:
               raise CollectionError(self.name, f"Request failed: {e}")
           
           return results
   \`\`\`
3. Register the collector in \`config/settings.yaml\` and initialize it inside \`main.py\`'s runtime loop.
`
  }
];
