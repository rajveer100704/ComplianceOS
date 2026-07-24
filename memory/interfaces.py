"""Base interface contracts for memory storage engines."""

from abc import ABC, abstractmethod
from typing import List
from memory.schemas import MemoryItem, MemoryQuery


class BaseMemoryStore(ABC):
    """Abstract interface contract for memory storage engine tiers."""

    @abstractmethod
    async def store(self, item: MemoryItem) -> str:
        """Stores a memory item and returns its ID."""
        pass

    @abstractmethod
    async def search(self, query: MemoryQuery) -> List[MemoryItem]:
        """Searches memories matching query parameters."""
        pass

    @abstractmethod
    async def delete(self, memory_id: str) -> bool:
        """Deletes a memory item by ID."""
        pass
