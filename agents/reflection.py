"""Reflection & Critique Agent (Sprint 2.7) executing ReflectionPipeline as final quality gate."""

import logging
from typing import Optional
from agents.base import Agent
from agent_runtime.state import AgentRuntimeState
from llm.base import BaseLLMProvider
from reflection import (
    ReflectionPipeline,
    ReflectionContext,
    ReflectionResult,
    ReflectionDecision,
)

logger = logging.getLogger("agents.reflection")


class ReflectionAgent(Agent):
    """Agent performing end-to-end QA critique across verification, risk, and report artifacts."""

    name = "reflection"
    description = "Performs end-to-end quality assurance critique, verifies consistency and citations, and evaluates output approval gates."

    def __init__(self, llm_provider: Optional[BaseLLMProvider] = None):
        super().__init__(llm_provider)
        self.pipeline = ReflectionPipeline()

    async def invoke(self, state: AgentRuntimeState) -> AgentRuntimeState:
        """Executes reflection critique pipeline over full state."""
        logger.info(f"ReflectionAgent evaluating quality gate for run {state.run_id}")

        context = ReflectionContext(
            requirements=state.requirements,
            retrieved_documents=state.retrieved_documents,
            verification_results=state.claims,
            risk_results=state.risk_assessment,
            structured_report=state.report,
            policy_results=state.policy_results,
            organization_id=state.organization_id,
        )

        result: ReflectionResult = await self.pipeline.reflect(context)

        # Attach reflection artifacts to state
        state.reflection = result.model_dump()
        state.reflection_trace = result.trace.model_dump() if result.trace else {}
        state.reflection_recommendations = result.recommendations
        state.approval_ready = result.decision == ReflectionDecision.APPROVED
        state.current_step = f"reflection_completed_{result.decision.value.lower()}"

        logger.info(
            f"Reflection completed for run {state.run_id}: decision={result.decision.value}, score={result.overall_score}"
        )
        return state
