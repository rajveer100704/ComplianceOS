# ComplianceOS Performance Engineering Rules

This document defines performance constraints, anti-patterns, and optimization rules for all ComplianceOS code. These rules apply to backend services, database access, retrieval operations, and worker processes.

---

## 1. Database Performance

### No N+1 Queries

```python
# ❌ N+1: Executes 1 + N queries
claims = await session.execute(select(Claim))
for claim in claims.scalars():
    comments = await session.execute(
        select(Comment).where(Comment.claim_id == claim.id)
    )

# ✅ Eager loading: Single query with JOIN
claims = await session.execute(
    select(Claim).options(selectinload(Claim.comments))
)
```

### Rules

- **Use `selectinload()` or `joinedload()`** for known relationships.
- **Batch operations**: Use `session.execute(insert(...).values(batch))` for bulk inserts.
- **Pagination on all list queries**: Never return unbounded result sets.
  ```python
  select(Claim).offset(skip).limit(page_size)
  ```
- **Index columns used in WHERE, ORDER BY, and JOIN**: Verify with `EXPLAIN ANALYZE`.
- **Connection pooling**: Use SQLAlchemy's built-in pool. Never create connections per request.
  ```python
  create_async_engine(url, pool_size=10, max_overflow=20, pool_timeout=30)
  ```

---

## 2. Async & Concurrency

### No Blocking I/O in Async Context

```python
# ❌ Blocks the event loop
import time
time.sleep(5)

# ✅ Non-blocking
import asyncio
await asyncio.sleep(5)

# ❌ Synchronous HTTP
import requests
resp = requests.get(url)

# ✅ Async HTTP
import httpx
async with httpx.AsyncClient() as client:
    resp = await client.get(url)
```

### Rules

- **All I/O must be async**: Database, HTTP, file operations, queue operations.
- **Never use `time.sleep()`** in async code. Use `asyncio.sleep()`.
- **Never use `requests`**. Use `httpx.AsyncClient`.
- **Reuse HTTP clients**: Create a single `httpx.AsyncClient` per service lifecycle, not per request.
  ```python
  # ✅ Shared client
  class IntegrationService:
      def __init__(self):
          self.client = httpx.AsyncClient(timeout=30.0)

      async def close(self):
          await self.client.aclose()
  ```
- **Use `asyncio.gather()`** for concurrent independent operations.
  ```python
  results = await asyncio.gather(
      retriever.search(query),
      service.get_metadata(doc_id),
  )
  ```

---

## 3. Embedding & Vector Operations

### Batch Embeddings

```python
# ❌ One embedding per call
for chunk in chunks:
    embedding = model.encode(chunk.text)

# ✅ Batch encoding
texts = [chunk.text for chunk in chunks]
embeddings = model.encode(texts, batch_size=64, show_progress_bar=False)
```

### Rules

- **Batch encode** using `model.encode(texts, batch_size=N)`. Never encode one text at a time.
- **Cache embeddings**: If the same text is embedded multiple times, cache the result.
- **Lazy model loading**: Don't load the embedding model at import time. Load on first use.
  ```python
  _model = None
  def get_model():
      global _model
      if _model is None:
          _model = SentenceTransformer("all-MiniLM-L6-v2")
      return _model
  ```
- **Qdrant batch upsert**: Use `client.upsert(points=batch)` with batches of 100–500 points.

---

## 4. File & Document Processing

### Streaming Uploads

```python
# ❌ Load entire file into memory
content = await file.read()  # Could be 500MB

# ✅ Stream in chunks
CHUNK_SIZE = 1024 * 1024  # 1MB
async for chunk in file:
    process(chunk)
```

### Rules

- **Never load entire PDFs into memory** for large files. Process page by page.
  ```python
  doc = fitz.open(stream=file_bytes, filetype="pdf")
  for page in doc:
      text = page.get_text()
      process_page(text)
  doc.close()
  ```
- **Close file handles** explicitly. Use context managers.
- **Limit upload size**: Enforce max file size at the router level.
- **Process documents asynchronously**: Queue heavy parsing to background workers.

---

## 5. Response Performance

### Pagination

```python
# Every list endpoint must support pagination
@router.get("/claims", response_model=PaginatedResponse[ClaimResponse])
async def list_claims(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    ...
```

### Rules

- **Default page size**: 50 items.
- **Maximum page size**: 200 items. Reject requests for more.
- **Return pagination metadata** in responses:
  ```json
  {
    "items": [...],
    "total": 1234,
    "page": 1,
    "page_size": 50,
    "pages": 25
  }
  ```
- **Use database-level pagination** (`OFFSET`/`LIMIT`), not Python slicing.

---

## 6. Caching

### Rules

- **Cache expensive computations**: Embedding model loading, TF-IDF vectorizer fitting, regulation corpus.
- **Cache keys must be deterministic**: Based on input data, not timestamps.
- **Set TTL on caches**: Don't cache indefinitely. Use time-based expiration.
- **Invalidate on mutation**: When data changes, invalidate affected cache entries.
- **Start simple**: Use in-memory caching (`functools.lru_cache`, dict-based) before introducing Redis.

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def build_tfidf_vectorizer(corpus_hash: str):
    """Cache the fitted vectorizer. Recompute only when corpus changes."""
    vectorizer = TfidfVectorizer()
    vectorizer.fit(corpus)
    return vectorizer
```

---

## 7. Connection & Resource Management

### Rules

- **Reuse database sessions**: Use scoped session factory. One session per request.
- **Reuse HTTP clients**: One `httpx.AsyncClient` per service, not per request.
- **Connection pool sizing**:
  - `pool_size`: Number of concurrent connections (default: 10).
  - `max_overflow`: Extra connections allowed during spikes (default: 20).
  - `pool_timeout`: Wait time for available connection (default: 30s).
- **Close resources on shutdown**: Use FastAPI lifespan events.
  ```python
  @asynccontextmanager
  async def lifespan(app: FastAPI):
      # Startup
      yield
      # Shutdown: close pools, clients, models
      await engine.dispose()
  ```

---

## 8. Worker Performance

### Rules

- **Batch process outbox events**: Don't process one event at a time.
  ```python
  events = await fetch_pending_events(limit=100)
  for event in events:
      await process_event(event)
  ```
- **Use exponential backoff** for retries: `delay = base * 2^attempt`.
- **Set job timeouts**: No job should run indefinitely.
- **Monitor queue depth**: Alert when pending events exceed threshold.
- **Idempotent handlers**: Processing the same event twice must be safe.

---

## 9. Performance Monitoring

### Key Metrics to Track

| Metric | Target | Alert Threshold |
| :--- | :--- | :--- |
| API P95 Latency | < 200ms | > 500ms |
| Retrieval P95 Latency | < 150ms | > 300ms |
| PDF Parse Time (50 pages) | < 5s | > 10s |
| Database Query P95 | < 50ms | > 200ms |
| Worker Queue Depth | < 100 | > 500 |
| Memory Usage | < 512MB | > 1GB |

### Instrumentation

```python
from time import perf_counter

start = perf_counter()
result = await service.process(request)
elapsed_ms = (perf_counter() - start) * 1000

logger.info("Request processed", extra={
    "elapsed_ms": elapsed_ms,
    "endpoint": "/claims",
    "request_id": request_id,
})
```
