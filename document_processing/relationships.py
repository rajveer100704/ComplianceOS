"""Relationship builder linking captions to tables/figures, section containment, and element references."""

import re
import logging
from typing import List
from document_processing.schemas import (
    DocumentElement,
    DocumentRelationship,
    RelationType,
    ElementType,
)

logger = logging.getLogger("document_processing.relationships")


class RelationshipBuilder:
    """Detects and constructs directed relationships between document elements."""

    def build_relationships(
        self, elements: List[DocumentElement]
    ) -> List[DocumentRelationship]:
        relationships: List[DocumentRelationship] = []

        for i, elem in enumerate(elements):
            # Parent/Child containment
            if elem.parent_id:
                relationships.append(
                    DocumentRelationship(
                        source_id=elem.parent_id,
                        target_id=elem.id,
                        relation_type=RelationType.CONTAINS,
                    )
                )

            # Sequential NEXT/PREVIOUS
            if i < len(elements) - 1:
                relationships.append(
                    DocumentRelationship(
                        source_id=elem.id,
                        target_id=elements[i + 1].id,
                        relation_type=RelationType.NEXT,
                    )
                )

            # Caption linking to adjacent Table/Figure
            if elem.type == ElementType.CAPTION and i > 0:
                prev_elem = elements[i - 1]
                if prev_elem.type in (ElementType.TABLE, ElementType.FIGURE):
                    relationships.append(
                        DocumentRelationship(
                            source_id=elem.id,
                            target_id=prev_elem.id,
                            relation_type=RelationType.CAPTION_OF,
                        )
                    )

            # Cross-references in text (e.g., "refer to Table 2", "see Figure 1")
            matches = re.findall(
                r"(?:table|figure|section|clause)\s+(\d+(?:\.\d+)?)",
                elem.text,
                re.IGNORECASE,
            )
            if matches:
                elem.metadata["cross_references"] = matches

        return relationships
