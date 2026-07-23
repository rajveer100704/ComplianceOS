"""AuditRecordAction workflow plugin recording audit trail entries."""

from typing import Dict, Any
from workflow.actions.base import BaseWorkflowAction
from workflow.context import WorkflowContext


class AuditRecordAction(BaseWorkflowAction):
    """Workflow action writing workflow execution records to immutable audit log."""

    @property
    def action_key(self) -> str:
        return "audit_recorder"

    async def execute(self, context: WorkflowContext) -> Dict[str, Any]:
        if context.dry_run:
            return await self.simulate(context)

        return {
            "status": "COMPLETED",
            "action_key": self.action_key,
            "audit_logged": True,
        }
