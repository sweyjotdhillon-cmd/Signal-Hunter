"""
Signal Hunter Repository Tracker.

Analyzes GitHub repository metrics, adoption velocity, developer engagement, and trending developer interest.
"""

from typing import Dict, Any, List, Optional


class RepositoryTracker:
    """
    Monitors GitHub repository activity, traction, velocity, and mentions across tracked signals.
    """

    def __init__(self) -> None:
        pass

    def analyze_repositories(
        self,
        detailed_items: List[Any],
        compressed_trends: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Extracts repository trends from research items and compressed trend histories.

        Returns:
            List[Dict[str, Any]]: List of trending repositories.
        """
        repos: Dict[str, Dict[str, Any]] = {}

        def register_repo(repo_url: str, velocity: float, mentions: int, sources: int, growth: Optional[float], score: float) -> None:
            url = repo_url.strip()
            if not url:
                return
            if url not in repos:
                repos[url] = {
                    "repository": url,
                    "mentions_count": 0,
                    "sources_count": 0,
                    "total_velocity": 0.0,
                    "total_growth": 0.0,
                    "growth_records": 0,
                    "associated_signals_count": 0,
                    "max_opportunity_score": 0.0,
                }
            r = repos[url]
            r["mentions_count"] += mentions
            r["sources_count"] += max(r["sources_count"], sources)
            r["total_velocity"] += velocity
            if growth is not None:
                r["total_growth"] += growth
                r["growth_records"] += 1
            r["associated_signals_count"] += 1
            r["max_opportunity_score"] = max(r["max_opportunity_score"], score)

        # 1. From detailed items
        for item in detailed_items:
            if item.github_repository:
                trend = item.trend_metadata
                register_repo(
                    item.github_repository,
                    velocity=trend.velocity,
                    mentions=trend.mentions_count,
                    sources=trend.sources_count,
                    growth=trend.growth_percentage,
                    score=item.opportunity_score,
                )

        # 2. From compressed trends
        for trend in compressed_trends:
            # Check if has a repo listed
            # Wait, some compressed trends might have repo in summary or fields, or we can use the opportunity history
            # But we can check if "github_repository" was saved in any way, or if we want to simulate
            # Let's check if "github_repository" is present in trend (we can add it if we serialize or extract)
            # Let's support trend.get("github_repository")
            repo = trend.get("github_repository")
            if repo:
                register_repo(
                    repo,
                    velocity=trend.get("velocity", 1.0),
                    mentions=trend.get("mentions_count", 1),
                    sources=trend.get("sources_count", 1),
                    growth=trend.get("growth_percentage", 0.0),
                    score=trend.get("opportunity_score", 0.0),
                )

        results: List[Dict[str, Any]] = []
        for url, stats in repos.items():
            sigs = stats["associated_signals_count"]
            avg_vel = stats["total_velocity"] / sigs if sigs > 0 else 0.0
            avg_growth = stats["total_growth"] / stats["growth_records"] if stats["growth_records"] > 0 else 0.0

            # Calculate a general traction/interest confidence score
            # Higher velocity, higher mentions, and high opportunity score increase confidence
            confidence = min(1.0, (stats["mentions_count"] / 10.0) + (avg_vel / 50.0) + (stats["max_opportunity_score"] / 2.0))

            results.append({
                "repository": url,
                "associated_signals_count": sigs,
                "total_mentions": stats["mentions_count"],
                "sources_count": stats["sources_count"],
                "average_velocity": round(avg_vel, 3),
                "average_growth_percentage": round(avg_growth, 2),
                "max_opportunity_score": round(stats["max_opportunity_score"], 3),
                "traction_confidence": round(confidence, 2),
            })

        # Sort by total mentions descending, then by avg velocity
        results.sort(key=lambda x: (x["total_mentions"], x["associated_signals_count"], x["average_velocity"]), reverse=True)
        return results
