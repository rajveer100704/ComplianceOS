"""Registry managing pluggable LLM provider instances and model fallbacks."""

import logging
from typing import Dict, List, Optional
from llm.base import BaseLLMProvider

logger = logging.getLogger("llm.registry")


class LLMProviderRegistry:
    """Registry maintaining active LLM providers."""

    def __init__(self):
        self._providers: Dict[str, BaseLLMProvider] = {}
        self._default_provider_name: Optional[str] = None

    def register(self, provider: BaseLLMProvider, default: bool = False) -> None:
        """Registers an LLM provider adapter."""
        self._providers[provider.name] = provider
        if default or not self._default_provider_name:
            self._default_provider_name = provider.name
        logger.info(f"LLM Provider '{provider.name}' successfully registered")

    def get(self, name: Optional[str] = None) -> Optional[BaseLLMProvider]:
        """Retrieves a provider by name, falling back to default."""
        target_name = name or self._default_provider_name
        if not target_name:
            return None
        return self._providers.get(target_name)

    def list_providers(self) -> List[str]:
        """Lists all registered LLM provider names."""
        return list(self._providers.keys())


# Singleton instance
llm_registry = LLMProviderRegistry()
