import logging
from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.integration import (
    IntegrationModel,
    IntegrationRuntimeStateModel,
    IntegrationDeliveryLogModel,
)
from database.models.enums import (
    IntegrationProvider,
    IntegrationHealthStatus,
    DeliveryStatus,
)

logger = logging.getLogger("integration_repository")


from sqlalchemy.orm import joinedload


class IntegrationRepository:
    """Tenant-scoped data access layer for integration models, runtime states, and delivery logs."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_integration(
        self,
        organization_id: str,
        provider: IntegrationProvider,
        name: str,
        encrypted_secret: Optional[str] = None,
        encrypted_access_token: Optional[str] = None,
        encrypted_refresh_token: Optional[str] = None,
        metadata_json: Optional[str] = None,
        is_active: bool = True,
    ) -> IntegrationModel:
        """Creates an integration record and initializes its runtime state."""
        integration = IntegrationModel(
            organization_id=organization_id,
            provider=provider,
            name=name,
            encrypted_secret=encrypted_secret,
            encrypted_access_token=encrypted_access_token,
            encrypted_refresh_token=encrypted_refresh_token,
            credential_version=1,
            rotated_at=datetime.now(timezone.utc),
            metadata_json=metadata_json,
            is_active=is_active,
        )
        self.session.add(integration)
        await self.session.flush()

        # Initialize corresponding runtime state
        runtime_state = IntegrationRuntimeStateModel(
            integration_id=integration.id,
            health_status=IntegrationHealthStatus.HEALTHY,
            consecutive_failures=0,
        )
        self.session.add(runtime_state)
        await self.session.flush()

        # Refresh integration with pre-fetched runtime state
        return await self.get_by_id(integration.id)

    async def get_by_id(self, integration_id: str) -> Optional[IntegrationModel]:
        """Retrieves an integration by ID with pre-fetched runtime state."""
        stmt = (
            select(IntegrationModel)
            .options(joinedload(IntegrationModel.runtime_state))
            .where(IntegrationModel.id == integration_id)
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def find_by_org_and_provider(
        self, organization_id: str, provider: IntegrationProvider
    ) -> List[IntegrationModel]:
        """Returns all active integrations for an organization matching a specific provider."""
        stmt = (
            select(IntegrationModel)
            .options(joinedload(IntegrationModel.runtime_state))
            .where(
                and_(
                    IntegrationModel.organization_id == organization_id,
                    IntegrationModel.provider == provider,
                    IntegrationModel.is_active == True,
                )
            )
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def list_for_org(
        self, organization_id: str, active_only: bool = True
    ) -> List[IntegrationModel]:
        """Lists all integrations belonging to an organization."""
        stmt = (
            select(IntegrationModel)
            .options(joinedload(IntegrationModel.runtime_state))
            .where(IntegrationModel.organization_id == organization_id)
        )
        if active_only:
            stmt = stmt.where(IntegrationModel.is_active == True)
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def update_integration(
        self,
        integration_id: str,
        name: Optional[str] = None,
        encrypted_secret: Optional[str] = None,
        encrypted_access_token: Optional[str] = None,
        encrypted_refresh_token: Optional[str] = None,
        metadata_json: Optional[str] = None,
        is_active: Optional[bool] = None,
        rotated_by: Optional[str] = None,
    ) -> Optional[IntegrationModel]:
        """Updates integration properties and increments credential version if secrets change."""
        integration = await self.get_by_id(integration_id)
        if not integration:
            return None

        secrets_changed = False
        if name is not None:
            integration.name = name
        if encrypted_secret is not None:
            integration.encrypted_secret = encrypted_secret
            secrets_changed = True
        if encrypted_access_token is not None:
            integration.encrypted_access_token = encrypted_access_token
            secrets_changed = True
        if encrypted_refresh_token is not None:
            integration.encrypted_refresh_token = encrypted_refresh_token
            secrets_changed = True
        if metadata_json is not None:
            integration.metadata_json = metadata_json
        if is_active is not None:
            integration.is_active = is_active

        if secrets_changed:
            integration.credential_version += 1
            integration.rotated_at = datetime.now(timezone.utc)
            if rotated_by:
                integration.rotated_by = rotated_by

        integration.updated_at = datetime.now(timezone.utc)
        await self.session.flush()
        return integration

    async def get_runtime_state(
        self, integration_id: str
    ) -> Optional[IntegrationRuntimeStateModel]:
        """Retrieves runtime operational state for an integration."""
        stmt = select(IntegrationRuntimeStateModel).where(
            IntegrationRuntimeStateModel.integration_id == integration_id
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def update_runtime_state(
        self,
        integration_id: str,
        health_status: Optional[IntegrationHealthStatus] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        probe_duration_ms: Optional[int] = None,
        next_retry_at: Optional[datetime] = None,
    ) -> Optional[IntegrationRuntimeStateModel]:
        """Updates health status and failure counters for an integration."""
        state = await self.get_runtime_state(integration_id)
        if not state:
            state = IntegrationRuntimeStateModel(integration_id=integration_id)
            self.session.add(state)

        now = datetime.now(timezone.utc)
        if success:
            state.health_status = health_status or IntegrationHealthStatus.HEALTHY
            state.last_success_at = now
            state.consecutive_failures = 0
            state.last_error_message = None
            state.next_retry_at = None
        else:
            state.last_failure_at = now
            state.consecutive_failures += 1
            state.last_error_message = error_message
            state.next_retry_at = next_retry_at
            if state.consecutive_failures >= 5:
                state.health_status = IntegrationHealthStatus.DISCONNECTED
            elif state.consecutive_failures >= 2:
                state.health_status = IntegrationHealthStatus.DEGRADED

        if probe_duration_ms is not None:
            state.last_probe_duration_ms = probe_duration_ms

        state.updated_at = now
        await self.session.flush()
        return state

    async def record_delivery_log(
        self,
        integration_id: str,
        organization_id: str,
        event_type: str,
        idempotency_key: str,
        status: DeliveryStatus,
        attempt_count: int = 1,
        response_code: Optional[int] = None,
        error_message: Optional[str] = None,
    ) -> IntegrationDeliveryLogModel:
        """Records an audit log entry for an outbox event delivery attempt."""
        log = IntegrationDeliveryLogModel(
            integration_id=integration_id,
            organization_id=organization_id,
            event_type=event_type,
            idempotency_key=idempotency_key,
            status=status,
            attempt_count=attempt_count,
            response_code=response_code,
            error_message=error_message,
            delivered_at=(
                datetime.now(timezone.utc)
                if status == DeliveryStatus.DELIVERED
                else None
            ),
        )
        self.session.add(log)
        await self.session.flush()
        return log

    async def find_delivery_log_by_idempotency_key(
        self, idempotency_key: str
    ) -> Optional[IntegrationDeliveryLogModel]:
        """Finds existing delivery log by idempotency key to prevent duplicate deliveries."""
        stmt = select(IntegrationDeliveryLogModel).where(
            IntegrationDeliveryLogModel.idempotency_key == idempotency_key
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def delete_integration(self, integration_id: str) -> bool:
        """Deletes an integration configuration and associated records."""
        integration = await self.get_by_id(integration_id)
        if not integration:
            return False
        await self.session.delete(integration)
        await self.session.flush()
        return True
