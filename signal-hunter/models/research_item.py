"""
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
