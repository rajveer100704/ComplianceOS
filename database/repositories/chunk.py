from typing import List, Tuple, Dict, Any
from retrieval.models.chunk import Chunk
from database.vector import VectorBackend

class ChunkRepository:
    """Handles vector chunk storage queries by delegating to the VectorBackend."""

    def __init__(self, vector_backend: VectorBackend):
        self.vector_backend = vector_backend

    async def upsert_chunks(self, chunks: List[Chunk], embeddings: List[List[float]]) -> None:
        await self.vector_backend.upsert(chunks, embeddings)

    async def search_chunks(self, query_vector: List[float], limit: int, filters: Dict[str, Any] = None) -> List[Tuple[Chunk, float]]:
        return await self.vector_backend.search(query_vector, limit, filters)

    async def delete_chunks(self, doc_id: int) -> None:
        await self.vector_backend.delete(doc_id)

    async def clear_chunks(self) -> None:
        await self.vector_backend.clear()
