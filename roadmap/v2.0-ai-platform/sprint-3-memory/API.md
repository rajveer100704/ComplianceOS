# Shared Memory Engine — API & Contract Specification

## `MemoryManager` Interface Methods

```python
async def store_memory(item: MemoryItem) -> str:
    ...

async def search_memories(query: MemoryQuery) -> List[MemoryItem]:
    ...

async def build_context(query_text: str, organization_id: str, max_tokens: int = 2000) -> MemoryContext:
    ...
```
