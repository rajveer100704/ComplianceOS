import logging
from typing import Callable, Any

logger = logging.getLogger("worker_retry")

class TaskRetryError(Exception):
    """Exception raised by tasks to request a retry execution."""
    def __init__(self, message: str, delay_sec: float = 0.0):
        super().__init__(message)
        self.delay_sec = delay_sec

class TaskPermanentError(Exception):
    """Exception raised by tasks for permanent, non-retryable failures."""
    pass

def get_retry_delay(retries: int, backoff_factor: float = 2.0, base_delay: float = 5.0) -> float:
    """Calculates exponential backoff delay: base_delay * (backoff_factor ** retries)"""
    return base_delay * (backoff_factor ** retries)
