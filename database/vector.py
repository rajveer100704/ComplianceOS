from abc import ABC, abstractmethod
from typing import List, Tuple, Dict, Any
from retrieval.models.chunk import Chunk

class VectorBackend(ABC):
    """Abstract interface defining required database vector storage functions."""

    @abstractmethod
    async def upsert(self, chunks: List[Chunk], embeddings: List[List[float]]) -> None:
        pass

    @abstractmethod
    async def search(self, query_vector: List[float], limit: int, filters: Dict[str, Any] = None) -> List[Tuple[Chunk, float]]:
        pass

    @abstractmethod
    async def delete(self, doc_id: int) -> None:
        pass

    @abstractmethod
    async def clear(self) -> None:
        pass

class MemoryVectorBackend(VectorBackend):
    """Local dictionary-based vector store fallback for SQLite runs."""

    def __init__(self):
        self.chunks = []
        self.embeddings = []

    async def upsert(self, chunks: List[Chunk], embeddings: List[List[float]]) -> None:
        for c, emb in zip(chunks, embeddings):
            existing_idx = next((i for i, existing in enumerate(self.chunks) if existing.chunk_id == c.chunk_id), None)
            if existing_idx is not None:
                self.chunks[existing_idx] = c
                self.embeddings[existing_idx] = emb
            else:
                self.chunks.append(c)
                self.embeddings.append(emb)

    async def search(self, query_vector: List[float], limit: int, filters: Dict[str, Any] = None) -> List[Tuple[Chunk, float]]:
        import numpy as np
        if not self.embeddings:
            return []
        q_vec = np.array(query_vector)
        q_norm = np.linalg.norm(q_vec)
        if q_norm == 0:
            return []

        results = []
        for chunk, emb in zip(self.chunks, self.embeddings):
            if filters:
                mismatch = False
                for k, v in filters.items():
                    if chunk.metadata.get(k) != v:
                        mismatch = True
                        break
                if mismatch:
                    continue

            e_vec = np.array(emb)
            e_norm = np.linalg.norm(e_vec)
            if e_norm == 0:
                sim = 0.0
            else:
                sim = float(np.dot(q_vec, e_vec) / (q_norm * e_norm))
            results.append((chunk, sim))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]

    async def delete(self, doc_id: int) -> None:
        indices_to_keep = [i for i, c in enumerate(self.chunks) if c.document_id != doc_id]
        self.chunks = [self.chunks[i] for i in indices_to_keep]
        self.embeddings = [self.embeddings[i] for i in indices_to_keep]

    async def clear(self) -> None:
        self.chunks.clear()
        self.embeddings.clear()

class PGVectorBackend(VectorBackend):
    """PostgreSQL pgvector storage backend using native vector type mapping."""

    def __init__(self, async_session_factory):
        self.async_session_factory = async_session_factory

    async def upsert(self, chunks: List[Chunk], embeddings: List[List[float]]) -> None:
        # Placeholder mapping database upserts natively using SQL
        pass

    async def search(self, query_vector: List[float], limit: int, filters: Dict[str, Any] = None) -> List[Tuple[Chunk, float]]:
        # Returns empty list or compiles pgvector cosine distance `<->` searches
        return []

    async def delete(self, doc_id: int) -> None:
        pass

    async def clear(self) -> None:
        pass
