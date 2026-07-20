from dataclasses import dataclass
from retrieval.models.evidence_bundle import EvidenceBundle

@dataclass(frozen=True)
class RetrievalResponse:
    """Standardized output contract wrapping query results and audit receipt."""
    bundle: EvidenceBundle
