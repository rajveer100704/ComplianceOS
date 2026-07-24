# Regulatory Knowledge Graph Engine — Key Design Decisions Log

## Summary of Key Graph Decisions

1. **6 Node & 8 Edge Taxonomy**: Constrained canonical graph vocabulary to prevent edge sprawl.
2. **Pluggable Storage Abstraction**: `BaseGraphStore` with in-memory NetworkX reference implementation.
3. **Multi-Hop Traversal Limit**: Maximum traversal depth capped at $\le 4$ hops for sub-50ms query latency.
4. **Memory-Graph Linkage**: Direct linkage via `graph_node_id`, `graph_edge_ids`, and `linked_entity_ids` on Sprint 3 `MemoryItem`.
