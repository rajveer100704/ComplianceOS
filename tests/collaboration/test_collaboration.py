"""Unit & integration tests for Real-Time Collaboration & Workspace Workstation (Sprint 5)."""

import pytest
from collaboration import (
    CollaborationManager,
    PresenceStatus,
    LockState,
)
from memory.manager import MemoryManager


@pytest.mark.asyncio
async def test_collaboration_workspace_session_and_locking():
    memory_mgr = MemoryManager()
    collab = CollaborationManager(memory_manager=memory_mgr)

    # 1. Create Workspace & Session
    ws = await collab.create_workspace(
        "Aerospace Safety Review", organization_id="org-acme"
    )
    sess = await collab.create_session(
        ws.id, "FAA 450 Verification", organization_id="org-acme"
    )

    assert ws.id.startswith("ws-")
    assert sess.id.startswith("sess-")

    # 2. User Alice acquires lock on Section CLM-001
    status_a, lock_a = await collab.acquire_lock(
        session_id=sess.id,
        section_id="CLM-001",
        user_id="alice",
        organization_id="org-acme",
        ttl_seconds=300,
    )
    assert status_a == LockState.ACQUIRED
    assert lock_a.owner_user_id == "alice"

    # 3. User Bob attempts to acquire lock on same section -> REJECTED
    status_b, lock_b = await collab.acquire_lock(
        session_id=sess.id,
        section_id="CLM-001",
        user_id="bob",
        organization_id="org-acme",
    )
    assert status_b == LockState.REJECTED

    # 4. User Alice releases lock
    released = await collab.release_lock(
        session_id=sess.id,
        section_id="CLM-001",
        user_id="alice",
        organization_id="org-acme",
    )
    assert released is True

    # 5. User Bob acquires lock after release -> ACQUIRED
    status_b2, lock_b2 = await collab.acquire_lock(
        session_id=sess.id,
        section_id="CLM-001",
        user_id="bob",
        organization_id="org-acme",
    )
    assert status_b2 == LockState.ACQUIRED
    assert lock_b2.owner_user_id == "bob"


@pytest.mark.asyncio
async def test_collaboration_threaded_comments_mentions_and_activity():
    memory_mgr = MemoryManager()
    collab = CollaborationManager(memory_manager=memory_mgr)

    ws = await collab.create_workspace("ASME Audit", organization_id="org-acme")
    sess = await collab.create_session(
        ws.id, "BPVC Verification", organization_id="org-acme"
    )

    # Add root comment with @mention
    cmt = await collab.add_comment(
        session_id=sess.id,
        section_id="CLM-002",
        author_id="alice",
        content="Please double check trajectory calculation @bob.smith",
        organization_id="org-acme",
    )

    assert "bob.smith" in cmt.mentions

    # Add nested reply comment
    reply = await collab.add_comment(
        session_id=sess.id,
        section_id="CLM-002",
        author_id="bob",
        content="Verified with PyMuPDF parser snippet.",
        organization_id="org-acme",
        parent_comment_id=cmt.id,
    )
    assert reply.parent_comment_id == cmt.id

    # Verify Activity Log
    events = await collab.get_activity_log(sess.id)
    assert len(events) >= 2
    assert events[0].event_type == "COMMENT_ADDED"


@pytest.mark.asyncio
async def test_collaboration_presence_tracking():
    collab = CollaborationManager()

    ws = await collab.create_workspace("Live Sync", organization_id="org-acme")
    sess = await collab.create_session(
        workspace_id=ws.id, title="Live Sync Session", organization_id="org-acme"
    )

    await collab.update_presence(
        session_id=sess.id,
        user_id="alice",
        organization_id="org-acme",
        status=PresenceStatus.ONLINE,
        active_section_id="CLM-001",
        cursor_offset=120,
    )

    active = await collab.get_active_participants(sess.id, organization_id="org-acme")
    assert len(active) == 1
    assert active[0].user_id == "alice"
    assert active[0].cursor_offset == 120
