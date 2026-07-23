import pytest
from unittest.mock import patch, MagicMock

from integrations.events import DomainEvent, DomainEventType
from integrations.adapters.slack import SlackAdapter
from integrations.adapters.teams import TeamsAdapter
from integrations.adapters.github import GitHubAdapter
from integrations.adapters.jira import JiraAdapter


@pytest.mark.asyncio
class TestAdapters:
    async def test_slack_adapter_execute(self):
        adapter = SlackAdapter()
        event = DomainEvent(
            event_type=DomainEventType.CLAIM_VERDICT_RECORDED,
            organization_id="org_123",
            payload={"verdict": "UNSUPPORTED", "claim_text": "Spec failure"},
        )
        config = {}
        secret = "https://hooks.slack.com/services/test"

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.return_value = MagicMock(status_code=200)
            res = await adapter.execute(event, config=config, secret=secret)
            assert res.success is True
            assert res.status_code == 200
            assert mock_post.called

    async def test_teams_adapter_execute(self):
        adapter = TeamsAdapter()
        event = DomainEvent(
            event_type=DomainEventType.REPORT_COMPILED,
            organization_id="org_123",
            payload={"title": "FAA Part 450 Report"},
        )
        secret = "https://outlook.office.com/webhook/test"

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.return_value = MagicMock(status_code=200)
            res = await adapter.execute(event, config={}, secret=secret)
            assert res.success is True

    async def test_github_adapter_execute(self):
        adapter = GitHubAdapter()
        event = DomainEvent(
            event_type=DomainEventType.CLAIM_VERDICT_RECORDED,
            organization_id="org_123",
            payload={"verdict": "UNSUPPORTED", "claim_text": "Non-compliant spec"},
        )
        config = {"owner": "test-org", "repo": "compliance-issues"}
        secret = "ghp_mock_token_123"

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.return_value = MagicMock(
                status_code=201, json=lambda: {"id": 999, "number": 42}
            )
            res = await adapter.execute(event, config=config, secret=secret)
            assert res.success is True
            assert res.status_code == 201

    async def test_jira_adapter_execute(self):
        adapter = JiraAdapter()
        event = DomainEvent(
            event_type=DomainEventType.CLAIM_VERDICT_RECORDED,
            organization_id="org_123",
            payload={"verdict": "UNSUPPORTED", "claim_text": "Non-compliant spec"},
        )
        config = {
            "domain": "test.atlassian.net",
            "email": "user@example.com",
            "project_key": "COMP",
        }
        secret = "jira_token_123"

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.return_value = MagicMock(
                status_code=201, json=lambda: {"key": "COMP-101"}
            )
            res = await adapter.execute(event, config=config, secret=secret)
            assert res.success is True
            assert res.status_code == 201
