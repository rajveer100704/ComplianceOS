"""Unit tests for Risk Analysis Engine (Sprint 2.5): RiskMatrixEvaluator, MultiDimensionalRiskScorer, RecommendationEngine, and RiskAnalyzerPipeline."""

import pytest
from risk import (
    RiskMatrixEvaluator,
    MultiDimensionalRiskScorer,
    RecommendationEngine,
    RiskAnalyzerPipeline,
    RiskContext,
    RiskLevel,
)


@pytest.mark.asyncio
async def test_risk_matrix_evaluator():
    evaluator = RiskMatrixEvaluator()
    matrix = evaluator.evaluate("High", "Severe")
    assert matrix.zone in (RiskLevel.RED, RiskLevel.CRITICAL)
    assert matrix.score >= 50.0


@pytest.mark.asyncio
async def test_risk_scorer_and_recommendations():
    scorer = MultiDimensionalRiskScorer()
    verifications = [
        {
            "requirement_id": "REQ-001",
            "status": "UNSUPPORTED",
            "grounding_score": 0.4,
            "hallucination_risk": 0.6,
        }
    ]
    policies = [
        {
            "requirement_id": "REQ-001",
            "decision": {"decision": "ESCALATE", "reason": "Mandatory clause failure"},
        }
    ]

    categories, overall_score, factors = scorer.score(verifications, policies)
    assert overall_score > 20.0
    assert len(factors) >= 2

    engine = RecommendationEngine()
    recs, actions, approvals = engine.generate_recommendations(factors, RiskLevel.RED)
    assert len(recs) > 0
    assert "Dual Approval Required" in approvals


@pytest.mark.asyncio
async def test_risk_analyzer_pipeline():
    pipeline = RiskAnalyzerPipeline()
    context = RiskContext(
        verification_results=[
            {"requirement_id": "REQ-101", "status": "SUPPORTED", "grounding_score": 0.9}
        ],
        policy_results=[],
    )
    result = await pipeline.analyze(context)
    assert result.overall_level == RiskLevel.GREEN
    assert result.confidence > 0.9
    assert result.trace is not None
