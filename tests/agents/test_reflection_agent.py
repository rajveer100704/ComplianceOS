"""Unit tests for ReflectionAgent (Sprint 2.7)."""

import pytest
from agents import ReflectionAgent
from agent_runtime.state import AgentRuntimeState
from llm.mock import MockLLMProvider


@pytest.mark.asyncio
async def test_reflection_agent_invocation():
    mock_llm = MockLLMProvider()
    agent = ReflectionAgent(llm_provider=mock_llm)

    state = AgentRuntimeState(
        run_id="run-refl-001",
        organization_id="org-1",
        requirements=[{"id": "REQ-001"}],
        claims=[
            {
                "id": "CLM-001",
                "requirement_id": "REQ-001",
                "status": "SUPPORTED",
                "citations": ["FAA-450.115"],
                "grounding_score": 0.95,
                "confidence": 0.95,
                "hallucination_risk": 0.05,
            }
        ],
        report={
            "sections": [
                {
                    "title": "Verification",
                    "content": "Findings for REQ-001 are fully supported.",
                }
            ]
        },
    )

    new_state = await agent.invoke(state)

    assert new_state.reflection is not None
    assert new_state.approval_ready is True
    assert "reflection_completed" in new_state.current_step
