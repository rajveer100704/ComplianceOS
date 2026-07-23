"""AuditExporter rendering audit trail logs to CSV and JSON export payloads."""

import json
import csv
import io
from typing import Sequence, Dict, Any
from audit.models import EnterpriseAuditLogModel


class AuditExporter:
    """Exporter converting audit log sequences into CSV spreadsheet strings or JSON arrays."""

    @staticmethod
    def export_to_json(logs: Sequence[EnterpriseAuditLogModel]) -> str:
        """Serializes audit log models to formatted JSON array string."""
        payload = []
        for log in logs:
            payload.append(
                {
                    "id": log.id,
                    "organization_id": log.organization_id,
                    "user_id": log.user_id,
                    "action": log.action,
                    "resource_type": log.resource_type,
                    "resource_id": log.resource_id,
                    "policy_version_id": log.policy_version_id,
                    "changes_json": log.changes_json,
                    "ip_address": log.ip_address,
                    "request_id": log.request_id,
                    "created_at": log.created_at.isoformat() if log.created_at else None,
                }
            )
        return json.dumps(payload, indent=2)

    @staticmethod
    def export_to_csv(logs: Sequence[EnterpriseAuditLogModel]) -> str:
        """Serializes audit log models to CSV string format."""
        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow(
            [
                "ID",
                "Organization ID",
                "User ID",
                "Action",
                "Resource Type",
                "Resource ID",
                "Policy Version ID",
                "IP Address",
                "Request ID",
                "Created At",
            ]
        )

        for log in logs:
            writer.writerow(
                [
                    log.id,
                    log.organization_id,
                    log.user_id or "",
                    log.action,
                    log.resource_type,
                    log.resource_id or "",
                    log.policy_version_id or "",
                    log.ip_address or "",
                    log.request_id or "",
                    log.created_at.isoformat() if log.created_at else "",
                ]
            )

        return output.getvalue()
