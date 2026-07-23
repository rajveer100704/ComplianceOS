"""Data access repository for Audit Log queries and search filtering."""

import uuid
from datetime import datetime
from typing import Optional, Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from audit.models import EnterpriseAuditLogModel


class AuditLogRepository:
    """Repository managing immutable audit log persistence, search, and retention queries."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_log(
        self,
        organization_id: str,
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        user_id: Optional[str] = None,
        policy_version_id: Optional[str] = None,
        changes_json: Optional[dict] = None,
        ip_address: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> EnterpriseAuditLogModel:
        """Records an immutable audit log entry."""
        log_id = str(uuid.uuid4())
        model = EnterpriseAuditLogModel(
            id=log_id,
            organization_id=organization_id,
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            policy_version_id=policy_version_id,
            changes_json=changes_json,
            ip_address=ip_address,
            request_id=request_id,
            created_at=datetime.utcnow(),
        )
        self.session.add(model)
        await self.session.flush()
        return model

    async def search_logs(
        self,
        organization_id: str,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Sequence[EnterpriseAuditLogModel]:
        """Queries audit logs with optional action, resource_type, and user_id filters."""
        stmt = (
            select(EnterpriseAuditLogModel)
            .where(EnterpriseAuditLogModel.organization_id == organization_id)
            .order_by(EnterpriseAuditLogModel.created_at.desc())
        )

        if action:
            stmt = stmt.where(EnterpriseAuditLogModel.action == action)
        if resource_type:
            stmt = stmt.where(EnterpriseAuditLogModel.resource_type == resource_type)
        if user_id:
            stmt = stmt.where(EnterpriseAuditLogModel.user_id == user_id)

        stmt = stmt.limit(limit).offset(offset)
        res = await self.session.execute(stmt)
        return res.scalars().all()
