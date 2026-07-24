"""Federated retriever querying across all memory storage tiers."""

import logging
from typing import List, Dict
from memory.schemas import MemoryItem, MemoryQuery, MemoryType
from memory.base import BaseMemoryStore

logger = logging.getLogger("memory.retrieval")


class FederatedMemoryRetriever:
    """Queries across multiple memory storage engine tiers."""

    def __init__(self, stores: Dict[MemoryType, BaseMemoryStore]):
        self.stores = stores

    async def retrieve(self, query: MemoryQuery) -> List[MemoryItem]:
        target_types = query.memory_types or list(self.stores.keys())
        all_items: List[MemoryItem] = []

        for m_type in target_types:
            store = self.stores.get(m_type)
            if store:
                items = await store.search(query)
                all_items.extend(items)

        logger.debug(f"Federated memory retrieval returned {len(all_items)} item(s)")
        return all_items
