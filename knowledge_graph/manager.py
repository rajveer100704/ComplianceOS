"""Centralized KnowledgeGraphManager facade orchestrating graph store, indexers, traversers, and queries."""

import logging
from typing import Dict, Any, List, Optional
from knowledge_graph.schemas import (
    GraphNode,
    GraphEdge,
    SubGraph,
    GraphPath,
    NodeType,
)
from knowledge_graph.store.base import BaseGraphStore
from knowledge_graph.store.memory_store import InMemoryGraphStore
from knowledge_graph.indexers.builder import GraphBuilder
from knowledge_graph.traversers.bfs_dfs import MultiHopTraverser
from knowledge_graph.queries import KnowledgeGraphQueryEngine
from memory.schemas import MemoryItem

logger = logging.getLogger("knowledge_graph.manager")


class KnowledgeGraphManager:
    """Centralized facade for building, traversing, and querying the Regulatory Knowledge Graph."""

    def __init__(self, store: Optional[BaseGraphStore] = None):
        self.store = store or InMemoryGraphStore()
        self.builder = GraphBuilder(self.store)
        self.traverser = MultiHopTraverser(self.store)
        self.query_engine = KnowledgeGraphQueryEngine(self.store)

    async def add_node(self, node: GraphNode) -> str:
        return await self.store.add_node(node)

    async def add_edge(self, edge: GraphEdge) -> str:
        return await self.store.add_edge(edge)

    async def get_node(self, node_id: str) -> Optional[GraphNode]:
        return await self.store.get_node(node_id)

    async def index_requirement(
        self, req_id: str, text: str, section: str, organization_id: str = "default"
    ) -> GraphNode:
        return await self.builder.index_requirement(
            req_id, text, section, organization_id
        )

    async def index_claim(
        self,
        claim_id: str,
        text: str,
        req_id: Optional[str] = None,
        organization_id: str = "default",
    ) -> GraphNode:
        return await self.builder.index_claim(claim_id, text, req_id, organization_id)

    async def index_evidence(
        self,
        evidence_id: str,
        snippet: str,
        claim_id: str,
        is_supporting: bool = True,
        organization_id: str = "default",
    ) -> GraphNode:
        return await self.builder.index_evidence(
            evidence_id, snippet, claim_id, is_supporting, organization_id
        )

    async def index_memory(self, memory_item: MemoryItem) -> GraphNode:
        """Links Sprint 3 MemoryItem into Knowledge Graph and returns the generated vertex."""
        return await self.builder.index_memory_item(memory_item)

    async def find_paths(
        self,
        source_node_id: str,
        target_node_types: Optional[List[NodeType]] = None,
        max_depth: int = 4,
        organization_id: str = "default",
    ) -> List[GraphPath]:
        return await self.traverser.find_paths(
            source_node_id, target_node_types, max_depth, organization_id
        )

    async def get_neighborhood(
        self, node_id: str, depth: int = 1, organization_id: str = "default"
    ) -> SubGraph:
        return await self.store.get_subgraph(node_id, depth, organization_id)

    async def query_impact(
        self, regulation_node_id: str, organization_id: str = "default"
    ) -> Dict[str, Any]:
        return await self.query_engine.query_impact(regulation_node_id, organization_id)
