import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from database.services.unit_of_work import UnitOfWork
from database.models.report import (
    ReportModel,
    ReportSectionModel,
    ReportFindingModel,
    ReportCitationModel,
    ReportActivityLogModel
)
from report.receipts.generation import ReportGenerationReceipt
from report.receipts.approval import ReportApprovalReceipt
from report.events import ReportEventPublisher

logger = logging.getLogger("report_service")

# Report Lifecycle State Machine
VALID_REPORT_TRANSITIONS = {
    "Draft": ["Generated"],
    "Generated": ["Under Review", "Draft"],
    "Under Review": ["Approved", "Rejected"],
    "Approved": ["Published"],
    "Rejected": ["Draft", "Generated"],
    "Published": ["Archived"],
    "Archived": []
}

# Role permissions
ROLE_REPORT_PERMISSIONS = {
    "generate": ["Reviewer", "Lead Reviewer", "Admin"],
    "transition_any": ["Reviewer", "Lead Reviewer", "Admin"],
    "transition_approval": ["Lead Reviewer", "Admin"]  # Approved, Published, Archived
}

class ReportService:
    """Orchestrates compliance report lifecycle states, template bindings, and approvals."""

    @staticmethod
    def check_permission(action: str, role: str) -> None:
        """Validates user authorization for reporting operations."""
        allowed = ROLE_REPORT_PERMISSIONS.get(action, [])
        if role not in allowed:
            raise PermissionError(f"User role '{role}' is not authorized to perform action '{action}'")

    @staticmethod
    def calculate_risk(severity: int, likelihood: int) -> tuple[int, str]:
        """Calculates risk score and maps to a transparency risk level label."""
        score = severity * likelihood
        if score <= 5:
            return score, "Low"
        elif score <= 12:
            return score, "Medium"
        elif score <= 19:
            return score, "High"
        else:
            return score, "Critical"

    @staticmethod
    async def generate_report(
        request_id: int,
        template_name: str,
        snapshot_version: int,
        creator: str,
        role: str
    ) -> ReportModel:
        """Generates a structured compliance report referencing a reviewed snapshot state."""
        ReportService.check_permission("generate", role)

        async with UnitOfWork() as uow:
            # 1. Resolve snapshot payload
            snap = await uow.snapshots.get_by_version(request_id, snapshot_version)
            if not snap:
                raise ValueError(f"Review snapshot version {snapshot_version} not found for request {request_id}")
            
            payload = snap.payload
            
            # 2. Resolve template configuration
            template = await uow.templates.get_by_name(template_name)
            if not template:
                raise ValueError(f"Report template '{template_name}' not found.")

            # 3. Resolve lineage
            prev_ver = await uow.reports.get_latest_version(request_id)
            prev_report = None
            if prev_ver > 0:
                prev_report = await uow.reports.get_by_version(request_id, prev_ver)

            # 4. Create new Report record
            report = ReportModel(
                request_id=request_id,
                template_id=template.id,
                version=prev_ver + 1,
                previous_version_id=prev_report.id if prev_report else None,
                snapshot_version=snapshot_version,
                status="Draft",
                created_by=creator,
                metadata_payload={
                    "template_version": "v1.0.0",
                    "report_generator_version": "v1.0.0",
                    "generated_timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
            uow.session.add(report)
            await uow.session.flush()  # Populate report.id

            # 5. Populate sections based on template configurations
            sections_conf = template.sections_config.get("sections", [])
            for s_conf in sections_conf:
                section = ReportSectionModel(
                    report_id=report.id,
                    title=s_conf["title"],
                    content=s_conf.get("default_content", "Section content pending review."),
                    section_type=s_conf["type"],
                    ordering=s_conf["order"]
                )
                uow.session.add(section)

            # 6. Group claims to generate findings and citations
            claims = payload.get("claims", [])
            finding_index = 1
            for c in claims:
                # Only include reviewed claims
                if c.get("reviewer_decision") not in ["Accept", "Reject", "Needs More Evidence"]:
                    continue

                decision = c["reviewer_decision"]
                severity = 5 if decision == "Reject" else (3 if decision == "Needs More Evidence" else 1)
                likelihood = 4 if decision == "Reject" else (2 if decision == "Needs More Evidence" else 1)
                score, r_level = ReportService.calculate_risk(severity, likelihood)

                finding = ReportFindingModel(
                    report_id=report.id,
                    title=f"Finding {finding_index}: {c['text'][:100]}",
                    recommendation=f"Address compliance status: {decision}.",
                    remediation=f"Remediation plan for regulator {payload['request']['regulator']}.",
                    priority="High" if r_level in ["Critical", "High"] else ("Medium" if r_level == "Medium" else "Low"),
                    severity=severity,
                    likelihood=likelihood,
                    risk_score=score,
                    risk_level=r_level
                )
                uow.session.add(finding)
                await uow.session.flush()  # Populate finding.id
                finding_index += 1

                # Generate citations
                citation = ReportCitationModel(
                    finding_id=finding.id,
                    claim_id=c["id"],
                    evidence_id=c["pinned_evidence"][0]["id"] if c.get("pinned_evidence") else None,
                    comment_id=c["comments"][0]["id"] if c.get("comments") else None
                )
                uow.session.add(citation)

            # 7. Record activity timeline
            activity = ReportActivityLogModel(
                report_id=report.id,
                event_type="ReportGenerated",
                user=creator,
                details=f"Draft report version {report.version} generated successfully."
            )
            uow.session.add(activity)

            await uow.commit()

            # Publish event
            await ReportEventPublisher.publish_report_generated(report.id, request_id, report.version, creator)

            return report

    @staticmethod
    async def transition_status(
        report_id: int,
        new_status: str,
        user: str,
        role: str
    ) -> ReportApprovalReceipt:
        """Transitions report status according to state machine constraints."""
        async with UnitOfWork() as uow:
            report = await uow.reports.get(report_id)
            if not report:
                raise ValueError(f"Report with ID {report_id} not found.")

            old_status = report.status
            allowed = VALID_REPORT_TRANSITIONS.get(old_status, [])

            if new_status not in allowed:
                raise ValueError(f"Invalid transition: Cannot move report from '{old_status}' to '{new_status}'")

            # Check permissions
            if new_status in ["Approved", "Published", "Archived"]:
                ReportService.check_permission("transition_approval", role)
            else:
                ReportService.check_permission("transition_any", role)

            # Update status
            report.status = new_status
            now_str = datetime.now(timezone.utc).isoformat()
            if new_status == "Approved":
                report.approved_by = user
                # update metadata
                meta = dict(report.metadata_payload or {})
                meta["approved_timestamp"] = now_str
                report.metadata_payload = meta
            elif new_status == "Published":
                report.published_by = user
                meta = dict(report.metadata_payload or {})
                meta["published_timestamp"] = now_str
                report.metadata_payload = meta

            # Record timeline activity
            activity = ReportActivityLogModel(
                report_id=report.id,
                event_type=f"Report{new_status}",
                user=user,
                details=f"Report transitioned from '{old_status}' to '{new_status}'."
            )
            uow.session.add(activity)
            await uow.commit()

            # Publish event
            if new_status == "Approved":
                await ReportEventPublisher.publish_report_approved(report_id, user, now_str)
            elif new_status == "Published":
                await ReportEventPublisher.publish_report_published(report_id, user, now_str)
            elif new_status == "Archived":
                await ReportEventPublisher.publish_report_archived(report_id, user, now_str)

            return ReportApprovalReceipt(
                report_id=report_id,
                approved_by=user,
                timestamp=now_str,
                version=report.version
            )
