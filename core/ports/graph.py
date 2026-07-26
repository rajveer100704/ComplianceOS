"""Graph Provider Port interface definition for Dependency Inversion (Sprint 2)."""

from typing import Protocol, List, Optional
from knowledge_graph.schemas import GraphNode, GraphEdge, GraphPath


class GraphProviderPort(Protocol):
    """Abstract port interface for graph storage engines (NetworkX, Neo4j, Memgraph)."""

    async def add_node(self, node: GraphNode) -> GraphNode: ...

    async def add_edge(self, edge: GraphEdge) -> GraphEdge: ...

    async def get_node(self, node_id: str) -> Optional[GraphNode]: ...

    async def find_paths(
        self, source_id: str, target_id: str, max_depth: int = 3
    ) -> List[GraphPath]: ...
