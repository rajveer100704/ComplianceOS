"""Multi-dimensional risk scoring across Compliance, Evidence, Verification, and Policy categories."""

import logging
from typing import Dict, Any, List, Tuple
from risk.schemas import RiskCategory, RiskFactor, RiskLevel

logger = logging.getLogger("risk.scoring")


class MultiDimensionalRiskScorer:
    """Computes category-specific scores (0-100) and identifies explicit risk factors."""

    def score(
        self,
        verification_results: List[Dict[str, Any]],
        policy_results: List[Dict[str, Any]],
    ) -> Tuple[Dict[str, float], float, List[RiskFactor]]:
        factors: List[RiskFactor] = []
        category_scores: Dict[str, float] = {
            RiskCategory.COMPLIANCE.value: 10.0,
            RiskCategory.EVIDENCE.value: 10.0,
            RiskCategory.VERIFICATION.value: 10.0,
            RiskCategory.POLICY.value: 10.0,
            RiskCategory.OPERATIONAL.value: 10.0,
            RiskCategory.DATA_QUALITY.value: 10.0,
        }

        unsupported_count = 0
        partial_count = 0
        factor_id = 1

        for res in verification_results:
            status = res.get("status", "SUPPORTED")
            g_score = res.get("grounding_score", 1.0)
            h_risk = res.get("hallucination_risk", 0.0)

            if status == "UNSUPPORTED":
                unsupported_count += 1
                category_scores[RiskCategory.COMPLIANCE.value] += 30.0
                category_scores[RiskCategory.VERIFICATION.value] += 25.0
                factors.append(
                    RiskFactor(
                        id=f"RF-{factor_id:03d}",
                        category=RiskCategory.VERIFICATION,
                        severity=RiskLevel.RED,
                        description=f"Requirement '{res.get('requirement_id')}' is UNSUPPORTED by evidence.",
                        source="VerificationAgent",
                        recommendation="Provide supporting engineering evidence or trigger manual lead review.",
                    )
                )
                factor_id += 1
            elif status == "PARTIAL":
                partial_count += 1
                category_scores[RiskCategory.COMPLIANCE.value] += 15.0
                category_scores[RiskCategory.VERIFICATION.value] += 10.0
                factors.append(
                    RiskFactor(
                        id=f"RF-{factor_id:03d}",
                        category=RiskCategory.VERIFICATION,
                        severity=RiskLevel.ORANGE,
                        description=f"Requirement '{res.get('requirement_id')}' is PARTIALLY supported.",
                        source="VerificationAgent",
                        recommendation="Attach missing citation pages or supplementary test data.",
                    )
                )
                factor_id += 1

            if g_score < 0.6:
                category_scores[RiskCategory.EVIDENCE.value] += 20.0
                factors.append(
                    RiskFactor(
                        id=f"RF-{factor_id:03d}",
                        category=RiskCategory.EVIDENCE,
                        severity=RiskLevel.YELLOW,
                        description=f"Low grounding score ({g_score}) for '{res.get('requirement_id')}'.",
                        source="GroundingEngine",
                        recommendation="Re-run hybrid vector retrieval with expanded section context.",
                    )
                )
                factor_id += 1

        for pol in policy_results:
            decision = pol.get("decision", {})
            if decision.get("decision") == "ESCALATE":
                category_scores[RiskCategory.POLICY.value] += 25.0
                factors.append(
                    RiskFactor(
                        id=f"RF-{factor_id:03d}",
                        category=RiskCategory.POLICY,
                        severity=RiskLevel.RED,
                        description=f"Policy Escalation triggered for '{pol.get('requirement_id')}': {decision.get('reason')}.",
                        source="PolicyEngine",
                        recommendation="Require dual approval before final report sign-off.",
                    )
                )
                factor_id += 1

        # Cap category scores at 100
        for k in category_scores:
            category_scores[k] = min(100.0, category_scores[k])

        overall_score = round(sum(category_scores.values()) / len(category_scores), 1)
        return category_scores, overall_score, factors
