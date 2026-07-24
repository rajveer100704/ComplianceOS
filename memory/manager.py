"""Centralized MemoryManager facade orchestrating all 5 memory storage tiers and intelligence pipelines."""

import logging
from typing import Any, Dict, List, Optional
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
            f"Memory item '{item_id}' stored in tier '{item.memory_type.value}' version '{item.version}'"
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

    async def latest(
        self, logical_id: str, memory_type: MemoryType
    ) -> Optional[MemoryItem]:
        """Retrieves the latest active version of a memory item."""
        store = self.stores.get(memory_type)
        return await store.latest(logical_id) if store else None

    async def history(
        self, logical_id: str, memory_type: MemoryType
    ) -> List[MemoryItem]:
        """Retrieves the full immutable version history list for a logical_id."""
        store = self.stores.get(memory_type)
        return await store.history(logical_id) if store else []

    async def insert_version(
        self, item: MemoryItem, memory_type: MemoryType
    ) -> Optional[MemoryItem]:
        """Inserts a new immutable version entry for a logical_id."""
        store = self.stores.get(memory_type)
        return await store.insert_version(item) if store else None

    async def archive_memory(
        self, item_id: str, memory_type: MemoryType
    ) -> Optional[MemoryItem]:
        """Archives a memory item by delegating append-only update to the tier store."""
        store = self.stores.get(memory_type)
        if store:
            archived = await store.archive(item_id)
            if archived:
                logger.info(f"Archived memory item '{item_id}' via store facade")
                return archived
        return None

    async def pin_memory(
        self, item_id: str, memory_type: MemoryType
    ) -> Optional[MemoryItem]:
        """Pins a memory item by delegating append-only update to the tier store."""
        store = self.stores.get(memory_type)
        if store:
            pinned = await store.pin(item_id)
            if pinned:
                logger.info(f"Pinned memory item '{item_id}' via store facade")
                return pinned
        return None

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
