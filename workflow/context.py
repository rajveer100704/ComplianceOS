"""WorkflowContext strongly-typed context passed through workflow action pipelines."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any


@dataclass
class WorkflowContext:
    """Context data container passed to each action step in a workflow execution pipeline."""

    organization_id: str
    user_id: Optional[str] = None
    claim_id: Optional[str] = None
    report_id: Optional[str] = None
    snapshot_id: Optional[str] = None
    dry_run: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    step_results: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
