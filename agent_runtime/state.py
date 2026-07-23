"""State models for Agent Runtime execution graphs."""

from typing import Dict, Any, List, Optional
from datetime import datetime, UTC
from pydantic import BaseModel, ConfigDict, Field
from agent_runtime.interfaces import BaseAgentState


class ExecutionStep(BaseModel):
    """Record of an individual step execution in the runtime."""

    model_config = ConfigDict(from_attributes=True)

    step_id: str
    node_name: str
    agent_name: Optional[str] = None
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    finished_at: Optional[datetime] = None
    latency_ms: float = 0.0
    status: str = "PENDING"  # PENDING, RUNNING, COMPLETED, FAILED, INTERRUPTED
    input_state: Dict[str, Any] = Field(default_factory=dict)
    output_state: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None


class AgentRuntimeState(BaseAgentState):
    """Frozen shared agent state carrying execution step history, multi-agent artifacts, and runtime controls."""

    user_id: Optional[str] = None
    workflow_id: Optional[str] = None
    current_step: str = "initial"

    # Multi-agent artifacts (Sprint 2 & beyond)
    retrieved_documents: List[Dict[str, Any]] = Field(default_factory=list)
    requirements: List[Dict[str, Any]] = Field(default_factory=list)
    claims: List[Dict[str, Any]] = Field(default_factory=list)
    evidence: List[Dict[str, Any]] = Field(default_factory=list)
    policy_results: List[Dict[str, Any]] = Field(default_factory=list)
    risk_assessment: Dict[str, Any] = Field(default_factory=dict)
    report: Dict[str, Any] = Field(default_factory=dict)
    report_sections: List[Dict[str, Any]] = Field(default_factory=list)
    report_trace: Dict[str, Any] = Field(default_factory=dict)
    reflection: Dict[str, Any] = Field(default_factory=dict)
    reflection_trace: Dict[str, Any] = Field(default_factory=dict)
    reflection_recommendations: List[str] = Field(default_factory=list)
    approval_ready: bool = False

    # Runtime tracking & tools
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)
    budget: Dict[str, Any] = Field(default_factory=dict)
    checkpoints: List[str] = Field(default_factory=list)
    memory_refs: Dict[str, Any] = Field(default_factory=dict)

    steps: List[ExecutionStep] = Field(default_factory=list)
    budget_limit_usd: float = 5.0
    max_steps: int = 50
    current_step_count: int = 0
    checkpoint_id: Optional[str] = None
    is_interrupted: bool = False
    interrupt_reason: Optional[str] = None
