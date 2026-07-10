"""
Source Registry, Filtering, and Selection implementations for the Source Intelligence System.
"""

import os
import random
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set
import yaml

from source_profiles.profile import SourceCategory, SourceProfile
from source_scoring.scoring import SourceWeight, SourceQuality


class SourceRegistry:
    """
    Centrally manages loaded research categories, source profiles, and weights,
    providing easy lookup APIs and configuration parsing.
    """

    def __init__(self, config_dir: Optional[str] = None) -> None:
        if not config_dir:
            # Resolve directory automatically relative to this file
            current_dir = os.path.dirname(os.path.abspath(__file__))
            parent_dir = os.path.dirname(current_dir)
            config_dir = os.path.join(parent_dir, "source_config")

        self.config_dir = config_dir
        self.categories: Dict[str, SourceCategory] = {}
        self.sources: Dict[str, SourceProfile] = {}
        self.weights = SourceWeight()
        self.quality_evaluator = SourceQuality()
        self.strategy: Dict[str, Any] = {}

        self.load_all()

    def load_all(self) -> None:
        """Loads all configurations from source_config directory."""
        # 1. Load source_categories.yaml
        cat_path = os.path.join(self.config_dir, "source_categories.yaml")
        if os.path.exists(cat_path):
            try:
                with open(cat_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                for cat_id, cat_data in data.get("categories", {}).items():
                    cat_data["id"] = cat_id
                    self.categories[cat_id] = SourceCategory(**cat_data)
            except Exception as e:
                print(f"Error loading source categories config: {e}")

        # 2. Load default_sources.yaml
        sources_path = os.path.join(self.config_dir, "default_sources.yaml")
        if os.path.exists(sources_path):
            try:
                with open(sources_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                for src_id, src_data in data.get("sources", {}).items():
                    src_data["id"] = src_id
                    self.sources[src_id] = SourceProfile(**src_data)
            except Exception as e:
                print(f"Error loading default sources config: {e}")

        # 3. Load weights
        weights_path = os.path.join(self.config_dir, "source_weights.yaml")
        self.weights = SourceWeight.load_from_yaml(weights_path)

        # 4. Load quality scoring config
        quality_path = os.path.join(self.config_dir, "quality_scoring.yaml")
        self.quality_evaluator = SourceQuality.load_from_yaml(quality_path)

        # 5. Load selection strategy config
        strategy_path = os.path.join(self.config_dir, "selection_strategy.yaml")
        if os.path.exists(strategy_path):
            try:
                with open(strategy_path, "r", encoding="utf-8") as f:
                    self.strategy = yaml.safe_load(f) or {}
            except Exception as e:
                print(f"Error loading selection strategy config: {e}")

    def get_category(self, cat_id: str) -> Optional[SourceCategory]:
        """Looks up a category by its identifier slug."""
        return self.categories.get(cat_id)

    def get_source(self, src_id: str) -> Optional[SourceProfile]:
        """Looks up a source profile by its identifier."""
        return self.sources.get(src_id)

    def list_categories(self) -> List[SourceCategory]:
        """Lists all categories sorted by priority."""
        return sorted(self.categories.values(), key=lambda c: c.priority)

    def list_sources(self) -> List[SourceProfile]:
        """Lists all registered sources."""
        return list(self.sources.values())

    def get_sources_by_category(self, cat_id: str) -> List[SourceProfile]:
        """Lists all sources registered under a specific category."""
        return [s for s in self.sources.values() if s.category == cat_id]

    def get_sources_by_type(self, source_type: str) -> List[SourceProfile]:
        """Lists all sources matching a source type."""
        return [s for s in self.sources.values() if s.source_type == source_type]


class SourceFilter:
    """
    Applies criteria and threshold rules to prune noise and qualify signals
    against category thresholds, max daily limits, and recency specifications.
    """

    def __init__(self, registry: SourceRegistry) -> None:
        self.registry = registry

    def filter_items_by_quality(self, items: List[Any]) -> List[Any]:
        """
        Filters out items that do not meet their category's quality thresholds.
        """
        qualified = []
        for item in items:
            category_id = self._detect_item_category(item)
            threshold = 0.70  # default
            if category_id:
                cat = self.registry.get_category(category_id)
                if cat:
                    threshold = cat.quality_threshold

            # Evaluate quality with associated source profile if any
            src_name = getattr(item, "source_name", "") or ""
            profile = None
            for p in self.registry.sources.values():
                if p.name.lower() in src_name.lower() or p.id.lower() == src_name.lower():
                    profile = p
                    break

            q_score = self.registry.quality_evaluator.evaluate_item_quality(item, profile)
            if q_score >= threshold:
                if hasattr(item, "extra_metadata"):
                    if item.extra_metadata is None:
                        item.extra_metadata = {}
                    item.extra_metadata["source_intelligence_score"] = q_score
                qualified.append(item)
        return qualified

    def filter_items_by_recency(self, items: List[Any]) -> List[Any]:
        """
        Filters items based on their category-defined maximum age in days.
        """
        qualified = []
        now = datetime.now(timezone.utc)
        for item in items:
            category_id = self._detect_item_category(item)
            max_age_days = 90  # default
            if category_id:
                cat = self.registry.get_category(category_id)
                if cat:
                    max_age_days = cat.recency_rules.max_age_days

            pub_date = getattr(item, "publication_date", None)
            if not pub_date:
                pub_date = getattr(item, "discovered_date", None)

            if pub_date:
                if not pub_date.tzinfo:
                    pub_date = pub_date.replace(tzinfo=timezone.utc)
                age = (now - pub_date).days
                if age <= max_age_days:
                    qualified.append(item)
            else:
                qualified.append(item)
        return qualified

    def apply_daily_caps(self, items: List[Any]) -> List[Any]:
        """
        Ensures category maximum daily ingest limits are respected.
        """
        cat_buckets: Dict[str, List[Any]] = {}
        for item in items:
            cat_id = self._detect_item_category(item) or "wildcards"
            if cat_id not in cat_buckets:
                cat_buckets[cat_id] = []
            cat_buckets[cat_id].append(item)

        capped_items = []
        for cat_id, cat_items in cat_buckets.items():
            cat_config = self.registry.get_category(cat_id)
            cap = cat_config.max_daily_items if cat_config else 10

            def get_score(itm: Any) -> float:
                meta = getattr(itm, "extra_metadata", {}) or {}
                return float(meta.get("source_intelligence_score", getattr(itm, "opportunity_score", 0.0)))

            sorted_items = sorted(cat_items, key=get_score, reverse=True)
            capped_items.extend(sorted_items[:cap])

        return capped_items

    def _detect_item_category(self, item: Any) -> Optional[str]:
        """Helper to find the corresponding SourceCategory ID for an item."""
        item_cats = getattr(item, "categories", []) or []
        if item_cats:
            for cat_slug in self.registry.categories.keys():
                if cat_slug in item_cats or cat_slug.replace("_", " ") in [c.lower() for c in item_cats]:
                    return cat_slug

        src_name = getattr(item, "source_name", "") or ""
        for p in self.registry.sources.values():
            if p.name.lower() in src_name.lower() or p.id.lower() == src_name.lower():
                return p.category

        return None


class SourceSelector:
    """
    Selects items from a pool according to the strict 70/30 source mix,
    70/30 category/discovery mix, and 70/20/10 recency mix distribution rules.
    """

    def __init__(self, registry: SourceRegistry) -> None:
        self.registry = registry

    def select(self, items: List[Any], user_interests: Optional[List[str]] = None) -> List[Any]:
        """
        Filters and selects items from a pool following the selection_strategy.yaml.
        """
        if not items:
            return []

        strategy = self.registry.strategy.get("selection_strategy", {})

        # 1. Identify Trusted Sources vs emerging
        trusted_src_ids = set()
        for cat in self.registry.categories.values():
            trusted_src_ids.update(cat.trusted_sources)

        trusted_items = []
        hidden_gems = []

        for item in items:
            src_name = getattr(item, "source_name", "").lower()
            is_trusted = False
            for src_id, src in self.registry.sources.items():
                if src_id in trusted_src_ids and (src_id == src_name or src.name.lower() in src_name):
                    is_trusted = True
                    break

            if is_trusted:
                trusted_items.append(item)
            else:
                hidden_gems.append(item)

        # 2. Setup user interests
        if not user_interests:
            personalization = strategy.get("personalization", {})
            if personalization.get("enabled", True):
                user_interests = personalization.get("user_interest_categories", [])
            else:
                user_interests = []

        interest_items = []
        random_items = []

        for item in items:
            cat_id = self._detect_item_category(item)
            if cat_id in user_interests:
                interest_items.append(item)
            else:
                random_items.append(item)

        # 3. Recency split
        now = datetime.now(timezone.utc)
        under_90_days = []
        under_1_year = []
        timeless = []

        for item in items:
            pub_date = getattr(item, "publication_date", None) or getattr(item, "discovered_date", None)
            if pub_date:
                if not pub_date.tzinfo:
                    pub_date = pub_date.replace(tzinfo=timezone.utc)
                age_days = (now - pub_date).days
                if age_days <= 90:
                    under_90_days.append(item)
                elif age_days <= 365:
                    under_1_year.append(item)
                else:
                    timeless.append(item)
            else:
                under_90_days.append(item)

        selected_set: Set[str] = set()
        selected_items = []

        # Target batch size
        target_count = min(len(items), 30)

        # Grab according to recency distribution (primary slice)
        recency_mix = strategy.get("recency_mix", {})
        r90_pct = recency_mix.get("within_90_days", 70.0) / 100.0
        r1y_pct = recency_mix.get("within_1_year", 20.0) / 100.0
        
        r90_target = int(target_count * r90_pct)
        r1y_target = int(target_count * r1y_pct)
        timeless_target = target_count - r90_target - r1y_target

        def grab_from(candidates: List[Any], count: int) -> List[Any]:
            grabbed = []
            available = [c for c in candidates if getattr(c, "unique_id", id(c)) not in selected_set]
            random.shuffle(available)
            for item_cand in available[:count]:
                uid = getattr(item_cand, "unique_id", id(item_cand))
                selected_set.add(uid)
                grabbed.append(item_cand)
            return grabbed

        selected_items.extend(grab_from(under_90_days, r90_target))
        selected_items.extend(grab_from(under_1_year, r1y_target))
        selected_items.extend(grab_from(timeless, timeless_target))

        # Fill remaining slots with trusted/hidden_gems or interest/random to satisfy targets
        remaining_slots = target_count - len(selected_items)
        if remaining_slots > 0:
            all_remaining = [item_cand for item_cand in items if getattr(item_cand, "unique_id", id(item_cand)) not in selected_set]
            selected_items.extend(grab_from(all_remaining, remaining_slots))

        return selected_items

    def _detect_item_category(self, item: Any) -> str:
        item_cats = getattr(item, "categories", []) or []
        if item_cats:
            for cat_slug in self.registry.categories.keys():
                if cat_slug in item_cats or cat_slug.replace("_", " ") in [c.lower() for c in item_cats]:
                    return cat_slug
        src_name = getattr(item, "source_name", "") or ""
        for p in self.registry.sources.values():
            if p.name.lower() in src_name.lower() or p.id.lower() == src_name.lower():
                return p.category
        return "wildcards"
