# Regulatory Knowledge Graph Engine — Implementation Checklist

- [x] Design Specification Package (PRD, ADR, ARCHITECTURE, DATABASE, API, TAXONOMY)
- [ ] Phase A Domain Schemas (`knowledge_graph/schemas.py`)
- [ ] Phase B Storage Engine (`knowledge_graph/store/base.py`, `knowledge_graph/store/memory_store.py`)
- [ ] Phase C Entity Resolution & Indexer (`knowledge_graph/indexers/resolution.py`, `knowledge_graph/indexers/builder.py`)
- [ ] Phase D Multi-Hop Traverser (`knowledge_graph/traversers/bfs_dfs.py`, `knowledge_graph/queries.py`)
- [ ] Phase E Facade & Memory Linkage (`knowledge_graph/manager.py`)
- [ ] Unit & Integration Tests (`tests/knowledge_graph/`)
- [ ] Full Platform Regression Check (208+ tests passing)
