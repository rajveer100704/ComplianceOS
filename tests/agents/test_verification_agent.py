"""Unit tests for VerificationAgent (Sprint 2.4)."""

import pytest
from agents import VerificationAgent
from agent_runtime.state import AgentRuntimeState
from llm.mock import MockLLMProvider


@pytest.mark.asyncio
async def test_verification_agent_invocation():
    mock_llm = MockLLMProvider()
    agent = VerificationAgent(llm_provider=mock_llm)

    state = AgentRuntimeState(
        run_id="run-ver-001",
        organization_id="org-1",
        evidence=[
            {
                "requirement": {
                    "id": "REQ-001",
                    "regulator": "FAA",
                    "clause": "450.115",
                    "section": "Safety",
                    "text": "Flight safety analysis required.",
                    "mandatory": True,
                },
                "retrieved_chunks": [
                    {"text": "Flight safety analysis required by operator."}
                ],
                "linked_tables": [],
                "linked_figures": [],
                "linked_captions": [],
                "source_pages": [10],
            }
        ],
    )

    new_state = await agent.invoke(state)

    assert len(new_state.claims) == 1
    claim = new_state.claims[0]
    assert claim["requirement_id"] == "REQ-001"
    assert claim["status"] in ("SUPPORTED", "PARTIAL")
    assert len(claim["citations"]) > 0
    assert new_state.current_step == "verification_completed"
