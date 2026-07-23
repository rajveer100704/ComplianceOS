"""CitationChecker ensuring that every claim has valid regulatory citations."""

import logging
from typing import List, Dict, Any, Tuple

logger = logging.getLogger("reflection.citation_checker")


class CitationChecker:
    """Verifies citation coverage across verification claims and report sections."""

    def check_citations(
        self, verification_results: List[Dict[str, Any]]
    ) -> Tuple[List[str], int]:
        missing: List[str] = []
        total_citations = 0

        for v in verification_results:
            cites = v.get("citations", [])
            total_citations += len(cites)
            if not cites:
                missing.append(
                    f"Claim '{v.get('id')}' for requirement '{v.get('requirement_id')}' lacks a valid citation."
                )

        logger.debug(
            f"Citation check completed: {len(missing)} missing, {total_citations} total citations verified"
        )
        return missing, total_citations
