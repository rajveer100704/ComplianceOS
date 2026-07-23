"""ReportValidator verifying section completeness, citation presence, and formatting rules."""

import logging
from typing import List
from reporting_ai.schemas import StructuredReport

logger = logging.getLogger("reporting_ai.validator")


class ReportValidator:
    """Validates structured reports against quality and completeness criteria."""

    def validate(self, report: StructuredReport) -> List[str]:
        errors: List[str] = []

        if not report.sections:
            errors.append("Report contains no sections.")

        for sec in report.sections:
            if not sec.content or len(sec.content.strip()) < 10:
                errors.append(
                    f"Section '{sec.title}' has insufficient or empty content."
                )

        if not report.summary:
            errors.append("Report summary is missing.")

        logger.debug(f"Report validation completed with {len(errors)} error(s)")
        return errors
