from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass(frozen=True)
class RetrievalQuery:
    """Standardized input contract for query pipeline execution."""

    query: str
    limit: int = 5
    filters: Dict[str, Any] = field(default_factory=dict)
