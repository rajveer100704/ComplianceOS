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

logger = logging.getLogger("adapter_github")


class GitHubAdapter(BaseIntegrationAdapter):
    """GitHub REST API Adapter for creating issue tickets on non-compliant claims."""

    provider = IntegrationProvider.GITHUB
    capabilities = ProviderCapabilities(
        supports_notifications=False,
        supports_issue_creation=True,
        supported_events={
            DomainEventType.CLAIM_VERDICT_RECORDED,
            DomainEventType.REPORT_COMPILED,
        },
    )

    async def execute(
        self, event: DomainEvent, config: Dict[str, Any], secret: Optional[str] = None
    ) -> IntegrationResult:
        token = secret or config.get("personal_access_token")
        owner = config.get("owner")
        repo = config.get("repo")

        if not token or not owner or not repo:
            return IntegrationResult(
                success=False,
                error_message="Missing required GitHub credentials (token, owner, or repo)",
            )

        # Only create issues for UNSUPPORTED / non-compliant claim verdicts or report warnings
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
            # Skip issue creation for supported claims
            return IntegrationResult(
                success=True,
                status_code=200,
                response_data={"skipped": True, "reason": "Claim is supported"},
            )

        issue_title = f"[Compliance Alert] Non-Compliant Claim Verdict: {verdict}"
        issue_body = (
            f"### ComplianceOS Claim Verification Alert\n\n"
            f"- **Organization ID:** `{event.organization_id}`\n"
            f"- **Event ID:** `{event.id}`\n"
            f"- **Verdict:** `{verdict}`\n"
            f"- **Claim Text:** {payload.get('claim_text', 'N/A')}\n"
        )

        url = f"https://api.github.com/repos/{owner}/{repo}/issues"
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        start_time = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    url,
                    headers=headers,
                    json={
                        "title": issue_title,
                        "body": issue_body,
                        "labels": ["compliance", "regulatory-gap"],
                    },
                )
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
                        error_message=f"GitHub API returned status {response.status_code}: {response.text}",
                        probe_duration_ms=duration_ms,
                    )
        except Exception as e:
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            logger.error(f"GitHub API issue creation exception: {str(e)}")
            return IntegrationResult(
                success=False,
                error_message=str(e),
                probe_duration_ms=duration_ms,
            )

    async def test_connection(
        self, config: Dict[str, Any], secret: Optional[str] = None
    ) -> IntegrationResult:
        token = secret or config.get("personal_access_token")
        owner = config.get("owner")
        repo = config.get("repo")

        if not token or not owner or not repo:
            return IntegrationResult(
                success=False,
                error_message="Missing required GitHub credentials (token, owner, or repo)",
            )

        url = f"https://api.github.com/repos/{owner}/{repo}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
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
                        error_message=f"GitHub probe returned status {response.status_code}",
                        probe_duration_ms=duration_ms,
                    )
        except Exception as e:
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            return IntegrationResult(
                success=False,
                error_message=str(e),
                probe_duration_ms=duration_ms,
            )
