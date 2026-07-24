# Architecture Decision Record (ADR 013): Real-Time Collaboration Subsystem Design

> **Status**: Accepted & Contract Frozen  
> **Date**: 2026-07-24  
> **Deciders**: AI Systems Architect, Compliance Engineering Lead

---

## Context

The 3-Pane Review Workstation SPA requires multi-user collaboration, real-time presence, concurrency control (section locking), inline comments, and audit logging to enable human-in-the-loop review alongside AI agents.

---

## Decisions

### Decision 013: Collaboration Architecture & Section Lock Engine
We implement a **Real-Time Collaboration Subsystem** (`collaboration/`) with:
1. **Workspace & Session Models**: Partitioned by `organization_id` and `workspace_id`.
2. **Section Lock Engine**: Non-blocking lock manager supporting exclusive section locks with auto-expiry.
3. **Threaded Comments & Annotations**: Hierarchical parent-child comment threads with text highlight offsets.
4. **Presence Manager**: Heartbeat-based user presence tracker (`ONLINE`, `IDLE`, `OFFLINE`).
5. **CollaborationManager Facade**: Centralized facade orchestrating workspace state and emitting events to Sprint 3 Memory (`ReviewerMemoryStore`) and Sprint 4 Knowledge Graph (`KnowledgeGraphManager`).

---

## Consequences

- **Pros**: Prevents concurrent edit collisions; audit-ready reviewer history; seamless SPA integration.
- **Cons**: Requires active heartbeat management for presence tracking.
