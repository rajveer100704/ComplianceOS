# Shared Memory Engine — Key Design Decisions Log

## Summary of Decisions

1. **Memory as Infrastructure**: Memory is treated as core infrastructure, managed via `MemoryManager`, not as an autonomous agent.
2. **Context Builder Abstraction**: Agents never query individual storage tiers directly; they call `MemoryManager.build_context()`.
3. **Stateless Agents**: Agents remain stateless orchestrators consuming token-budgeted `MemoryContext` objects.
4. **Append-Only & Versioning**: Memory items are append-only; updates generate a new `version` (e.g. `v1.0.1`), preserving full auditability.
5. **Mandatory Memory Provenance & Knowledge Graph Hooks**: Every memory item records `source_agent`, `source_entity`, `checksum`, `linked_entities`, and `graph_node_id` for seamless integration into Sprint 4 Knowledge Graph.
6. **Pinned Memory Immunity**: Memories flagged `is_pinned = True` are immune to auto-expiration.
