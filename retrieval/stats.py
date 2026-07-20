class RetrievalStats:
    """Accumulates system-wide search statistics and latencies."""
    
    _queries_count = 0
    _cache_hits = 0
    _total_latency_ms = 0

    @classmethod
    def record_query(cls, latency_ms: int, cache_hit: bool) -> None:
        cls._queries_count += 1
        cls._total_latency_ms += latency_ms
        if cache_hit:
            cls._cache_hits += 1

    @classmethod
    def get_stats(cls) -> dict:
        avg_latency = cls._total_latency_ms / cls._queries_count if cls._queries_count > 0 else 0.0
        return {
            "queries": cls._queries_count,
            "cache_hits": cls._cache_hits,
            "cache_rate": cls._cache_hits / cls._queries_count if cls._queries_count > 0 else 0.0,
            "average_latency_ms": avg_latency
        }

    @classmethod
    def reset(cls) -> None:
        cls._queries_count = 0
        cls._cache_hits = 0
        cls._total_latency_ms = 0
