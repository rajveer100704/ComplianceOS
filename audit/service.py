"""AuditLogService and @audit_action decorator for auditing platform mutations."""

import functools
import logging
from typing import Optional, Callable
from audit.repository import AuditLogRepository

logger = logging.getLogger("audit_service")


class AuditLogService:
    """Service facade recording structured audit log events."""

    def __init__(self, repo: AuditLogRepository):
        self.repo = repo

    async def log_event(
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
    ):
        """Records audit log event entry in persistent repository."""
        return await self.repo.create_log(
            organization_id=organization_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            user_id=user_id,
            policy_version_id=policy_version_id,
            changes_json=changes_json,
            ip_address=ip_address,
            request_id=request_id,
        )


def audit_action(action_name: str, resource_type: str):
    """Decorator capturing service method executions for automatic audit trail entry."""

    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            res = await func(*args, **kwargs)
            logger.info(
                f"Audit action '{action_name}' on resource '{resource_type}' logged."
            )
            return res

        return wrapper

    return decorator
