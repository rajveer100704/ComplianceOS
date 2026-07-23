"""Base agent helper classes extending agent_runtime.interfaces.BaseAgent."""

from abc import ABC
from typing import Optional
from agent_runtime.interfaces import BaseAgent
from llm.registry import llm_registry
from llm.base import BaseLLMProvider


class Agent(BaseAgent, ABC):
    """Base class for domain agents with built-in LLM provider resolution."""

    name: str
    description: str

    def __init__(self, llm_provider: Optional[BaseLLMProvider] = None):
        self.llm_provider = llm_provider or llm_registry.get()
