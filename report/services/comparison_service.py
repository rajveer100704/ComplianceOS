import logging
from typing import Dict, Any, List
from sqlalchemy import select
from database.services.unit_of_work import UnitOfWork
from database.models.report import ReportModel, ReportFindingModel, ReportSectionModel

logger = logging.getLogger("comparison_service")


class ComparisonService:
    """Computes semantic diff comparisons between different report versions."""

    @staticmethod
    async def compare_reports(report_id_a: int, report_id_b: int) -> Dict[str, Any]:
        """Compares two report versions highlighting status, sections, and findings changes."""
        async with UnitOfWork() as uow:
            report_a = await uow.reports.get(report_id_a)
            report_b = await uow.reports.get(report_id_b)

            if not report_a or not report_b:
                raise ValueError(
                    f"One or both reports (IDs: {report_id_a}, {report_id_b}) not found."
                )

            # Load sections for both
            stmt_sec_a = select(ReportSectionModel).where(
                ReportSectionModel.report_id == report_id_a,
                ReportSectionModel.is_deleted == False,
            )
            res_sec_a = await uow.session.execute(stmt_sec_a)
            sections_a = {s.section_type: s for s in res_sec_a.scalars().all()}

            stmt_sec_b = select(ReportSectionModel).where(
                ReportSectionModel.report_id == report_id_b,
                ReportSectionModel.is_deleted == False,
            )
            res_sec_b = await uow.session.execute(stmt_sec_b)
            sections_b = {s.section_type: s for s in res_sec_b.scalars().all()}

            # Load findings for both
            stmt_find_a = select(ReportFindingModel).where(
                ReportFindingModel.report_id == report_id_a,
                ReportFindingModel.is_deleted == False,
            )
            res_find_a = await uow.session.execute(stmt_find_a)
            findings_a = {f.title: f for f in res_find_a.scalars().all()}

            stmt_find_b = select(ReportFindingModel).where(
                ReportFindingModel.report_id == report_id_b,
                ReportFindingModel.is_deleted == False,
            )
            res_find_b = await uow.session.execute(stmt_find_b)
            findings_b = {f.title: f for f in res_find_b.scalars().all()}

            diff = {
                "report_id_a": report_id_a,
                "report_id_b": report_id_b,
                "status_change": {"from": report_a.status, "to": report_b.status},
                "section_changes": [],
                "finding_changes": {"added": [], "deleted": [], "modified": []},
            }

            # 1. Compare sections
            all_types = set(sections_a.keys()).union(sections_b.keys())
            for stype in all_types:
                sec_a = sections_a.get(stype)
                sec_b = sections_b.get(stype)

                if sec_a and not sec_b:
                    diff["section_changes"].append(
                        {
                            "section_type": stype,
                            "change": "deleted",
                            "title": sec_a.title,
                        }
                    )
                elif not sec_a and sec_b:
                    diff["section_changes"].append(
                        {"section_type": stype, "change": "added", "title": sec_b.title}
                    )
                elif sec_a.content != sec_b.content:
                    diff["section_changes"].append(
                        {
                            "section_type": stype,
                            "change": "modified",
                            "title": sec_b.title,
                            "diff": f"Content updated. Length: {len(sec_a.content)} -> {len(sec_b.content)}",
                        }
                    )

            # 2. Compare findings
            for title, f_b in findings_b.items():
                f_a = findings_a.get(title)
                if not f_a:
                    diff["finding_changes"]["added"].append(
                        {
                            "title": title,
                            "risk_level": f_b.risk_level,
                            "priority": f_b.priority,
                        }
                    )
                else:
                    # Check modifications
                    modified_fields = {}
                    if f_a.risk_level != f_b.risk_level:
                        modified_fields["risk_level"] = {
                            "from": f_a.risk_level,
                            "to": f_b.risk_level,
                        }
                    if f_a.priority != f_b.priority:
                        modified_fields["priority"] = {
                            "from": f_a.priority,
                            "to": f_b.priority,
                        }
                    if f_a.recommendation != f_b.recommendation:
                        modified_fields["recommendation"] = {
                            "from": f_a.recommendation,
                            "to": f_b.recommendation,
                        }

                    if modified_fields:
                        diff["finding_changes"]["modified"].append(
                            {"title": title, "changes": modified_fields}
                        )

            for title, f_a in findings_a.items():
                if title not in findings_b:
                    diff["finding_changes"]["deleted"].append(
                        {"title": title, "risk_level": f_a.risk_level}
                    )

            return diff
