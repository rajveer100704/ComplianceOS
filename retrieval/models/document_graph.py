from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
from retrieval.models.chunk import Chunk, DocumentNode, SectionNode, ParagraphNode


@dataclass
class DocumentGraph:
    """Graph structure capturing relationships between structural nodes and raw chunks."""

    documents: Dict[int, DocumentNode] = field(default_factory=dict)
    sections: Dict[str, SectionNode] = field(default_factory=dict)
    paragraphs: Dict[str, ParagraphNode] = field(default_factory=dict)
    chunks: Dict[str, Chunk] = field(default_factory=dict)

    # Adjacency maps for relationship mapping
    child_parent: Dict[str, str] = field(
        default_factory=dict
    )  # maps child_id to parent_id
    parent_children: Dict[str, List[str]] = field(
        default_factory=dict
    )  # maps parent_id to child_ids list
    sibling_links: Dict[str, Tuple[Optional[str], Optional[str]]] = field(
        default_factory=dict
    )  # maps chunk_id to (prev_chunk_id, next_chunk_id)
