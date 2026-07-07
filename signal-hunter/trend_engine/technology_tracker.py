"""
Signal Hunter Technology Tracker.

Traces technology activity, acceleration, emergence, and decline over temporal horizons.
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional


class TechnologyTracker:
    """
    Identifies accelerating, emerging, and declining technologies based on frequency and score dynamics.
    """

    def __init__(self, recent_days: int = 30, historic_days: int = 180) -> None:
        """
        Initialize TechnologyTracker.

        Args:
            recent_days (int): Sliding window size in days to classify "recent" items.
            historic_days (int): Maximum history scope in days to classify "historical" items.
        """
        self.recent_days = recent_days
        self.historic_days = historic_days

    def analyze_technologies(
        self,
        detailed_items: List[Any],
        compressed_trends: List[Dict[str, Any]],
        cut_off_date: Optional[datetime] = None,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Analyzes technologies from active ResearchItems and compressed trend summaries.

        Args:
            detailed_items: List of active ResearchItem models.
            compressed_trends: List of archived trend dict objects.
            cut_off_date (Optional[datetime]): Reference date for analysis. Defaults to current UTC time.

        Returns:
            Dict[str, List[Dict[str, Any]]]: Categories: 'accelerating', 'emerging', 'declining'.
        """
        if not cut_off_date:
            cut_off_date = datetime.now(timezone.utc)
        elif cut_off_date.tzinfo is None:
            cut_off_date = cut_off_date.replace(tzinfo=timezone.utc)

        recent_horizon = cut_off_date - timedelta(days=self.recent_days)
        medium_horizon = cut_off_date - timedelta(days=90)
        max_horizon = cut_off_date - timedelta(days=self.historic_days)

        # Track technology metrics: list of (date, opportunity_score)
        tech_events: Dict[str, List[tuple]] = {}

        def register_tech(tech_name: str, discovered_dt: datetime, opp_score: float) -> None:
            name = tech_name.strip()
            if not name:
                return
            if name not in tech_events:
                tech_events[name] = []
            
            dt = discovered_dt if discovered_dt.tzinfo is not None else discovered_dt.replace(tzinfo=timezone.utc)
            tech_events[name].append((dt, opp_score))

        # 1. Gather events from detailed items
        for item in detailed_items:
            for tech in item.technologies:
                register_tech(tech, item.discovered_date, item.opportunity_score)

        # 2. Gather events from compressed trends
        for trend in compressed_trends:
            disc_date_str = trend.get("discovered_date")
            try:
                dt = datetime.fromisoformat(disc_date_str) if disc_date_str else cut_off_date
            except ValueError:
                dt = cut_off_date
            opp_score = trend.get("opportunity_score", 0.0)

            for tech in trend.get("technologies", []):
                register_tech(tech, dt, opp_score)

        accelerating: List[Dict[str, Any]] = []
        emerging: List[Dict[str, Any]] = []
        declining: List[Dict[str, Any]] = []

        for tech, events in tech_events.items():
            # Classify into recent (0-30 days), medium (30-90 days), and old (90+ days)
            recent_events = [e for e in events if e[0] >= recent_horizon]
            medium_events = [e for e in events if medium_horizon <= e[0] < recent_horizon]
            old_events = [e for e in events if max_horizon <= e[0] < medium_horizon]

            rc = len(recent_events)
            mc = len(medium_events)
            oc = len(old_events)
            total_count = len(events)

            avg_score_recent = sum(e[1] for e in recent_events) / rc if rc > 0 else 0.0
            avg_score_historic = sum(e[1] for e in (medium_events + old_events)) / (mc + oc) if (mc + oc) > 0 else 0.0

            # 1. Accelerating
            # Technology has rising frequency or rising scores in the recent period compared to historic
            # We can define growth velocity:
            # growth = (recent_count / 30.0) - (historic_count / 150.0)
            historic_count = mc + oc
            growth_rate = rc - (historic_count / 5.0)  # normalized relative growth
            score_growth = avg_score_recent - avg_score_historic if rc > 0 and historic_count > 0 else 0.0

            # Acceleration is strong if both count and scores are rising, or if count is substantially rising
            acceleration = growth_rate + (score_growth * 5.0)

            if rc > 0 and (growth_rate > 0 or score_growth > 0):
                confidence = min(1.0, (rc + mc) / 10.0)
                accelerating.append({
                    "technology": tech,
                    "growth_rate": round(growth_rate, 3),
                    "score_growth": round(score_growth, 3),
                    "acceleration": round(acceleration, 3),
                    "confidence": round(confidence, 2),
                    "recent_count": rc,
                    "total_count": total_count,
                })

            # 2. Emerging
            # First seen recently, no old history (only in last 60-90 days), showing rapid initial momentum
            sorted_dates = sorted([e[0] for e in events])
            first_seen = sorted_dates[0]
            last_seen = sorted_dates[-1]

            # If first seen is within last 60 days and has some recent occurrences
            is_new = (cut_off_date - first_seen).days <= 60
            if is_new and rc >= 2:
                # Emerging confidence is based on the speed of adoption and high average score
                emerging_velocity = rc / max(1, (last_seen - first_seen).days)
                confidence = min(1.0, (rc / 5.0) * (avg_score_recent / 0.5))
                emerging.append({
                    "technology": tech,
                    "first_seen": first_seen.isoformat(),
                    "recent_count": rc,
                    "avg_opportunity_score": round(avg_score_recent, 3),
                    "velocity": round(emerging_velocity, 3),
                    "confidence": round(confidence, 2),
                })

            # 3. Declining
            # Used to be active in historic period (at least 3 sightings), but 0 sightings in recent period
            if rc == 0 and (mc + oc) >= 3:
                # Decline velocity: how long has it been inactive
                days_inactive = (cut_off_date - last_seen).days
                confidence = min(1.0, (mc + oc) / 10.0)
                declining.append({
                    "technology": tech,
                    "last_seen": last_seen.isoformat(),
                    "historic_count": mc + oc,
                    "days_inactive": days_inactive,
                    "confidence": round(confidence, 2),
                })

        # Sort the lists
        accelerating.sort(key=lambda x: (x["acceleration"], x["recent_count"]), reverse=True)
        emerging.sort(key=lambda x: (x["velocity"], x["avg_opportunity_score"]), reverse=True)
        declining.sort(key=lambda x: (x["days_inactive"], x["historic_count"]), reverse=True)

        return {
            "accelerating": accelerating,
            "emerging": emerging,
            "declining": declining,
        }
