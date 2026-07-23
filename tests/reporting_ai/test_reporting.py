"""Unit tests for AI Reporting Engine (Sprint 2.6): ReportPlanner, SectionGenerators, ReportValidator, and ReportDraftingPipeline."""

import pytest
from reporting_ai import (
    ReportPlanner,
    SectionGenerators,
    ReportDraftingPipeline,
    ReportContext,
    ReportFormat,
)
from llm.mock import MockLLMProvider


@pytest.mark.asyncio
async def test_report_planner():
    planner = ReportPlanner()
    plan = planner.plan_sections(ReportFormat.AUDIT)
    assert len(plan) == 7
    assert plan[0]["id"] == "exec_summary"


@pytest.mark.asyncio
async def test_section_generators_and_validator():
    generators = SectionGenerators()
    context = ReportContext(
        requirements=[{"id": "REQ-001"}],
        verification_results=[
            {
                "id": "CLM-001",
                "requirement_id": "REQ-001",
                "status": "SUPPORTED",
                "grounding_score": 0.9,
                "citations": ["FAA-450.115"],
            }
        ],
        risk_results={
            "overall_level": "GREEN",
            "overall_score": 10.0,
            "recommendations": ["Proceed to audit."],
        },
    )

    exec_sec = generators.generate_exec_summary(context)
    assert "SUPPORTED" in exec_sec.content or "1/1" in exec_sec.content

    ver_sec = generators.generate_verification_section(context)
    assert "FAA-450.115" in ver_sec.citations


@pytest.mark.asyncio
async def test_report_drafting_pipeline():
    mock_llm = MockLLMProvider()
    pipeline = ReportDraftingPipeline(llm_provider=mock_llm)

    context = ReportContext(
        requirements=[{"id": "REQ-001"}],
        verification_results=[
            {
                "id": "CLM-001",
                "requirement_id": "REQ-001",
                "status": "SUPPORTED",
                "grounding_score": 0.95,
            }
        ],
        risk_results={
            "overall_level": "GREEN",
            "overall_score": 5.0,
            "recommendations": ["No risk detected."],
        },
    )

    report = await pipeline.generate_report(context)
    assert report.title is not None
    assert len(report.sections) >= 4
    assert report.trace is not None
