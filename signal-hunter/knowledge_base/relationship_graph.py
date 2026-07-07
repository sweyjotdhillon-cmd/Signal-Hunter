"""
Signal Hunter Knowledge Base Relationship Graph.

Defines a serialized entity-relationship graph supporting directed relationship mapping,
weights, neighborhood exploration, and path tracing for strategic convergence.
"""

import logging
from typing import Dict, Any, List, Optional, Set
from utils.logger import setup_logger


class RelationshipGraph:
    """
    In-memory representation of entities and relationships.
    Can be serialized to and from compact JSON structures.
    """

    def __init__(self) -> None:
        """Initialize empty graph nodes and edges."""
        self.logger = setup_logger(
            "signal_hunter.knowledge_base.relationship_graph",
            log_level="INFO",
        )
        self.nodes: Dict[str, Dict[str, Any]] = {}
        # Adjacency list: node_id -> list of edge dicts
        self.edges: Dict[str, List[Dict[str, Any]]] = {}

    def add_node(self, node_id: str, node_type: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Add an entity node to the graph if it doesn't already exist.
        If it exists, merges the metadata.

        Args:
            node_id (str): Unique identifier for the node.
            node_type (str): Type of entity (e.g., 'research_item', 'topic', 'technology', 'organization', 'author', 'repository', 'category', 'opportunity').
            metadata (Optional[Dict[str, Any]]): Arbitrary metadata properties.
        """
        if not node_id:
            return

        if node_id not in self.nodes:
            self.nodes[node_id] = {
                "id": node_id,
                "type": node_type,
                "metadata": metadata or {},
            }
            self.edges[node_id] = []
        else:
            if metadata:
                self.nodes[node_id]["metadata"].update(metadata)

    def add_edge(
        self,
        source_id: str,
        target_id: str,
        rel_type: str,
        weight: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Add a directed/undirected edge between source and target nodes.
        Auto-creates missing nodes with 'unknown' type.

        Args:
            source_id (str): Source node identifier.
            target_id (str): Target node identifier.
            rel_type (str): Type of relationship (e.g., 'uses_technology', 'published_by', 'collaborated_with', 'enables_opportunity').
            weight (float): Relationship strength or confidence. Defaults to 1.0.
            metadata (Optional[Dict[str, Any]]): Arbitrary edge metadata.
        """
        if not source_id or not target_id:
            return

        # Ensure both nodes exist
        self.add_node(source_id, "unknown")
        self.add_node(target_id, "unknown")

        # Check for duplicates
        exists = False
        for edge in self.edges[source_id]:
            if edge["target"] == target_id and edge["type"] == rel_type:
                edge["weight"] = max(edge["weight"], weight)
                if metadata:
                    edge["metadata"].update(metadata)
                exists = True
                break

        if not exists:
            self.edges[source_id].append({
                "source": source_id,
                "target": target_id,
                "type": rel_type,
                "weight": weight,
                "metadata": metadata or {},
            })

    def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve node info by ID."""
        return self.nodes.get(node_id)

    def get_neighbors(self, node_id: str, rel_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all adjacent neighbor nodes connected from this node.

        Args:
            node_id (str): Source node ID.
            rel_type (Optional[str]): Filters neighbors by specific relationship type.

        Returns:
            List[Dict[str, Any]]: List of neighbor node dicts.
        """
        neighbors = []
        if node_id not in self.edges:
            return neighbors

        for edge in self.edges[node_id]:
            if rel_type is None or edge["type"] == rel_type:
                target_node = self.nodes.get(edge["target"])
                if target_node:
                    neighbors.append(target_node)
        return neighbors

    def find_paths(self, start_id: str, end_type: str, max_depth: int = 5) -> List[List[str]]:
        """
        Trace all paths from a start node to any node of a specific end type.
        Uses depth-first search (DFS) with loop protection.

        Args:
            start_id (str): ID of starting node.
            end_type (str): Target entity type (e.g., 'opportunity').
            max_depth (int): Maximum depth to traverse.

        Returns:
            List[List[str]]: List of paths where each path is a list of node IDs.
        """
        paths: List[List[str]] = []
        if start_id not in self.nodes:
            return paths

        def dfs(curr_id: str, current_path: List[str], visited: Set[str]) -> None:
            if len(current_path) > max_depth:
                return

            curr_node = self.nodes.get(curr_id)
            if not curr_node:
                return

            if curr_node["type"] == end_type:
                paths.append(list(current_path))
                # Continue searching or stop? Let's keep exploring

            # Traverse outbound edges
            for edge in self.edges.get(curr_id, []):
                target = edge["target"]
                if target not in visited:
                    visited.add(target)
                    current_path.append(target)
                    dfs(target, current_path, visited)
                    current_path.pop()
                    visited.remove(target)

        dfs(start_id, [start_id], {start_id})
        return paths

    def to_dict(self) -> Dict[str, Any]:
        """Serialize graph to standard JSON-compatible dictionary."""
        all_edges = []
        for src_id, edge_list in self.edges.items():
            all_edges.extend(edge_list)

        return {
            "nodes": list(self.nodes.values()),
            "edges": all_edges,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RelationshipGraph":
        """Reconstruct RelationshipGraph from a dictionary."""
        graph = cls()
        for node in data.get("nodes", []):
            graph.add_node(node["id"], node["type"], node.get("metadata"))

        for edge in data.get("edges", []):
            graph.add_edge(
                source_id=edge["source"],
                target_id=edge["target"],
                rel_type=edge["type"],
                weight=edge.get("weight", 1.0),
                metadata=edge.get("metadata"),
            )
        return graph
