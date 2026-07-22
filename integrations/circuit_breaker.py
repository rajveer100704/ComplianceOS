import time
from enum import Enum
from typing import Dict


class CircuitBreakerState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """Per-integration circuit breaker preventing cascading failures to downstream external services."""

    def __init__(
        self, failure_threshold: int = 5, recovery_timeout_seconds: float = 60.0
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout_seconds = recovery_timeout_seconds
        self._failures: Dict[str, int] = {}
        self._last_failure_time: Dict[str, float] = {}
        self._state: Dict[str, CircuitBreakerState] = {}

    def get_state(self, integration_id: str) -> CircuitBreakerState:
        state = self._state.get(integration_id, CircuitBreakerState.CLOSED)
        if state == CircuitBreakerState.OPEN:
            last_fail = self._last_failure_time.get(integration_id, 0)
            if time.time() - last_fail >= self.recovery_timeout_seconds:
                self._state[integration_id] = CircuitBreakerState.HALF_OPEN
                return CircuitBreakerState.HALF_OPEN
        return state

    def allow_request(self, integration_id: str) -> bool:
        state = self.get_state(integration_id)
        return state in (CircuitBreakerState.CLOSED, CircuitBreakerState.HALF_OPEN)

    def record_success(self, integration_id: str) -> None:
        self._failures[integration_id] = 0
        self._state[integration_id] = CircuitBreakerState.CLOSED

    def record_failure(self, integration_id: str) -> None:
        count = self._failures.get(integration_id, 0) + 1
        self._failures[integration_id] = count
        self._last_failure_time[integration_id] = time.time()
        if count >= self.failure_threshold:
            self._state[integration_id] = CircuitBreakerState.OPEN


_global_circuit_breaker = CircuitBreaker()


def get_circuit_breaker() -> CircuitBreaker:
    return _global_circuit_breaker
