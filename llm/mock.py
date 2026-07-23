"""Deterministic Mock LLM provider for unit testing and offline fallback."""

from typing import Dict, List, Optional
from llm.base import BaseLLMProvider, LLMResponse


class MockLLMProvider(BaseLLMProvider):
    """Mock LLM provider returning pre-configured or canned responses."""

    name = "mock"
    default_model = "mock-model"

    def __init__(self, canned_response: str = "Mock reasoning response"):
        self.canned_response = canned_response

    async def generate(
        self,
        messages: List[Dict[str, str]],
        system_instruction: Optional[str] = None,
        temperature: float = 0.2,
        max_output_tokens: Optional[int] = None,
        response_format: Optional[str] = None,
    ) -> LLMResponse:
        prompt_len = sum(len(m.get("content", "")) for m in messages)
        completion_len = len(self.canned_response)

        prompt_tokens = max(10, prompt_len // 4)
        completion_tokens = max(5, completion_len // 4)

        return LLMResponse(
            content=self.canned_response,
            model_name=self.default_model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            estimated_cost_usd=0.0,
            finish_reason="stop",
        )
