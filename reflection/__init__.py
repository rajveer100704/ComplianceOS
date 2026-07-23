"""Reflection & Critique Subsystem package for v2.0 AI Platform."""

from reflection.schemas import (
    ReflectionDecision,
    ReflectionTrace,
    ReflectionContext,
    ReflectionResult,
)
from reflection.consistency import ConsistencyChecker
from reflection.citation_checker import CitationChecker
from reflection.hallucination import HallucinationDetector
from reflection.confidence import ConfidenceEngine
from reflection.pipeline import ReflectionPipeline

__all__ = [
    "ReflectionDecision",
    "ReflectionTrace",
    "ReflectionContext",
    "ReflectionResult",
    "ConsistencyChecker",
    "CitationChecker",
    "HallucinationDetector",
    "ConfidenceEngine",
    "ReflectionPipeline",
]
