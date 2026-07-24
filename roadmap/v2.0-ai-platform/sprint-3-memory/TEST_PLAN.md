# Shared Memory Engine — Test Plan

## Test Strategy

1. **Unit Tests (`tests/memory/test_memory_stores.py`)**: Validate CRUD operations across all 5 memory stores (Semantic, Episodic, Organizational, Reviewer, Workflow).
2. **Intelligence Pipeline Tests (`tests/memory/test_memory_intelligence.py`)**: Validate ranking, importance scoring, context window compression, and TTL expiration.
3. **Context Builder Tests (`tests/memory/test_context_builder.py`)**: Validate token-budgeted `MemoryContext` construction.
4. **Platform Integration Test (`tests/agents/test_end_to_end_pipeline.py`)**: Verify that all 6 agents execute cleanly with memory context enabled.
