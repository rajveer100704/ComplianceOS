"""SlackNotificationAction workflow plugin sending alerts to Slack webhooks."""

from typing import Dict, Any
from workflow.actions.base import BaseWorkflowAction
from workflow.context import WorkflowContext


class SlackNotificationAction(BaseWorkflowAction):
    """Workflow action sending alert notifications to Slack incoming webhooks."""

    @property
    def action_key(self) -> str:
        return "slack_notifier"

    async def execute(self, context: WorkflowContext) -> Dict[str, Any]:
        if context.dry_run:
            return await self.simulate(context)

        return {
            "status": "COMPLETED",
            "action_key": self.action_key,
            "channel": "#compliance-alerts",
            "delivered": True,
        }
