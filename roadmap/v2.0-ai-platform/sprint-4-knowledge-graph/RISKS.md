# Regulatory Knowledge Graph Engine — Risk Management Document

## Identified Graph Risks & Mitigations

1. **Combinatorial Explosion in Multi-Hop Search**: Deep path exploration exhausting CPU memory.
   - *Mitigation*: Hard cap `max_depth = 4` in traversers and enforce tenant `organization_id` sub-graph filtering.
2. **Dangling Edges on Entity Deletion**: Orphaned relationship edges referencing deleted nodes.
   - *Mitigation*: Cascading edge deletion or soft-archiving (`is_archived = True`) on node state transitions.
3. **Cross-Tenant Graph Contamination**: Intermingling graph nodes across different organizations.
   - *Mitigation*: Mandatory `organization_id` partitioning enforced at the `BaseGraphStore` level.
