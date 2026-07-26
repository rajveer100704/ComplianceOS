"""Chaos resilience and failure injection test suite for ComplianceOS."""

import pytest
from core.reliability.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerOpenException,
    CircuitState,
)


def test_circuit_breaker_trips_to_open_on_failures():
    """Verify circuit breaker transitions from CLOSED to OPEN after failure threshold reached."""
    breaker = CircuitBreaker(failure_threshold=3, recovery_timeout_s=10.0)

    def faulty_call():
        raise RuntimeError("Simulated infrastructure failure")

    # Fail 3 times
    for _ in range(3):
        with pytest.raises(RuntimeError):
            breaker.call(faulty_call)

    assert breaker.state == CircuitState.OPEN

    # 4th call should immediately raise CircuitBreakerOpenException (fast-fail)
    with pytest.raises(CircuitBreakerOpenException):
        breaker.call(faulty_call)
