from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Any
from retrieval.models.chunk import Chunk


@dataclass
class RetrievalState:
    """Tracks intermediary candidates and scores across pipeline stages."""

    query: str
    session_id: str
    candidates: List[Tuple[Chunk, float]] = field(default_factory=list)
    scores: Dict[str, Dict[str, float]] = field(
        default_factory=dict
    )  # chunk_id -> {dense/bm25/rrf/rerank -> score}
    metadata: Dict[str, Any] = field(default_factory=dict)
