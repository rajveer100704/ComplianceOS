from dataclasses import dataclass, field
from typing import Dict, Any

@dataclass(frozen=True)
class RetrievalSession:
    """Represents a unique retrieval operation execution scope."""
    session_id: str
    request_id: int
    run_id: int
    query_id: str
    config: Dict[str, Any] = field(default_factory=dict)
