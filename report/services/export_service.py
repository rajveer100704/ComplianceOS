import os
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List
from pathlib import Path
from database.services.unit_of_work import UnitOfWork
from database.models.report import (
    ReportModel,
    ReportFindingModel,
    ReportSectionModel,
    ReportCitationModel,
)
from report.receipts.export import ReportExportReceipt
from report.events import ReportEventPublisher

logger = logging.getLogger("export_service")


class BaseExporter:
    """Interface for pluggable report format compilation."""

    def compile(
        self,
        report: ReportModel,
        sections: List[ReportSectionModel],
        findings: List[ReportFindingModel],
    ) -> str:
        raise NotImplementedError


class JSONExporter(BaseExporter):
    """Compiles compliance report payload to standard JSON string."""

    def compile(
        self,
        report: ReportModel,
        sections: List[ReportSectionModel],
        findings: List[ReportFindingModel],
    ) -> str:
        payload = {
            "report_id": report.id,
            "request_id": report.request_id,
            "version": report.version,
            "status": report.status,
            "created_by": report.created_by,
            "sections": [
                {
                    "title": s.title,
                    "content": s.content,
                    "type": s.section_type,
                    "order": s.ordering,
                }
                for s in sections
            ],
            "findings": [
                {
                    "title": f.title,
                    "recommendation": f.recommendation,
                    "remediation": f.remediation,
                    "priority": f.priority,
                    "risk_score": f.risk_score,
                    "risk_level": f.risk_level,
                }
                for f in findings
            ],
        }
        return json.dumps(payload, indent=2)


class MarkdownExporter(BaseExporter):
    """Compiles compliance report to structured clean Markdown document."""

    def compile(
        self,
        report: ReportModel,
        sections: List[ReportSectionModel],
        findings: List[ReportFindingModel],
    ) -> str:
        lines = [
            f"# Compliance Report - Version {report.version}",
            f"**Status:** {report.status} | **Creator:** {report.created_by}",
            f"**Report ID:** {report.id} | **Request ID:** {report.request_id}",
            "---",
        ]

        # Append sections in sorted order
        for s in sections:
            lines.append(f"## {s.title}")
            lines.append(s.content)
            lines.append("")

        lines.append("## Compliance Findings")
        for idx, f in enumerate(findings, 1):
            lines.append(f"### {f.title}")
            lines.append(f"- **Risk Level:** {f.risk_level} (Score: {f.risk_score})")
            lines.append(f"- **Priority:** {f.priority}")
            lines.append(f"- **Recommendation:** {f.recommendation}")
            lines.append(f"- **Remediation:** {f.remediation}")
            lines.append("")

        return "\n".join(lines)


class HTMLExporter(BaseExporter):
    """Compiles compliance report to beautifully styled HTML document markup."""

    def compile(
        self,
        report: ReportModel,
        sections: List[ReportSectionModel],
        findings: List[ReportFindingModel],
    ) -> str:
        sections_html = ""
        for s in sections:
            sections_html += f"""
            <section class="report-section">
                <h2>{s.title}</h2>
                <p>{s.content}</p>
            </section>
            """

        findings_html = ""
        for f in findings:
            findings_html += f"""
            <div class="finding-card risk-{f.risk_level.lower()}">
                <h3>{f.title}</h3>
                <p><strong>Risk Level:</strong> {f.risk_level} (Score: {f.risk_score}) | <strong>Priority:</strong> {f.priority}</p>
                <p><strong>Recommendation:</strong> {f.recommendation}</p>
                <p><strong>Remediation:</strong> {f.remediation}</p>
            </div>
            """

        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Compliance Report - Version {report.version}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; line-height: 1.6; max-width: 800px; margin: 40px auto; padding: 0 20px; color: #333; }}
        h1 {{ border-bottom: 2px solid #eaeaea; padding-bottom: 10px; }}
        .metadata {{ color: #666; margin-bottom: 30px; }}
        .report-section {{ margin-bottom: 30px; }}
        .finding-card {{ border: 1px solid #ddd; border-left: 5px solid #ccc; padding: 15px; margin-bottom: 20px; border-radius: 4px; }}
        .risk-low {{ border-left-color: #28a745; }}
        .risk-medium {{ border-left-color: #ffc107; }}
        .risk-high {{ border-left-color: #fd7e14; }}
        .risk-critical {{ border-left-color: #dc3545; }}
    </style>
</head>
<body>
    <h1>Compliance Report - Version {report.version}</h1>
    <div class="metadata">
        <p><strong>Status:</strong> {report.status} | <strong>Creator:</strong> {report.created_by}</p>
        <p><strong>Report ID:</strong> {report.id} | <strong>Request ID:</strong> {report.request_id}</p>
    </div>
    {sections_html}
    <hr>
    <h2>Compliance Findings</h2>
    {findings_html}
</body>
</html>
"""


class ExportService:
    """Compiles and writes compliance reports using pluggable exporters."""

    EXPORTERS = {
        "json": JSONExporter(),
        "markdown": MarkdownExporter(),
        "html": HTMLExporter(),
    }

    @staticmethod
    async def export_report(
        report_id: int, format_str: str, exporter_user: str
    ) -> ReportExportReceipt:
        """Runs the validation checks, compiles the document content, and writes to storage."""
        format_key = format_str.lower()
        if format_key not in ExportService.EXPORTERS:
            raise ValueError(f"Unsupported export format '{format_str}'")

        async with UnitOfWork() as uow:
            # 1. Fetch Report
            report = await uow.reports.get(report_id)
            if not report:
                raise ValueError(f"Report with ID {report_id} not found.")

            # 2. Security Check: must be Approved or Published
            if report.status not in ["Approved", "Published"]:
                raise ValueError(
                    f"Report must be Approved or Published to be exported (current: '{report.status}')."
                )

            # 3. Fetch associated Sections (preserving template section ordering)
            from sqlalchemy import select

            stmt_sections = (
                select(ReportSectionModel)
                .where(
                    ReportSectionModel.report_id == report_id,
                    ReportSectionModel.is_deleted == False,
                )
                .order_by(ReportSectionModel.ordering.asc())
            )
            res_sections = await uow.session.execute(stmt_sections)
            sections = list(res_sections.scalars().all())

            # 4. Fetch Findings
            stmt_findings = select(ReportFindingModel).where(
                ReportFindingModel.report_id == report_id,
                ReportFindingModel.is_deleted == False,
            )
            res_findings = await uow.session.execute(stmt_findings)
            findings = list(res_findings.scalars().all())

            # 5. Citation Check: Every finding must have at least one citation
            for f in findings:
                stmt_citations = select(ReportCitationModel).where(
                    ReportCitationModel.finding_id == f.id,
                    ReportCitationModel.is_deleted == False,
                )
                res_citations = await uow.session.execute(stmt_citations)
                citations = list(res_citations.scalars().all())
                if not citations:
                    raise ValueError(
                        f"Export failed: Finding '{f.title}' (ID {f.id}) has no citations to evidence."
                    )

            # 6. Run Exporter Compiler
            exporter = ExportService.EXPORTERS[format_key]
            content = exporter.compile(report, sections, findings)

            # 7. Write to storage
            workspace_root = Path(__file__).parent.parent.parent
            export_dir = workspace_root / "storage" / "exports"
            os.makedirs(export_dir, exist_ok=True)

            now_str = datetime.now(timezone.utc).isoformat()
            file_name = f"report_{report_id}_{int(datetime.now(timezone.utc).timestamp())}.{format_key}"
            file_path = export_dir / file_name

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            # 8. Record timeline activity
            from database.models.report import ReportActivityLogModel

            activity = ReportActivityLogModel(
                report_id=report_id,
                event_type="ReportExported",
                user=exporter_user,
                details=f"Report compiled and exported to {format_key.upper()} format.",
            )
            uow.session.add(activity)
            await uow.commit()

            # 9. Publish event
            await ReportEventPublisher.publish_report_exported(
                report_id, format_key, exporter_user, now_str
            )

            return ReportExportReceipt(
                report_id=report_id,
                format=format_key,
                exported_by=exporter_user,
                timestamp=now_str,
                file_path=str(file_path.absolute()),
            )
