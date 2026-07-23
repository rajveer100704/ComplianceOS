from database.models.enums import IntegrationProvider
from integrations.events import DomainEvent, DomainEventType
from integrations.adapters.base import (
    BaseIntegrationAdapter,
    ProviderCapabilities,
    IntegrationResult,
)
from integrations.registry import AdapterRegistry


class DummySlackAdapter(BaseIntegrationAdapter):
    provider = IntegrationProvider.SLACK
    capabilities = ProviderCapabilities(
        supports_notifications=True,
        supported_events={DomainEventType.CLAIM_VERDICT_RECORDED},
    )

    async def execute(self, event: DomainEvent, config: dict, secret: str = None):
        return IntegrationResult(success=True, status_code=200)

    async def test_connection(self, config: dict, secret: str = None):
        return IntegrationResult(success=True, status_code=200)


class TestAdapterRegistry:
    def setup_method(self):
        AdapterRegistry.clear()

    def test_register_and_get_adapter(self):
        adapter = DummySlackAdapter()
        AdapterRegistry.register(adapter)

        retrieved = AdapterRegistry.get(IntegrationProvider.SLACK)
        assert retrieved is adapter
        assert retrieved.capabilities.supports_notifications is True

    def test_get_by_string_provider(self):
        adapter = DummySlackAdapter()
        AdapterRegistry.register(adapter)

        retrieved = AdapterRegistry.get("slack")
        assert retrieved is adapter

    def test_get_unregistered_provider_returns_none(self):
        assert AdapterRegistry.get(IntegrationProvider.GITHUB) is None

    def test_list_providers(self):
        adapter = DummySlackAdapter()
        AdapterRegistry.register(adapter)

        providers = AdapterRegistry.list_providers()
        assert IntegrationProvider.SLACK in providers
