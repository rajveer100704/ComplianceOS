"""Document Processing package for v2.0 AI Platform."""

from document_processing.schemas import (
    ElementType,
    RequirementType,
    RelationType,
    DocumentElement,
    DocumentRelationship,
    Requirement,
    RequirementAnalysisResult,
)
from document_processing.parser import (
    BaseDocumentParser,
    SimpleTextParser,
    parser_registry,
)
from document_processing.layout import LayoutProcessor
from document_processing.relationships import RelationshipBuilder
from document_processing.requirement_extractor import RequirementExtractor
from document_processing.validator import RequirementValidator

__all__ = [
    "ElementType",
    "RequirementType",
    "RelationType",
    "DocumentElement",
    "DocumentRelationship",
    "Requirement",
    "RequirementAnalysisResult",
    "BaseDocumentParser",
    "SimpleTextParser",
    "parser_registry",
    "LayoutProcessor",
    "RelationshipBuilder",
    "RequirementExtractor",
    "RequirementValidator",
]
