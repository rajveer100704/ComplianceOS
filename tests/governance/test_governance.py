"""Unit & integration tests for AI Governance & Audit Engine (Sprint 6)."""

import pytest
from events import EventBus, PlatformEvent, EventCategory
from governance import (
    GovernanceManager,
    ComplianceRule,
    RuleOperator,
    GateStatus,
)
from collaboration.manager import CollaborationManager


@pytest.mark.asyncio
async def test_governance_audit_ledger_cryptographic_chain():
    gov = GovernanceManager()

    evt1 = PlatformEvent(
        event_type="MEMORY_STORED",
        category=EventCategory.MEMORY,
        actor_id="AgentRetriever",
        target_id="MEM-001",
        organization_id="org-acme",
    )
    entry1 = await gov.record_event(evt1)
    assert entry1.sequence_number == 1
    assert entry1.prev_hash == "0" * 64
    assert len(entry1.current_hash) == 64

    evt2 = PlatformEvent(
        event_type="LOCK_ACQUIRED",
        category=EventCategory.COLLABORATION,
        actor_id="user-alice",
        target_id="CLM-001",
        organization_id="org-acme",
    )
    entry2 = await gov.record_event(evt2)
    assert entry2.sequence_number == 2
    assert entry2.prev_hash == entry1.current_hash

    # Validate chain integrity
    is_valid, count = await gov.verify_ledger("org-acme")
    assert is_valid is True
    assert count == 2


@pytest.mark.asyncio
async def test_governance_eventbus_pubsub_observation():
    bus = EventBus()
    gov = GovernanceManager(event_bus=bus)
    collab = CollaborationManager(event_bus=bus)

    # 1. Create workspace & session
    ws = await collab.create_workspace(
        "Gov Audit Workspace", organization_id="org-acme"
    )
    sess = await collab.create_session(
        ws.id, "Gov Audit Session", organization_id="org-acme"
    )

    # 2. Acquire lock & add comment via CollaborationManager -> emits PlatformEvent onto EventBus
    await collab.acquire_lock(sess.id, "CLM-001", "alice", "org-acme")
    await collab.add_comment(
        sess.id, "CLM-001", "alice", "Reviewing claim evidence.", "org-acme"
    )

    # 3. Verify GovernanceManager observed both events automatically via EventBus subscriber
    entries = await gov.get_audit_trail("org-acme")
    assert len(entries) >= 2
    event_types = [e.event_type for e in entries]
    assert "LOCK_ACQUIRED" in event_types
    assert "COMMENT_ADDED" in event_types

    # 4. Verify chain integrity
    is_valid, count = await gov.verify_ledger("org-acme")
    assert is_valid is True


@pytest.mark.asyncio
async def test_governance_compliance_signoff_gates():
    gov = GovernanceManager()

    # Rule 1: Grounding score >= 0.85 (blocking)
    await gov.add_rule(
        ComplianceRule(
            name="Minimum Grounding Score",
            metric_name="grounding_score",
            operator=RuleOperator.GREATER_THAN_EQUAL,
            threshold_value=0.85,
            is_blocking=True,
            organization_id="org-acme",
        )
    )

    # Context passing rule
    res_pass = await gov.evaluate_gate(
        "sess-001", {"grounding_score": 0.92}, organization_id="org-acme"
    )
    assert res_pass.status == GateStatus.PASSED
    assert res_pass.failed_rules_count == 0

    # Context failing rule
    res_fail = await gov.evaluate_gate(
        "sess-002", {"grounding_score": 0.70}, organization_id="org-acme"
    )
    assert res_fail.status == GateStatus.REJECTED
    assert res_fail.failed_rules_count == 1
