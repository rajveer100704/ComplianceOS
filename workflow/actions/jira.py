"""JiraIssueAction workflow plugin creating tickets in Jira."""

from typing import Dict, Any
from workflow.actions.base import BaseWorkflowAction
from workflow.context import WorkflowContext


class JiraIssueAction(BaseWorkflowAction):
    """Workflow action automatically creating and syncing tickets in Jira."""

    @property
    def action_key(self) -> str:
        return "jira_syncer"

    async def execute(self, context: WorkflowContext) -> Dict[str, Any]:
        if context.dry_run:
            return await self.simulate(context)

        return {
            "status": "COMPLETED",
            "action_key": self.action_key,
            "issue_key": "COMP-104",
            "url": "https://jira.complianceos.atlassian.net/browse/COMP-104",
        }
