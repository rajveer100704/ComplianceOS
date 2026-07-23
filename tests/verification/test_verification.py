"""Unit tests for Verification Engine: CitationResolver, GroundingEngine, and VerifierPipeline."""

import pytest
from document_processing.schemas import Requirement
from agents.retrieval_schemas import EvidenceBundle
from verification import (
    CitationResolver,
    GroundingEngine,
    VerifierPipeline,
    VerificationContext,
    VerificationStatus,
    PromptVersion,
)
from llm.mock import MockLLMProvider


@pytest.mark.asyncio
async def test_prompt_version_checksum():
    pv = PromptVersion.create("v1.0.0", "Verification template prompt")
    assert pv.id == "v1.0.0"
    assert len(pv.checksum) == 64  # SHA-256 length


@pytest.mark.asyncio
async def test_citation_resolver():
    resolver = CitationResolver()
    req = Requirement(
        id="REQ-101",
        regulator="FAA",
        section="Safety",
        clause="450.115",
        text="Safety analysis required",
    )
    bundle = EvidenceBundle(requirement=req, source_pages=[12, 14])

    citations = resolver.resolve_citations(req, bundle)
    assert "FAA-450.115" in citations
    assert "Page 12, 14" in citations


@pytest.mark.asyncio
async def test_grounding_engine():
    engine = GroundingEngine()
    req = Requirement(
        id="REQ-101",
        text="The applicant shall perform a flight safety analysis for public risk.",
    )
    bundle = EvidenceBundle(
        requirement=req,
        retrieved_chunks=[
            {
                "text": "The applicant shall perform a flight safety analysis for public risk."
            }
        ],
    )

    g_score, h_risk, missing, contradictions = engine.evaluate_grounding(req, bundle)
    assert g_score >= 0.8
    assert h_risk <= 0.2
    assert len(missing) == 0


@pytest.mark.asyncio
async def test_verifier_pipeline():
    mock_llm = MockLLMProvider()
    pipeline = VerifierPipeline(llm_provider=mock_llm)

    req = Requirement(
        id="REQ-101",
        regulator="FAA",
        clause="450.115",
        text="Flight safety analysis required",
    )
    bundle = EvidenceBundle(
        requirement=req,
        retrieved_chunks=[{"text": "Flight safety analysis required by operator."}],
    )

    context = VerificationContext(requirement=req, evidence_bundle=bundle)
    res = await pipeline.verify(context)

    assert res.status in (VerificationStatus.SUPPORTED, VerificationStatus.PARTIAL)
    assert res.confidence > 0.5
    assert len(res.citations) > 0
    assert res.trace is not None
