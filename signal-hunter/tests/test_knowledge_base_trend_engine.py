"""
Unit tests for Signal Hunter Knowledge Base and Trend Engine.

Covers:
- RelationshipGraph: creation, serialization, neighborhood query, path tracing.
- KnowledgeBaseManager: saving, indexing, retrieving, and 6-month archival compression with breakthrough preservation.
- TrendEngine: accelerating/emerging/declining technologies, popular topics, breakthrough organizations, stronger opportunities, convergence, and startup path generation.
"""

import os
import shutil
import unittest
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List, Set

from config.config_loader import MemoryConfig
from models.research_item import ResearchItem, Author, VerificationStatus, TrendMetadata
from knowledge_base.relationship_graph import RelationshipGraph
from knowledge_base.manager import KnowledgeBaseManager
from trend_engine.engine import TrendEngine


class TestKnowledgeBaseAndTrendEngine(unittest.TestCase):
    """Extensive unit test suite for long-term intelligence, indexing, and trend tracing."""

    def setUp(self) -> None:
        """Create a clean, isolated temporary storage directory for each test run."""
        self.test_dir = os.path.join(os.path.dirname(__file__), "temp_test_data")
        self.config = MemoryConfig(storage_dir=self.test_dir, backup_enabled=False)

        # Clear any leftover test data
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def tearDown(self) -> None:
        """Remove temporary storage after test execution."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def create_mock_item(
        self,
        item_id: str,
        title: str,
        org: Optional[str] = None,
        days_ago: int = 0,
        is_breakthrough: bool = False,
        techs: list = None,
        tags: list = None,
        opportunities: list = None,
        scores: dict = None,
    ) -> ResearchItem:
        """Helper to construct rich mock ResearchItems."""
        discovered_dt = datetime.now(timezone.utc) - timedelta(days=days_ago)
        
        default_scores = {
            "opportunity_score": 0.8 if is_breakthrough else 0.5,
            "engineering_score": 0.85 if is_breakthrough else 0.4,
            "scientific_score": 0.9 if is_breakthrough else 0.3,
            "startup_score": 0.75 if is_breakthrough else 0.4,
            "confidence_score": 0.95 if is_breakthrough else 0.5,
            "novelty_score": 0.9 if is_breakthrough else 0.4,
        }
        if scores:
            default_scores.update(scores)

        return ResearchItem(
            unique_id=item_id,
            title=title,
            source_name="ArXiv",
            source_type="preprint",
            url=f"https://arxiv.org/abs/{item_id}",
            discovered_date=discovered_dt,
            publication_date=discovered_dt,
            organization=org,
            authors=[Author(name="Jane Doe", affiliation=org)],
            summary=f"Technical abstract for {title}.",
            tags=tags or ["deep learning"],
            categories=["Artificial Intelligence"],
            technologies=techs or ["PyTorch"],
            github_repository="https://github.com/example/repo",
            build_opportunities=opportunities or ["Industrial Automation"],
            opportunity_score=default_scores["opportunity_score"],
            engineering_score=default_scores["engineering_score"],
            scientific_score=default_scores["scientific_score"],
            startup_score=default_scores["startup_score"],
            confidence_score=default_scores["confidence_score"],
            novelty_score=default_scores["novelty_score"],
            verification_status=VerificationStatus(
                state="verified" if is_breakthrough else "pending",
                is_breakthrough=is_breakthrough,
                score=0.9 if is_breakthrough else 0.4,
            ),
            trend_metadata=TrendMetadata(
                velocity=25.0 if is_breakthrough else 2.0,
                sentiment_score=0.8 if is_breakthrough else 0.1,
                interest_level="high" if is_breakthrough else "low",
                mentions_count=10 if is_breakthrough else 1,
                sources_count=2 if is_breakthrough else 1,
            )
        )

    def test_relationship_graph(self) -> None:
        """Verify adding nodes, edges, querying neighbors, tracing paths, and serialization."""
        graph = RelationshipGraph()

        # Add nodes
        graph.add_node("PyTorch", "technology", {"popularity": "extremely-high"})
        graph.add_node("Robotics", "topic")
        
        # Verify node properties
        node = graph.get_node("PyTorch")
        self.assertIsNotNone(node)
        self.assertEqual(node["type"], "technology")
        self.assertEqual(node["metadata"]["popularity"], "extremely-high")

        # Add edges
        graph.add_edge("PyTorch", "Robotics", "enables", weight=0.9)
        
        # Check neighbors
        neighbors = graph.get_neighbors("PyTorch")
        self.assertEqual(len(neighbors), 1)
        self.assertEqual(neighbors[0]["id"], "Robotics")

        # Trace paths (DFS)
        graph.add_node("Warehouse_Bot", "opportunity")
        graph.add_edge("Robotics", "Warehouse_Bot", "leads_to")
        
        paths = graph.find_paths("PyTorch", "opportunity")
        self.assertEqual(len(paths), 1)
        self.assertEqual(paths[0], ["PyTorch", "Robotics", "Warehouse_Bot"])

        # Dict serialization/deserialization
        serialized = graph.to_dict()
        reconstructed = RelationshipGraph.from_dict(serialized)
        
        recon_node = reconstructed.get_node("PyTorch")
        self.assertIsNotNone(recon_node)
        self.assertEqual(recon_node["metadata"]["popularity"], "extremely-high")

    def test_knowledge_base_indexing_and_saving(self) -> None:
        """Verify KnowledgeBaseManager properly indexes topics, tech, authors, orgs, and graph relations."""
        manager = KnowledgeBaseManager(self.config)

        item = self.create_mock_item(
            item_id="12345",
            title="Attention is All You Need",
            org="Google Research",
            techs=["Transformers", "PyTorch"],
            tags=["nlp", "attention"],
            opportunities=["Translation System"],
        )

        manager.add_research_item(item)

        # Check saved item file exists
        self.assertTrue(os.path.exists(os.path.join(manager.items_dir, "12345.json")))

        # Verify active list retrieval
        items_list = manager.list_research_items()
        self.assertEqual(len(items_list), 1)
        self.assertEqual(items_list[0].title, "Attention is All You Need")

        # Check Topic / Tech indexing
        self.assertIn("nlp", manager.topics)
        self.assertEqual(manager.topics["nlp"]["count"], 1)
        self.assertIn("Transformers", manager.technologies)
        self.assertEqual(manager.technologies["Transformers"]["count"], 1)

        # Check Org / Author indexing
        self.assertIn("Google Research", manager.organizations)
        self.assertEqual(manager.organizations["Google Research"]["count"], 1)
        self.assertIn("Jane Doe", manager.authors)

        # Check Opportunity History
        self.assertEqual(len(manager.opportunity_history), 1)
        self.assertEqual(manager.opportunity_history[0]["opportunity"], "Translation System")

        # Check Graph integration
        paths = manager.graph.find_paths("12345", "opportunity")
        self.assertTrue(len(paths) >= 1)
        self.assertIn(["12345", "Translation System"], paths)

        # Verify load_all behaves properly on reload
        new_manager = KnowledgeBaseManager(self.config)
        self.assertIn("nlp", new_manager.topics)
        self.assertEqual(new_manager.topics["nlp"]["count"], 1)
        self.assertEqual(len(new_manager.opportunity_history), 1)

    def test_knowledge_base_archival_compression(self) -> None:
        """Verify older non-breakthrough records are compressed/deleted, and breakthroughs are preserved."""
        manager = KnowledgeBaseManager(self.config)

        # 1. Fresh item (keep detailed)
        item_fresh = self.create_mock_item(
            item_id="fresh", title="Recent AI Paper", days_ago=10, is_breakthrough=False
        )

        # 2. Old non-breakthrough (should compress)
        item_old_nb = self.create_mock_item(
            item_id="old_nb", title="Old Standard Work", days_ago=200, is_breakthrough=False, techs=["CUDA"]
        )

        # 3. Old breakthrough (should NOT compress, keep detailed)
        item_old_bt = self.create_mock_item(
            item_id="old_bt", title="Famous Transformer Breakthrough", days_ago=210, is_breakthrough=True, techs=["Transformers"]
        )

        manager.add_research_item(item_fresh)
        manager.add_research_item(item_old_nb)
        manager.add_research_item(item_old_bt)

        # Confirm all 3 exist initially
        self.assertTrue(os.path.exists(os.path.join(manager.items_dir, "fresh.json")))
        self.assertTrue(os.path.exists(os.path.join(manager.items_dir, "old_nb.json")))
        self.assertTrue(os.path.exists(os.path.join(manager.items_dir, "old_bt.json")))

        # Run compression
        manager.compress_old_records()

        # Check detailed files
        self.assertTrue(os.path.exists(os.path.join(manager.items_dir, "fresh.json")))
        self.assertFalse(os.path.exists(os.path.join(manager.items_dir, "old_nb.json"))) # Deleted!
        self.assertTrue(os.path.exists(os.path.join(manager.items_dir, "old_bt.json"))) # Preserved Breakthrough!

        # Check Trend object list
        compressed = manager.get_compressed_trends()
        self.assertEqual(len(compressed), 1)
        self.assertEqual(compressed[0]["item_id"], "old_nb")
        self.assertEqual(compressed[0]["title"], "Old Standard Work")
        self.assertIn("CUDA", compressed[0]["technologies"])

    def test_trend_engine_queries(self) -> None:
        """Verify TrendEngine queries can properly trace accelerating/emerging/declining tech, popular topics, orgs, and opportunities."""
        manager = KnowledgeBaseManager(self.config)

        # Feed some historical and recent items to establish trends
        # Accelerated Tech: PyTorch (recent 3, historic 1)
        # Declining Tech: TensorFlow (recent 0, historic 3)
        # Emerging Tech: Jax (recent 2, historic 0 - first seen recently)
        
        # Recent items (0-15 days ago)
        manager.add_research_item(self.create_mock_item("r1", "Paper 1", "DeepMind", days_ago=2, techs=["PyTorch", "Jax"], tags=["VLM"]))
        manager.add_research_item(self.create_mock_item("r2", "Paper 2", "OpenAI", days_ago=5, techs=["PyTorch", "Jax"], tags=["VLM"]))
        manager.add_research_item(self.create_mock_item("r3", "Paper 3", "Meta", days_ago=10, techs=["PyTorch"], tags=["VLM"]))

        # Historical items (100-120 days ago)
        manager.add_research_item(self.create_mock_item("h1", "Paper 4", "DeepMind", days_ago=100, techs=["PyTorch", "TensorFlow"], tags=["CNN"], is_breakthrough=True))
        manager.add_research_item(self.create_mock_item("h2", "Paper 5", "Google", days_ago=110, techs=["TensorFlow"], tags=["CNN"]))
        manager.add_research_item(self.create_mock_item("h3", "Paper 6", "Stanford", days_ago=120, techs=["TensorFlow"], tags=["CNN"]))

        engine = TrendEngine(manager)

        # 1. Accelerating Tech
        accel = engine.get_accelerating_technologies()
        self.assertTrue(len(accel) >= 1)
        accel_techs = [t["technology"] for t in accel]
        self.assertIn("PyTorch", accel_techs)
        self.assertIn("Jax", accel_techs)

        # 2. Declining Tech
        decline = engine.get_declining_technologies()
        self.assertTrue(len(decline) >= 1)
        self.assertEqual(decline[0]["technology"], "TensorFlow")

        # 3. Emerging Tech
        emerge = engine.get_emerging_technologies()
        self.assertTrue(len(emerge) >= 1)
        self.assertEqual(emerge[0]["technology"], "Jax")

        # 4. Suddenly Popular Topics
        topics = engine.get_suddenly_popular_topics()
        self.assertTrue(len(topics) >= 1)
        # VLM has 3 recent, 0 historic. CNN has 0 recent, 3 historic. VLM should be ranked above CNN.
        self.assertEqual(topics[0]["topic"], "VLM")

        # 5. Breakthrough Orgs
        orgs = engine.get_breakthrough_organizations()
        self.assertTrue(len(orgs) >= 1)
        # DeepMind published h1 which was a breakthrough
        self.assertEqual(orgs[0]["organization"], "DeepMind")
        self.assertEqual(orgs[0]["breakthrough_count"], 1)

    def test_repeated_discoveries_and_convergences(self) -> None:
        """Verify repeated discovery detection, technology convergence, and startup path generation."""
        manager = KnowledgeBaseManager(self.config)

        # Add overlapping publications: different orgs publishing similar topics with same techs in 10-day window
        manager.add_research_item(self.create_mock_item(
            "o1", "OpenAI VLM paper", "OpenAI", days_ago=2, techs=["VLM", "Transformer"], tags=["robots"], opportunities=["Robotic Maid"]
        ))
        manager.add_research_item(self.create_mock_item(
            "o2", "DeepMind Robotics paper", "DeepMind", days_ago=5, techs=["VLM", "Transformer"], tags=["robots"], opportunities=["Robotic Maid"]
        ))

        engine = TrendEngine(manager)

        # 1. Repeated Discoveries
        repeated = engine.detect_repeated_discoveries()
        self.assertEqual(len(repeated), 1)
        self.assertIn("OpenAI", repeated[0]["organizations"])
        self.assertIn("DeepMind", repeated[0]["organizations"])

        # 2. Tech Convergence
        convergence = engine.detect_technology_convergence()
        self.assertTrue(len(convergence) >= 1)
        self.assertEqual(convergence[0]["technology_a"], "Transformer")
        self.assertEqual(convergence[0]["technology_b"], "VLM")

        # 3. Startup Opportunities Path Tracing
        startup_opps = engine.detect_startup_opportunities()
        self.assertTrue(len(startup_opps) >= 1)
        self.assertEqual(startup_opps[0]["opportunity"], "Robotic Maid")
        self.assertTrue(len(startup_opps[0]["relationship_path"]) >= 4)
        self.assertIn("VLM", startup_opps[0]["relationship_path"])
        self.assertIn("Robotic Maid", startup_opps[0]["relationship_path"])


if __name__ == "__main__":
    unittest.main()
