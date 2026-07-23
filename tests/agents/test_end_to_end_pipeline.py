"""Golden end-to-end multi-agent pipeline integration test for Sprint 2 completion.

Validates the full sequential workflow:
RequirementAnalysisAgent -> EvidenceRetrievalAgent -> VerificationAgent -> RiskAssessmentAgent -> ReportDraftingAgent -> ReflectionAgent
"""

import pytest
from agent_runtime.state import AgentRuntimeState
from agents import (
    RequirementAnalysisAgent,
    EvidenceRetrievalAgent,
    VerificationAgent,
    RiskAssessmentAgent,
    ReportDraftingAgent,
    ReflectionAgent,
)
from llm.mock import MockLLMProvider


@pytest.mark.asyncio
async def test_golden_multi_agent_end_to_end_pipeline():
    mock_llm = MockLLMProvider()

    # Instantiate all 6 Sprint 2 agents
    req_agent = RequirementAnalysisAgent(llm_provider=mock_llm)
    ret_agent = EvidenceRetrievalAgent(llm_provider=mock_llm)
    ver_agent = VerificationAgent(llm_provider=mock_llm)
    risk_agent = RiskAssessmentAgent(llm_provider=mock_llm)
    rep_agent = ReportDraftingAgent(llm_provider=mock_llm)
    refl_agent = ReflectionAgent(llm_provider=mock_llm)

    # Initial state with regulatory document text
    sample_doc_text = """
    FAA PART 450 — LAUNCH SAFETY STANDARDS
    Section 450.115 Flight Safety Analysis
    The launch operator shall perform a comprehensive flight safety analysis for public risk control.
    Mandatory Clause 450.115(a): Public risk must not exceed 1e-4 expected casualties per launch.
    """

    state = AgentRuntimeState(
        run_id="run-golden-001",
        organization_id="org-acme-aerospace",
        metadata={
            "text_content": sample_doc_text,
            "filename": "FAA_Part450_Safety.pdf",
            "regulator": "FAA",
        },
    )

    # Step 1: Requirement Analysis
    state = await req_agent.invoke(state)
    assert len(state.requirements) > 0
    assert state.current_step == "requirement_analysis_completed"

    # Step 2: Evidence Retrieval
    state = await ret_agent.invoke(state)
    assert len(state.evidence) > 0
    assert len(state.retrieved_documents) > 0
    assert state.current_step == "evidence_retrieval_completed"

    # Step 3: Verification
    state = await ver_agent.invoke(state)
    assert len(state.claims) > 0
    assert state.claims[0]["status"] in ("SUPPORTED", "PARTIAL")
    assert len(state.claims[0]["citations"]) > 0
    assert state.current_step == "verification_completed"

    # Step 4: Risk Assessment
    state = await risk_agent.invoke(state)
    assert state.risk_assessment is not None
    assert "overall_level" in state.risk_assessment
    assert "risk_matrix" in state.metadata
    assert state.current_step == "risk_assessment_completed"

    # Step 5: Report Drafting
    state = await rep_agent.invoke(state)
    assert state.report is not None
    assert len(state.report_sections) >= 4
    assert state.current_step == "report_drafting_completed"

    # Step 6: Reflection & Critique Quality Gate
    state = await refl_agent.invoke(state)
    assert state.reflection is not None
    assert state.approval_ready is True
    assert "reflection_completed" in state.current_step

    # Final assertions on pipeline consistency
    assert state.report["title"] is not None
    assert len(state.reflection["missing_citations"]) == 0
    assert len(state.reflection["consistency_errors"]) == 0
