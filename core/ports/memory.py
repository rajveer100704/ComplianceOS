"""Memory Store Port interface definition for Dependency Inversion (Sprint 2)."""

from typing import Protocol, List, Optional, Any
from memory.schemas import MemoryItem


class MemoryStorePort(Protocol):
    """Abstract port interface for version-aware memory stores."""

    async def latest(
        self, logical_id: str, organization_id: str = "default"
    ) -> Optional[MemoryItem]: ...

    async def history(
        self, logical_id: str, organization_id: str = "default"
    ) -> List[MemoryItem]: ...

    async def insert_version(self, item: MemoryItem) -> MemoryItem: ...

    async def search_by_metadata(
        self, organization_id: str, key: str, value: Any, tier: Optional[str] = None
    ) -> List[MemoryItem]: ...
