"""Supervisor Agent (Sprint 2.1) decomposed into Planner, Executor, Evaluator, and Recovery Manager."""

import logging
from typing import List, Optional
from agents.base import Agent
from agent_runtime.state import AgentRuntimeState
from llm.base import BaseLLMProvider

logger = logging.getLogger("agents.supervisor")


class PlannerSubModule:
    """Sub-module responsible for breaking down verification requests into execution plans."""

    def __init__(self, llm_provider: Optional[BaseLLMProvider] = None):
        self.llm_provider = llm_provider

    async def plan(self, state: AgentRuntimeState) -> List[str]:
        """Generates an ordered list of step names to execute."""
        # Default plan sequence
        plan_steps = [
            "requirement_analysis",
            "evidence_retrieval",
            "claim_verification",
            "risk_assessment",
            "report_drafting",
        ]
        logger.info(
            f"Planner generated {len(plan_steps)} execution steps for run {state.run_id}"
        )
        return plan_steps


class ExecutorSubModule:
    """Sub-module responsible for node step dispatching."""

    async def dispatch(
        self, step_name: str, state: AgentRuntimeState
    ) -> AgentRuntimeState:
        """Dispatches execution to the target agent node."""
        logger.debug(f"Executor dispatching step '{step_name}'")
        state.current_step = step_name
        return state


class EvaluatorSubModule:
    """Sub-module responsible for evaluating step outputs and completion criteria."""

    async def evaluate(self, state: AgentRuntimeState) -> bool:
        """Evaluates whether current state satisfies completion requirements."""
        if state.error:
            return False
        # Checked if required artifacts exist
        return bool(state.requirements or state.claims or state.report)


class RecoveryManagerSubModule:
    """Sub-module responsible for handling node failures, retries, and step fallback."""

    async def recover(
        self, step_name: str, state: AgentRuntimeState, error: str
    ) -> AgentRuntimeState:
        """Attempts recovery or marks run interrupted on unrecoverable failure."""
        logger.warning(f"RecoveryManager handling error on step '{step_name}': {error}")
        state.metadata["last_recovery_attempt"] = step_name
        state.interrupt_reason = f"Step '{step_name}' failed: {error}"
        state.is_interrupted = True
        return state


class SupervisorAgent(Agent):
    """Central supervisor coordinator managing Planner, Executor, Evaluator, and Recovery Manager."""

    name = "supervisor"
    description = "Orchestrates regulatory verification workflow through sub-module decomposition."

    def __init__(self, llm_provider: Optional[BaseLLMProvider] = None):
        super().__init__(llm_provider)
        self.planner = PlannerSubModule(self.llm_provider)
        self.executor = ExecutorSubModule()
        self.evaluator = EvaluatorSubModule()
        self.recovery_manager = RecoveryManagerSubModule()

    async def invoke(self, state: AgentRuntimeState) -> AgentRuntimeState:
        """Executes orchestration planning and evaluates workflow progress."""
        try:
            plan = await self.planner.plan(state)
            state.metadata["execution_plan"] = plan

            if not state.current_step or state.current_step == "initial":
                state = await self.executor.dispatch(plan[0], state)

            is_valid = await self.evaluator.evaluate(state)
            state.metadata["evaluator_passed"] = is_valid

        except Exception as err:
            state = await self.recovery_manager.recover(
                state.current_step, state, str(err)
            )

        return state
