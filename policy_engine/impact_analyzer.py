"""PolicyImpactAnalyzer calculating pre-activation impact metrics for policy versions."""

from dataclasses import dataclass
from typing import List, Dict, Any
from policy_engine.simulator import PolicySimulator


@dataclass
class ImpactAnalysisResult:
    """Pre-activation policy impact analysis metrics report."""

    total_evaluated: int
    would_allow: int
    would_block: int
    would_escalate: int
    estimated_false_positive_rate: float
    avg_latency_increase_ms: float
    recommendation: (
        str  # "SAFE_TO_ACTIVATE", "HIGH_BLOCK_RATE_WARNING", "REQUIRES_REVIEW"
    )


class PolicyImpactAnalyzer:
    """Analyzes expected operational impact of candidate policies prior to deployment."""

    def __init__(self):
        self.simulator = PolicySimulator()

    def analyze(
        self, expression: str, sample_claims: List[Dict[str, Any]], organization_id: str
    ) -> ImpactAnalysisResult:
        """Runs batch simulation and derives pre-activation metrics and recommendations."""
        sim_res = self.simulator.simulate_expression(
            expression, sample_claims, organization_id
        )
        total = sim_res.total_evaluated or 1

        block_rate = (sim_res.blocked_count / total) * 100.0
        escalate_rate = (sim_res.escalated_count / total) * 100.0

        # Estimate false positive rate (unsupported claims blocked that had high confidence)
        false_positives = sum(
            1
            for t in sim_res.simulation_trace
            if not t["allowed"] and t.get("confidence", 1.0) > 0.85
        )
        fp_rate = round((false_positives / total) * 100.0, 2)

        # Average latency delta calculation
        latencies = [t["evaluation_latency_ms"] for t in sim_res.simulation_trace]
        avg_latency = round(sum(latencies) / len(latencies), 2) if latencies else 0.5

        if block_rate > 50.0:
            recommendation = "HIGH_BLOCK_RATE_WARNING"
        elif fp_rate > 10.0:
            recommendation = "REQUIRES_REVIEW"
        else:
            recommendation = "SAFE_TO_ACTIVATE"

        return ImpactAnalysisResult(
            total_evaluated=sim_res.total_evaluated,
            would_allow=sim_res.allowed_count,
            would_block=sim_res.blocked_count,
            would_escalate=sim_res.escalated_count,
            estimated_false_positive_rate=fp_rate,
            avg_latency_increase_ms=avg_latency,
            recommendation=recommendation,
        )
