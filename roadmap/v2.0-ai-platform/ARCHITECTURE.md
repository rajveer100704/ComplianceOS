# ComplianceOS v2.0 — AI Platform Architecture Specification

> **Constitution for the v2.0 AI-Native Enterprise Platform**
> Defines state boundaries, memory ownership, communication channels, checkpointing strategy, and abstract interfaces.

---

## 1. System Layering & Component Ownership

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Enterprise Applications & SPA                   │
└────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        Agent Runtime OS (Sprint 1)                     │
│  ├── StateGraph Engine     ├── Checkpointer       ├── Interrupt Manager │
│  ├── Agent & Tool Registry ├── Shared Context     ├── Budget Manager    │
│  └── Streaming Event Bus   └── Event Scheduler    └── Observability     │
└────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌────────────────────────────────────────────────────────────────────────┐
│                     Multi-Agent Subsystem (Sprint 2)                   │
│  ├── Supervisor (Planner ➔ Executor ➔ Evaluator ➔ Recovery Manager)    │
│  ├── Requirement Analysis Agent     ├── Evidence Retrieval Agent       │
│  ├── Verification Agent             ├── Risk Assessment Agent          │
│  └── Report Drafting Agent          └── Reflection & Critique Agent    │
└────────────────────────────────────────────────────────────────────────┘
                 │                   │                   │
                 ▼                   ▼                   ▼
┌──────────────────┐       ┌──────────────────┐       ┌──────────────────┐
│  Shared Memory   │       │ Knowledge Graph  │       │  AI Governance   │
│   (Sprint 3)     │       │   (Sprint 4)     │       │   (Sprint 6)     │
└──────────────────┘       └──────────────────┘       └──────────────────┘
```

---

## 2. Architectural Principles & State Boundaries

### 1. State Ownership
- **Agent State**: Encapsulated within `AgentState` Pydantic models. Owned exclusively by the `LangGraph` `StateGraph` runtime during execution.
- **Persistent Checkpoints**: Saved atomically via `BaseCheckpointStore` (PostgreSQL / SQLite fallback). Agents do not persist their own state directly.
- **Workflow State**: Long-running asynchronous execution states managed via `WorkflowContext` and versioned ORM records.

### 2. Memory Ownership
- Memory is managed by the **Shared Memory Subsystem** (`Sprint 3`), not by individual agents.
- Agents query memory via `BaseMemory` interface (`Semantic`, `Episodic`, `Organizational`, `Reviewer`, `Workflow`).

### 3. Stateless vs. Stateful Components
- **Stateless**: Agents, Tools, Prompt Templates, Evaluators, Rerankers, Vector search routines.
- **Stateful**: LangGraph StateGraph Execution Instances, Checkpointers, Memory Stores, WebSocket Connections.

### 4. Dependency Inversion
- Agents depend ONLY on abstract interfaces (`BaseTool`, `BaseMemory`, `BaseLLMProvider`).
- No direct coupling between individual agents; all cross-agent communication occurs via the `Supervisor` or shared `AgentState`.

---

## 3. Core Interface Contracts

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, AsyncGenerator
from pydantic import BaseModel


class BaseAgentState(BaseModel):
    """Strongly-typed state passed through LangGraph StateGraph nodes."""
    run_id: str
    organization_id: str
    current_node: str
    metadata: Dict[str, Any] = {}


class BaseTool(ABC):
    """Abstract interface for pluggable agent tools."""
    name: str
    description: str

    @abstractmethod
    async def run(self, **kwargs) -> Any:
        pass


class BaseAgent(ABC):
    """Abstract interface for all autonomous reasoning agents."""
    name: str

    @abstractmethod
    async def invoke(self, state: BaseAgentState) -> BaseAgentState:
        pass


class BaseMemory(ABC):
    """Abstract interface for multi-tier memory providers."""
    @abstractmethod
    async def store(self, key: str, value: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None) -> None:
        pass

    @abstractmethod
    async def retrieve(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        pass


class BaseCheckpointStore(ABC):
    """Abstract interface for state graph persistence & interrupts."""
    @abstractmethod
    async def save_checkpoint(self, thread_id: str, state: Dict[str, Any]) -> str:
        pass

    @abstractmethod
    async def load_checkpoint(self, thread_id: str) -> Optional[Dict[str, Any]]:
        pass


class BaseEventBus(ABC):
    """Abstract interface for streaming agent thoughts & execution events."""
    @abstractmethod
    async def publish(self, channel: str, event: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    async def subscribe(self, channel: str) -> AsyncGenerator[Dict[str, Any], None]:
        pass
```

---

## 4. Sprint 1 Implementation Plan — Agent Runtime

Sprint 1 builds the **Agent Runtime OS**:
1. `agent_runtime/state.py`: Strongly-typed `AgentState` schema.
2. `agent_runtime/checkpoint.py`: Async SQLite / PostgreSQL `Checkpointer`.
3. `agent_runtime/budget.py`: `BudgetManager` enforcing token budgets & model cost tracking.
4. `agent_runtime/registry.py`: `AgentRegistry` & `ToolRegistry`.
5. `agent_runtime/events.py`: Async `AgentEventBus` supporting SSE / WebSocket event streaming.
6. `agent_runtime/engine.py`: `AgentRuntimeEngine` wrapping LangGraph compilation and execution.
