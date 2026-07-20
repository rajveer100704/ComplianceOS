from typing import List, Tuple
from retrieval.models.chunk import Chunk

class ReciprocalRankFusion:
    """Merges candidate rankings using standard reciprocal rank equations."""

    def __init__(self, k: int = 60):
        self.k = k

    def fuse(self, dense_results: List[Tuple[Chunk, float]], bm25_results: List[Tuple[Chunk, float]], limit: int) -> List[Tuple[Chunk, float]]:
        rrf_scores = {}

        # Process dense rankings
        for rank, (chunk, _) in enumerate(dense_results):
            rrf_scores[chunk] = rrf_scores.get(chunk, 0.0) + (1.0 / (self.k + rank + 1))

        # Process BM25 rankings
        for rank, (chunk, _) in enumerate(bm25_results):
            rrf_scores[chunk] = rrf_scores.get(chunk, 0.0) + (1.0 / (self.k + rank + 1))

        # Sort and truncate
        fused = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
        return fused[:limit]
