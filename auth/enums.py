from enum import Enum
from typing import Dict, Set, Union
from database.models.enums import UserRole


class Permission(str, Enum):
    """Fine-grained enterprise business permissions."""

    ALL = "*"

    # Claims & Standard Requirements
    CLAIMS_READ = "claims:read"
    CLAIMS_WRITE = "claims:write"
    CLAIMS_ALL = "claims:*"

    # Reports
    REPORTS_READ = "reports:read"
    REPORTS_WRITE = "reports:write"
    REPORTS_APPROVE = "reports:approve"
    REPORTS_ALL = "reports:*"

    # User Management
    USERS_READ = "users:read"
    USERS_MANAGE = "users:manage"
    USERS_ALL = "users:*"

    # Settings & Observability
    SETTINGS_MANAGE = "settings:manage"
    AUDIT_LOGS_READ = "audit_logs:read"


ROLE_PERMISSIONS_MAP: Dict[UserRole, Set[Permission]] = {
    UserRole.OWNER: {Permission.ALL},
    UserRole.ADMIN: {
        Permission.CLAIMS_ALL,
        Permission.REPORTS_ALL,
        Permission.USERS_ALL,
        Permission.SETTINGS_MANAGE,
        Permission.AUDIT_LOGS_READ,
    },
    UserRole.LEAD_REVIEWER: {
        Permission.CLAIMS_READ,
        Permission.CLAIMS_WRITE,
        Permission.REPORTS_READ,
        Permission.REPORTS_WRITE,
        Permission.REPORTS_APPROVE,
        Permission.AUDIT_LOGS_READ,
    },
    UserRole.REVIEWER: {
        Permission.CLAIMS_READ,
        Permission.CLAIMS_WRITE,
        Permission.REPORTS_READ,
        Permission.REPORTS_WRITE,
    },
    UserRole.AUDITOR: {
        Permission.CLAIMS_READ,
        Permission.REPORTS_READ,
        Permission.AUDIT_LOGS_READ,
    },
}


def has_permission(
    user_permissions: Set[Permission],
    required_permission: Union[Permission, str],
) -> bool:
    """Evaluates whether user permissions satisfy a required permission, supporting wildcards (* and domain:*)."""
    user_perm_values = {
        p.value if isinstance(p, Enum) else str(p) for p in user_permissions
    }

    if "*" in user_perm_values or Permission.ALL.value in user_perm_values:
        return True

    req_val = (
        required_permission.value
        if isinstance(required_permission, Enum)
        else str(required_permission)
    )

    if req_val in user_perm_values:
        return True

    # Check domain wildcard (e.g. reports:* satisfies reports:read)
    if ":" in req_val:
        domain = req_val.split(":")[0]
        domain_wildcard = f"{domain}:*"
        if domain_wildcard in user_perm_values:
            return True

    return False
