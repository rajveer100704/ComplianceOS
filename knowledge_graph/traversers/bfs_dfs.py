"""Multi-hop path traverser and path search engine."""

import logging
from typing import List, Optional
from knowledge_graph.schemas import GraphPath, NodeType
from knowledge_graph.store.base import BaseGraphStore

logger = logging.getLogger("knowledge_graph.traversers.bfs_dfs")


class MultiHopTraverser:
    """Executes multi-hop path search and lineage discovery across graph vertices."""

    def __init__(self, store: BaseGraphStore):
        self.store = store

    async def find_paths(
        self,
        source_node_id: str,
        target_node_types: Optional[List[NodeType]] = None,
        max_depth: int = 4,
        organization_id: str = "default",
    ) -> List[GraphPath]:
        start_node = await self.store.get_node(source_node_id)
        if not start_node or start_node.organization_id != organization_id:
            return []

        paths: List[GraphPath] = []
        target_types = set(target_node_types) if target_node_types else None

        # Queue storing tuple of: (current_node, depth, path_nodes, path_edges)
        queue = [(start_node, 0, [start_node], [])]

        while queue:
            curr_node, depth, curr_nodes, curr_edges = queue.pop(0)

            if depth > 0 and (not target_types or curr_node.node_type in target_types):
                paths.append(
                    GraphPath(
                        source_node_id=source_node_id,
                        target_node_id=curr_node.id,
                        hops=depth,
                        nodes=curr_nodes,
                        edges=curr_edges,
                    )
                )

            if depth >= max_depth:
                continue

            neighbors = await self.store.get_neighbors(
                curr_node.id, organization_id=organization_id
            )
            visited_ids = {n.id for n in curr_nodes}

            for neighbor in neighbors:
                if neighbor.id not in visited_ids:
                    queue.append(
                        (
                            neighbor,
                            depth + 1,
                            curr_nodes + [neighbor],
                            curr_edges,  # Edge metadata placeholder
                        )
                    )

        logger.debug(
            f"MultiHopTraverser found {len(paths)} path(s) from '{source_node_id}' max_depth={max_depth}"
        )
        return paths
