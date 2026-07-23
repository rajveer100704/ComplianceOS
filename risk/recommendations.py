"""Deterministic RecommendationEngine mapping risk factors and policy escalations to actionable recommendations."""

import logging
from typing import List, Tuple
from risk.schemas import RiskFactor, RiskLevel

logger = logging.getLogger("risk.recommendations")


class RecommendationEngine:
    """Generates deterministic actionable recommendations and required approval workflows."""

    def generate_recommendations(
        self, factors: List[RiskFactor], overall_level: RiskLevel
    ) -> Tuple[List[str], List[str], List[str]]:
        """Returns tuple of (recommendations, policy_actions, approval_requirements)."""
        recommendations: List[str] = []
        policy_actions: List[str] = []
        approval_requirements: List[str] = ["Lead Reviewer Sign-off"]

        for f in factors:
            if f.recommendation and f.recommendation not in recommendations:
                recommendations.append(f.recommendation)

            if f.severity in (RiskLevel.RED, RiskLevel.CRITICAL):
                policy_actions.append(f"BLOCK_PUBLICATION: {f.description}")
                if "Dual Approval Required" not in approval_requirements:
                    approval_requirements.append("Dual Approval Required")
            elif f.severity == RiskLevel.ORANGE:
                policy_actions.append(f"ESCALATE_REVIEW: {f.description}")

        if overall_level in (RiskLevel.RED, RiskLevel.CRITICAL):
            if "Executive Compliance Sign-off" not in approval_requirements:
                approval_requirements.append("Executive Compliance Sign-off")

        if not recommendations:
            recommendations.append(
                "All requirements verified with acceptable evidence coverage. Proceed to report drafting."
            )

        return recommendations, policy_actions, approval_requirements
