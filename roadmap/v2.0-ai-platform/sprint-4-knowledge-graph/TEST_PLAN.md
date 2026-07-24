# Regulatory Knowledge Graph Engine — Test Plan

## Test Strategy

1. **Unit Tests (`tests/knowledge_graph/test_graph_core.py`)**: Validate Node and Edge creation, property serialization, and checksum calculation.
2. **Entity Resolution Tests (`tests/knowledge_graph/test_entity_resolution.py`)**: Verify that duplicate nodes are deduplicated into canonical vertices based on checksum and logical ID.
3. **Multi-Hop Traversal Tests (`tests/knowledge_graph/test_traversal.py`)**: Test BFS/DFS path search from `Claim` to `Regulation` across 4 hops.
4. **Neighborhood & Impact Analysis Tests (`tests/knowledge_graph/test_impact_analysis.py`)**: Verify that regulation revisions correctly flag all downstream requirements, claims, and reports.
5. **Memory-to-Graph Linkage Integration Test (`tests/knowledge_graph/test_memory_graph_linkage.py`)**: Verify that Sprint 3 `MemoryItem` entries link seamlessly to graph vertices.
