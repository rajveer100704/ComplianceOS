"""RiskAnalyzerPipeline orchestrating scoring, matrix evaluation, recommendation generation, and trace logging."""

import time
import logging
from risk.schemas import (
    RiskContext,
    RiskResult,
    RiskLevel,
    RiskTrace,
)
from risk.scoring import MultiDimensionalRiskScorer
from risk.matrix import RiskMatrixEvaluator
from risk.recommendations import RecommendationEngine

logger = logging.getLogger("risk.analyzer")


class RiskAnalyzerPipeline:
    """Pipeline executing multi-dimensional risk scoring, 5x5 safety matrix evaluation, and recommendation generation."""

    def __init__(self):
        self.scorer = MultiDimensionalRiskScorer()
        self.matrix_evaluator = RiskMatrixEvaluator()
        self.recommendation_engine = RecommendationEngine()

    async def analyze(self, context: RiskContext) -> RiskResult:
        start_time = time.perf_counter()

        verifications = context.verification_results
        policy_res = context.policy_results

        # 1. Multi-dimensional scoring
        categories, overall_score, factors = self.scorer.score(
            verifications, policy_res
        )

        # 2. Derive overall risk level
        if overall_score >= 70.0:
            overall_level = RiskLevel.CRITICAL
            likelihood, impact = "Critical", "Catastrophic"
        elif overall_score >= 50.0:
            overall_level = RiskLevel.RED
            likelihood, impact = "High", "Severe"
        elif overall_score >= 35.0:
            overall_level = RiskLevel.ORANGE
            likelihood, impact = "Medium", "Major"
        elif overall_score >= 20.0:
            overall_level = RiskLevel.YELLOW
            likelihood, impact = "Low", "Moderate"
        else:
            overall_level = RiskLevel.GREEN
            likelihood, impact = "Very Low", "Minor"

        # 3. 5x5 Safety Matrix Evaluation
        matrix = self.matrix_evaluator.evaluate(likelihood, impact)

        # 4. Actionable recommendations & approvals
        recommendations, actions, approvals = (
            self.recommendation_engine.generate_recommendations(factors, overall_level)
        )

        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

        trace = RiskTrace(
            risk_factors_count=len(factors),
            latency_ms=latency_ms,
            reasoning_steps=[
                f"Scored {len(categories)} risk categories",
                f"Evaluated matrix zone: {matrix.zone.value}",
                f"Generated {len(recommendations)} recommendation(s)",
            ],
        )

        return RiskResult(
            overall_score=overall_score,
            overall_level=overall_level,
            categories=categories,
            risk_factors=factors,
            recommendations=recommendations,
            policy_actions=actions,
            approval_requirements=approvals,
            risk_matrix=matrix,
            confidence=0.95,
            trace=trace,
        )
