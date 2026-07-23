"""Unit tests for RiskAssessmentAgent (Sprint 2.5)."""

import pytest
from agents import RiskAssessmentAgent
from agent_runtime.state import AgentRuntimeState
from llm.mock import MockLLMProvider


@pytest.mark.asyncio
async def test_risk_assessment_agent_invocation():
    mock_llm = MockLLMProvider()
    agent = RiskAssessmentAgent(llm_provider=mock_llm)

    state = AgentRuntimeState(
        run_id="run-risk-001",
        organization_id="org-1",
        claims=[
            {
                "id": "CLM-001",
                "requirement_id": "REQ-001",
                "status": "SUPPORTED",
                "grounding_score": 0.85,
                "hallucination_risk": 0.15,
            }
        ],
        policy_results=[],
    )

    new_state = await agent.invoke(state)

    assert new_state.risk_assessment is not None
    assert new_state.risk_assessment["overall_level"] in ("GREEN", "YELLOW")
    assert "risk_matrix" in new_state.metadata
    assert new_state.current_step == "risk_assessment_completed"
