import json
import hashlib
import asyncio
import logging
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.enums import DeliveryStatus
from database.repositories.integration_repository import IntegrationRepository
from integrations.events import DomainEvent
from integrations.registry import AdapterRegistry
from integrations.crypto import CredentialService
from integrations.circuit_breaker import get_circuit_breaker

logger = logging.getLogger("event_dispatcher")


class EventDispatcher:
    """Parallel outbox event dispatcher routing domain events across target integration adapters."""

    @staticmethod
    def generate_idempotency_key(event_id: str, integration_id: str) -> str:
        """Computes SHA-256 idempotency key: SHA-256(event_id + integration_id)."""
        raw = f"{event_id}:{integration_id}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    @classmethod
    async def dispatch_event(
        cls, session: AsyncSession, event: DomainEvent
    ) -> List[Dict[str, Any]]:
        """Dispatches a DomainEvent concurrently to all active, supporting adapters for the target tenant."""
        repo = IntegrationRepository(session)
        circuit_breaker = get_circuit_breaker()

        # Fetch active integrations for the tenant
        integrations = await repo.list_for_org(event.organization_id, active_only=True)
        if not integrations:
            return []

        async def _deliver_to_integration(integration):
            # Check circuit breaker
            if not circuit_breaker.allow_request(integration.id):
                logger.warning(
                    f"Circuit breaker OPEN for integration '{integration.id}' ({integration.provider.value}). Skipping delivery."
                )
                return {
                    "integration_id": integration.id,
                    "provider": integration.provider.value,
                    "status": "circuit_open",
                }

            # Resolve adapter
            adapter = AdapterRegistry.get(integration.provider)
            if not adapter or not adapter.supports(event):
                return {
                    "integration_id": integration.id,
                    "provider": integration.provider.value,
                    "status": "unsupported",
                }

            # Check idempotency log
            idempotency_key = cls.generate_idempotency_key(event.id, integration.id)
            existing_log = await repo.find_delivery_log_by_idempotency_key(
                idempotency_key
            )
            if existing_log and existing_log.status == DeliveryStatus.DELIVERED:
                return {
                    "integration_id": integration.id,
                    "provider": integration.provider.value,
                    "status": "already_delivered",
                }

            # Decrypt credentials
            secret = CredentialService.decrypt(integration.encrypted_secret)
            config = {}
            if integration.metadata_json:
                try:
                    config = json.loads(integration.metadata_json)
                except Exception:
                    config = {}

            # Execute adapter delivery safely
            try:
                result = await adapter.execute(event, config=config, secret=secret)
                if result.success:
                    circuit_breaker.record_success(integration.id)
                    await repo.update_runtime_state(
                        integration_id=integration.id,
                        success=True,
                        probe_duration_ms=result.probe_duration_ms,
                    )
                    await repo.record_delivery_log(
                        integration_id=integration.id,
                        organization_id=event.organization_id,
                        event_type=event.event_type.value,
                        idempotency_key=idempotency_key,
                        status=DeliveryStatus.DELIVERED,
                        response_code=result.status_code,
                    )
                    return {
                        "integration_id": integration.id,
                        "provider": integration.provider.value,
                        "status": "delivered",
                    }
                else:
                    circuit_breaker.record_failure(integration.id)
                    await repo.update_runtime_state(
                        integration_id=integration.id,
                        success=False,
                        error_message=result.error_message,
                        probe_duration_ms=result.probe_duration_ms,
                    )
                    await repo.record_delivery_log(
                        integration_id=integration.id,
                        organization_id=event.organization_id,
                        event_type=event.event_type.value,
                        idempotency_key=idempotency_key,
                        status=DeliveryStatus.FAILED,
                        response_code=result.status_code,
                        error_message=result.error_message,
                    )
                    return {
                        "integration_id": integration.id,
                        "provider": integration.provider.value,
                        "status": "failed",
                        "error": result.error_message,
                    }
            except Exception as e:
                circuit_breaker.record_failure(integration.id)
                err_msg = str(e)
                await repo.update_runtime_state(
                    integration_id=integration.id,
                    success=False,
                    error_message=err_msg,
                )
                await repo.record_delivery_log(
                    integration_id=integration.id,
                    organization_id=event.organization_id,
                    event_type=event.event_type.value,
                    idempotency_key=idempotency_key,
                    status=DeliveryStatus.FAILED,
                    error_message=err_msg,
                )
                return {
                    "integration_id": integration.id,
                    "provider": integration.provider.value,
                    "status": "error",
                    "error": err_msg,
                }

        # Execute all integration deliveries in parallel without blocking each other
        results = await asyncio.gather(
            *[_deliver_to_integration(i) for i in integrations],
            return_exceptions=True,
        )

        formatted_results = []
        for r in results:
            if isinstance(r, Exception):
                logger.error(f"EventDispatcher execution exception: {str(r)}")
            else:
                formatted_results.append(r)

        return formatted_results
