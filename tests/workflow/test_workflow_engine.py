"""Unit tests for Workflow Action Registry, Actions, DAG Executor, and Dry-Run mode."""

import pytest
from workflow.context import WorkflowContext
from workflow.registry import action_registry
from workflow.actions.pdf import PDFReportAction
from workflow.actions.storage import StorageUploadAction
from workflow.actions.slack import SlackNotificationAction
from workflow.actions.jira import JiraIssueAction
from workflow.actions.audit import AuditRecordAction
from workflow.executor import WorkflowExecutor
from workflow.retry import calculate_delay_seconds, RetryPolicy
from workflow.scheduler.triggers import CronTrigger, EventTrigger, TriggerType


@pytest.fixture(autouse=True)
def setup_actions():
    action_registry.clear()
    action_registry.register(PDFReportAction())
    action_registry.register(StorageUploadAction())
    action_registry.register(SlackNotificationAction())
    action_registry.register(JiraIssueAction())
    action_registry.register(AuditRecordAction())


def test_action_registry_registration():
    actions = action_registry.list_actions()
    assert "pdf_exporter" in actions
    assert "storage_uploader" in actions
    assert "slack_notifier" in actions
    assert "jira_syncer" in actions
    assert "audit_recorder" in actions


@pytest.mark.asyncio
async def test_workflow_executor_live_run():
    executor = WorkflowExecutor()
    ctx = WorkflowContext(organization_id="org-test", report_id="rep-101", dry_run=False)

    steps = ["pdf_exporter", "storage_uploader", "slack_notifier"]
    res = await executor.execute_dag("wf-1", steps, ctx)

    assert res.success is True
    assert res.dry_run is False
    assert len(res.step_results) == 3
    assert res.step_results[0]["status"] == "COMPLETED"


@pytest.mark.asyncio
async def test_workflow_executor_dry_run():
    executor = WorkflowExecutor()
    ctx = WorkflowContext(organization_id="org-test", report_id="rep-101", dry_run=True)

    steps = ["pdf_exporter", "storage_uploader", "slack_notifier", "jira_syncer"]
    res = await executor.execute_dag("wf-2", steps, ctx)

    assert res.success is True
    assert res.dry_run is True
    assert len(res.step_results) == 4
    assert res.step_results[0]["output"]["status"] == "SIMULATED"


def test_retry_policy_delay():
    delay_none = calculate_delay_seconds(RetryPolicy.NONE, 1)
    assert delay_none == 0.0

    delay_linear = calculate_delay_seconds(RetryPolicy.LINEAR, 2, base_delay=2.0)
    assert delay_linear == 4.0

    delay_exp = calculate_delay_seconds(RetryPolicy.EXPONENTIAL, 3, base_delay=1.0)
    assert delay_exp == 4.0


def test_triggers():
    cron = CronTrigger("0 * * * *")
    assert cron.trigger_type == TriggerType.CRON
    assert cron.cron_expression == "0 * * * *"

    evt = EventTrigger("claim.approved")
    assert evt.trigger_type == TriggerType.EVENT
    assert evt.event_name == "claim.approved"
