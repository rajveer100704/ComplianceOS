from typing import List, Tuple
import numpy as np
from retrieval.base import BaseVectorStore
from retrieval.capabilities import VectorStoreCapabilities
from retrieval.models.chunk import Chunk
from retrieval.registry import register_vector_store


@register_vector_store("local")
class LocalVectorStore(BaseVectorStore):
    """Memory-resident dictionary indexing chunks and computing cosine distance metrics."""

    def __init__(self, **kwargs):
        self.chunks = []
        self.embeddings = []

    @property
    def capabilities(self) -> VectorStoreCapabilities:
        return VectorStoreCapabilities(filtering=True, hybrid=False)

    def upsert(self, chunks: List[Chunk], embeddings: List[List[float]]) -> None:
        for c, emb in zip(chunks, embeddings):
            existing_idx = next(
                (
                    i
                    for i, existing in enumerate(self.chunks)
                    if existing.chunk_id == c.chunk_id
                ),
                None,
            )
            if existing_idx is not None:
                self.chunks[existing_idx] = c
                self.embeddings[existing_idx] = emb
            else:
                self.chunks.append(c)
                self.embeddings.append(emb)

    def search(
        self, query_vector: List[float], limit: int, filters: dict = None
    ) -> List[Tuple[Chunk, float]]:
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

    def delete(self, doc_id: int) -> None:
        indices_to_keep = [
            i for i, c in enumerate(self.chunks) if c.document_id != doc_id
        ]
        self.chunks = [self.chunks[i] for i in indices_to_keep]
        self.embeddings = [self.embeddings[i] for i in indices_to_keep]

    def clear(self) -> None:
        self.chunks.clear()
        self.embeddings.clear()
