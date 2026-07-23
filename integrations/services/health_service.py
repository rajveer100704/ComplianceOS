import json
import logging
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from database.repositories.integration_repository import IntegrationRepository
from database.models.enums import IntegrationHealthStatus
from integrations.registry import AdapterRegistry
from integrations.crypto import CredentialService

logger = logging.getLogger("health_service")


class IntegrationHealthCheckService:
    """Background service executing operational health probes for active tenant integrations."""

    @classmethod
    async def probe_integration(
        cls, session: AsyncSession, integration_id: str
    ) -> Dict[str, Any]:
        """Probes a single integration's connectivity and updates its runtime state."""
        repo = IntegrationRepository(session)
        integration = await repo.get_by_id(integration_id)
        if not integration or not integration.is_active:
            return {
                "integration_id": integration_id,
                "health_status": "inactive",
            }

        adapter = AdapterRegistry.get(integration.provider)
        if not adapter:
            await repo.update_runtime_state(
                integration_id=integration.id,
                health_status=IntegrationHealthStatus.DISCONNECTED,
                success=False,
                error_message=f"No registered adapter found for provider '{integration.provider.value}'",
            )
            return {
                "integration_id": integration.id,
                "health_status": IntegrationHealthStatus.DISCONNECTED.value,
            }

        secret = CredentialService.decrypt(integration.encrypted_secret)
        config = {}
        if integration.metadata_json:
            try:
                config = json.loads(integration.metadata_json)
            except Exception:
                config = {}

        try:
            result = await adapter.test_connection(config=config, secret=secret)
            if result.success:
                state = await repo.update_runtime_state(
                    integration_id=integration.id,
                    health_status=IntegrationHealthStatus.HEALTHY,
                    success=True,
                    probe_duration_ms=result.probe_duration_ms,
                )
                return {
                    "integration_id": integration.id,
                    "health_status": IntegrationHealthStatus.HEALTHY.value,
                    "probe_duration_ms": result.probe_duration_ms,
                }
            else:
                state = await repo.update_runtime_state(
                    integration_id=integration.id,
                    success=False,
                    error_message=result.error_message,
                    probe_duration_ms=result.probe_duration_ms,
                )
                return {
                    "integration_id": integration.id,
                    "health_status": state.health_status.value if state else "degraded",
                    "error": result.error_message,
                }
        except Exception as e:
            err_msg = str(e)
            state = await repo.update_runtime_state(
                integration_id=integration.id,
                success=False,
                error_message=err_msg,
            )
            return {
                "integration_id": integration.id,
                "health_status": state.health_status.value if state else "disconnected",
                "error": err_msg,
            }
