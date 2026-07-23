"""Unit tests for EvidenceRetrievalAgent and retrieval DTO schemas (Sprint 2.3)."""

import pytest
from agents import (
    EvidenceRetrievalAgent,
    RetrievalTrace,
    RetrievalContext,
)
from agent_runtime.state import AgentRuntimeState
from llm.mock import MockLLMProvider


@pytest.mark.asyncio
async def test_retrieval_schemas():
    trace = RetrievalTrace(
        dense_score=0.92,
        bm25_score=0.85,
        rerank_score=0.95,
        total_latency_ms=12.5,
    )
    assert trace.dense_score == 0.92

    context = RetrievalContext(
        query="FAA 450.115 safety criteria",
        retrieved_chunks=[{"text": "Flight safety requirements..."}],
        trace=trace,
    )
    assert len(context.retrieved_chunks) == 1
    assert context.trace.total_latency_ms == 12.5


@pytest.mark.asyncio
async def test_evidence_retrieval_agent_invocation():
    mock_llm = MockLLMProvider()
    agent = EvidenceRetrievalAgent(llm_provider=mock_llm)

    state = AgentRuntimeState(
        run_id="run-ret-001",
        organization_id="org-1",
        requirements=[
            {
                "id": "REQ-001",
                "regulator": "FAA",
                "section": "Flight Safety",
                "clause": "450.115",
                "title": "Safety Analysis",
                "text": "The applicant shall perform a flight safety analysis.",
                "mandatory": True,
            }
        ],
    )

    new_state = await agent.invoke(state)

    assert len(new_state.evidence) == 1
    bundle = new_state.evidence[0]
    assert bundle["requirement"]["id"] == "REQ-001"
    assert len(bundle["retrieved_chunks"]) > 0
    assert new_state.current_step == "evidence_retrieval_completed"
    assert len(new_state.retrieved_documents) > 0
