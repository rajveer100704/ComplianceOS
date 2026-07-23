"""Unit tests for SupervisorAgent (Sprint 2.1) and Planner, Executor, Evaluator, and Recovery Manager sub-modules."""

import pytest
from agents import (
    SupervisorAgent,
    PlannerSubModule,
    ExecutorSubModule,
    EvaluatorSubModule,
    RecoveryManagerSubModule,
)
from agent_runtime.state import AgentRuntimeState
from llm.mock import MockLLMProvider


@pytest.mark.asyncio
async def test_planner_submodule():
    planner = PlannerSubModule()
    state = AgentRuntimeState(run_id="test-plan-1", organization_id="org-1")
    plan = await planner.plan(state)

    assert len(plan) == 5
    assert "requirement_analysis" in plan
    assert "claim_verification" in plan


@pytest.mark.asyncio
async def test_executor_submodule():
    executor = ExecutorSubModule()
    state = AgentRuntimeState(run_id="test-exec-1", organization_id="org-1")
    state = await executor.dispatch("evidence_retrieval", state)

    assert state.current_step == "evidence_retrieval"


@pytest.mark.asyncio
async def test_evaluator_submodule():
    evaluator = EvaluatorSubModule()
    state = AgentRuntimeState(run_id="test-eval-1", organization_id="org-1")

    # Empty state should return False
    assert await evaluator.evaluate(state) is False

    # Populated state should return True
    state.requirements.append({"id": "REQ-1"})
    assert await evaluator.evaluate(state) is True


@pytest.mark.asyncio
async def test_recovery_manager_submodule():
    recovery = RecoveryManagerSubModule()
    state = AgentRuntimeState(run_id="test-rec-1", organization_id="org-1")
    state = await recovery.recover("claim_verification", state, "Timeout error")

    assert state.is_interrupted is True
    assert "Timeout error" in state.interrupt_reason


@pytest.mark.asyncio
async def test_supervisor_agent_invocation():
    mock_llm = MockLLMProvider()
    supervisor = SupervisorAgent(llm_provider=mock_llm)
    state = AgentRuntimeState(run_id="test-sup-1", organization_id="org-1")

    new_state = await supervisor.invoke(state)

    assert "execution_plan" in new_state.metadata
    assert new_state.current_step == "requirement_analysis"
    assert "evaluator_passed" in new_state.metadata
