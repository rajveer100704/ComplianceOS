"""ConfidenceEngine aggregating grounding scores, citation coverage, verification confidence, and risk levels."""

import logging
from typing import List, Dict, Any

logger = logging.getLogger("reflection.confidence")


class ConfidenceEngine:
    """Aggregates multi-dimensional metrics into a single explainable overall confidence score (0.0 to 1.0)."""

    def compute_overall_confidence(
        self,
        verification_results: List[Dict[str, Any]],
        missing_citations: List[str],
        consistency_errors: List[str],
        hallucination_risk: float,
    ) -> float:
        if not verification_results:
            return 1.0

        avg_grounding = sum(
            v.get("grounding_score", 1.0) for v in verification_results
        ) / len(verification_results)
        avg_confidence = sum(
            v.get("confidence", 1.0) for v in verification_results
        ) / len(verification_results)

        citation_penalty = 0.15 if missing_citations else 0.0
        consistency_penalty = 0.15 if consistency_errors else 0.0

        overall = (
            (avg_grounding * 0.4)
            + (avg_confidence * 0.4)
            + ((1.0 - hallucination_risk) * 0.2)
        )
        final_confidence = round(
            max(0.0, min(1.0, overall - citation_penalty - consistency_penalty)), 2
        )

        logger.debug(f"Computed aggregated confidence score: {final_confidence}")
        return final_confidence
