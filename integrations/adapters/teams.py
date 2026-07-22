import time
import logging
import httpx
from typing import Dict, Any, Optional
from database.models.enums import IntegrationProvider
from integrations.events import DomainEvent, DomainEventType
from integrations.adapters.base import (
    BaseIntegrationAdapter,
    ProviderCapabilities,
    IntegrationResult,
)

logger = logging.getLogger("adapter_teams")


class TeamsAdapter(BaseIntegrationAdapter):
    """Microsoft Teams Incoming Webhooks Adapter formatting Adaptive Cards JSON."""

    provider = IntegrationProvider.TEAMS
    capabilities = ProviderCapabilities(
        supports_notifications=True,
        supports_issue_creation=False,
        supported_events={
            DomainEventType.CLAIM_VERDICT_RECORDED,
            DomainEventType.REPORT_COMPILED,
            DomainEventType.REPORT_PUBLISHED,
            DomainEventType.SNAPSHOT_CREATED,
        },
    )

    def _build_adaptive_card(self, event: DomainEvent) -> Dict[str, Any]:
        """Formats a DomainEvent into a Microsoft Teams Adaptive Card JSON payload."""
        event_title = event.event_type.value.replace(".", " ").title()

        return {
            "type": "message",
            "attachments": [
                {
                    "contentType": "application/vnd.microsoft.card.adaptive",
                    "contentUrl": None,
                    "content": {
                        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                        "type": "AdaptiveCard",
                        "version": "1.4",
                        "body": [
                            {
                                "type": "TextBlock",
                                "size": "Large",
                                "weight": "Bolder",
                                "text": f"🛡️ ComplianceOS: {event_title}",
                            },
                            {
                                "type": "FactSet",
                                "facts": [
                                    {
                                        "title": "Organization ID:",
                                        "value": event.organization_id,
                                    },
                                    {"title": "Event ID:", "value": event.id},
                                    {
                                        "title": "Timestamp:",
                                        "value": event.timestamp.isoformat(),
                                    },
                                ],
                            },
                        ],
                    },
                }
            ],
        }

    async def execute(
        self, event: DomainEvent, config: Dict[str, Any], secret: Optional[str] = None
    ) -> IntegrationResult:
        webhook_url = secret or config.get("webhook_url")
        if not webhook_url:
            return IntegrationResult(
                success=False, error_message="Missing Teams webhook URL credential"
            )

        payload = self._build_adaptive_card(event)
        start_time = time.perf_counter()

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(webhook_url, json=payload)
                duration_ms = int((time.perf_counter() - start_time) * 1000)

                if response.status_code in (200, 202):
                    return IntegrationResult(
                        success=True,
                        status_code=response.status_code,
                        probe_duration_ms=duration_ms,
                    )
                else:
                    return IntegrationResult(
                        success=False,
                        status_code=response.status_code,
                        error_message=f"Teams webhook returned status {response.status_code}: {response.text}",
                        probe_duration_ms=duration_ms,
                    )
        except Exception as e:
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            logger.error(f"Teams webhook delivery exception: {str(e)}")
            return IntegrationResult(
                success=False,
                error_message=str(e),
                probe_duration_ms=duration_ms,
            )

    async def test_connection(
        self, config: Dict[str, Any], secret: Optional[str] = None
    ) -> IntegrationResult:
        webhook_url = secret or config.get("webhook_url")
        if not webhook_url:
            return IntegrationResult(
                success=False, error_message="Missing Teams webhook URL credential"
            )

        probe_payload = {
            "text": "✅ ComplianceOS Integration Test: Connection established successfully!"
        }
        start_time = time.perf_counter()

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(webhook_url, json=probe_payload)
                duration_ms = int((time.perf_counter() - start_time) * 1000)

                if response.status_code in (200, 202):
                    return IntegrationResult(
                        success=True,
                        status_code=response.status_code,
                        probe_duration_ms=duration_ms,
                    )
                else:
                    return IntegrationResult(
                        success=False,
                        status_code=response.status_code,
                        error_message=f"Teams probe returned status {response.status_code}",
                        probe_duration_ms=duration_ms,
                    )
        except Exception as e:
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            return IntegrationResult(
                success=False,
                error_message=str(e),
                probe_duration_ms=duration_ms,
            )
