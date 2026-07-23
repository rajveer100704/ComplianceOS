"""Independent section generators formatting verification, risk, and policy data into audit-ready markdown."""

import logging
from typing import List
from reporting_ai.schemas import ReportSection, ReportContext

logger = logging.getLogger("reporting_ai.sections")


class SectionGenerators:
    """Generates individual report sections from structured context DTOs."""

    def generate_exec_summary(self, context: ReportContext) -> ReportSection:
        verifications = context.verification_results
        risk = context.risk_results or {}
        overall_level = risk.get("overall_level", "GREEN")
        overall_score = risk.get("overall_score", 0.0)

        total_reqs = len(context.requirements)
        supported_count = sum(
            1 for v in verifications if v.get("status") == "SUPPORTED"
        )

        content = (
            f"This regulatory compliance report evaluates {total_reqs} requirement(s).\n"
            f"- **Overall Risk Level**: {overall_level} (Score: {overall_score}/100)\n"
            f"- **Supported Requirements**: {supported_count}/{total_reqs}\n"
            f"- **Organization**: {context.organization_id}\n"
        )
        return ReportSection(
            id="exec_summary",
            title="1. Executive Summary",
            content=content,
            order=1,
            citations=[],
        )

    def generate_verification_section(self, context: ReportContext) -> ReportSection:
        verifications = context.verification_results
        lines = [
            "| Claim ID | Requirement | Status | Grounding Score | Citations |",
            "| --- | --- | --- | --- | --- |",
        ]
        all_citations: List[str] = []

        for v in verifications:
            c_id = v.get("id", "CLM-001")
            r_id = v.get("requirement_id", "REQ-001")
            st = v.get("status", "SUPPORTED")
            g_score = v.get("grounding_score", 1.0)
            cites = ", ".join(v.get("citations", []))
            lines.append(f"| {c_id} | {r_id} | {st} | {g_score} | {cites} |")
            all_citations.extend(v.get("citations", []))

        return ReportSection(
            id="verification_results",
            title="3. Verification & Grounding Findings",
            content="\n".join(lines),
            order=3,
            citations=list(set(all_citations)),
        )

    def generate_risk_section(self, context: ReportContext) -> ReportSection:
        risk = context.risk_results or {}
        matrix = risk.get("risk_matrix", {})

        content = (
            f"- **Risk Matrix Zone**: {matrix.get('zone', 'GREEN')}\n"
            f"- **Likelihood**: {matrix.get('likelihood', 'Low')}\n"
            f"- **Impact**: {matrix.get('impact', 'Minor')}\n\n"
            "### Risk Category Breakdown:\n"
        )

        categories = risk.get("categories", {})
        for cat, score in categories.items():
            content += f"- **{cat.title()}**: {score}/100\n"

        return ReportSection(
            id="risk_assessment",
            title="4. Multi-Dimensional Risk Analysis",
            content=content,
            order=4,
            citations=[],
        )

    def generate_recommendations_section(self, context: ReportContext) -> ReportSection:
        risk = context.risk_results or {}
        recs = risk.get("recommendations", ["No specific actions required."])
        approvals = risk.get("approval_requirements", ["Lead Reviewer Sign-off"])

        content = "### Actionable Recommendations:\n"
        for r in recs:
            content += f"1. {r}\n"

        content += "\n### Required Approval Workflows:\n"
        for a in approvals:
            content += f"- [ ] {a}\n"

        return ReportSection(
            id="recommendations",
            title="6. Actionable Recommendations & Approvals",
            content=content,
            order=6,
            citations=[],
        )
