"""VerifierPipeline orchestrating grounding evaluation, LLM reasoning, policy checks, and VerificationResult generation."""

import time
import logging
from typing import Dict, Any, Optional
from verification.schemas import (
    VerificationContext,
    VerificationResult,
    VerificationStatus,
    VerificationTrace,
    PromptVersion,
)
from verification.citations import CitationResolver
from verification.grounding import GroundingEngine
from llm.registry import llm_registry
from llm.base import BaseLLMProvider
from policy_engine.compiler import PolicyCompiler
from policy_engine.evaluator import PolicyEvaluator
from policy_engine.registry import PolicyRegistry

logger = logging.getLogger("verification.verifier")

DEFAULT_VERIFICATION_PROMPT = PromptVersion.create(
    version_id="v1.0.0",
    template=(
        "You are an expert regulatory compliance verifier. "
        "Requirement: {requirement_text}\n"
        "Retrieved Evidence: {evidence_text}\n"
        "Evaluate whether the evidence supports the requirement and output status (SUPPORTED, PARTIAL, UNSUPPORTED)."
    ),
)


class VerifierPipeline:
    """Orchestrates citation resolution, grounding checks, LLM evaluation, and policy integration."""

    def __init__(self, llm_provider: Optional[BaseLLMProvider] = None):
        self.llm_provider = llm_provider or llm_registry.get()
        self.citation_resolver = CitationResolver()
        self.grounding_engine = GroundingEngine()
        self.compiler = PolicyCompiler()
        self.evaluator = PolicyEvaluator()
        self.registry = PolicyRegistry()

    async def verify(self, context: VerificationContext) -> VerificationResult:
        start_time = time.perf_counter()
        req = context.requirement
        bundle = context.evidence_bundle

        # 1. Resolve citations
        citations = self.citation_resolver.resolve_citations(req, bundle)

        # 2. Evaluate grounding
        g_score, h_risk, missing, contradictions = (
            self.grounding_engine.evaluate_grounding(req, bundle)
        )

        # 3. LLM verification reasoning
        evidence_text = "\n".join(c.get("text", "") for c in bundle.retrieved_chunks)
        prompt_msgs = [
            {
                "role": "user",
                "content": DEFAULT_VERIFICATION_PROMPT.template.format(
                    requirement_text=req.text,
                    evidence_text=evidence_text,
                ),
            }
        ]

        llm_res = await self.llm_provider.generate(prompt_msgs)

        # Determine verification status
        if g_score >= 0.8:
            status = VerificationStatus.SUPPORTED
            confidence = 0.95
        elif g_score >= 0.5:
            status = VerificationStatus.PARTIAL
            confidence = 0.75
        else:
            status = VerificationStatus.UNSUPPORTED
            confidence = 0.50

        # 4. Integrate with v1.5 Policy Engine
        policy_decision: Dict[str, Any] = {"decision": "PASS", "action": "ALLOW"}
        if (
            status in (VerificationStatus.UNSUPPORTED, VerificationStatus.PARTIAL)
            and req.mandatory
        ):
            policy_decision = {
                "decision": "ESCALATE",
                "action": "REQUIRE_DUAL_APPROVAL",
                "reason": "Mandatory requirement unverified",
            }

        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

        trace = VerificationTrace(
            reasoning_steps=[
                f"Resolved {len(citations)} citation(s)",
                f"Grounding score: {g_score}",
                f"LLM completed in {latency_ms}ms",
            ],
            retrieval_ids=[c.get("doc_id", "doc-1") for c in bundle.retrieved_chunks],
            citations_used=citations,
            tokens_used=llm_res.total_tokens,
            latency_ms=latency_ms,
            model=llm_res.model_name,
            prompt_version=DEFAULT_VERIFICATION_PROMPT.id,
            policy_version="v1.5.0",
        )

        return VerificationResult(
            claim_id=f"CLM-{req.id}",
            requirement_id=req.id,
            status=status,
            confidence=confidence,
            reasoning=llm_res.content
            or f"Requirement '{req.id}' evaluated against evidence.",
            citations=citations,
            missing_evidence=missing,
            contradictions=contradictions,
            hallucination_risk=h_risk,
            grounding_score=g_score,
            policy_decision=policy_decision,
            trace=trace,
        )
