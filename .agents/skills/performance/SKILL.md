---
name: performance
description: >
  Use when optimizing performance: N+1 query detection, pagination enforcement,
  streaming uploads, batch operations, connection pooling, caching strategies,
  lazy loading, memory profiling, and async compliance.
---

# Performance Skill

## When to Use

- Reviewing code for N+1 queries or unbounded result sets.
- Adding pagination to list endpoints.
- Optimizing database queries or embedding operations.
- Implementing caching or connection pooling.
- Profiling memory usage or response latency.

## Quick Checks

1. **N+1 queries**: Does any loop execute a query per iteration? → Use `selectinload()`.
2. **Unbounded results**: Does any endpoint return all rows? → Add `OFFSET`/`LIMIT`.
3. **Blocking I/O**: Is `time.sleep()`, `requests.get()`, or sync file I/O used in async? → Replace.
4. **One-at-a-time embeddings**: Is `model.encode()` called per chunk? → Batch with `batch_size=64`.
5. **Resource leaks**: Are HTTP clients or DB sessions created per request without cleanup? → Reuse.

## Performance Targets

| Operation | P95 Target |
| :--- | :--- |
| API response | < 200ms |
| Retrieval search | < 150ms |
| PDF parse (50 pages) | < 5s |
| Database query | < 50ms |
| Embedding (100 chunks) | < 10s |

## References

- [PERFORMANCE.md](../../PERFORMANCE.md)
