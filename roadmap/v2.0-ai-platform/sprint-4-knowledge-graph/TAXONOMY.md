# Regulatory Knowledge Graph Engine — Taxonomy Reference

## Node Types Taxonomy (6 Canonical Types)

1. **`REGULATION`**: High-level standard or regulatory document (e.g. FAA Part 450, ASME BPVC).
2. **`REQUIREMENT`**: Atomic extracted mandatory or definition clause (e.g. Clause 450.115(a)).
3. **`CLAIM`**: System design or engineering claim submitted for verification.
4. **`EVIDENCE`**: Document text snippet, table cell, image, or telemetry data chunk.
5. **`DECISION`**: Verification outcome (`SUPPORTED`, `UNSUPPORTED`, `CONDITIONAL`), grounding score, and risk matrix result.
6. **`MEMORY`**: Sprint 3 `MemoryItem` entry (Semantic, Episodic, Organizational, Reviewer, Workflow).

---

## Edge Types Taxonomy (8 Directed Relationships)

| Edge Type | Source Node | Target Node | Business Semantics |
| :--- | :--- | :--- | :--- |
| `CONTAINS` | `REGULATION` | `REQUIREMENT` | Standard contains specific requirement clause |
| `REQUIRES` | `CLAIM` | `REQUIREMENT` | Claim must satisfy standard requirement |
| `SUPPORTS` | `EVIDENCE` | `CLAIM` | Evidence chunk substantiates claim |
| `CONTRADICTS` | `EVIDENCE` | `CLAIM` | Evidence chunk refutes claim |
| `VERIFIES` | `DECISION` | `CLAIM` | Decision records evaluation of claim |
| `CITES` | `DECISION` | `EVIDENCE` | Decision relies on specific evidence snippet |
| `GENERATED_BY` | `DECISION` | `MEMORY` | Decision leverages historical memory trace |
| `SUPERSEDES` | `REGULATION` | `REGULATION` | Standard revision supersedes past standard version |
