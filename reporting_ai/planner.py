"""ReportPlanner defining section blueprints based on requested ReportFormat."""

import logging
from typing import List, Dict, Any
from reporting_ai.schemas import ReportFormat

logger = logging.getLogger("reporting_ai.planner")


class ReportPlanner:
    """Plans section hierarchy and order based on ReportFormat."""

    def plan_sections(self, report_format: ReportFormat) -> List[Dict[str, Any]]:
        base_plan = [
            {"id": "exec_summary", "title": "1. Executive Summary", "order": 1},
            {
                "id": "requirements_summary",
                "title": "2. Regulatory Requirements Overview",
                "order": 2,
            },
            {
                "id": "verification_results",
                "title": "3. Verification & Grounding Findings",
                "order": 3,
            },
            {
                "id": "risk_assessment",
                "title": "4. Multi-Dimensional Risk Analysis",
                "order": 4,
            },
            {
                "id": "policy_decisions",
                "title": "5. Policy Engine & Escalation Decisions",
                "order": 5,
            },
            {
                "id": "recommendations",
                "title": "6. Actionable Recommendations & Approvals",
                "order": 6,
            },
            {"id": "appendix", "title": "7. Appendix & Citation Index", "order": 7},
        ]

        if report_format == ReportFormat.EXECUTIVE:
            # High-level concise plan
            return [
                {
                    "id": "exec_summary",
                    "title": "Executive Summary & Compliance Status",
                    "order": 1,
                },
                {
                    "id": "risk_assessment",
                    "title": "High-Level Risk & Safety Matrix",
                    "order": 2,
                },
                {
                    "id": "recommendations",
                    "title": "Required Actions & Sign-offs",
                    "order": 3,
                },
            ]

        logger.debug(
            f"Planned {len(base_plan)} section(s) for format {report_format.value}"
        )
        return base_plan
