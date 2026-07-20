from typing import List, Tuple
from retrieval.models.chunk import Chunk

class CandidatePipeline:
    """Manages candidate formatting, deduplication, and pipeline filtering operations."""

    @staticmethod
    def deduplicate(candidates: List[Tuple[Chunk, float]]) -> List[Tuple[Chunk, float]]:
        """Removes duplicate chunk records, preserving the highest similarity scores."""
        seen = set()
        deduped = []
        for chunk, score in candidates:
            if chunk.chunk_id not in seen:
                seen.add(chunk.chunk_id)
                deduped.append((chunk, score))
        return deduped
