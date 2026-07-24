"""Abstract base class implementation for memory storage engine tiers."""

import logging
from datetime import datetime, UTC
from typing import List, Dict, Optional
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
            f"Stored memory item '{item.id}' of type '{item.memory_type.value}' version '{item.version}'"
        )
        return item.id

    async def search(self, query: MemoryQuery) -> List[MemoryItem]:
        results: List[MemoryItem] = []
        for item in self._items.values():
            if item.organization_id != query.organization_id:
                continue
            if not query.include_archived and item.is_archived:
                continue
            if query.memory_types and item.memory_type not in query.memory_types:
                continue
            if item.importance_score < query.min_importance:
                continue

            # Metadata key-value match filter
            if query.filters:
                match = True
                for fk, fv in query.filters.items():
                    if item.metadata.get(fk) != fv:
                        match = False
                        break
                if not match:
                    continue

            if query.query_text.lower() in item.content.lower():
                results.append(item)
            elif not query.query_text:
                results.append(item)

        results.sort(key=lambda x: x.importance_score, reverse=True)
        return results[: query.top_k]

    async def archive(self, memory_id: str) -> Optional[MemoryItem]:
        item = self._items.get(memory_id)
        if not item:
            return None

        # Bump patch version for append-only record update
        ver_parts = item.version.lstrip("v").split(".")
        new_ver = f"v{ver_parts[0]}.{ver_parts[1]}.{int(ver_parts[2]) + 1}"

        archived_item = item.model_copy(
            update={
                "version": new_ver,
                "is_archived": True,
                "updated_at": datetime.now(UTC),
            }
        )
        self._items[memory_id] = archived_item
        logger.info(f"Archived memory '{memory_id}' with version '{new_ver}'")
        return archived_item

    async def pin(self, memory_id: str) -> Optional[MemoryItem]:
        item = self._items.get(memory_id)
        if not item:
            return None

        ver_parts = item.version.lstrip("v").split(".")
        new_ver = f"v{ver_parts[0]}.{ver_parts[1]}.{int(ver_parts[2]) + 1}"

        pinned_item = item.model_copy(
            update={
                "version": new_ver,
                "is_pinned": True,
                "updated_at": datetime.now(UTC),
            }
        )
        self._items[memory_id] = pinned_item
        logger.info(f"Pinned memory '{memory_id}' with version '{new_ver}'")
        return pinned_item

    async def delete(self, memory_id: str) -> bool:
        if memory_id in self._items:
            del self._items[memory_id]
            return True
        return False
