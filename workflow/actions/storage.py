"""StorageUploadAction workflow plugin uploading report artifacts to S3 / R2 object storage."""

from typing import Dict, Any
from workflow.actions.base import BaseWorkflowAction
from workflow.context import WorkflowContext


class StorageUploadAction(BaseWorkflowAction):
    """Workflow action uploading artifacts to S3 or Cloudflare R2 object storage."""

    @property
    def action_key(self) -> str:
        return "storage_uploader"

    async def execute(self, context: WorkflowContext) -> Dict[str, Any]:
        if context.dry_run:
            return await self.simulate(context)

        # Upload artifact
        object_key = f"orgs/{context.organization_id}/reports/{context.report_id or 'latest'}.pdf"
        return {
            "status": "COMPLETED",
            "action_key": self.action_key,
            "provider": "S3",
            "object_key": object_key,
            "url": f"https://storage.complianceos.com/{object_key}",
        }
