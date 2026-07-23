"""SHA-256 checksum-keyed in-memory AST compiler cache."""

import hashlib
from typing import Optional, Dict, Any


class PolicyCompilerCache:
    """In-memory cache for compiled policy AST expressions to avoid redundant parsing overhead."""

    def __init__(self, max_size: int = 1000):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.max_size = max_size

    def get(self, expression: str) -> Optional[Dict[str, Any]]:
        """Retrieves compiled AST for expression using SHA-256 checksum key."""
        checksum = hashlib.sha256(expression.encode("utf-8")).hexdigest()
        return self._cache.get(checksum)

    def put(self, expression: str, ast: Dict[str, Any]) -> str:
        """Caches compiled AST and returns the SHA-256 checksum key."""
        checksum = hashlib.sha256(expression.encode("utf-8")).hexdigest()
        if len(self._cache) >= self.max_size:
            # Evict oldest entry simple FIFO
            self._cache.pop(next(iter(self._cache)))
        self._cache[checksum] = ast
        return checksum

    def clear(self):
        """Clears the AST compiler cache."""
        self._cache.clear()


# Global singleton compiler cache
compiler_cache = PolicyCompilerCache()
