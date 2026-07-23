"""Unit tests for ReportDraftingAgent (Sprint 2.6)."""

import pytest
from agents import ReportDraftingAgent
from agent_runtime.state import AgentRuntimeState
from llm.mock import MockLLMProvider


@pytest.mark.asyncio
async def test_report_drafting_agent_invocation():
    mock_llm = MockLLMProvider()
    agent = ReportDraftingAgent(llm_provider=mock_llm)

    state = AgentRuntimeState(
        run_id="run-rep-001",
        organization_id="org-1",
        requirements=[{"id": "REQ-001", "text": "Safety analysis required."}],
        claims=[
            {
                "id": "CLM-001",
                "requirement_id": "REQ-001",
                "status": "SUPPORTED",
                "grounding_score": 0.95,
            }
        ],
        risk_assessment={
            "overall_level": "GREEN",
            "overall_score": 5.0,
            "recommendations": ["Report ready."],
        },
        policy_results=[],
    )

    new_state = await agent.invoke(state)

    assert new_state.report is not None
    assert len(new_state.report_sections) >= 4
    assert new_state.current_step == "report_drafting_completed"
