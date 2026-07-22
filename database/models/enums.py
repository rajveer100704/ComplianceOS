from enum import Enum


class UserRole(str, Enum):
    """Role-based access control roles (deprecated — use MembershipRole)."""

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


class MembershipRole(str, Enum):
    """Per-organization role assigned to an OrganizationMembership."""

    OWNER = "owner"
    ADMIN = "admin"
    LEAD_REVIEWER = "lead_reviewer"
    REVIEWER = "reviewer"
    AUDITOR = "auditor"


class InvitationStatus(str, Enum):
    """Lifecycle status of an organization invitation."""

    PENDING = "pending"
    ACCEPTED = "accepted"
    EXPIRED = "expired"
    REVOKED = "revoked"


class OrganizationPlan(str, Enum):
    """Subscription plan tier for an organization."""

    FREE = "free"
    PRO = "pro"
    BUSINESS = "business"
    ENTERPRISE = "enterprise"


class IntegrationProvider(str, Enum):
    """Supported enterprise third-party integration providers."""

    SLACK = "slack"
    TEAMS = "teams"
    JIRA = "jira"
    GITHUB = "github"


class IntegrationHealthStatus(str, Enum):
    """Operational health status of an active integration."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DISCONNECTED = "disconnected"
    EXPIRED = "expired"


class DeliveryStatus(str, Enum):
    """Status of an outbox event delivery attempt to an integration provider."""

    PENDING = "pending"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRYING = "retrying"
