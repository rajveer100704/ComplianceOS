"""Abstract base class implementation for memory storage engine tiers."""

import logging
from typing import List, Dict
from memory.interfaces import BaseMemoryStore
from memory.schemas import MemoryItem, MemoryQuery

logger = logging.getLogger("memory.base")


class InMemoryStore(BaseMemoryStore):
    """In-memory reference storage engine for fast tier operations and test execution."""

    def __init__(self):
        self._items: Dict[str, MemoryItem] = {}

    async def store(self, item: MemoryItem) -> str:
        self._items[item.id] = item
        logger.debug(
            f"Stored memory item '{item.id}' of type '{item.memory_type.value}'"
        )
        return item.id

    async def search(self, query: MemoryQuery) -> List[MemoryItem]:
        results: List[MemoryItem] = []
        for item in self._items.values():
            if item.organization_id != query.organization_id:
                continue
            if query.memory_types and item.memory_type not in query.memory_types:
                continue
            if item.importance_score < query.min_importance:
                continue
            if query.query_text.lower() in item.content.lower():
                results.append(item)
            elif not query.query_text:
                results.append(item)

        results.sort(key=lambda x: x.importance_score, reverse=True)
        return results[: query.top_k]

    async def delete(self, memory_id: str) -> bool:
        if memory_id in self._items:
            del self._items[memory_id]
            return True
        return False
