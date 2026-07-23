"""Abstract interface contracts for v2.0 Agent Runtime components."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, AsyncGenerator
from pydantic import BaseModel, ConfigDict, Field


class BaseAgentState(BaseModel):
    """Strongly-typed state container passed through agent execution graphs."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    run_id: str
    organization_id: str
    current_node: str = "initial"
    messages: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    tokens_used: int = 0
    estimated_cost_usd: float = 0.0
    is_completed: bool = False
    error: Optional[str] = None


class BaseTool(ABC):
    """Abstract base class for pluggable agent tools."""

    name: str
    description: str

    @abstractmethod
    async def run(self, **kwargs) -> Any:
        """Executes the tool asynchronously with provided keyword arguments."""
        pass


class BaseAgent(ABC):
    """Abstract base class for autonomous reasoning agents."""

    name: str
    description: str

    @abstractmethod
    async def invoke(self, state: BaseAgentState) -> BaseAgentState:
        """Executes one reasoning/action step over the state."""
        pass


class BaseMemory(ABC):
    """Abstract base class for multi-tier memory providers."""

    @abstractmethod
    async def store(
        self, key: str, value: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Persists a memory entry."""
        pass

    @abstractmethod
    async def retrieve(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Retrieves relevant memory entries."""
        pass


class BaseCheckpointStore(ABC):
    """Abstract base class for state graph persistence & interrupts."""

    @abstractmethod
    async def save_checkpoint(self, thread_id: str, state: BaseAgentState) -> str:
        """Saves state checkpoint for a thread, returning checkpoint ID."""
        pass

    @abstractmethod
    async def load_checkpoint(self, thread_id: str) -> Optional[BaseAgentState]:
        """Loads latest state checkpoint for a thread."""
        pass


class BaseEventBus(ABC):
    """Abstract base class for streaming agent thoughts & execution events."""

    @abstractmethod
    async def publish(self, channel: str, event: Dict[str, Any]) -> None:
        """Publishes an event payload to a channel."""
        pass

    @abstractmethod
    async def subscribe(self, channel: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Subscribes to an event stream channel."""
        pass
