"""
Signal Hunter Knowledge Base Manager.

Coordinates long-term persistence, indexing of entities (Topics, Technologies, etc.),
updates the relationship graph, and handles the automatic 6-month archival compression.
"""

import logging
import os
import shutil
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional, Set

from config.config_loader import MemoryConfig
from models.research_item import ResearchItem
from knowledge_base.relationship_graph import RelationshipGraph
from utils.helpers import safe_read_json, safe_write_json
from utils.logger import setup_logger


class KnowledgeBaseManager:
    """
    State manager for Signal Hunter's Knowledge Base.
    Keeps track of:
    - ResearchItems (saved individually under `{storage_dir}/items/{item_id}.json`)
    - Topics
    - Technologies
    - Organizations
    - Authors
    - GitHub repositories
    - Categories
    - Opportunity history
    - Compressed older trends
    - Semantic Entity Relationship Graph
    """

    def __init__(self, config: MemoryConfig) -> None:
        """
        Initialize KnowledgeBaseManager.

        Args:
            config (MemoryConfig): Config containing storage paths.
        """
        self.config = config
        self.logger = setup_logger(
            "signal_hunter.knowledge_base.manager",
            log_level="INFO",
        )

        self.base_dir = self.config.storage_dir
        self.items_dir = os.path.join(self.base_dir, "items")
        self.kb_dir = os.path.join(self.base_dir, "kb")

        # Create directories
        os.makedirs(self.items_dir, exist_ok=True)
        os.makedirs(self.kb_dir, exist_ok=True)

        # Initialize Graph
        self.graph = RelationshipGraph()

        # Initialize indices / storage states
        self.topics: Dict[str, Dict[str, Any]] = {}
        self.technologies: Dict[str, Dict[str, Any]] = {}
        self.organizations: Dict[str, Dict[str, Any]] = {}
        self.authors: Dict[str, Dict[str, Any]] = {}
        self.repositories: Dict[str, Dict[str, Any]] = {}
        self.categories: Dict[str, Dict[str, Any]] = {}
        self.opportunity_history: List[Dict[str, Any]] = []
        self.compressed_trends: List[Dict[str, Any]] = []

        # Load all existing indices on startup
        self.load_all()

    def add_research_item(self, item: ResearchItem) -> None:
        """
        Add a new ResearchItem to the knowledge base, enrich indices, and update the RelationshipGraph.

        Args:
            item (ResearchItem): Item representing the target signal source.
        """
        # 1. Save detailed item JSON
        item_filepath = os.path.join(self.items_dir, f"{item.id}.json")
        data = item.model_dump()
        # Ensure dates are serialized properly
        data["discovered_date"] = item.discovered_date.isoformat()
        if item.publication_date:
            data["publication_date"] = item.publication_date.isoformat()
        if item.verification_status.verified_at:
            data["verification_status"]["verified_at"] = item.verification_status.verified_at.isoformat()
        
        safe_write_json(item_filepath, data)

        # 2. Extract entities and update indices
        now_str = datetime.utcnow().isoformat()

        # Topics
        for tag in item.tags:
            tag_name = tag.strip()
            if tag_name:
                if tag_name not in self.topics:
                    self.topics[tag_name] = {"name": tag_name, "count": 0, "first_seen": now_str, "last_seen": now_str}
                self.topics[tag_name]["count"] += 1
                self.topics[tag_name]["last_seen"] = now_str
                self.graph.add_node(tag_name, "topic")
                self.graph.add_edge(item.id, tag_name, "has_topic", weight=1.0)

        # Technologies
        for tech in item.technologies:
            tech_name = tech.strip()
            if tech_name:
                if tech_name not in self.technologies:
                    self.technologies[tech_name] = {"name": tech_name, "count": 0, "first_seen": now_str, "last_seen": now_str}
                self.technologies[tech_name]["count"] += 1
                self.technologies[tech_name]["last_seen"] = now_str
                self.graph.add_node(tech_name, "technology")
                self.graph.add_edge(item.id, tech_name, "uses_technology", weight=1.0)

        # Organizations
        if item.organization:
            org_name = item.organization.strip()
            if org_name:
                if org_name not in self.organizations:
                    self.organizations[org_name] = {"name": org_name, "count": 0, "first_seen": now_str, "last_seen": now_str}
                self.organizations[org_name]["count"] += 1
                self.organizations[org_name]["last_seen"] = now_str
                self.graph.add_node(org_name, "organization")
                self.graph.add_edge(org_name, item.id, "published_item", weight=1.0)

        # Authors
        for author in item.authors:
            author_name = author.name.strip() if author.name else ""
            if author_name:
                if author_name not in self.authors:
                    self.authors[author_name] = {
                        "name": author_name,
                        "email": author.email,
                        "affiliation": author.affiliation,
                        "github_username": author.github_username,
                        "count": 0,
                    }
                self.authors[author_name]["count"] += 1
                self.graph.add_node(author_name, "author", metadata={"affiliation": author.affiliation})
                self.graph.add_edge(author_name, item.id, "authored_item", weight=1.0)
                if item.organization:
                    self.graph.add_edge(author_name, item.organization, "affiliated_with", weight=1.0)

        # Repositories
        if item.github_repository:
            repo_url = item.github_repository.strip()
            if repo_url:
                if repo_url not in self.repositories:
                    self.repositories[repo_url] = {"url": repo_url, "count": 0, "last_seen": now_str}
                self.repositories[repo_url]["count"] += 1
                self.repositories[repo_url]["last_seen"] = now_str
                self.graph.add_node(repo_url, "repository")
                self.graph.add_edge(item.id, repo_url, "has_repository", weight=1.0)

        # Categories
        for cat in item.categories:
            cat_name = cat.strip()
            if cat_name:
                if cat_name not in self.categories:
                    self.categories[cat_name] = {"name": cat_name, "count": 0, "last_seen": now_str}
                self.categories[cat_name]["count"] += 1
                self.categories[cat_name]["last_seen"] = now_str
                self.graph.add_node(cat_name, "category")
                self.graph.add_edge(item.id, cat_name, "belongs_to_category", weight=1.0)

        # Opportunity History
        if item.build_opportunities:
            for opp in item.build_opportunities:
                opp_name = opp.strip()
                if opp_name:
                    self.opportunity_history.append({
                        "item_id": item.id,
                        "title": item.title,
                        "opportunity": opp_name,
                        "discovered_date": item.discovered_date.isoformat(),
                        "opportunity_score": item.opportunity_score,
                    })
                    self.graph.add_node(opp_name, "opportunity")
                    self.graph.add_edge(item.id, opp_name, "offers_opportunity", weight=item.opportunity_score)

                    # Create connection between technology and opportunity to trace paths!
                    for tech in item.technologies:
                        self.graph.add_edge(tech, opp_name, "enables_opportunity", weight=item.opportunity_score)
                        self.graph.add_edge(opp_name, tech, "enabled_by_technology", weight=item.opportunity_score)

        # Add ResearchItem Node itself
        self.graph.add_node(
            item.id,
            "research_item",
            metadata={
                "title": item.title,
                "opportunity_score": item.opportunity_score,
                "confidence_score": item.confidence_score,
                "is_breakthrough": item.verification_status.is_breakthrough,
                "discovered_date": item.discovered_date.isoformat(),
            }
        )

        # Save all states immediately
        self.save_all()

    def get_research_item(self, item_id: str) -> Optional[ResearchItem]:
        """
        Retrieve a single detailed ResearchItem by its unique ID.

        Args:
            item_id (str): Unique ID.

        Returns:
            Optional[ResearchItem]: The ResearchItem if found, otherwise None.
        """
        item_filepath = os.path.join(self.items_dir, f"{item_id}.json")
        data = safe_read_json(item_filepath)
        if not data:
            return None
        try:
            return ResearchItem(**data)
        except Exception as e:
            self.logger.error("Failed to parse ResearchItem from %s: %s", item_filepath, e)
            return None

    def list_research_items(self) -> List[ResearchItem]:
        """
        List all active detailed ResearchItem records currently on disk.

        Returns:
            List[ResearchItem]: List of active items.
        """
        items: List[ResearchItem] = []
        if not os.path.exists(self.items_dir):
            return items

        for filename in os.listdir(self.items_dir):
            if filename.endswith(".json"):
                item_id = filename[:-5]
                item = self.get_research_item(item_id)
                if item:
                    items.append(item)

        items.sort(key=lambda x: x.discovered_date, reverse=True)
        return items

    def compress_old_records(self, cut_off_date: Optional[datetime] = None) -> None:
        """
        Scan all active detailed ResearchItem records.
        Records older than 6 months (180 days) from the cutoff date that are NOT marked as major breakthroughs
        will be compressed into summarized trend objects, and their detailed JSON files deleted.

        Args:
            cut_off_date (Optional[datetime]): Reference date for 6-month horizon. Defaults to current UTC time.
        """
        if not cut_off_date:
            cut_off_date = datetime.now(timezone.utc)

        horizon = cut_off_date - timedelta(days=180)
        self.logger.info("Starting archival compression. Horizon: %s", horizon.isoformat())

        active_items = self.list_research_items()
        compressed_count = 0

        for item in active_items:
            # Check if item is older than 6 months
            # Pydantic field may be offset-aware or naive. Let's make sure both are comparable.
            item_date = item.discovered_date
            if item_date.tzinfo is None:
                item_date = item_date.replace(tzinfo=timezone.utc)

            if item_date < horizon:
                # NEVER delete major breakthroughs
                if item.verification_status.is_breakthrough or item.is_verified and item.confidence_score >= 0.9:
                    self.logger.info("Skipping compression of major breakthrough item: %s", item.title)
                    continue

                # Create summarized trend object
                trend_summary = {
                    "item_id": item.id,
                    "title": item.title,
                    "discovered_date": item.discovered_date.isoformat(),
                    "summary": item.summary or f"Archived technical summary of {item.title}.",
                    "technologies": item.technologies,
                    "categories": item.categories,
                    "topics": item.tags,
                    "organization": item.organization,
                    "opportunity_score": item.opportunity_score,
                    "scientific_score": item.scientific_score,
                    "engineering_score": item.engineering_score,
                    "startup_score": item.startup_score,
                    "confidence_score": item.confidence_score,
                    "build_opportunities": item.build_opportunities,
                }

                # Save trend summary to list
                # Avoid duplicates in compressed trends
                if not any(t["item_id"] == item.id for t in self.compressed_trends):
                    self.compressed_trends.append(trend_summary)

                # Delete the detailed file
                item_filepath = os.path.join(self.items_dir, f"{item.id}.json")
                if os.path.exists(item_filepath):
                    os.remove(item_filepath)
                    compressed_count += 1

        self.logger.info("Archival compression completed. Compressed %d files.", compressed_count)
        self.save_all()

    def get_compressed_trends(self) -> List[Dict[str, Any]]:
        """Retrieve all compressed trend objects."""
        return self.compressed_trends

    def load_all(self) -> None:
        """Load indices and graph from files, fallback to empty states if files don't exist."""
        self.topics = safe_read_json(os.path.join(self.kb_dir, "topics.json")) or {}
        self.technologies = safe_read_json(os.path.join(self.kb_dir, "technologies.json")) or {}
        self.organizations = safe_read_json(os.path.join(self.kb_dir, "organizations.json")) or {}
        self.authors = safe_read_json(os.path.join(self.kb_dir, "authors.json")) or {}
        self.repositories = safe_read_json(os.path.join(self.kb_dir, "repositories.json")) or {}
        self.categories = safe_read_json(os.path.join(self.kb_dir, "categories.json")) or {}
        self.opportunity_history = safe_read_json(os.path.join(self.kb_dir, "opportunity_history.json")) or []
        self.compressed_trends = safe_read_json(os.path.join(self.kb_dir, "compressed_trends.json")) or []

        graph_data = safe_read_json(os.path.join(self.kb_dir, "relationship_graph.json"))
        if graph_data:
            self.graph = RelationshipGraph.from_dict(graph_data)
        else:
            self.graph = RelationshipGraph()

    def save_all(self) -> None:
        """Persist indices, opportunity histories, and graph states securely to disk as compact JSON files."""
        safe_write_json(os.path.join(self.kb_dir, "topics.json"), self.topics)
        safe_write_json(os.path.join(self.kb_dir, "technologies.json"), self.technologies)
        safe_write_json(os.path.join(self.kb_dir, "organizations.json"), self.organizations)
        safe_write_json(os.path.join(self.kb_dir, "authors.json"), self.authors)
        safe_write_json(os.path.join(self.kb_dir, "repositories.json"), self.repositories)
        safe_write_json(os.path.join(self.kb_dir, "categories.json"), self.categories)
        safe_write_json(os.path.join(self.kb_dir, "opportunity_history.json"), self.opportunity_history)
        safe_write_json(os.path.join(self.kb_dir, "compressed_trends.json"), self.compressed_trends)
        safe_write_json(os.path.join(self.kb_dir, "relationship_graph.json"), self.graph.to_dict())
