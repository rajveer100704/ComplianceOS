# Architecture Decision Record (ADR 011): Regulatory Knowledge Graph Engine Design

> **Status**: Accepted & Contract Frozen  
> **Date**: 2026-07-24  
> **Deciders**: AI Systems Architect, Compliance Engineering Lead

---

## Context

ComplianceOS requires deep relational visibility across regulatory clauses, extracted requirements, claims, evidence, verification outcomes, and durable agent memories. Vector similarity alone cannot answer multi-hop lineage queries or change-impact traversals.

---

## Decisions

### Decision 011: Knowledge Graph Architecture & Facade
We implement a dedicated **Regulatory Knowledge Graph Engine** (`knowledge_graph/`) featuring:
1. **Typed Node & Edge Models**: Enforced Pydantic schemas for 6 Node types and 8 Directed Edge types.
2. **Entity Resolution Engine**: Resolves candidate nodes to canonical graph vertices using SHA-256 content checksums and entity IDs.
3. **Multi-Hop Traverser**: Exposes BFS/DFS path search, neighborhood extraction, and lineage tracing algorithms.
4. **KnowledgeGraphManager Facade**: Centralized interface orchestrating graph storage, indexing, traversal, and Sprint 3 `MemoryItem` linkage.
5. **Pluggable Storage Abstraction**: In-memory NetworkX reference engine for fast testing, backed by a persistent graph storage contract.

### Decision 012: Memory-to-Graph Linkage Protocol
Sprint 3 `MemoryItem` instances link to the Knowledge Graph via explicit pointers:
- `graph_node_id`: Connects the memory to its corresponding vertex.
- `graph_edge_ids`: Lists active relationship edges.
- `linked_entity_ids`: Links memories directly to target `Requirement`, `Claim`, or `Evidence` nodes.

---

## Consequences

- **Pros**: Enables audit-ready multi-hop lineage queries; provides change-impact analysis when regulations update; seamless integration with Sprint 3 Shared Memory.
- **Cons**: Requires explicit graph schema management and edge consistency maintenance during document processing.
