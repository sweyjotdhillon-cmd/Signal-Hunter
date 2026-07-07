"""
Signal Hunter Organization Tracker.

Monitors publishing activity, breakthrough consistency, and detects overlapping/similar
research initiatives across distinct organizations.
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional, Set


class OrganizationTracker:
    """
    Tracks corporate and academic research organizations, identifying breakthrough publishers
    and overlapping, parallel efforts.
    """

    def __init__(self) -> None:
        pass

    def analyze_breakthrough_publishers(
        self,
        detailed_items: List[Any],
        compressed_trends: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Identify organizations that repeatedly publish breakthroughs (highly verified or high scores).

        Returns:
            List[Dict[str, Any]]: Organizations ranked by breakthrough frequency and average scores.
        """
        org_stats: Dict[str, Dict[str, Any]] = {}

        def register_publication(org_name: str, is_bt: bool, sci_score: float, eng_score: float, conf_score: float) -> None:
            name = org_name.strip()
            if not name:
                return
            if name not in org_stats:
                org_stats[name] = {
                    "organization": name,
                    "publications_count": 0,
                    "breakthrough_count": 0,
                    "total_scientific": 0.0,
                    "total_engineering": 0.0,
                    "total_confidence": 0.0,
                }
            stats = org_stats[name]
            stats["publications_count"] += 1
            if is_bt or (sci_score >= 0.85 and eng_score >= 0.85):
                stats["breakthrough_count"] += 1
            stats["total_scientific"] += sci_score
            stats["total_engineering"] += eng_score
            stats["total_confidence"] += conf_score

        # Gather from active items
        for item in detailed_items:
            if item.organization:
                is_bt = item.verification_status.is_breakthrough
                register_publication(
                    item.organization,
                    is_bt,
                    item.scientific_score,
                    item.engineering_score,
                    item.confidence_score,
                )

        # Gather from compressed trends
        for trend in compressed_trends:
            org = trend.get("organization")
            if org:
                # Compressed items don't have nested status, but we check confidence/opportunity
                opp_score = trend.get("opportunity_score", 0.0)
                sci_score = trend.get("scientific_score", 0.0)
                eng_score = trend.get("engineering_score", 0.0)
                conf_score = trend.get("confidence_score", 0.0)
                is_bt = conf_score >= 0.85 or opp_score >= 0.85
                register_publication(org, is_bt, sci_score, eng_score, conf_score)

        results: List[Dict[str, Any]] = []
        for name, stats in org_stats.items():
            pub_count = stats["publications_count"]
            avg_sci = stats["total_scientific"] / pub_count
            avg_eng = stats["total_engineering"] / pub_count
            avg_conf = stats["total_confidence"] / pub_count
            bt_count = stats["breakthrough_count"]

            # Confidence score of organization's reputation/ranking
            confidence = min(1.0, (pub_count / 3.0) * (avg_conf))

            results.append({
                "organization": name,
                "publications_count": pub_count,
                "breakthrough_count": bt_count,
                "average_scientific_score": round(avg_sci, 3),
                "average_engineering_score": round(avg_eng, 3),
                "average_confidence_score": round(avg_conf, 3),
                "reputation_confidence": round(confidence, 2),
            })

        # Rank primarily by breakthrough count descending, then by avg scientific score
        results.sort(key=lambda x: (x["breakthrough_count"], x["publications_count"], x["average_scientific_score"]), reverse=True)
        return results

    def detect_overlapping_research(
        self,
        detailed_items: List[Any],
        compressed_trends: List[Dict[str, Any]],
        window_days: int = 60,
    ) -> List[Dict[str, Any]]:
        """
        Detect similar research efforts from different organizations published around the same time.
        Compares shared technologies, tags, or categories.

        Returns:
            List[Dict[str, Any]]: Overlapping research incidents.
        """
        # Form unified list of records with: id, title, org, date, technologies, categories, topics
        records: List[Dict[str, Any]] = []

        for item in detailed_items:
            if not item.organization:
                continue
            records.append({
                "id": item.id,
                "title": item.title,
                "organization": item.organization,
                "date": item.discovered_date if item.discovered_date.tzinfo is not None else item.discovered_date.replace(tzinfo=timezone.utc),
                "technologies": set(item.technologies),
                "categories": set(item.categories),
                "topics": set(item.tags),
            })

        for trend in compressed_trends:
            org = trend.get("organization")
            if not org:
                continue
            disc_date_str = trend.get("discovered_date")
            try:
                dt = datetime.fromisoformat(disc_date_str) if disc_date_str else datetime.now(timezone.utc)
            except ValueError:
                dt = datetime.now(timezone.utc)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)

            records.append({
                "id": trend["item_id"],
                "title": trend["title"],
                "organization": org,
                "date": dt,
                "technologies": set(trend.get("technologies", [])),
                "categories": set(trend.get("categories", [])),
                "topics": set(trend.get("topics", [])),
            })

        overlaps: List[Dict[str, Any]] = []

        # Compare pairs of records from distinct organizations
        for i in range(len(records)):
            for j in range(i + 1, len(records)):
                rec_a = records[i]
                rec_b = records[j]

                if rec_a["organization"] == rec_b["organization"]:
                    continue

                # Check temporal window overlap
                days_diff = abs((rec_a["date"] - rec_b["date"]).days)
                if days_diff > window_days:
                    continue

                # Check technical overlap: shared technologies or categories/topics
                shared_techs = rec_a["technologies"].intersection(rec_b["technologies"])
                shared_cats = rec_a["categories"].intersection(rec_b["categories"])
                shared_topics = rec_a["topics"].intersection(rec_b["topics"])

                # Overlap criteria: at least 2 shared techs, or 1 tech + 1 category, or 1 category + 2 topics
                is_overlap = (
                    len(shared_techs) >= 2
                    or (len(shared_techs) >= 1 and len(shared_cats) >= 1)
                    or (len(shared_cats) >= 1 and len(shared_topics) >= 2)
                )

                if is_overlap:
                    # Calculate overlapping similarity score
                    total_shared = len(shared_techs) + len(shared_cats) + len(shared_topics)
                    similarity_score = min(1.0, total_shared / 10.0)

                    overlaps.append({
                        "item_a": {
                            "id": rec_a["id"],
                            "title": rec_a["title"],
                            "organization": rec_a["organization"],
                            "date": rec_a["date"].isoformat(),
                        },
                        "item_b": {
                            "id": rec_b["id"],
                            "title": rec_b["title"],
                            "organization": rec_b["organization"],
                            "date": rec_b["date"].isoformat(),
                        },
                        "shared_technologies": list(shared_techs),
                        "shared_categories": list(shared_cats),
                        "days_difference": days_diff,
                        "similarity_score": round(similarity_score, 2),
                    })

        # Sort overlaps by similarity score descending
        overlaps.sort(key=lambda x: x["similarity_score"], reverse=True)
        return overlaps
