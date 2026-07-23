"""Admin REST API router for Audit Search, Filtering, and Exporting."""

from typing import Optional
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from auth.dependencies import require_permission, get_db_session
from auth.enums import Permission
from audit.repository import AuditLogRepository
from audit.exporter import AuditExporter

router = APIRouter(prefix="/admin/audit-logs", tags=["Admin Audit Trail"])


@router.get(
    "",
    dependencies=[Depends(require_permission(Permission.ORGANIZATIONS_READ))],
)
async def list_audit_logs_api(
    org_id: str,
    action: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db_session),
):
    """Lists enterprise audit trail logs with filtering."""
    repo = AuditLogRepository(db)
    logs = await repo.search_logs(
        organization_id=org_id,
        action=action,
        resource_type=resource_type,
        user_id=user_id,
        limit=limit,
        offset=offset,
    )
    return logs


@router.get(
    "/export",
    dependencies=[Depends(require_permission(Permission.ORGANIZATIONS_READ))],
)
async def export_audit_logs_api(
    org_id: str,
    format: str = Query("csv", pattern="^(csv|json)$"),
    db: AsyncSession = Depends(get_db_session),
):
    """Exports audit trail logs to downloadable CSV or JSON file."""
    repo = AuditLogRepository(db)
    logs = await repo.search_logs(organization_id=org_id, limit=500)

    if format == "json":
        json_content = AuditExporter.export_to_json(logs)
        return Response(content=json_content, media_type="application/json")
    else:
        csv_content = AuditExporter.export_to_csv(logs)
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=audit_trail_{org_id}.csv"
            },
        )
