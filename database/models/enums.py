from enum import Enum


class UserRole(str, Enum):
    """Role-based access control roles."""

    OWNER = "Owner"
    ADMIN = "Admin"
    LEAD_REVIEWER = "Lead Reviewer"
    REVIEWER = "Reviewer"
    AUDITOR = "Auditor"


class UserStatus(str, Enum):
    """User account lifecycle status."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"
