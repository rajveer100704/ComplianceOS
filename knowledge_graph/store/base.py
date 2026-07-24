"""Base interface contract for Knowledge Graph storage engines."""

from abc import ABC, abstractmethod
from typing import List, Optional
from knowledge_graph.schemas import GraphNode, GraphEdge, SubGraph, EdgeType


class BaseGraphStore(ABC):
    """Abstract interface contract for Knowledge Graph storage engines."""

    @abstractmethod
    async def add_node(self, node: GraphNode) -> str:
        """Adds a graph node or updates existing node by ID."""
        pass

    @abstractmethod
    async def get_node(self, node_id: str) -> Optional[GraphNode]:
        """Retrieves a graph node by ID."""
        pass

    @abstractmethod
    async def add_edge(self, edge: GraphEdge) -> str:
        """Adds a directed graph edge between source and target nodes."""
        pass

    @abstractmethod
    async def get_neighbors(
        self,
        node_id: str,
        organization_id: str,
        edge_types: Optional[List[EdgeType]] = None,
    ) -> List[GraphNode]:
        """Retrieves immediate 1-hop neighbor vertices of a node."""
        pass

    @abstractmethod
    async def get_subgraph(
        self, node_id: str, depth: int = 1, organization_id: str = "default"
    ) -> SubGraph:
        """Extracts a sub-graph neighborhood surrounding target node up to specified depth."""
        pass
