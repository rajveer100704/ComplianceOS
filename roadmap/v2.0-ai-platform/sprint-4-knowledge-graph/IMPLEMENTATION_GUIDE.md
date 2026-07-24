# Regulatory Knowledge Graph Engine — Implementation Guide

## Sequential Implementation Phases

1. **Phase A (Domain Models & Schemas)**:
   - `knowledge_graph/schemas.py` — Define `NodeType`, `EdgeType`, `GraphNode`, `GraphEdge`, `SubGraph`, `GraphPath`.
2. **Phase B (Graph Storage Engine)**:
   - `knowledge_graph/store/base.py` — `BaseGraphStore` interface.
   - `knowledge_graph/store/memory_store.py` — NetworkX in-memory reference store.
3. **Phase C (Indexer & Entity Resolution)**:
   - `knowledge_graph/indexers/resolution.py` — `EntityResolver` matching nodes by checksum and entity ID.
   - `knowledge_graph/indexers/builder.py` — Transforms `Requirement`, `Claim`, `Evidence`, `VerificationResult`, and `MemoryItem` into graph vertices and edges.
4. **Phase D (Multi-Hop Traverser & Path Search)**:
   - `knowledge_graph/traversers/bfs_dfs.py` — Multi-hop BFS/DFS path traversal.
   - `knowledge_graph/queries.py` — Declarative neighborhood and change-impact query builder.
5. **Phase E (Centralized Facade & Memory Linkage)**:
   - `knowledge_graph/manager.py` — `KnowledgeGraphManager` facade unifying store, indexer, and traverser.
   - Link `MemoryItem.graph_node_id` & `graph_edge_ids` to `KnowledgeGraphManager`.
