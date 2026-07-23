"""Risk Assessment Agent (Sprint 2.5) executing RiskAnalyzerPipeline over verification results and policy decisions."""

import logging
from typing import Optional
from agents.base import Agent
from agent_runtime.state import AgentRuntimeState
from llm.base import BaseLLMProvider
from risk import (
    RiskAnalyzerPipeline,
    RiskContext,
    RiskResult,
)

logger = logging.getLogger("agents.risk_assessment")


class RiskAssessmentAgent(Agent):
    """Agent evaluating multi-dimensional compliance risk, 5x5 safety matrices, risk factors, and required approval actions."""

    name = "risk_assessment"
    description = "Evaluates multi-dimensional risk scores, generates safety matrices, identifies risk factors, and determines approval requirements."

    def __init__(self, llm_provider: Optional[BaseLLMProvider] = None):
        super().__init__(llm_provider)
        self.pipeline = RiskAnalyzerPipeline()

    async def invoke(self, state: AgentRuntimeState) -> AgentRuntimeState:
        """Executes multi-dimensional risk analysis over state verification and policy results."""
        verifications = state.claims
        policy_res = state.policy_results

        logger.info(f"RiskAssessmentAgent evaluating risk for run {state.run_id}")

        context = RiskContext(
            verification_results=verifications,
            policy_results=policy_res,
            requirements=state.requirements,
            organization_id=state.organization_id,
        )

        result: RiskResult = await self.pipeline.analyze(context)

        # Attach rich risk artifacts to state
        state.risk_assessment = result.model_dump()
        state.metadata["risk_factors"] = [f.model_dump() for f in result.risk_factors]
        state.metadata["recommendations"] = result.recommendations
        state.metadata["risk_matrix"] = result.risk_matrix.model_dump()
        state.current_step = "risk_assessment_completed"

        logger.info(
            f"Risk analysis completed for run {state.run_id}: score={result.overall_score}, level={result.overall_level.value}"
        )
        return state
