import time

class RetrievalTimingMiddleware:
    """Interceptor tracking latency parameters of query flows."""
    
    def __init__(self):
        self._start = None

    def start(self) -> None:
        self._start = time.perf_counter()

    def elapsed_ms(self) -> int:
        if self._start is None:
            return 0
        return int((time.perf_counter() - self._start) * 1000)
