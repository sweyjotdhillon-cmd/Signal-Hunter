"""
Signal Hunter ResearchItem Data Model.

This module defines the primary data transfer object (DTO) used throughout
the Signal Hunter pipeline.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ResearchItem(BaseModel):
    """
    Common data model representing a collected research, tech blog, or project.

    This forms the backbone of the Signal Hunter intelligence pipeline.
    """

    id: str = Field(
        ...,
        description="Unique identifier for the item (typically SHA-256 hash of the URL)",
    )
    title: str = Field(
        ...,
        description="Title of the research paper, article, or repository",
    )
    url: str = Field(
        ...,
        description="Canonical source URL of the signal",
    )
    source_type: str = Field(
        ...,
        description="Source classifier (e.g., 'paper', 'engineering_blog', 'documentation', 'github')",
    )
    raw_content: str = Field(
        ...,
        description="Raw fetched text content, abstract, or description",
    )
    author: Optional[str] = Field(
        None,
        description="Author, team, or publishing institution",
    )
    published_at: Optional[str] = Field(
        None,
        description="ISO timestamp or text representing when the source was published",
    )
    collected_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="UTC timestamp of when this item was ingested into the pipeline",
    )

    # Intelligence & Analysis (populated by Analyzers and Verifiers)
    summary: Optional[str] = Field(
        None,
        description="Core technical summary and key architectural takeaways",
    )
    signals: List[str] = Field(
        default_factory=list,
        description="Extracted early opportunities, scientific discoveries, or startup signals",
    )
    confidence_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Overall signal validity score between 0.0 and 1.0",
    )
    is_verified: bool = Field(
        default=False,
        description="Flag indicating whether this signal has been verified by the Verifier module",
    )
    verifier_notes: Optional[str] = Field(
        None,
        description="Explanation or critique regarding signal authenticity or breakthrough potential",
    )

    # Custom extension point
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Flexible key-value store for pipeline, collector, or analyzer metadata",
    )

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "id": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                "title": "Attention Is All You Need",
                "url": "https://arxiv.org/abs/1706.03762",
                "source_type": "paper",
                "raw_content": "We propose a new simple network architecture, the Transformer, based solely on attention mechanisms...",
                "author": "Ashish Vaswani et al.",
                "published_at": "2017-06-12T00:00:00Z",
                "summary": "Introduction of the Transformer architecture removing recurrence and convolutions entirely.",
                "signals": [
                    "Highly scalable sequence modeling",
                    "Parallelized training foundation for large models",
                ],
                "confidence_score": 0.98,
                "is_verified": True,
                "verifier_notes": "Breakthrough architecture that will reshape deep learning workflows.",
                "metadata": {"arxiv_id": "1706.03762"},
            }
        }
