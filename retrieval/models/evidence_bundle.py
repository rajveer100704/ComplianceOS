from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass(frozen=True)
class EvidenceBundle:
    """Encapsulates retrieved chunks, structural contexts, latency statistics, and score rankings."""

    query: str
    chunks: List[Any]  # list of Chunk objects
    scores: Dict[str, Dict[str, float]]  # chunk_id -> score components
    document_provenance: Dict[int, str]  # doc_id -> filename
    page_numbers: List[int]
    selection_reason: str
    receipt: Dict[str, Any]
