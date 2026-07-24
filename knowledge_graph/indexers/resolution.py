"""Entity Resolution Engine matching candidate nodes to canonical graph vertices."""

import logging
from typing import Dict
from knowledge_graph.schemas import GraphNode
from knowledge_graph.store.base import BaseGraphStore

logger = logging.getLogger("knowledge_graph.indexers.resolution")


class EntityResolver:
    """Resolves duplicate nodes into canonical graph vertices using content SHA-256 checksums."""

    def __init__(self, store: BaseGraphStore):
        self.store = store
        self._checksum_index: Dict[str, str] = {}  # checksum -> node_id

    async def resolve_or_create(self, node: GraphNode) -> GraphNode:
        """Resolves existing node by checksum or registers new node."""
        if node.checksum and node.checksum in self._checksum_index:
            existing_id = self._checksum_index[node.checksum]
            existing = await self.store.get_node(existing_id)
            if existing:
                logger.debug(
                    f"Resolved duplicate node to existing canonical node '{existing.id}'"
                )
                return existing

        await self.store.add_node(node)
        if node.checksum:
            self._checksum_index[node.checksum] = node.id

        return node
