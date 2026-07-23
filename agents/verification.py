"""Verification Agent (Sprint 2.4) executing VerifierPipeline over EvidenceBundles."""

import logging
from typing import Optional, Dict, Any, List
from agents.base import Agent
from agent_runtime.state import AgentRuntimeState
from llm.base import BaseLLMProvider
from agents.retrieval_schemas import EvidenceBundle
from verification import (
    VerifierPipeline,
    VerificationContext,
    VerificationResult,
)

logger = logging.getLogger("agents.verification")


class VerificationAgent(Agent):
    """Agent evaluating requirement evidence, computing grounding score, generating citations, and executing policy checks."""

    name = "verification"
    description = "Evaluates requirement grounding against evidence bundles, generates verifiable citations, and computes policy decisions."

    def __init__(self, llm_provider: Optional[BaseLLMProvider] = None):
        super().__init__(llm_provider)
        self.pipeline = VerifierPipeline(llm_provider=self.llm_provider)

    async def invoke(self, state: AgentRuntimeState) -> AgentRuntimeState:
        """Executes verification pipeline across all EvidenceBundles in state."""
        raw_bundles = state.evidence
        if not raw_bundles:
            logger.warning(f"No evidence bundles found in state for run {state.run_id}")
            state.current_step = "verification_completed"
            return state

        logger.info(
            f"VerificationAgent evaluating {len(raw_bundles)} evidence bundle(s)"
        )

        claims: List[Dict[str, Any]] = []
        policy_results: List[Dict[str, Any]] = []

        for raw_b in raw_bundles:
            bundle = (
                EvidenceBundle.model_validate(raw_b)
                if isinstance(raw_b, dict)
                else raw_b
            )

            context = VerificationContext(
                requirement=bundle.requirement,
                evidence_bundle=bundle,
                organization_id=state.organization_id,
            )

            result: VerificationResult = await self.pipeline.verify(context)

            claim_record = {
                "id": result.claim_id,
                "requirement_id": result.requirement_id,
                "status": result.status.value,
                "confidence": result.confidence,
                "citations": result.citations,
                "reasoning": result.reasoning,
                "grounding_score": result.grounding_score,
                "hallucination_risk": result.hallucination_risk,
                "missing_evidence": result.missing_evidence,
            }
            claims.append(claim_record)

            if result.policy_decision:
                policy_results.append(
                    {
                        "claim_id": result.claim_id,
                        "requirement_id": result.requirement_id,
                        "decision": result.policy_decision,
                    }
                )

        state.claims = claims
        state.policy_results = policy_results
        state.current_step = "verification_completed"

        logger.info(f"Verified {len(claims)} claim(s) for run {state.run_id}")
        return state
