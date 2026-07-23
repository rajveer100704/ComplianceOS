"""RetryPolicy strategies and delay calculation helper for workflow actions."""

import enum
import random


class RetryPolicy(str, enum.Enum):
    NONE = "NONE"
    LINEAR = "LINEAR"
    EXPONENTIAL = "EXPONENTIAL"
    EXPONENTIAL_JITTER = "EXPONENTIAL_JITTER"


def calculate_delay_seconds(
    policy: RetryPolicy, attempt: int, base_delay: float = 1.0, max_delay: float = 60.0
) -> float:
    """Calculates backoff delay in seconds for an attempt number based on RetryPolicy."""
    if policy == RetryPolicy.NONE or attempt <= 0:
        return 0.0

    if policy == RetryPolicy.LINEAR:
        delay = base_delay * attempt
    elif policy == RetryPolicy.EXPONENTIAL:
        delay = base_delay * (2 ** (attempt - 1))
    elif policy == RetryPolicy.EXPONENTIAL_JITTER:
        backoff = base_delay * (2 ** (attempt - 1))
        delay = backoff * (0.5 + random.random())
    else:
        delay = base_delay

    return min(delay, max_delay)
