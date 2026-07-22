from dataclasses import dataclass, field
from typing import Dict, Any, Optional


@dataclass(frozen=True)
class Chunk:
    """Immutable data record representing a single text chunk of a parsed document."""

    chunk_id: str
    document_id: int
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "chunk_id": self.chunk_id,
            "document_id": self.document_id,
            "text": self.text,
            "metadata": self.metadata,
        }

    def __hash__(self) -> int:
        return hash((self.chunk_id, self.document_id))

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Chunk):
            return False
        return self.chunk_id == other.chunk_id and self.document_id == other.document_id


@dataclass(frozen=True)
class DocumentNode:
    """Immutable node representing an entire document."""

    document_id: int
    filename: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SectionNode:
    """Immutable node representing a structural section/heading of a document."""

    section_id: str
    document_id: int
    title: str
    parent_section_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ParagraphNode:
    """Immutable node representing a single layout paragraph."""

    paragraph_id: str
    document_id: int
    text: str
    section_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
