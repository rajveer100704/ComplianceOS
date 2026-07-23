"""Unit tests for RequirementAnalysisAgent (Sprint 2.2)."""

import pytest
from agents import RequirementAnalysisAgent
from agent_runtime.state import AgentRuntimeState
from llm.mock import MockLLMProvider


@pytest.mark.asyncio
async def test_requirement_analysis_agent_invocation():
    mock_llm = MockLLMProvider()
    agent = RequirementAnalysisAgent(llm_provider=mock_llm)

    sample_doc = (
        "Section 450.115 Flight Safety Requirements\n"
        "The operator shall comply with public risk criteria specified by the FAA.\n"
        "Launch operator shall maintain emergency response containment."
    )

    state = AgentRuntimeState(
        run_id="run-req-001",
        organization_id="org-1",
        metadata={"text_content": sample_doc, "regulator": "FAA"},
    )

    new_state = await agent.invoke(state)

    assert len(new_state.requirements) == 2
    assert new_state.requirements[0]["regulator"] == "FAA"
    assert new_state.current_step == "requirement_analysis_completed"
    assert "requirement_analysis_result" in new_state.metadata
    result = new_state.metadata["requirement_analysis_result"]
    assert result["statistics"]["total_requirements"] == 2
