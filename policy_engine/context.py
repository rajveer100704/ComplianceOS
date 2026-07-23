"""PolicyContext strongly-typed data holder passed to the policy engine for evaluation."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List


@dataclass
class PolicyContext:
    """Context container holding environment variables, tenant info, and claim metadata for rule evaluation."""

    organization_id: str
    user_id: Optional[str] = None
    claim: Optional[Dict[str, Any]] = None
    report: Optional[Dict[str, Any]] = None
    snapshot: Optional[Dict[str, Any]] = None
    permissions: List[str] = field(default_factory=list)
    request_headers: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Flatten context into a dictionary for evaluation access."""
        return {
            "organization_id": self.organization_id,
            "user_id": self.user_id,
            "claim": self.claim or {},
            "report": self.report or {},
            "snapshot": self.snapshot or {},
            "permissions": self.permissions,
            "metadata": self.metadata,
            "risk_score": (self.claim or {}).get("risk_score", 0.0),
            "risk_level": (self.claim or {}).get("risk_level", "low"),
            "confidence": (self.claim or {}).get("confidence", 1.0),
            "status": (self.claim or {}).get("status", "UNSUPPORTED"),
            "pinned_evidence_count": len((self.claim or {}).get("evidence", [])),
        }
