"""Centralized Domain Event Catalog enum defining all platform events."""

import enum


class DomainEventCatalog(str, enum.Enum):
    """Single source of truth for platform domain event types."""

    # Claim & Review Events
    CLAIM_CREATED = "claim.created"
    CLAIM_UPDATED = "claim.updated"
    CLAIM_ASSIGNED = "claim.assigned"
    CLAIM_APPROVED = "claim.approved"
    CLAIM_REJECTED = "claim.rejected"
    CLAIM_RESOLVED = "claim.resolved"
    CLAIM_ESCALATED = "claim.escalated"

    # Report & Snapshot Events
    REPORT_GENERATED = "report.generated"
    REPORT_APPROVED = "report.approved"
    REPORT_EXPORTED = "report.exported"
    SNAPSHOT_CREATED = "snapshot.created"

    # Policy & Governance Events
    POLICY_CREATED = "policy.created"
    POLICY_ACTIVATED = "policy.activated"
    POLICY_DEACTIVATED = "policy.deactivated"
    POLICY_BLOCKED = "policy.blocked"

    # Workflow & Action Events
    WORKFLOW_STARTED = "workflow.started"
    WORKFLOW_COMPLETED = "workflow.completed"
    WORKFLOW_FAILED = "workflow.failed"

    # System & Authentication Events
    USER_LOGGED_IN = "user.logged_in"
    USER_LOGGED_OUT = "user.logged_out"
    ORGANIZATION_CREATED = "organization.created"
