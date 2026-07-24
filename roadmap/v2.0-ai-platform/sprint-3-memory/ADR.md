# Architecture Decision Record (ADR 008): Shared Memory Engine Design

> **Status**: Accepted  
> **Date**: 2026-07-24  
> **Deciders**: AI Systems Architect, Compliance Engineering Lead

---

## Context

Agents in ComplianceOS previously operated with stateless in-memory execution states (`AgentRuntimeState`). To support long-term learning, tenant-specific policy adaptation, reviewer feedback alignment, and execution checkpointing, a durable shared memory infrastructure is required.

---

## Decision

We will implement a **Multi-Tiered Shared Memory Subsystem** (`memory/`) with the following principles:

1. **Memory as Infrastructure**: Memory is NOT an agent. It is a shared infrastructure subsystem managed via `MemoryManager`.
2. **5 Tiers**:
   - **Semantic**: Clause & standard embeddings.
   - **Episodic**: Agent execution trajectories & reasoning logs.
   - **Organizational**: Tenant guidelines & policy interpretations.
   - **Reviewer**: Human reviewer overrides & feedback patterns.
   - **Workflow**: Execution graph state checkpoints.
3. **Context Builder Pattern**: Agents never query individual memory tiers. `MemoryManager.build_context()` handles retrieval, ranking, compression, and token budgeting before returning a unified `MemoryContext`.

---

## Consequences

- **Pros**: Agents remain stateless orchestrators; memory access is unified and token-budgeted; tenant isolation is strictly enforced.
- **Cons**: Requires additional database tables and in-memory caches.
