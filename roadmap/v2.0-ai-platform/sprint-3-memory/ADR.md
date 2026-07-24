# Architecture Decision Record (ADR 008): Shared Memory Engine Design

> **Status**: Accepted & Contract Frozen  
> **Date**: 2026-07-24  
> **Deciders**: AI Systems Architect, Compliance Engineering Lead

---

## Context

Agents in ComplianceOS previously operated with stateless in-memory execution states (`AgentRuntimeState`). To support long-term learning, tenant-specific policy adaptation, reviewer feedback alignment, and execution checkpointing, a durable shared memory infrastructure is required.

---

## Decisions

### Decision 008: Multi-Tiered Subsystem Architecture
We implement a **Multi-Tiered Shared Memory Subsystem** (`memory/`) with 5 storage tiers (Semantic, Episodic, Organizational, Reviewer, Workflow).

### Decision 009: Append-Only & Versioned Memories
Memories are **append-only and versioned**. Existing memory items are never mutated in place; updates generate a new `version` (e.g. `v1.0.1`), preserving full historical auditability.
- **Historical Immutability**: Historical `MemoryItem` instances are immutable records. Repository implementations may maintain a separate "latest" index for efficient retrieval, but historical versions must never be deleted or rewritten.
- **Reference InMemoryStore**: Maintains the active latest version per `logical_id` for fast search, alongside an immutable version history list (`_history[logical_id]`).
- **Production Persistent Store**: Persists all historical version rows indexed by `(logical_id, version, record_id, is_latest)` to guarantee complete immutable auditability for regulatory compliance.

### Decision 010: Mandatory Memory Provenance & Knowledge Graph Hooks
Every `MemoryItem` must carry explicit provenance (`source_agent`, `source_entity`, `checksum`, `version`) and Knowledge Graph integration hooks (`graph_node_id`, `graph_edge_ids`, `linked_entity_ids`).

---

## Consequences

- **Pros**: Immutable audit trail; seamless integration with Sprint 4 Knowledge Graph; tenant-isolated, token-budgeted memory contexts.
- **Cons**: Requires explicit metadata indexing and version management in persistent DB adapters.
