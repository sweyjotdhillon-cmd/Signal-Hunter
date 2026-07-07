"""
Signal Hunter Topic Tracker.

Calculates topic frequency, growth rate, and spike factors over sliding temporal windows.
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional


class TopicTracker:
    """
    Tracks and analyzes popularity and sudden popularity spikes of topics and categories.
    """

    def __init__(self, recent_days: int = 30) -> None:
        """
        Initialize TopicTracker.

        Args:
            recent_days (int): Sliding window size in days to classify "recent" vs "historical".
        """
        self.recent_days = recent_days

    def analyze_topics(
        self,
        detailed_items: List[Any],
        compressed_trends: List[Dict[str, Any]],
        cut_off_date: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """
        Analyzes topics from both active ResearchItems and compressed trend summaries.

        Args:
            detailed_items: List of active ResearchItem models.
            compressed_trends: List of archived trend dict objects.
            cut_off_date (Optional[datetime]): Reference date for analysis. Defaults to current UTC time.

        Returns:
            List[Dict[str, Any]]: List of topics with calculated spike metrics.
        """
        if not cut_off_date:
            cut_off_date = datetime.now(timezone.utc)
        elif cut_off_date.tzinfo is None:
            cut_off_date = cut_off_date.replace(tzinfo=timezone.utc)

        recent_horizon = cut_off_date - timedelta(days=self.recent_days)

        # Map to hold recent and historical occurrences of each topic/tag/category
        topic_counts: Dict[str, Dict[str, int]] = {}

        def register_topic(topic_name: str, discovered_dt: datetime) -> None:
            name = topic_name.strip()
            if not name:
                return
            if name not in topic_counts:
                topic_counts[name] = {"recent": 0, "historical": 0}

            dt = discovered_dt if discovered_dt.tzinfo is not None else discovered_dt.replace(tzinfo=timezone.utc)
            if dt >= recent_horizon:
                topic_counts[name]["recent"] += 1
            else:
                topic_counts[name]["historical"] += 1

        # Extract from detailed items
        for item in detailed_items:
            # Gather tags/categories
            tags_to_check = set(item.tags + item.categories)
            for tag in tags_to_check:
                register_topic(tag, item.discovered_date)

        # Extract from compressed trends
        for trend in compressed_trends:
            disc_date_str = trend.get("discovered_date")
            try:
                dt = datetime.fromisoformat(disc_date_str) if disc_date_str else cut_off_date
            except ValueError:
                dt = cut_off_date

            tags_to_check = set(trend.get("topics", []) + trend.get("categories", []))
            for tag in tags_to_check:
                register_topic(tag, dt)

        # Calculate spike metrics
        results: List[Dict[str, Any]] = []
        for topic, counts in topic_counts.items():
            r = counts["recent"]
            h = counts["historical"]
            
            # Simple, robust spike factor metric:
            # (recent_count) / (historical_count + 1)
            # If historical is 0, we avoid division by zero and get a clear spike of r.
            spike_factor = float(r) / (float(h) + 1.0)

            # Confidence is derived from sample size of recent occurrences
            # 1 occurrence: 0.2 confidence, 5+ occurrences: 1.0 confidence
            confidence = min(1.0, r / 5.0) if r > 0 else 0.0

            results.append({
                "topic": topic,
                "recent_count": r,
                "historical_count": h,
                "spike_factor": round(spike_factor, 3),
                "confidence": round(confidence, 2),
            })

        # Sort by spike factor descending, then by recent count
        results.sort(key=lambda x: (x["spike_factor"], x["recent_count"]), reverse=True)
        return results
