import logging
from typing import Dict, Optional, List
from database.models.enums import IntegrationProvider
from integrations.adapters.base import BaseIntegrationAdapter

logger = logging.getLogger("adapter_registry")


class AdapterRegistry:
    """Thread-safe registry mapping IntegrationProvider types dynamically to adapter instances."""

    _adapters: Dict[IntegrationProvider, BaseIntegrationAdapter] = {}

    @classmethod
    def register(cls, adapter: BaseIntegrationAdapter) -> None:
        """Registers an integration adapter instance."""
        if not hasattr(adapter, "provider") or not adapter.provider:
            raise ValueError(
                f"Adapter {adapter} must specify a valid IntegrationProvider"
            )
        cls._adapters[adapter.provider] = adapter
        logger.info(
            f"Registered integration adapter for provider: '{adapter.provider.value}'"
        )

    @classmethod
    def get(cls, provider: IntegrationProvider) -> Optional[BaseIntegrationAdapter]:
        """Retrieves registered adapter for a given provider enum or string."""
        if isinstance(provider, str):
            try:
                provider = IntegrationProvider(provider)
            except ValueError:
                return None
        return cls._adapters.get(provider)

    @classmethod
    def list_providers(cls) -> List[IntegrationProvider]:
        """Returns list of currently registered integration providers."""
        return list(cls._adapters.keys())

    @classmethod
    def clear(cls) -> None:
        """Clears all registered adapters (useful in tests)."""
        cls._adapters.clear()
