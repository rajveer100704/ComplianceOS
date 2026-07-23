"""ReflectionPipeline orchestrating QA critique, decision gates, and trace logging."""

import time
import logging
from typing import List
from reflection.schemas import (
    ReflectionContext,
    ReflectionResult,
    ReflectionDecision,
    ReflectionTrace,
)
from reflection.consistency import ConsistencyChecker
from reflection.citation_checker import CitationChecker
from reflection.hallucination import HallucinationDetector
from reflection.confidence import ConfidenceEngine

logger = logging.getLogger("reflection.pipeline")


class ReflectionPipeline:
    """Pipeline executing QA critique, consistency checks, citation verification, and decision gate evaluation."""

    def __init__(self):
        self.consistency_checker = ConsistencyChecker()
        self.citation_checker = CitationChecker()
        self.hallucination_detector = HallucinationDetector()
        self.confidence_engine = ConfidenceEngine()

    async def reflect(self, context: ReflectionContext) -> ReflectionResult:
        start_time = time.perf_counter()

        verifications = context.verification_results
        report = context.structured_report or {}

        # 1. Consistency check
        consistency_errors = self.consistency_checker.check_consistency(
            verifications, report
        )

        # 2. Citation coverage check
        missing_citations, total_citations = self.citation_checker.check_citations(
            verifications
        )

        # 3. Hallucination risk assessment
        h_risk = self.hallucination_detector.detect_hallucination_risk(verifications)

        # 4. Aggregated confidence score
        overall_confidence = self.confidence_engine.compute_overall_confidence(
            verifications, missing_citations, consistency_errors, h_risk
        )

        recommendations: List[str] = []
        requires_rerun = False
        target_agent = None

        # Determine ReflectionDecision gate
        if overall_confidence < 0.6:
            decision = ReflectionDecision.REQUIRES_RERUN
            requires_rerun = True
            target_agent = "evidence_retrieval"
            recommendations.append(
                "Low overall confidence score (<0.6). Re-run Evidence Retrieval with expanded search parameters."
            )
        elif consistency_errors or missing_citations or h_risk > 0.3:
            decision = ReflectionDecision.REQUIRES_REVIEW
            recommendations.append(
                "QA issues detected (missing citations or consistency warnings). Lead reviewer approval required."
            )
        else:
            decision = ReflectionDecision.APPROVED
            recommendations.append(
                "All QA critique checks passed cleanly. Report is ready for final sign-off."
            )

        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

        trace = ReflectionTrace(
            checks_performed=[
                "ConsistencyChecker",
                "CitationChecker",
                "HallucinationDetector",
                "ConfidenceEngine",
            ],
            citations_checked=total_citations,
            sections_checked=len(report.get("sections", [])),
            confidence=overall_confidence,
            latency_ms=latency_ms,
        )

        return ReflectionResult(
            overall_score=overall_confidence,
            confidence=overall_confidence,
            hallucination_risk=h_risk,
            missing_citations=missing_citations,
            consistency_errors=consistency_errors,
            recommendations=recommendations,
            decision=decision,
            requires_rerun=requires_rerun,
            rerun_target_agent=target_agent,
            trace=trace,
        )
