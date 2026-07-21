from dataclasses import dataclass
from retrieval.models.chunk import Chunk


@dataclass(frozen=True)
class ScoredCandidate:
    """Represents a candidate chunk scored by an indexing retriever engine."""

    chunk: Chunk
    score: float
