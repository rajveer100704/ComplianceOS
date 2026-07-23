"""Layout module for element classification, page grouping, and reading-order normalization."""

import logging
from typing import List, Dict
from document_processing.schemas import DocumentElement, ElementType

logger = logging.getLogger("document_processing.layout")


class LayoutProcessor:
    """Classifies document elements, organizes section hierarchies, and sets parent-child IDs."""

    def process_layout(self, elements: List[DocumentElement]) -> List[DocumentElement]:
        """Builds section hierarchy parent-child links across elements."""
        current_heading_id: str | None = None
        processed = []

        for idx, elem in enumerate(elements):
            elem.reading_order = idx + 1

            if elem.type == ElementType.HEADING or elem.type == ElementType.TITLE:
                current_heading_id = elem.id
            elif current_heading_id and elem.id != current_heading_id:
                elem.parent_id = current_heading_id

            processed.append(elem)

        # Update parent children_ids lists
        parent_map: Dict[str, List[str]] = {}
        for elem in processed:
            if elem.parent_id:
                parent_map.setdefault(elem.parent_id, []).append(elem.id)

        for elem in processed:
            if elem.id in parent_map:
                elem.children_ids = parent_map[elem.id]

        return processed
