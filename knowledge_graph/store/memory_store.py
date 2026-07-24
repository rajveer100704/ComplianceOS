"""In-memory NetworkX reference storage engine for Regulatory Knowledge Graph."""

import logging
from typing import List, Dict, Optional, Set
import networkx as nx
from knowledge_graph.store.base import BaseGraphStore
from knowledge_graph.schemas import GraphNode, GraphEdge, SubGraph, EdgeType

logger = logging.getLogger("knowledge_graph.store.memory")


class InMemoryGraphStore(BaseGraphStore):
    """In-memory reference graph store backed by NetworkX DiGraph."""

    def __init__(self):
        self._graph = nx.DiGraph()
        self._nodes: Dict[str, GraphNode] = {}
        self._edges: Dict[str, GraphEdge] = {}

    async def add_node(self, node: GraphNode) -> str:
        self._nodes[node.id] = node
        self._graph.add_node(
            node.id,
            organization_id=node.organization_id,
            node_type=node.node_type.value,
        )
        logger.debug(f"Added graph node '{node.id}' of type '{node.node_type.value}'")
        return node.id

    async def get_node(self, node_id: str) -> Optional[GraphNode]:
        return self._nodes.get(node_id)

    async def add_edge(self, edge: GraphEdge) -> str:
        self._edges[edge.id] = edge
        self._graph.add_edge(
            edge.source_node_id,
            edge.target_node_id,
            id=edge.id,
            edge_type=edge.edge_type.value,
            weight=edge.weight,
        )
        logger.debug(
            f"Added graph edge '{edge.id}': {edge.source_node_id} -[{edge.edge_type.value}]-> {edge.target_node_id}"
        )
        return edge.id

    async def get_neighbors(
        self,
        node_id: str,
        organization_id: str,
        edge_types: Optional[List[EdgeType]] = None,
    ) -> List[GraphNode]:
        if node_id not in self._graph:
            return []

        allowed_edge_strings = [et.value for et in edge_types] if edge_types else None
        neighbors: List[GraphNode] = []

        # Outgoing edges
        for succ in self._graph.successors(node_id):
            edge_data = self._graph.get_edge_data(node_id, succ)
            if (
                allowed_edge_strings
                and edge_data.get("edge_type") not in allowed_edge_strings
            ):
                continue
            succ_node = self._nodes.get(succ)
            if succ_node and succ_node.organization_id == organization_id:
                neighbors.append(succ_node)

        # Incoming edges
        for pred in self._graph.predecessors(node_id):
            edge_data = self._graph.get_edge_data(pred, node_id)
            if (
                allowed_edge_strings
                and edge_data.get("edge_type") not in allowed_edge_strings
            ):
                continue
            pred_node = self._nodes.get(pred)
            if (
                pred_node
                and pred_node.organization_id == organization_id
                and pred_node not in neighbors
            ):
                neighbors.append(pred_node)

        return neighbors

    async def get_subgraph(
        self, node_id: str, depth: int = 1, organization_id: str = "default"
    ) -> SubGraph:
        if node_id not in self._graph:
            return SubGraph(organization_id=organization_id)

        sub_node_ids: Set[str] = {node_id}
        current_layer: Set[str] = {node_id}

        for _ in range(depth):
            next_layer: Set[str] = set()
            for current_node in current_layer:
                # Add successors and predecessors
                for nxt in set(self._graph.successors(current_node)).union(
                    set(self._graph.predecessors(current_node))
                ):
                    n_obj = self._nodes.get(nxt)
                    if n_obj and n_obj.organization_id == organization_id:
                        next_layer.add(nxt)
            sub_node_ids.update(next_layer)
            current_layer = next_layer

        nodes = [self._nodes[nid] for nid in sub_node_ids if nid in self._nodes]
        edges = [
            e
            for e in self._edges.values()
            if e.source_node_id in sub_node_ids
            and e.target_node_id in sub_node_ids
            and e.organization_id == organization_id
        ]

        return SubGraph(organization_id=organization_id, nodes=nodes, edges=edges)
