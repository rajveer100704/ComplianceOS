from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Set, Optional, Dict, Any

from database.models.enums import IntegrationProvider
from integrations.events import DomainEvent, DomainEventType


@dataclass
class ProviderCapabilities:
    """Advertises supported features and domain event triggers for an adapter."""

    supports_notifications: bool = False
    supports_issue_creation: bool = False
    supported_events: Set[DomainEventType] = field(default_factory=set)


@dataclass
class IntegrationResult:
    """Standardized response object returned by adapter execution and connection probes."""

    success: bool
    status_code: Optional[int] = None
    response_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    probe_duration_ms: Optional[int] = None


class BaseIntegrationAdapter(ABC):
    """Abstract base contract for all third-party integration adapters."""

    provider: IntegrationProvider
    capabilities: ProviderCapabilities

    def supports(self, event: DomainEvent) -> bool:
        """Determines if this adapter supports processing the given domain event."""
        return event.event_type in self.capabilities.supported_events

    @abstractmethod
    async def execute(
        self, event: DomainEvent, config: Dict[str, Any], secret: Optional[str] = None
    ) -> IntegrationResult:
        """Executes adapter delivery for a domain event."""
        pass

    @abstractmethod
    async def test_connection(
        self, config: Dict[str, Any], secret: Optional[str] = None
    ) -> IntegrationResult:
        """Probes the integration endpoint to verify credentials and connectivity."""
        pass
