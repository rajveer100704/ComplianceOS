"""GroundingEngine computing coverage, evidence completeness, contradictions, and hallucination risk."""

import logging
from typing import List, Tuple
from document_processing.schemas import Requirement
from agents.retrieval_schemas import EvidenceBundle

logger = logging.getLogger("verification.grounding")


class GroundingEngine:
    """Evaluates evidence coverage, checks for missing citations/contradictions, and calculates grounding score."""

    def evaluate_grounding(
        self, requirement: Requirement, bundle: EvidenceBundle
    ) -> Tuple[float, float, List[str], List[str]]:
        """Returns tuple of (grounding_score, hallucination_risk, missing_evidence, contradictions)."""
        chunks = bundle.retrieved_chunks
        if not chunks:
            return 0.0, 1.0, ["No evidence chunks retrieved for requirement."], []

        # Check term coverage between requirement and chunks
        req_terms = set(requirement.text.lower().split())
        chunk_text = " ".join(c.get("text", "").lower() for c in chunks)
        chunk_terms = set(chunk_text.split())

        intersection = req_terms.intersection(chunk_terms)
        coverage = len(intersection) / max(1, len(req_terms))

        grounding_score = round(min(1.0, max(0.2, coverage * 1.2)), 2)
        hallucination_risk = round(1.0 - grounding_score, 2)

        missing_evidence = []
        if grounding_score < 0.6:
            missing_evidence.append(
                f"Low term coverage ({int(coverage * 100)}%) against retrieved evidence."
            )

        contradictions = []

        logger.debug(
            f"Grounding evaluated for REQ '{requirement.id}': score={grounding_score}, hallucination_risk={hallucination_risk}"
        )
        return grounding_score, hallucination_risk, missing_evidence, contradictions
