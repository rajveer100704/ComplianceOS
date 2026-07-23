"""Unit tests for Reflection & Critique Subsystem (Sprint 2.7): ConsistencyChecker, CitationChecker, HallucinationDetector, ConfidenceEngine, and ReflectionPipeline."""

import pytest
from reflection import (
    ConsistencyChecker,
    CitationChecker,
    HallucinationDetector,
    ConfidenceEngine,
    ReflectionPipeline,
    ReflectionContext,
    ReflectionDecision,
)


@pytest.mark.asyncio
async def test_reflection_checkers():
    verifications = [
        {
            "id": "CLM-001",
            "requirement_id": "REQ-001",
            "citations": ["FAA-450.115"],
            "grounding_score": 0.9,
            "confidence": 0.95,
            "hallucination_risk": 0.1,
        }
    ]
    report = {
        "sections": [
            {
                "title": "Verification",
                "content": "Findings for REQ-001 are fully supported.",
            }
        ]
    }

    consistency = ConsistencyChecker()
    errors = consistency.check_consistency(verifications, report)
    assert len(errors) == 0

    citation_chk = CitationChecker()
    missing, count = citation_chk.check_citations(verifications)
    assert len(missing) == 0
    assert count == 1

    hallucination = HallucinationDetector()
    risk = hallucination.detect_hallucination_risk(verifications)
    assert risk == 0.1

    confidence = ConfidenceEngine()
    score = confidence.compute_overall_confidence(verifications, missing, errors, risk)
    assert score >= 0.8


@pytest.mark.asyncio
async def test_reflection_pipeline():
    pipeline = ReflectionPipeline()
    context = ReflectionContext(
        requirements=[{"id": "REQ-001"}],
        verification_results=[
            {
                "id": "CLM-001",
                "requirement_id": "REQ-001",
                "citations": ["FAA-450.115"],
                "grounding_score": 0.95,
                "confidence": 0.95,
                "hallucination_risk": 0.05,
            }
        ],
        structured_report={
            "sections": [
                {"title": "Findings", "content": "REQ-001 is fully supported."}
            ]
        },
    )

    result = await pipeline.reflect(context)
    assert result.decision == ReflectionDecision.APPROVED
    assert result.confidence >= 0.85
    assert result.trace is not None
