"""Unit tests for Generic StateMachine[T] and Audit Exporter."""

import pytest
from review.state_machine import (
    StateMachine,
    StandardState,
    InvalidStateTransitionError,
)
from audit.exporter import AuditExporter
from audit.models import EnterpriseAuditLogModel
from datetime import datetime


def test_state_machine_valid_transitions():
    sm = StateMachine()

    # Draft -> Pending Review
    s1 = sm.transition(StandardState.DRAFT, StandardState.PENDING_REVIEW)
    assert s1 == StandardState.PENDING_REVIEW

    # Pending Review -> Pending Approval
    s2 = sm.transition(StandardState.PENDING_REVIEW, StandardState.PENDING_APPROVAL)
    assert s2 == StandardState.PENDING_APPROVAL

    # Pending Approval -> Approved
    s3 = sm.transition(StandardState.PENDING_APPROVAL, StandardState.APPROVED)
    assert s3 == StandardState.APPROVED

    # Approved -> Published
    s4 = sm.transition(StandardState.APPROVED, StandardState.PUBLISHED)
    assert s4 == StandardState.PUBLISHED


def test_state_machine_invalid_transition():
    sm = StateMachine()

    # Published state has no outgoing transitions
    with pytest.raises(InvalidStateTransitionError):
        sm.transition(StandardState.PUBLISHED, StandardState.DRAFT)

    # Draft directly to Published is illegal
    with pytest.raises(InvalidStateTransitionError):
        sm.transition(StandardState.DRAFT, StandardState.PUBLISHED)


def test_audit_exporter_json_and_csv():
    log = EnterpriseAuditLogModel(
        id="log-1",
        organization_id="org-1",
        user_id="usr-1",
        action="claim.approved",
        resource_type="claim",
        resource_id="clm-100",
        policy_version_id="ver-1",
        changes_json={"status": "APPROVED"},
        ip_address="127.0.0.1",
        request_id="req-555",
        created_at=datetime(2026, 7, 23, 12, 0, 0),
    )

    json_output = AuditExporter.export_to_json([log])
    assert "log-1" in json_output
    assert "claim.approved" in json_output

    csv_output = AuditExporter.export_to_csv([log])
    assert (
        "log-1,org-1,usr-1,claim.approved,claim,clm-100,ver-1,127.0.0.1,req-555"
        in csv_output
    )
