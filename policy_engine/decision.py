"""Structured PolicyDecision and explainable EvaluationTrace output classes."""

from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class RuleTrace:
    """Detailed execution result for an individual rule within a policy."""

    rule_id: str
    rule_name: str
    status: str  # "PASSED", "FAILED", "SKIPPED"
    reason: str


@dataclass
class EvaluationTrace:
    """Explainable evaluation trace recording rule execution history."""

    traces: List[RuleTrace] = field(default_factory=list)
    evaluation_time_ms: float = 0.0


@dataclass
class PolicyDecision:
    """Structured decision output emitted by the policy engine."""

    allowed: bool
    policy_id: str
    policy_version_id: str
    matched_rules: List[str] = field(default_factory=list)
    blocked_rules: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    actions: List[Dict[str, Any]] = field(default_factory=list)
    audit_entries: List[Dict[str, Any]] = field(default_factory=list)
    trace: EvaluationTrace = field(default_factory=EvaluationTrace)
