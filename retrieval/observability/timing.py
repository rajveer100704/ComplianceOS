import time
from contextlib import contextmanager
from typing import Generator, Dict


@contextmanager
def measure_time() -> Generator[Dict[str, float], None, None]:
    """Context manager to measure the execution time of a code block in milliseconds."""
    metrics = {"elapsed_ms": 0.0}
    start = time.perf_counter()
    try:
        yield metrics
    finally:
        end = time.perf_counter()
        metrics["elapsed_ms"] = (end - start) * 1000.0
