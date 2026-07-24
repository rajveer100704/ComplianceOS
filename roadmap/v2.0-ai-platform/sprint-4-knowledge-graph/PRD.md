# Sprint 4 — Regulatory Knowledge Graph Engine: Product Requirements Document (PRD)

> **Version**: 2.0.0  
> **Status**: Approved & Frozen  
> **Target Milestone**: v2.0-alpha

---

## 1. Executive Summary

Sprint 4 introduces the **Regulatory Knowledge Graph Engine** (`knowledge_graph/`), creating a connected relational topology across regulatory standard clauses, extracted engineering requirements, verified claims, pinned evidence, risk evaluations, final reports, human reviewer feedback, and Sprint 3 `MemoryItem` entries. 

The Knowledge Graph enables multi-hop lineage tracing, regulatory conflict detection, semantic neighborhood search, and impact analysis when standards or document clauses are revised.

---

## 2. Core User Stories & Functional Requirements

1. **Multi-Hop Regulatory Traceability**: As an auditor, I want to traverse from a final report claim back through its verification decision, pinned evidence chunk, extracted clause requirement, and source regulatory standard.
2. **Impact & Change Analysis**: As a compliance manager, I want to query which active claims and reports are affected when a specific FAA or ASME regulatory section is updated.
3. **Memory Graph Linkage**: As an AI agent, I want memories stored in Sprint 3 to link directly to Knowledge Graph nodes (`graph_node_id`, `graph_edge_ids`, `linked_entity_ids`) so historical reasoning informs graph traversal.
4. **Regulatory Conflict Detection**: As a supervisor agent, I want to query contradicting evidence across overlapping regulatory standards (e.g. FAA Part 450 vs. NASA-STD-8719.24).

---

## 3. Node & Edge Taxonomies

### 6 Core Graph Node Types
- `REGULATION`: Source standards (e.g. FAA Part 450, ASME BPVC Section VIII).
- `REQUIREMENT`: Extracted mandatory/definition clauses (e.g. `REQ-450.115-a`).
- `CLAIM`: Engineering assertion undergoing compliance verification.
- `EVIDENCE`: Pinned document text chunk or telemetry data snippet.
- `DECISION`: Verification result (SUPPORTED, UNSUPPORTED, CONDITIONAL) & grounding score.
- `MEMORY`: Sprint 3 `MemoryItem` entry.

### 8 Directed Edge Types
- `CONTAINS`: `REGULATION` $\rightarrow$ `REQUIREMENT`
- `REQUIRES`: `CLAIM` $\rightarrow$ `REQUIREMENT`
- `SUPPORTS`: `EVIDENCE` $\rightarrow$ `CLAIM`
- `CONTRADICTS`: `EVIDENCE` $\rightarrow$ `CLAIM`
- `VERIFIES`: `DECISION` $\rightarrow$ `CLAIM`
- `CITES`: `DECISION` $\rightarrow$ `EVIDENCE`
- `GENERATED_BY`: `DECISION` $\rightarrow$ `MEMORY`
- `SUPERSEDES`: `REGULATION` (v2) $\rightarrow$ `REGULATION` (v1)

---

## 4. Non-Functional Requirements

- **Traversal Latency**: Multi-hop graph traversals up to 4 hops must complete within $\le 30\text{ms}$.
- **Entity Resolution**: Automatic entity deduplication based on content SHA-256 checksums and canonical URI identifiers.
- **Tenant Isolation**: Mandatory `organization_id` partitioning across all graph queries and sub-graph traversals.
- **Immutable Provenance**: Graph nodes preserve immutable record pointers (`logical_id`, `record_id`, `version`).
