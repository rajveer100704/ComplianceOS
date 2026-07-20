class RetrievalCache:
    """Memory-resident key-value cache placeholder for search responses."""

    def __init__(self):
        self._cache = {}

    def get(self, query: str, filters: dict = None) -> list:
        key = (query, tuple(sorted(filters.items())) if filters else None)
        return self._cache.get(key)

    def set(self, query: str, filters: dict, value: list) -> None:
        key = (query, tuple(sorted(filters.items())) if filters else None)
        self._cache[key] = value

    def clear(self) -> None:
        self._cache.clear()
