from typing import List, Tuple
from retrieval.models.chunk import Chunk


class ContextBuilder:
    """Combines extracted chunks with neighboring siblings or parent section nodes."""

    @staticmethod
    def expand_context(candidates: List[Tuple[Chunk, float]]) -> List[Chunk]:
        # Seam for future graph neighbor/parent resolution.
        # Currently returns extracted chunks directly.
        return [item[0] for item in candidates]
