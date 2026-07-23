"""Canonical models and schemas for Risk Analysis Engine (Sprint 2.5)."""

from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class RiskLevel(str, Enum):
    GREEN = "GREEN"  # Low / Acceptable
    YELLOW = "YELLOW"  # Moderate / Monitor
    ORANGE = "ORANGE"  # High / Review Required
    RED = "RED"  # Severe / Escalation Mandatory
    CRITICAL = "CRITICAL"  # Catastrophic / Block Publication


class RiskCategory(str, Enum):
    COMPLIANCE = "compliance"
    EVIDENCE = "evidence"
    VERIFICATION = "verification"
    POLICY = "policy"
    OPERATIONAL = "operational"
    DATA_QUALITY = "data_quality"


class RiskFactor(BaseModel):
    """Explicit risk factor entry."""

    id: str
    category: RiskCategory
    severity: RiskLevel
    description: str
    source: str
    recommendation: Optional[str] = None


class RiskMatrix(BaseModel):
    """5x5 Likelihood x Impact safety engineering risk matrix."""

    likelihood: str = "Low"  # Very Low, Low, Medium, High, Critical
    impact: str = "Minor"  # Minor, Moderate, Major, Severe, Catastrophic
    zone: RiskLevel = RiskLevel.GREEN
    score: float = 10.0


class RiskTrace(BaseModel):
    """Trace log for risk scoring, factors, latency, and prompt/policy versions."""

    model_config = ConfigDict(from_attributes=True)

    model: str = "gemini-2.0-flash"
    prompt_version: str = "v1.0.0"
    policy_versions: List[str] = Field(default_factory=list)
    risk_factors_count: int = 0
    latency_ms: float = 0.0
    reasoning_steps: List[str] = Field(default_factory=list)


class RiskContext(BaseModel):
    """Deterministic input context for risk analysis."""

    model_config = ConfigDict(from_attributes=True)

    verification_results: List[Dict[str, Any]] = Field(default_factory=list)
    policy_results: List[Dict[str, Any]] = Field(default_factory=list)
    requirements: List[Dict[str, Any]] = Field(default_factory=list)
    organization_id: str = "default"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RiskResult(BaseModel):
    """Rich multi-dimensional risk assessment result."""

    model_config = ConfigDict(from_attributes=True)

    overall_score: float = 0.0  # 0.0 (Safe) to 100.0 (Extreme Risk)
    overall_level: RiskLevel = RiskLevel.GREEN
    categories: Dict[str, float] = Field(
        default_factory=dict
    )  # Category -> score (0-100)
    risk_factors: List[RiskFactor] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    policy_actions: List[str] = Field(default_factory=list)
    approval_requirements: List[str] = Field(default_factory=list)
    risk_matrix: RiskMatrix = Field(default_factory=RiskMatrix)
    confidence: float = 1.0
    trace: Optional[RiskTrace] = None
