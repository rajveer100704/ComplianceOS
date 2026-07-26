"""Retriever Port interface definition for Dependency Inversion (Sprint 2)."""

from typing import Protocol, List, Dict, Any


class RetrieverPort(Protocol):
    """Abstract port interface for dense/sparse/hybrid retrieval engines."""

    async def search(
        self, query: str, top_k: int = 5, filters: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]: ...
