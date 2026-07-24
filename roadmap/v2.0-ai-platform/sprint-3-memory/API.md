# Shared Memory Engine — API & Contract Specification

## `MemoryManager` Interface Methods

```python
async def store(item: MemoryItem) -> str:
    """Stores a new memory item or new version into its corresponding tier."""
    ...

async def search(query: MemoryQuery) -> List[MemoryItem]:
    """Searches memory items across targeted storage tiers."""
    ...

async def build_context(
    query_text: str,
    organization_id: str,
    memory_types: Optional[List[MemoryType]] = None,
    top_k: int = 5,
    token_budget: int = 2000,
) -> MemoryContext:
    """Unified entry point for agents to acquire token-budgeted MemoryContext."""
    ...

async def archive_memory(item_id: str, memory_type: MemoryType) -> bool:
    """Archives a memory item by setting is_archived = True."""
    ...

async def pin_memory(item_id: str, memory_type: MemoryType) -> bool:
    """Pins a memory item by setting is_pinned = True to prevent auto-expiration."""
    ...

async def search_by_metadata(
    organization_id: str,
    key: str,
    value: Any,
    memory_types: Optional[List[MemoryType]] = None,
) -> List[MemoryItem]:
    """Searches memories matching specific metadata key-value filters."""
    ...
```
