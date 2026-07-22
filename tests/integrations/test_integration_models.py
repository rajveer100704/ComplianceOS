import pytest
from database.models.enums import (
    IntegrationProvider,
    IntegrationHealthStatus,
    DeliveryStatus,
)
from database.models.integration import (
    IntegrationModel,
    IntegrationRuntimeStateModel,
    IntegrationDeliveryLogModel,
)


class TestIntegrationModels:
    def test_integration_provider_enums(self):
        assert IntegrationProvider.SLACK.value == "slack"
        assert IntegrationProvider.TEAMS.value == "teams"
        assert IntegrationProvider.JIRA.value == "jira"
        assert IntegrationProvider.GITHUB.value == "github"

    def test_integration_health_status_enums(self):
        assert IntegrationHealthStatus.HEALTHY.value == "healthy"
        assert IntegrationHealthStatus.DEGRADED.value == "degraded"
        assert IntegrationHealthStatus.DISCONNECTED.value == "disconnected"
        assert IntegrationHealthStatus.EXPIRED.value == "expired"

    def test_delivery_status_enums(self):
        assert DeliveryStatus.PENDING.value == "pending"
        assert DeliveryStatus.DELIVERED.value == "delivered"
        assert DeliveryStatus.FAILED.value == "failed"
        assert DeliveryStatus.RETRYING.value == "retrying"

    def test_integration_model_instantiation(self):
        integration = IntegrationModel(
            organization_id="org_123",
            provider=IntegrationProvider.SLACK,
            name="Primary Slack Webhook",
            credential_version=1,
            is_active=True,
        )
        assert integration.organization_id == "org_123"
        assert integration.provider == IntegrationProvider.SLACK
        assert integration.name == "Primary Slack Webhook"
        assert integration.credential_version == 1
        assert integration.is_active is True

    def test_integration_runtime_state_instantiation(self):
        state = IntegrationRuntimeStateModel(
            integration_id="int_123",
            health_status=IntegrationHealthStatus.HEALTHY,
            consecutive_failures=0,
        )
        assert state.integration_id == "int_123"
        assert state.health_status == IntegrationHealthStatus.HEALTHY
        assert state.consecutive_failures == 0
