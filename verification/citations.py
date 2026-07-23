"""CitationResolver component resolving exact regulatory section, page, and table citations."""

import logging
from typing import List
from document_processing.schemas import Requirement
from agents.retrieval_schemas import EvidenceBundle

logger = logging.getLogger("verification.citations")


class CitationResolver:
    """Resolves precise regulatory citations from Requirements and EvidenceBundles."""

    def resolve_citations(
        self, requirement: Requirement, bundle: EvidenceBundle
    ) -> List[str]:
        citations: List[str] = []

        # 1. Add Clause / Section citation e.g. "FAA-450.115"
        base_citation = (
            f"{requirement.regulator}-{requirement.clause}"
            if requirement.clause
            else requirement.regulator
        )
        citations.append(base_citation)

        # 2. Add Page citations
        if bundle.source_pages:
            pages_str = ", ".join(str(p) for p in sorted(set(bundle.source_pages)))
            citations.append(f"Page {pages_str}")

        # 3. Add Table & Figure citations if present in bundle
        for tbl in bundle.linked_tables:
            tbl_title = tbl.get("title") or tbl.get("id", "Table")
            citations.append(f"Table: {tbl_title}")

        for fig in bundle.linked_figures:
            fig_title = fig.get("title") or fig.get("id", "Figure")
            citations.append(f"Figure: {fig_title}")

        logger.debug(
            f"Resolved {len(citations)} citations for requirement {requirement.id}"
        )
        return citations
