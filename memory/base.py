"""Abstract base class implementation for memory storage engine tiers."""

import uuid
import logging
from datetime import datetime, UTC
from typing import List, Dict, Optional
from memory.interfaces import BaseMemoryStore
from memory.schemas import MemoryItem, MemoryQuery

logger = logging.getLogger("memory.base")


class InMemoryStore(BaseMemoryStore):
    """In-memory reference storage engine implementing version history tracking."""

    def __init__(self):
        self._items: Dict[str, MemoryItem] = {}  # logical_id -> latest MemoryItem
        self._history: Dict[str, List[MemoryItem]] = (
            {}
        )  # logical_id -> List[MemoryItem]

    async def store(self, item: MemoryItem) -> str:
        logical_id = item.logical_id or item.id
        if logical_id not in self._history:
            self._history[logical_id] = []

        item.is_latest = True
        self._items[logical_id] = item
        self._history[logical_id].append(item)
        logger.debug(
            f"Stored memory item '{logical_id}' of type '{item.memory_type.value}' version '{item.version}'"
        )
        return logical_id

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

    async def latest(self, logical_id: str) -> Optional[MemoryItem]:
        """Retrieves the latest active version of a memory item."""
        return self._items.get(logical_id)

    async def history(self, logical_id: str) -> List[MemoryItem]:
        """Retrieves the full immutable version history list for a logical_id."""
        return self._history.get(logical_id, [])

    async def insert_version(self, item: MemoryItem) -> MemoryItem:
        """Inserts a new immutable version entry into history and marks it as latest."""
        logical_id = item.logical_id or item.id

        # Mark previous versions as not latest
        if logical_id in self._history:
            for prev in self._history[logical_id]:
                prev.is_latest = False

        ver_parts = item.version.lstrip("v").split(".")
        new_ver = f"v{ver_parts[0]}.{ver_parts[1]}.{int(ver_parts[2]) + 1}"

        new_record = item.model_copy(
            update={
                "record_id": str(uuid.uuid4()),
                "version": new_ver,
                "is_latest": True,
                "updated_at": datetime.now(UTC),
            }
        )
        if logical_id not in self._history:
            self._history[logical_id] = []

        self._history[logical_id].append(new_record)
        self._items[logical_id] = new_record
        logger.info(
            f"Inserted new version '{new_ver}' for logical_id '{logical_id}' record_id '{new_record.record_id}'"
        )
        return new_record

    async def archive(self, memory_id: str) -> Optional[MemoryItem]:
        item = await self.latest(memory_id)
        if not item:
            return None

        # Create new version with is_archived = True
        archived_item = item.model_copy(update={"is_archived": True})
        return await self.insert_version(archived_item)

    async def pin(self, memory_id: str) -> Optional[MemoryItem]:
        item = await self.latest(memory_id)
        if not item:
            return None

        # Create new version with is_pinned = True
        pinned_item = item.model_copy(update={"is_pinned": True})
        return await self.insert_version(pinned_item)

    async def delete(self, memory_id: str) -> bool:
        if memory_id in self._items:
            del self._items[memory_id]
            if memory_id in self._history:
                del self._history[memory_id]
            return True
        return False
