"""Unit tests for LLM provider abstraction layer (BaseLLMProvider, LLMProviderRegistry, MockLLMProvider, GeminiLLMProvider)."""

import pytest
from llm import (
    LLMResponse,
    LLMProviderRegistry,
    MockLLMProvider,
    GeminiLLMProvider,
)


@pytest.mark.asyncio
async def test_mock_llm_provider():
    provider = MockLLMProvider(canned_response="Test response content")
    messages = [{"role": "user", "content": "Explain safety standards"}]

    res = await provider.generate(messages)
    assert isinstance(res, LLMResponse)
    assert res.content == "Test response content"
    assert res.model_name == "mock-model"
    assert res.total_tokens > 0


@pytest.mark.asyncio
async def test_llm_registry():
    registry = LLMProviderRegistry()
    mock_prov = MockLLMProvider()

    registry.register(mock_prov, default=True)
    assert registry.get() is mock_prov
    assert registry.get("mock") is mock_prov
    assert "mock" in registry.list_providers()


@pytest.mark.asyncio
async def test_gemini_provider_fallback_without_api_key():
    # When api_key is None, GeminiLLMProvider should gracefully fallback to mock response
    provider = GeminiLLMProvider(api_key=None)
    res = await provider.generate([{"role": "user", "content": "Hello"}])
    assert isinstance(res, LLMResponse)
    assert "Fallback" in res.content
