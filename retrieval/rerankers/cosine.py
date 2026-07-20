from typing import List, Tuple
import numpy as np
from retrieval.base import BaseReranker
from retrieval.models.chunk import Chunk
from retrieval.registry import register_reranker

@register_reranker("cosine")
class CosineReranker(BaseReranker):
    """Reranks candidates using cosine similarities from standard text vectors."""

    def __init__(self, embedding_provider = None, **kwargs):
        if embedding_provider is None:
            from retrieval.embeddings.tfidf import TFIDFEmbeddingProvider
            self.embedding_provider = TFIDFEmbeddingProvider()
        else:
            self.embedding_provider = embedding_provider

    def rerank(self, query: str, candidates: List[Tuple[Chunk, float]]) -> List[Tuple[Chunk, float]]:
        if not candidates:
            return []
        q_vec = np.array(self.embedding_provider.embed_query(query))
        q_norm = np.linalg.norm(q_vec)
        if q_norm == 0:
            return candidates

        reranked = []
        for chunk, _ in candidates:
            e_vec = np.array(self.embedding_provider.embed_query(chunk.text))
            e_norm = np.linalg.norm(e_vec)
            if e_norm == 0:
                sim = 0.0
            else:
                sim = float(np.dot(q_vec, e_vec) / (q_norm * e_norm))
            reranked.append((chunk, sim))

        reranked.sort(key=lambda x: x[1], reverse=True)
        return reranked
