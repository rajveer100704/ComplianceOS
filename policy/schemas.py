"""Pydantic DTO schemas for Policy Storage, Versioning, Packs, and Simulation."""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from policy.models import PolicyVersionStatus, PolicyRuleType


class PolicyRuleCreate(BaseModel):
    rule_type: PolicyRuleType
    action_key: Optional[str] = None
    action_config_json: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class PolicyRuleResponse(PolicyRuleCreate):
    model_config = ConfigDict(from_attributes=True)

    id: str


class PolicyVersionCreate(BaseModel):
    expression: str = Field(..., description="Human readable condition expression")
    rules: List[PolicyRuleCreate] = Field(default_factory=list)


class PolicyVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    policy_id: str
    version: int
    expression: str
    compiled_expression_json: Dict[str, Any]
    checksum: str
    status: PolicyVersionStatus
    created_by_user_id: Optional[str] = None
    created_at: datetime
    rules: List[PolicyRuleResponse] = Field(default_factory=list)


class PolicyCreate(BaseModel):
    name: str = Field(..., max_length=128)
    description: Optional[str] = None
    trigger_event: str
    priority: int = 100
    expression: str
    rules: List[PolicyRuleCreate] = Field(default_factory=list)


class PolicyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    pack_id: Optional[str] = None
    name: str
    description: Optional[str] = None
    trigger_event: str
    current_version_id: Optional[str] = None
    is_active: bool
    priority: int
    created_at: datetime


class SystemPolicyPackResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    framework: str
    description: Optional[str] = None
    version: str
    is_system_pack: bool
    created_at: datetime


class PolicySimulationRequest(BaseModel):
    expression: str
    sample_claim_ids: Optional[List[str]] = None


class PolicySimulationResponse(BaseModel):
    total_evaluated: int
    allowed_count: int
    blocked_count: int
    escalated_count: int
    simulation_trace: List[Dict[str, Any]]
