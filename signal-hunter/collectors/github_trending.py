"""
Signal Hunter GitHub Trending Collector.

Queries the official GitHub Search API to discover trending code repositories,
respects rate limits, and maps outputs into standard ResearchItem models.
"""

import time
import logging
from datetime import datetime, timezone
from typing import Any, List, Optional
import requests

from collectors.base import BaseCollector
from models.research_item import ResearchItem, Author, Source
from utils.exceptions import CollectionError


class GitHubTrendingCollector(BaseCollector):
    """
    Ingests trending developer repositories from GitHub.
    """

    BASE_URL = "https://api.github.com/search/repositories"

    @property
    def name(self) -> str:
        """
        Return the unique descriptive name of the collector.
        """
        return "GitHub_Trending"

    def collect(self) -> List[ResearchItem]:
        """
        Scan GitHub Search API and gather raw ResearchItem objects.
        """
        self.logger.info("Starting collection from GitHub Search API")

        # Load configuration options
        topics: List[str] = self.config.sources or ["python", "typescript", "go"]
        min_stars: int = int(self.config.params.get("min_stars", 100))
        max_results: int = int(self.config.params.get("max_results", 15))
        timeout: float = float(self.config.params.get("timeout", 10.0))

        collected_items: List[ResearchItem] = []
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; SignalHunter/2.0; +https://ai.studio/build)",
            "Accept": "application/vnd.github.v3+json",
        }

        # Divide results to fetch per topic
        results_per_topic = max(1, max_results // len(topics))

        for topic in topics:
            topic = topic.strip()
            if not topic:
                continue

            self.logger.info("Querying GitHub for topic: %s (min_stars: %d)", topic, min_stars)

            # Construct query: e.g. "topic:machine-learning stars:>=100" or "language:python stars:>=100"
            if topic.lower() in ["python", "typescript", "go", "rust", "c++", "javascript", "java"]:
                q = f"language:{topic} stars:>={min_stars}"
            else:
                q = f"{topic} stars:>={min_stars}"

            params = {
                "q": q,
                "sort": "stars",
                "order": "desc",
                "per_page": min(30, results_per_topic),
            }

            try:
                # Polite rate limiting sleep between topics
                if collected_items:
                    time.sleep(1.0)

                response = requests.get(self.BASE_URL, params=params, headers=headers, timeout=timeout)
                if response.status_code == 403:
                    self.logger.warning("GitHub API rate limited (403). Returning gathered items so far.")
                    break
                elif response.status_code != 200:
                    self.logger.error("GitHub API returned error status %d: %s", response.status_code, response.text)
                    continue

                data = response.json()
                repos = data.get("items", [])

                for repo in repos:
                    # Avoid duplicates
                    if any(x.unique_id == f"github-{repo['id']}" for x in collected_items):
                        continue

                    # Map to ResearchItem
                    authors_list = []
                    owner = repo.get("owner", {})
                    if owner.get("login"):
                        authors_list.append(
                            Author(
                                name=owner["login"],
                                github_username=owner["login"],
                                website=owner.get("html_url"),
                            )
                        )

                    # Extract tags/topics
                    tags = repo.get("topics", [])
                    if repo.get("language") and repo["language"].lower() not in [t.lower() for t in tags]:
                        tags.append(repo["language"].lower())

                    # Create standard model
                    created_at_str = repo.get("created_at")
                    pub_date = None
                    if created_at_str:
                        try:
                            # Parse ISO timestamp
                            pub_date = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
                        except Exception:
                            pub_date = datetime.now(timezone.utc)

                    item = ResearchItem(
                        id=f"github-{repo['id']}",
                        title=repo.get("name", "Untitled GitHub Repository"),
                        source_name="GitHub",
                        source_type="code_repository",
                        url=repo.get("html_url", ""),
                        publication_date=pub_date,
                        discovered_date=datetime.now(timezone.utc),
                        authors=authors_list,
                        organization=owner.get("login") if owner.get("type") == "Organization" else None,
                        summary=repo.get("description") or f"A trending {repo.get('language', '')} project on GitHub: {repo.get('full_name')}",
                        tags=tags,
                        categories=[repo.get("language", "Software Engineering")],
                        github_repository=repo.get("html_url"),
                        version=f"v{repo.get('default_branch', 'main')}",
                        raw_content=repo.get("description") or "",
                        raw_metadata={
                            "stars": repo.get("stargazers_count", 0),
                            "forks": repo.get("forks_count", 0),
                            "watchers": repo.get("watchers_count", 0),
                            "open_issues": repo.get("open_issues_count", 0),
                            "license": repo.get("license", {}).get("name") if repo.get("license") else None,
                        }
                    )
                    collected_items.append(item)
                    if len(collected_items) >= max_results:
                        break

            except Exception as e:
                self.logger.error("GitHub search failed for query '%s': %s", q, e)
                # Keep processing other topics rather than crashing completely
                continue

            if len(collected_items) >= max_results:
                break

        self.logger.info("Completed GitHub trending collection. Gathered: %d repository(s).", len(collected_items))
        return collected_items
