"""
Source Profile & Category definitions for the Source Intelligence System.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class RecencyRule(BaseModel):
    """Rules defining how fresh research items must be within this category."""
    model_config = ConfigDict(extra="ignore")
    max_age_days: int = Field(default=90, description="Maximum age of items in days.")


class SourceCategory(BaseModel):
    """
    Represents a knowledge domain / category of research.
    """
    model_config = ConfigDict(extra="ignore")

    id: str = Field(..., description="Unique slug for the category (e.g. 'ai_ml').")
    name: str = Field(..., description="Descriptive human-readable name.")
    priority: int = Field(default=1, description="Priority rank (lower = higher priority).")
    weight: float = Field(default=1.0, description="Multiplier weight for category items.")
    trusted_sources: List[str] = Field(default_factory=list, description="IDs of trusted profiles.")
    emerging_sources: List[str] = Field(default_factory=list, description="IDs of emerging/hidden gem profiles.")
    recency_rules: RecencyRule = Field(default_factory=RecencyRule, description="Recency limitations.")
    quality_threshold: float = Field(default=0.70, ge=0.0, le=1.0, description="Minimum quality score to retain.")
    max_daily_items: int = Field(default=10, description="Capping limit for daily ingest.")
    random_discovery_percentage: float = Field(default=15.0, ge=0.0, le=100.0, description="Discovery quota for wildcards/hidden gems.")


class SourceProfile(BaseModel):
    """
    Represents a research ecosystem or publisher with its scores, limits, and adapters.
    """
    model_config = ConfigDict(extra="ignore")

    id: str = Field(..., description="Unique identifier for the source (e.g. 'arxiv_cs_ai').")
    name: str = Field(..., description="Descriptive human-readable name.")
    category: str = Field(..., description="The knowledge category ID this source belongs to.")
    source_type: str = Field(..., description="Type of source (e.g. 'Research Papers', 'Engineering Blogs').")
    quality_score: float = Field(default=0.8, ge=0.0, le=1.0, description="Baseline quality rating.")
    reliability: float = Field(default=0.8, ge=0.0, le=1.0, description="Trustworthiness of publication/source.")
    popularity: float = Field(default=0.5, ge=0.0, le=1.0, description="Ecosystem prominence.")
    bias_score: float = Field(default=0.1, ge=0.0, le=1.0, description="Ecosystem/company/affiliation bias (lower = better).")
    freshness: float = Field(default=0.8, ge=0.0, le=1.0, description="Speed of update propagation.")
    update_frequency: str = Field(default="daily", description="How often new data is published.")
    rate_limits: Dict[str, Any] = Field(default_factory=dict, description="API or crawler limits.")
    verification_strategy: str = Field(default="standard", description="Strategy used to verify information from this source.")
    api_available: bool = Field(default=True, description="True if API access is possible.")
    collector_available: bool = Field(default=False, description="True if a collector has been implemented.")
