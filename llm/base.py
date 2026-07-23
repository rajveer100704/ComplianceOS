"""Base interface contracts for LLM providers."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class LLMResponse(BaseModel):
    """Standardized response object returned by all LLM providers."""

    content: str
    model_name: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0
    finish_reason: str = "stop"
    raw_response: Dict[str, Any] = Field(default_factory=dict)


class BaseLLMProvider(ABC):
    """Abstract interface for pluggable LLM provider adapters."""

    name: str
    default_model: str

    @abstractmethod
    async def generate(
        self,
        messages: List[Dict[str, str]],
        system_instruction: Optional[str] = None,
        temperature: float = 0.2,
        max_output_tokens: Optional[int] = None,
        response_format: Optional[str] = None,
    ) -> LLMResponse:
        """Generates a text/structured completion asynchronously."""
        pass
