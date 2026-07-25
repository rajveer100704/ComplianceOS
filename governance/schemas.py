"""Canonical DTOs and models for AI Governance & Audit Engine (Sprint 6)."""

import uuid
import hashlib
from enum import Enum
from typing import Dict, Any, List
from datetime import datetime, UTC
from pydantic import BaseModel, ConfigDict, Field


class RuleOperator(str, Enum):
    GREATER_THAN_EQUAL = "GREATER_THAN_EQUAL"
    LESS_THAN_EQUAL = "LESS_THAN_EQUAL"
    EQUALS = "EQUALS"


class ViolationSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class GateStatus(str, Enum):
    PASSED = "PASSED"
    REJECTED = "REJECTED"


class AuditLedgerEntry(BaseModel):
    """Immutable audit record with SHA-256 parent block chaining."""

    model_config = ConfigDict(from_attributes=True)

    entry_id: str = Field(default_factory=lambda: f"audit-{uuid.uuid4().hex[:8]}")
    sequence_number: int = 1
    organization_id: str = "default"
    event_id: str
    event_type: str
    actor_id: str
    target_id: str
    prev_hash: str = "0" * 64
    current_hash: str = ""
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def compute_hash(self) -> str:
        payload = f"{self.sequence_number}:{self.organization_id}:{self.event_id}:{self.event_type}:{self.actor_id}:{self.target_id}:{self.prev_hash}:{self.timestamp.isoformat()}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class ComplianceRule(BaseModel):
    """Configurable quantitative compliance threshold rule."""

    model_config = ConfigDict(from_attributes=True)

    rule_id: str = Field(default_factory=lambda: f"rule-{uuid.uuid4().hex[:8]}")
    organization_id: str = "default"
    name: str
    metric_name: str  # e.g. grounding_score, hallucination_risk
    operator: RuleOperator
    threshold_value: float
    is_blocking: bool = True


class GateEvaluationResult(BaseModel):
    """Evaluation result for sign-off gate across active compliance rules."""

    model_config = ConfigDict(from_attributes=True)

    session_id: str
    status: GateStatus
    organization_id: str = "default"
    evaluated_rules_count: int = 0
    passed_rules_count: int = 0
    failed_rules_count: int = 0
    violations: List[Dict[str, Any]] = Field(default_factory=list)
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ComplianceViolation(BaseModel):
    """Recorded governance policy violation."""

    model_config = ConfigDict(from_attributes=True)

    violation_id: str = Field(default_factory=lambda: f"viol-{uuid.uuid4().hex[:8]}")
    organization_id: str = "default"
    rule_id: str
    event_id: str
    severity: ViolationSeverity = ViolationSeverity.MEDIUM
    details: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
