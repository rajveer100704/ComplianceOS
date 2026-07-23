"""HallucinationDetector calculating hallucination risk across verification and report findings."""

import logging
from typing import List, Dict, Any

logger = logging.getLogger("reflection.hallucination")


class HallucinationDetector:
    """Evaluates grounding scores and hallucination risks from verification claims."""

    def detect_hallucination_risk(
        self, verification_results: List[Dict[str, Any]]
    ) -> float:
        if not verification_results:
            return 0.0

        total_risk = sum(v.get("hallucination_risk", 0.0) for v in verification_results)
        avg_risk = round(total_risk / len(verification_results), 2)

        logger.debug(f"Evaluated average hallucination risk: {avg_risk}")
        return avg_risk
