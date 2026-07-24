# Sprint 3 — Shared Memory Engine: Product Requirements Document (PRD)

> **Version**: 2.0.0  
> **Status**: Approved & Refined  
> **Target Milestone**: v2.0-alpha

---

## 1. Executive Summary

Sprint 3 delivers the **Shared Memory Engine** (`memory/`), providing multi-tiered, durable, stateful memory infrastructure for the v2.0 AI Platform. Memory is structured into 5 independent storage tiers (Semantic, Episodic, Organizational, Reviewer, Workflow), governed by a centralized `MemoryManager` facade and intelligence pipeline (Ranking, Importance, Compression, Expiration, Context Building).

---

## 2. Core User Stories & Requirements

1. **Semantic Memory**: As an AI agent, I want to retrieve past similar regulatory clauses and engineering standards so that verification decisions leverage historical domain context.
2. **Episodic Memory**: As an AI agent, I want to inspect prior execution trajectories and reasoning steps for similar documents to improve verification accuracy.
3. **Organizational Memory**: As an enterprise customer, I want the system to enforce tenant-specific compliance policies, interpretations, and rules.
4. **Reviewer Memory**: As a reviewer, I want the AI to remember my past feedback, corrections, and manual overrides so that future reports align with my preferences.
5. **Workflow Memory**: As the Agent Runtime OS, I want to persist long-running workflow state checkpoints so that interrupted executions can be restored seamlessly.

---

## 3. Memory Lifecycle Specification

Memories transition through a deterministic 7-stage lifecycle:

$$\text{Store} \longrightarrow \text{Version} \longrightarrow \text{Link (KG)} \longrightarrow \text{Compress} \longrightarrow \text{Expire} \longrightarrow \text{Archive} \longrightarrow \text{Delete}$$

- **Store**: Initial memory item creation with `source_agent`, `source_entity`, and `version` metadata.
- **Version**: Append-only updates creating new versions (e.g. `v1.0.1`) without mutating historical records.
- **Link (KG)**: Knowledge Graph entity indexing via `linked_entity_ids`, `graph_node_id`, and `graph_edge_ids`.
- **Compress**: Multi-item summarization during Context Building.
- **Expire**: Temporal decay and TTL expiration (unless `is_pinned = True`).
- **Archive**: Soft-deletion marking `is_archived = True`, excluding memories from active context building while retaining graph auditability.
- **Delete**: Soft/Hard removal per organization data retention policies.

---

## 4. Agent Memory Writer Ownership Matrix

| Agent | Memory Tier Written | Purpose |
| :--- | :--- | :--- |
| **Requirement Analysis Agent** | Semantic Memory | Store extracted regulatory requirements and definitions. |
| **Verification Agent** | Episodic Memory | Store verification claims, grounding scores, and reasoning steps. |
| **Reflection Agent** | Reviewer Memory | Store QA critique feedback, missing citations, and reviewer overrides. |
| **Supervisor Agent** | Workflow Memory | Store execution checkpoints and graph state transitions. |
| **Policy Engine Subsystem** | Organizational Memory | Store tenant compliance guidelines and policy rules. |

---

## 5. Non-Functional Requirements

- **Latency**: Memory retrieval and context building must complete within $\le 50\text{ms}$.
- **Decoupling**: Memory engines must be stateless infrastructure components; agents must consume memories solely via `MemoryContext`.
- **Token Efficiency**: Memory context handed to agents must be compressed and ranked within strict token budget limits.
- **Tenant Isolation**: Organizational and Reviewer memories must enforce strict tenant/organization-level isolation.
- **Knowledge Graph Hooks**: Every `MemoryItem` includes `graph_node_id`, `graph_edge_ids`, and `linked_entity_ids` ready for Sprint 4 indexing.
