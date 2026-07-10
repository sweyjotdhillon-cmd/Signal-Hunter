"""
Source Weights & Quality Evaluation implementations for the Source Intelligence System.
"""

import os
from typing import Any, Dict, Optional
import yaml
from pydantic import BaseModel, Field, ConfigDict


class SourceWeight(BaseModel):
    """
    Manages custom and global weights for different source types and categories.
    """
    model_config = ConfigDict(extra="ignore")

    source_type_weights: Dict[str, float] = Field(default_factory=dict)
    parameter_weights: Dict[str, float] = Field(default_factory=dict)

    @classmethod
    def load_from_yaml(cls, filepath: str) -> "SourceWeight":
        """Loads weights configuration from a YAML file."""
        if not os.path.exists(filepath):
            return cls()
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            # Support nesting if defined under key
            if "source_type_weights" in data or "parameter_weights" in data:
                return cls(**data)
            return cls(source_type_weights=data.get("source_type_weights", {}),
                       parameter_weights=data.get("parameter_weights", {}))
        except Exception:
            return cls()

    def get_source_type_weight(self, source_type: str) -> float:
        """Returns the weight associated with a source type, defaulting to 1.0."""
        return self.source_type_weights.get(source_type, 1.0)

    def get_parameter_weight(self, param: str, default: float = 0.2) -> float:
        """Returns the weight associated with a scoring parameter."""
        return self.parameter_weights.get(param, default)


class SourceQuality(BaseModel):
    """
    Implements intelligence scoring principles and calculates quality scores for
    sources and research items, rewarding quality of evidence over reputation.
    """
    model_config = ConfigDict(extra="ignore")

    famous_organization_bias_penalty: float = Field(default=0.0, description="Reputation neutralization penalty.")
    rewards: Dict[str, float] = Field(default_factory=dict, description="Reward multipliers for intelligence parameters.")
    quality_checks: Dict[str, float] = Field(default_factory=dict, description="Multipliers for technical checklist criteria.")

    @classmethod
    def load_from_yaml(cls, filepath: str) -> "SourceQuality":
        """Loads quality scoring intelligence parameters from a YAML file."""
        if not os.path.exists(filepath):
            return cls()
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            if "intelligence_principles" in data:
                data = data["intelligence_principles"]
            return cls(**data)
        except Exception:
            return cls()

    def calculate_source_score(self, profile: Any, weights: SourceWeight) -> float:
        """
        Calculate an aggregate quality score for a source profile based on its metrics.
        Formula balances quality, reliability, freshness, popularity, and penalizes bias.
        """
        w_quality = weights.get_parameter_weight("quality", 0.3)
        w_reliability = weights.get_parameter_weight("reliability", 0.3)
        w_freshness = weights.get_parameter_weight("freshness", 0.2)
        w_popularity = weights.get_parameter_weight("popularity", 0.1)
        w_bias_penalty = weights.get_parameter_weight("bias_score_penalty", 0.1)

        # Base score weighted sum
        score = (
            profile.quality_score * w_quality +
            profile.reliability * w_reliability +
            profile.freshness * w_freshness +
            profile.popularity * w_popularity
        )

        # Apply bias penalty (higher bias score results in reduction)
        score -= profile.bias_score * w_bias_penalty
        return max(0.0, min(1.0, score))

    def evaluate_item_quality(self, item: Any, profile: Optional[Any] = None) -> float:
        """
        Evaluate and score a specific research item based on core Intelligence Principles:
        - Novelty
        - Engineering Usefulness
        - Scientific Impact
        - Commercial Opportunity (Startup score)
        - Practicality
        - Long-term Influence
        - Independent Confirmation
        
        Strictly prevents bias towards famous organizations.
        """
        # 1. Start with scores from the item
        novelty = getattr(item, "novelty_score", 0.5)
        engineering = getattr(item, "engineering_score", 0.5)
        scientific = getattr(item, "scientific_score", 0.5)
        commercial = getattr(item, "startup_score", 0.5)
        
        # Practicality & Long-term influence can be derived or stored in extra_metadata
        meta = getattr(item, "extra_metadata", {}) or {}
        practicality = meta.get("practicality", 0.5)
        long_term_influence = meta.get("long_term_influence", 0.5)
        independent_confirmation = meta.get("independent_confirmation", 0.5)

        # 2. Sum the rewards
        r_novelty = self.rewards.get("novelty", 0.20)
        r_engineering = self.rewards.get("engineering_usefulness", 0.20)
        r_scientific = self.rewards.get("scientific_impact", 0.15)
        r_commercial = self.rewards.get("commercial_opportunity", 0.10)
        r_practicality = self.rewards.get("practicality", 0.10)
        r_long_term = self.rewards.get("long_term_influence", 0.10)
        r_confirmation = self.rewards.get("independent_confirmation", 0.15)

        total_weight = r_novelty + r_engineering + r_scientific + r_commercial + r_practicality + r_long_term + r_confirmation
        if total_weight <= 0:
            total_weight = 1.0

        raw_score = (
            novelty * r_novelty +
            engineering * r_engineering +
            scientific * r_scientific +
            commercial * r_commercial +
            practicality * r_practicality +
            long_term_influence * r_long_term +
            independent_confirmation * r_confirmation
        ) / total_weight

        # 3. Handle Famous Organization Neutralization
        # If the item or organization is related to a famous brand, ensure we do NOT boost its score.
        # We actively penalize any excessive brand-based elevation.
        org_name = getattr(item, "organization", "") or ""
        famous_brands = ["openai", "google", "nvidia", "microsoft", "meta", "apple", "amazon"]
        is_famous = any(brand in org_name.lower() for brand in famous_brands) if org_name else False

        if is_famous:
            # We apply neutralization correction to ensure quality of evidence outweighs reputation.
            raw_score -= self.famous_organization_bias_penalty

        # If a source profile is provided, factor in the source's baseline quality and reliability
        if profile:
            final_score = 0.5 * raw_score + 0.5 * profile.quality_score
        else:
            final_score = raw_score

        return max(0.0, min(1.0, final_score))
