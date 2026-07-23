"""Unit tests for Agent Runtime OS (Sprint 1): Engine, Budget, Registry, Checkpointing, and Event Bus."""

import pytest
from agent_runtime import (
    AgentRuntimeState,
    AgentRuntimeEngine,
    TokenBudgetManager,
    BudgetExceededError,
    AgentRegistry,
    ToolRegistry,
    BaseAgent,
    BaseTool,
    BaseAgentState,
    InMemoryCheckpointStore,
    AgentEventBus,
)


class DummyTool(BaseTool):
    name = "dummy_tool"
    description = "Dummy tool for testing"

    async def run(self, input_text: str = "") -> str:
        return f"Tool result for: {input_text}"


class DummyAgent(BaseAgent):
    name = "dummy_agent"
    description = "Dummy agent for testing"

    async def invoke(self, state: BaseAgentState) -> BaseAgentState:
        state.messages.append(
            {"role": "assistant", "content": "Hello from dummy agent"}
        )
        return state


@pytest.mark.asyncio
async def test_budget_manager():
    mgr = TokenBudgetManager(max_budget_usd=0.01, max_tokens=1000)
    # Record usage below budget
    mgr.record_usage(prompt_tokens=100, completion_tokens=100)
    assert mgr.tokens_used == 200
    assert mgr.accumulated_cost_usd > 0

    # Over token limit should raise error
    with pytest.raises(BudgetExceededError):
        mgr.record_usage(prompt_tokens=500, completion_tokens=500)


@pytest.mark.asyncio
async def test_registry():
    agent_reg = AgentRegistry()
    tool_reg = ToolRegistry()

    agent = DummyAgent()
    tool = DummyTool()

    agent_reg.register(agent)
    tool_reg.register(tool)

    assert agent_reg.get("dummy_agent") is agent
    assert tool_reg.get("dummy_tool") is tool
    assert "dummy_agent" in agent_reg.list_agents()
    assert "dummy_tool" in tool_reg.list_tools()


@pytest.mark.asyncio
async def test_checkpoint_store():
    store = InMemoryCheckpointStore()
    state = AgentRuntimeState(run_id="run-101", organization_id="org-1")

    chk_id = await store.save_checkpoint("run-101", state)
    assert chk_id is not None

    loaded = await store.load_checkpoint("run-101")
    assert loaded is not None
    assert loaded.run_id == "run-101"


@pytest.mark.asyncio
async def test_agent_runtime_engine_execution():
    engine = AgentRuntimeEngine()
    state = AgentRuntimeState(
        run_id="run-202", organization_id="org-1", budget_limit_usd=1.0
    )

    async def dummy_node(st: AgentRuntimeState) -> AgentRuntimeState:
        st.metadata["processed"] = True
        return st

    # Execute step 1
    new_state = await engine.execute_step(
        state=state,
        node_name="dummy_node",
        step_func=dummy_node,
        agent_name="dummy_agent",
    )

    assert new_state.current_node == "dummy_node"
    assert new_state.metadata.get("processed") is True
    assert len(new_state.steps) == 1
    assert new_state.steps[0].status == "COMPLETED"
    assert new_state.checkpoint_id is not None


@pytest.mark.asyncio
async def test_agent_event_bus():
    bus = AgentEventBus()
    events_received = []

    async def subscriber():
        async for event in bus.subscribe("run:test-123"):
            events_received.append(event)
            if len(events_received) == 1:
                break

    import asyncio

    sub_task = asyncio.create_task(subscriber())
    await asyncio.sleep(0.01)

    await bus.publish("run:test-123", {"event_type": "test_event", "payload": "data"})
    await asyncio.wait_for(sub_task, timeout=2.0)

    assert len(events_received) == 1
    assert events_received[0]["event_type"] == "test_event"


@pytest.mark.asyncio
async def test_execution_coordinator():
    from agent_runtime import ExecutionCoordinator

    coord = ExecutionCoordinator()
    state = AgentRuntimeState(run_id="run-303", organization_id="org-1")

    async def step1(st: AgentRuntimeState) -> AgentRuntimeState:
        st.requirements.append({"id": "REQ-1", "title": "Safety Standard"})
        return st

    async def step2(st: AgentRuntimeState) -> AgentRuntimeState:
        st.claims.append({"id": "CLM-1", "status": "SUPPORTED"})
        return st

    nodes = [
        {"node_name": "node_1", "agent_name": "req_agent", "func": step1},
        {"node_name": "node_2", "agent_name": "verify_agent", "func": step2},
    ]

    final_state = await coord.run_pipeline(state, nodes)
    assert len(final_state.steps) == 2
    assert len(final_state.requirements) == 1
    assert len(final_state.claims) == 1
    assert final_state.current_node == "node_2"
