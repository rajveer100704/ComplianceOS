"""Centralized MemoryManager facade orchestrating all 5 memory storage tiers and intelligence pipelines."""

import logging
from typing import Dict, List, Optional
from memory.schemas import (
    MemoryItem,
    MemoryQuery,
    MemoryContext,
    MemoryType,
)
from memory.interfaces import BaseMemoryStore
from memory.semantic.store import SemanticMemoryStore
from memory.episodic.store import EpisodicMemoryStore
from memory.organizational.store import OrganizationalMemoryStore
from memory.reviewer.store import ReviewerMemoryStore
from memory.workflow.store import WorkflowMemoryStore
from memory.retrieval import FederatedMemoryRetriever
from memory.builder import MemoryContextBuilder

logger = logging.getLogger("memory.manager")


class MemoryManager:
    """Centralized facade for storing, searching, and building token-budgeted memory contexts across all 5 tiers."""

    def __init__(
        self, custom_stores: Optional[Dict[MemoryType, BaseMemoryStore]] = None
    ):
        self.stores: Dict[MemoryType, BaseMemoryStore] = custom_stores or {
            MemoryType.SEMANTIC: SemanticMemoryStore(),
            MemoryType.EPISODIC: EpisodicMemoryStore(),
            MemoryType.ORGANIZATIONAL: OrganizationalMemoryStore(),
            MemoryType.REVIEWER: ReviewerMemoryStore(),
            MemoryType.WORKFLOW: WorkflowMemoryStore(),
        }
        self.retriever = FederatedMemoryRetriever(self.stores)
        self.context_builder = MemoryContextBuilder()

    async def store(self, item: MemoryItem) -> str:
        """Stores a memory item into its corresponding tier."""
        store = self.stores.get(item.memory_type)
        if not store:
            raise ValueError(
                f"No store registered for memory type '{item.memory_type}'"
            )
        item_id = await store.store(item)
        logger.info(
            f"Memory item '{item_id}' stored in tier '{item.memory_type.value}'"
        )
        return item_id

    async def search(self, query: MemoryQuery) -> List[MemoryItem]:
        """Searches memory items across targeted tiers."""
        return await self.retriever.retrieve(query)

    async def build_context(
        self,
        query_text: str,
        organization_id: str,
        memory_types: Optional[List[MemoryType]] = None,
        top_k: int = 5,
        token_budget: int = 2000,
    ) -> MemoryContext:
        """Unified entry point for agents to acquire token-budgeted MemoryContext."""
        query = MemoryQuery(
            query_text=query_text,
            organization_id=organization_id,
            memory_types=memory_types or [],
            top_k=top_k,
        )
        items = await self.retriever.retrieve(query)
        return self.context_builder.build(
            raw_items=items,
            query_text=query_text,
            organization_id=organization_id,
            token_budget=token_budget,
        )

    async def archive_memory(self, item_id: str, memory_type: MemoryType) -> bool:
        """Archives a memory item by setting is_archived = True."""
        store = self.stores.get(memory_type)
        if store and hasattr(store, "_items") and item_id in store._items:
            store._items[item_id].is_archived = True
            logger.info(f"Archived memory item '{item_id}'")
            return True
        return False

    async def pin_memory(self, item_id: str, memory_type: MemoryType) -> bool:
        """Pins a memory item by setting is_pinned = True to prevent auto-expiration."""
        store = self.stores.get(memory_type)
        if store and hasattr(store, "_items") and item_id in store._items:
            store._items[item_id].is_pinned = True
            logger.info(f"Pinned memory item '{item_id}'")
            return True
        return False

    async def search_by_metadata(
        self,
        organization_id: str,
        key: str,
        value: Any,
        memory_types: Optional[List[MemoryType]] = None,
    ) -> List[MemoryItem]:
        """Searches memories matching specific metadata key-value filters."""
        query = MemoryQuery(
            query_text="",
            organization_id=organization_id,
            memory_types=memory_types or [],
            filters={key: value},
        )
        return await self.retriever.retrieve(query)
