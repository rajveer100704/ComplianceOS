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

logger = logging.getLogger("adapter_slack")


class SlackAdapter(BaseIntegrationAdapter):
    """Slack Incoming Webhooks Adapter formatting notifications as Block Kit JSON."""

    provider = IntegrationProvider.SLACK
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

    def _build_block_kit_payload(self, event: DomainEvent) -> Dict[str, Any]:
        """Formats a DomainEvent into Slack Block Kit JSON structure."""
        event_title = event.event_type.value.replace(".", " ").title()
        payload = event.payload

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"🚨 ComplianceOS Alert: {event_title}",
                    "emoji": True,
                },
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Organization ID:*\n`{event.organization_id}`",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Event ID:*\n`{event.id}`",
                    },
                ],
            },
        ]

        if event.event_type == DomainEventType.CLAIM_VERDICT_RECORDED:
            verdict = payload.get("verdict", "UNKNOWN")
            claim_text = payload.get("claim_text", "")
            blocks.append(
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Verdict:* `{verdict}`\n*Claim:* {claim_text[:200]}...",
                    },
                }
            )
        elif event.event_type in (
            DomainEventType.REPORT_COMPILED,
            DomainEventType.REPORT_PUBLISHED,
        ):
            report_title = payload.get("title", "Compliance Report")
            status = payload.get("status", "draft")
            blocks.append(
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Report Title:* {report_title}\n*Status:* `{status}`",
                    },
                }
            )

        return {"blocks": blocks}

    async def execute(
        self, event: DomainEvent, config: Dict[str, Any], secret: Optional[str] = None
    ) -> IntegrationResult:
        webhook_url = secret or config.get("webhook_url")
        if not webhook_url:
            return IntegrationResult(
                success=False, error_message="Missing Slack webhook URL credential"
            )

        payload = self._build_block_kit_payload(event)
        start_time = time.perf_counter()

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(webhook_url, json=payload)
                duration_ms = int((time.perf_counter() - start_time) * 1000)

                if response.status_code == 200:
                    return IntegrationResult(
                        success=True,
                        status_code=200,
                        probe_duration_ms=duration_ms,
                    )
                else:
                    return IntegrationResult(
                        success=False,
                        status_code=response.status_code,
                        error_message=f"Slack webhook returned status {response.status_code}: {response.text}",
                        probe_duration_ms=duration_ms,
                    )
        except Exception as e:
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            logger.error(f"Slack webhook delivery exception: {str(e)}")
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
                success=False, error_message="Missing Slack webhook URL credential"
            )

        probe_payload = {
            "text": "✅ ComplianceOS Integration Test: Connection established successfully!"
        }
        start_time = time.perf_counter()

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(webhook_url, json=probe_payload)
                duration_ms = int((time.perf_counter() - start_time) * 1000)

                if response.status_code == 200:
                    return IntegrationResult(
                        success=True,
                        status_code=200,
                        probe_duration_ms=duration_ms,
                    )
                else:
                    return IntegrationResult(
                        success=False,
                        status_code=response.status_code,
                        error_message=f"Slack probe returned status {response.status_code}",
                        probe_duration_ms=duration_ms,
                    )
        except Exception as e:
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            return IntegrationResult(
                success=False,
                error_message=str(e),
                probe_duration_ms=duration_ms,
            )
