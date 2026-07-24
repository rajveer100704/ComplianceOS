"""Declarative query engine for impact analysis and sub-graph neighborhood search."""

import logging
from typing import Dict, Any
from knowledge_graph.schemas import GraphNode, NodeType
from knowledge_graph.store.base import BaseGraphStore
from knowledge_graph.traversers.bfs_dfs import MultiHopTraverser

logger = logging.getLogger("knowledge_graph.queries")


class KnowledgeGraphQueryEngine:
    """Executes impact analysis and declarative graph queries."""

    def __init__(self, store: BaseGraphStore):
        self.store = store
        self.traverser = MultiHopTraverser(store)

    async def query_impact(
        self, regulation_node_id: str, organization_id: str = "default"
    ) -> Dict[str, Any]:
        """Calculates all requirements, claims, and evidence impacted by a regulation update."""
        paths = await self.traverser.find_paths(
            source_node_id=regulation_node_id,
            target_node_types=[NodeType.REQUIREMENT, NodeType.CLAIM, NodeType.EVIDENCE],
            max_depth=3,
            organization_id=organization_id,
        )

        impacted_nodes: Dict[str, GraphNode] = {}
        for p in paths:
            impacted_nodes[p.target_node_id] = p.nodes[-1]

        reqs = [
            n for n in impacted_nodes.values() if n.node_type == NodeType.REQUIREMENT
        ]
        claims = [n for n in impacted_nodes.values() if n.node_type == NodeType.CLAIM]
        evidence = [
            n for n in impacted_nodes.values() if n.node_type == NodeType.EVIDENCE
        ]

        return {
            "source_regulation_id": regulation_node_id,
            "total_impacted_count": len(impacted_nodes),
            "impacted_requirements": [r.id for r in reqs],
            "impacted_claims": [c.id for c in claims],
            "impacted_evidence": [e.id for e in evidence],
        }
