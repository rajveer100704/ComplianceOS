"""PolicySimulator executing dry-run batch evaluations over sample historical claims."""

from typing import List, Dict, Any
from policy_engine.compiler import PolicyCompiler
from policy_engine.evaluator import PolicyEvaluator
from policy_engine.context import PolicyContext
from policy_engine.decision import PolicyDecision
from policy.schemas import PolicySimulationResponse


class PolicySimulator:
    """Simulates draft or candidate policies against historical claim context sets."""

    def __init__(self):
        self.compiler = PolicyCompiler()
        self.evaluator = PolicyEvaluator()

    def simulate_expression(
        self, expression: str, sample_claims: List[Dict[str, Any]], organization_id: str
    ) -> PolicySimulationResponse:
        """Evaluates an uncompiled expression against a sample batch of claims."""
        ast = self.compiler.compile(expression)
        allowed_count = 0
        blocked_count = 0
        escalated_count = 0
        traces: List[Dict[str, Any]] = []

        for claim in sample_claims:
            ctx = PolicyContext(
                organization_id=organization_id,
                claim=claim,
            )
            decision: PolicyDecision = self.evaluator.evaluate(
                policy_id="sim-policy",
                policy_version_id="sim-version",
                ast=ast,
                context=ctx,
            )

            if decision.allowed:
                allowed_count += 1
            else:
                blocked_count += 1

            if claim.get("risk_score", 0) > 85:
                escalated_count += 1

            traces.append(
                {
                    "claim_id": claim.get("id", "unknown"),
                    "allowed": decision.allowed,
                    "matched_rules": decision.matched_rules,
                    "blocked_rules": decision.blocked_rules,
                    "evaluation_latency_ms": decision.trace.evaluation_time_ms,
                }
            )

        return PolicySimulationResponse(
            total_evaluated=len(sample_claims),
            allowed_count=allowed_count,
            blocked_count=blocked_count,
            escalated_count=escalated_count,
            simulation_trace=traces,
        )
