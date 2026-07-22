import pytest
from unittest.mock import patch, MagicMock
from database.models.enums import IntegrationProvider
from database.repositories.integration_repository import IntegrationRepository
from integrations.events import DomainEvent, DomainEventType
from integrations.dispatcher import EventDispatcher
from integrations.crypto import CredentialService


@pytest.mark.asyncio
class TestEventDispatcher:
    async def test_dispatch_event_to_active_integrations(self, db_session):
        repo = IntegrationRepository(db_session)
        org_id = "org_dispatch_test"

        # Create integration
        encrypted_secret = CredentialService.encrypt(
            "https://hooks.slack.com/services/test"
        )
        integration = await repo.create_integration(
            organization_id=org_id,
            provider=IntegrationProvider.SLACK,
            name="Slack Alert Channel",
            encrypted_secret=encrypted_secret,
        )

        event = DomainEvent(
            event_type=DomainEventType.CLAIM_VERDICT_RECORDED,
            organization_id=org_id,
            payload={"verdict": "UNSUPPORTED", "claim_text": "Spec failure"},
        )

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.return_value = MagicMock(status_code=200)
            results = await EventDispatcher.dispatch_event(db_session, event)

            assert len(results) == 1
            assert results[0]["status"] == "delivered"
            assert results[0]["integration_id"] == integration.id

    async def test_idempotent_duplicate_event_prevention(self, db_session):
        repo = IntegrationRepository(db_session)
        org_id = "org_idempotent_test"

        encrypted_secret = CredentialService.encrypt(
            "https://hooks.slack.com/services/test"
        )
        integration = await repo.create_integration(
            organization_id=org_id,
            provider=IntegrationProvider.SLACK,
            name="Slack Alert Channel",
            encrypted_secret=encrypted_secret,
        )

        event = DomainEvent(
            event_type=DomainEventType.CLAIM_VERDICT_RECORDED,
            organization_id=org_id,
            payload={"verdict": "UNSUPPORTED"},
        )

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.return_value = MagicMock(status_code=200)

            # First delivery
            res1 = await EventDispatcher.dispatch_event(db_session, event)
            assert res1[0]["status"] == "delivered"

            # Duplicate delivery with same event.id
            res2 = await EventDispatcher.dispatch_event(db_session, event)
            assert res2[0]["status"] == "already_delivered"
