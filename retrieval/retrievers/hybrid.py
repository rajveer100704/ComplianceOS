from typing import List, Tuple
from retrieval.base import BaseRetriever
from retrieval.capabilities import RetrieverCapabilities
from retrieval.models.chunk import Chunk
from retrieval.registry import register_retriever
from retrieval.fusion.rrf import ReciprocalRankFusion

@register_retriever("hybrid")
class HybridRetriever(BaseRetriever):
    """Orchestrates combined dense search and keyword BM25 indexing operations."""

    def __init__(self, dense_retriever=None, bm25_retriever=None, rrf=None):
        self.dense_retriever = dense_retriever
        self.bm25_retriever = bm25_retriever
        self.rrf = rrf or ReciprocalRankFusion()

    @property
    def capabilities(self) -> RetrieverCapabilities:
        return RetrieverCapabilities(hybrid=True, metadata=True, filters=True)

    def retrieve(self, query: str, limit: int, filters: dict = None) -> List[Tuple[Chunk, float]]:
        dense_results = []
        if self.dense_retriever:
            dense_results = self.dense_retriever.retrieve(query, limit=20, filters=filters)

        bm25_results = []
        if self.bm25_retriever:
            bm25_results = self.bm25_retriever.retrieve(query, limit=20, filters=filters)

        # Merge via Reciprocal Rank Fusion
        return self.rrf.fuse(dense_results, bm25_results, limit=limit)
