import time
import base64
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

logger = logging.getLogger("adapter_jira")


class JiraAdapter(BaseIntegrationAdapter):
    """Jira Cloud REST API v3 Adapter for creating issue tickets on non-compliant claims."""

    provider = IntegrationProvider.JIRA
    capabilities = ProviderCapabilities(
        supports_notifications=False,
        supports_issue_creation=True,
        supported_events={
            DomainEventType.CLAIM_VERDICT_RECORDED,
            DomainEventType.REPORT_COMPILED,
        },
    )

    def _build_auth_header(self, email: str, api_token: str) -> Dict[str, str]:
        credentials = f"{email}:{api_token}"
        encoded = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")
        return {"Authorization": f"Basic {encoded}"}

    async def execute(
        self, event: DomainEvent, config: Dict[str, Any], secret: Optional[str] = None
    ) -> IntegrationResult:
        domain = config.get("domain")  # e.g. company.atlassian.net
        email = config.get("email")
        project_key = config.get("project_key")
        api_token = secret or config.get("api_token")

        if not domain or not email or not project_key or not api_token:
            return IntegrationResult(
                success=False,
                error_message="Missing required Jira credentials (domain, email, project_key, or api_token)",
            )

        payload = event.payload
        verdict = payload.get("verdict", "").upper()
        if (
            event.event_type == DomainEventType.CLAIM_VERDICT_RECORDED
            and verdict
            not in (
                "UNSUPPORTED",
                "PARTIAL",
            )
        ):
            return IntegrationResult(
                success=True,
                status_code=200,
                response_data={"skipped": True, "reason": "Claim is supported"},
            )

        summary = f"[ComplianceOS] Regulatory Gap: {verdict}"
        url = f"https://{domain}/rest/api/3/issue"
        headers = self._build_auth_header(email, api_token)
        headers["Content-Type"] = "application/json"

        jira_payload = {
            "fields": {
                "project": {"key": project_key},
                "summary": summary,
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"ComplianceOS Event ID: {event.id} | Verdict: {verdict}",
                                }
                            ],
                        }
                    ],
                },
                "issuetype": {"name": "Task"},
            }
        }

        start_time = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, headers=headers, json=jira_payload)
                duration_ms = int((time.perf_counter() - start_time) * 1000)

                if response.status_code == 201:
                    return IntegrationResult(
                        success=True,
                        status_code=201,
                        response_data=response.json(),
                        probe_duration_ms=duration_ms,
                    )
                else:
                    return IntegrationResult(
                        success=False,
                        status_code=response.status_code,
                        error_message=f"Jira API returned status {response.status_code}: {response.text}",
                        probe_duration_ms=duration_ms,
                    )
        except Exception as e:
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            logger.error(f"Jira API issue creation exception: {str(e)}")
            return IntegrationResult(
                success=False,
                error_message=str(e),
                probe_duration_ms=duration_ms,
            )

    async def test_connection(
        self, config: Dict[str, Any], secret: Optional[str] = None
    ) -> IntegrationResult:
        domain = config.get("domain")
        email = config.get("email")
        api_token = secret or config.get("api_token")

        if not domain or not email or not api_token:
            return IntegrationResult(
                success=False,
                error_message="Missing required Jira credentials (domain, email, or api_token)",
            )

        url = f"https://{domain}/rest/api/3/myself"
        headers = self._build_auth_header(email, api_token)
        start_time = time.perf_counter()

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url, headers=headers)
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
                        error_message=f"Jira probe returned status {response.status_code}",
                        probe_duration_ms=duration_ms,
                    )
        except Exception as e:
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            return IntegrationResult(
                success=False,
                error_message=str(e),
                probe_duration_ms=duration_ms,
            )
