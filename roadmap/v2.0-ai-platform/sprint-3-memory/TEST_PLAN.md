# Shared Memory Engine — Test Plan

## Extended Test Suite Specification

1. **Cross-Tenant Isolation Test**: Verify that Organization A can never retrieve Organization B memories under any query parameters.
2. **Token Budget & Compression Test**: Input 500 memory items and verify that `MemoryContextBuilder` outputs a compressed `MemoryContext` within $\le 2000$ tokens.
3. **TTL Expiration & Pinning Test**: Verify that expired items are filtered out, while pinned items (`is_pinned = True`) are preserved regardless of TTL.
4. **Relevance & Importance Ranking Test**: Verify that high-importance and query-matching memories are ranked first.
5. **Provenance & Knowledge Graph Hook Test**: Verify that stored items correctly carry `source_agent`, `version`, `checksum`, `linked_entities`, and `graph_node_id`.
6. **Concurrent Writer Test**: Verify that multiple agents storing memories simultaneously encounter zero race conditions.
7. **Platform Integration & Golden E2E Test**: Verify that all 6 Sprint 2 agents execute cleanly with memory context enabled.
