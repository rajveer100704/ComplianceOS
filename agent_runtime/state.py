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
    """Extended agent state carrying execution step history and runtime controls."""

    steps: List[ExecutionStep] = Field(default_factory=list)
    budget_limit_usd: float = 5.0
    max_steps: int = 50
    current_step_count: int = 0
    checkpoint_id: Optional[str] = None
    is_interrupted: bool = False
    interrupt_reason: Optional[str] = None
