"""Circuit breaker and resilience policy implementations for ComplianceOS."""

import time
import logging
import functools
from enum import Enum
from typing import Callable, Any

logger = logging.getLogger("core.reliability.circuit_breaker")


class CircuitState(str, Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class CircuitBreakerOpenException(Exception):
    """Raised when an operation is executed while circuit breaker is OPEN."""

    pass


class CircuitBreaker:
    """Stateful circuit breaker protecting external service calls."""

    def __init__(self, failure_threshold: int = 5, recovery_timeout_s: float = 30.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout_s = recovery_timeout_s
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.state = CircuitState.CLOSED

    def __call__(self, func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return self.call(func, *args, **kwargs)

        return wrapper

    def call(self, func: Callable, *args, **kwargs) -> Any:
        now = time.time()
        if self.state == CircuitState.OPEN:
            if now - self.last_failure_time > self.recovery_timeout_s:
                self.state = CircuitState.HALF_OPEN
                logger.info("CircuitBreaker state transitioned from OPEN to HALF_OPEN")
            else:
                raise CircuitBreakerOpenException(
                    "Circuit breaker is OPEN. Fast failing request."
                )

        try:
            result = func(*args, **kwargs)
            if self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                logger.info(
                    "CircuitBreaker state reset to CLOSED after successful execution."
                )
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = now
            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
                logger.error(
                    f"CircuitBreaker state tripped to OPEN after {self.failure_count} failures: {e}"
                )
            raise


class RetryPolicy:
    """Configurable retry policy with exponential backoff."""

    def __init__(
        self,
        max_retries: int = 3,
        initial_delay_s: float = 0.5,
        backoff_factor: float = 2.0,
    ):
        self.max_retries = max_retries
        self.initial_delay_s = initial_delay_s
        self.backoff_factor = backoff_factor

    def execute(self, func: Callable, *args, **kwargs) -> Any:
        delay = self.initial_delay_s
        last_exception = None
        for attempt in range(1, self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                logger.warning(
                    f"Attempt {attempt}/{self.max_retries} failed with error: {e}. Retrying in {delay}s..."
                )
                time.sleep(delay)
                delay *= self.backoff_factor
        raise last_exception
