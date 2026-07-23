"""LLM provider package for v2.0 AI Platform."""

from llm.base import BaseLLMProvider, LLMResponse
from llm.registry import LLMProviderRegistry, llm_registry
from llm.mock import MockLLMProvider
from llm.gemini import GeminiLLMProvider

# Register default mock & gemini providers
llm_registry.register(MockLLMProvider(), default=True)
llm_registry.register(GeminiLLMProvider())

__all__ = [
    "BaseLLMProvider",
    "LLMResponse",
    "LLMProviderRegistry",
    "llm_registry",
    "MockLLMProvider",
    "GeminiLLMProvider",
]
