"""Canonical models and schemas for Document Processing & Requirement Analysis."""

from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ElementType(str, Enum):
    TITLE = "title"
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    TABLE = "table"
    FIGURE = "figure"
    CAPTION = "caption"
    LIST = "list"
    FOOTNOTE = "footnote"


class RequirementType(str, Enum):
    MANDATORY_CONSTRAINT = "mandatory_constraint"
    DEFINITION = "definition"
    EXCEPTION = "exception"
    REFERENCE = "reference"
    FORMULA = "formula"
    INFORMATIVE = "informative"


class RelationType(str, Enum):
    CONTAINS = "contains"
    CAPTION_OF = "caption_of"
    REFERENCES = "references"
    PARENT = "parent"
    CHILD = "child"
    NEXT = "next"
    PREVIOUS = "previous"


class DocumentElement(BaseModel):
    """Canonical layout-aware document element."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    type: ElementType
    page: int = 1
    bbox: Optional[List[float]] = None  # [x0, y0, x1, y1]
    text: str = ""
    parent_id: Optional[str] = None
    children_ids: List[str] = Field(default_factory=list)
    reading_order: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DocumentRelationship(BaseModel):
    """Directed link between document elements."""

    source_id: str
    target_id: str
    relation_type: RelationType
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Requirement(BaseModel):
    """Structured requirement model extracted from regulatory documents."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    regulator: str = "FAA"
    section: str = ""
    clause: str = ""
    title: str = ""
    text: str
    type: RequirementType = RequirementType.MANDATORY_CONSTRAINT
    mandatory: bool = True
    confidence: float = 1.0
    source_element_ids: List[str] = Field(default_factory=list)
    page_numbers: List[int] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RequirementAnalysisResult(BaseModel):
    """Result artifact produced by RequirementAnalysisAgent."""

    model_config = ConfigDict(from_attributes=True)

    document_id: str
    filename: str
    total_pages: int = 0
    requirements: List[Requirement] = Field(default_factory=list)
    elements: List[DocumentElement] = Field(default_factory=list)
    relationships: List[DocumentRelationship] = Field(default_factory=list)
    statistics: Dict[str, Any] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)
