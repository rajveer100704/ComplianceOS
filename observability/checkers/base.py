from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class HealthResult:
    """Standardized result emitted by a component health checker."""

    name: str
    healthy: bool
    status: str  # "healthy", "degraded", "unhealthy"
    latency_ms: float
    details: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class BaseHealthChecker(ABC):
    """Abstract base class for modular dependency health checkers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier name for this health checker."""
        pass

    @abstractmethod
    async def check(self) -> HealthResult:
        """Executes the health check and returns a HealthResult."""
        pass
