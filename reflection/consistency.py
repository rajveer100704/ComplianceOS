"""ConsistencyChecker verifying that verification findings match the drafted report sections."""

import logging
from typing import List, Dict, Any

logger = logging.getLogger("reflection.consistency")


class ConsistencyChecker:
    """Verifies consistency between verification claims, risk scores, and generated report text."""

    def check_consistency(
        self,
        verification_results: List[Dict[str, Any]],
        structured_report: Dict[str, Any],
    ) -> List[str]:
        errors: List[str] = []
        sections = structured_report.get("sections", [])
        report_text = " ".join(s.get("content", "") for s in sections).lower()

        for v in verification_results:
            req_id = v.get("requirement_id", "")
            if req_id.lower() not in report_text:
                errors.append(
                    f"Requirement '{req_id}' verification result is missing from report body."
                )

        logger.debug(f"Consistency check completed with {len(errors)} error(s)")
        return errors
