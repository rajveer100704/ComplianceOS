import json
import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from database.repositories.integration_repository import IntegrationRepository
from database.models.integration import IntegrationModel
from integrations.schemas import IntegrationCreate, IntegrationUpdate
from integrations.crypto import CredentialService
from integrations.services.health_service import IntegrationHealthCheckService

logger = logging.getLogger("integration_service")


class IntegrationService:
    """High-level business service managing integration lifecycle, credential encryption, and probe testing."""

    @classmethod
    async def create_integration(
        cls, session: AsyncSession, organization_id: str, payload: IntegrationCreate
    ) -> IntegrationModel:
        repo = IntegrationRepository(session)

        encrypted_secret = CredentialService.encrypt(payload.secret)
        encrypted_access_token = CredentialService.encrypt(payload.access_token)
        encrypted_refresh_token = CredentialService.encrypt(payload.refresh_token)

        metadata_json = (
            json.dumps(payload.metadata) if payload.metadata is not None else None
        )

        integration = await repo.create_integration(
            organization_id=organization_id,
            provider=payload.provider,
            name=payload.name,
            encrypted_secret=encrypted_secret,
            encrypted_access_token=encrypted_access_token,
            encrypted_refresh_token=encrypted_refresh_token,
            metadata_json=metadata_json,
            is_active=payload.is_active,
        )
        return integration

    @classmethod
    async def get_integration(
        cls, session: AsyncSession, integration_id: str
    ) -> Optional[IntegrationModel]:
        repo = IntegrationRepository(session)
        return await repo.get_by_id(integration_id)

    @classmethod
    async def list_integrations(
        cls, session: AsyncSession, organization_id: str, active_only: bool = True
    ) -> List[IntegrationModel]:
        repo = IntegrationRepository(session)
        return await repo.list_for_org(organization_id, active_only=active_only)

    @classmethod
    async def update_integration(
        cls,
        session: AsyncSession,
        integration_id: str,
        payload: IntegrationUpdate,
        user_id: Optional[str] = None,
    ) -> Optional[IntegrationModel]:
        repo = IntegrationRepository(session)

        encrypted_secret = (
            CredentialService.encrypt(payload.secret)
            if payload.secret is not None
            else None
        )
        encrypted_access_token = (
            CredentialService.encrypt(payload.access_token)
            if payload.access_token is not None
            else None
        )
        encrypted_refresh_token = (
            CredentialService.encrypt(payload.refresh_token)
            if payload.refresh_token is not None
            else None
        )

        metadata_json = (
            json.dumps(payload.metadata) if payload.metadata is not None else None
        )

        return await repo.update_integration(
            integration_id=integration_id,
            name=payload.name,
            encrypted_secret=encrypted_secret,
            encrypted_access_token=encrypted_access_token,
            encrypted_refresh_token=encrypted_refresh_token,
            metadata_json=metadata_json,
            is_active=payload.is_active,
            rotated_by=user_id,
        )

    @classmethod
    async def rotate_secret(
        cls,
        session: AsyncSession,
        integration_id: str,
        new_secret: str,
        user_id: Optional[str] = None,
    ) -> Optional[IntegrationModel]:
        repo = IntegrationRepository(session)
        encrypted_secret = CredentialService.encrypt(new_secret)
        return await repo.update_integration(
            integration_id=integration_id,
            encrypted_secret=encrypted_secret,
            rotated_by=user_id,
        )

    @classmethod
    async def delete_integration(
        cls, session: AsyncSession, integration_id: str
    ) -> bool:
        repo = IntegrationRepository(session)
        return await repo.delete_integration(integration_id)

    @classmethod
    async def test_connection(
        cls, session: AsyncSession, integration_id: str
    ) -> Dict[str, Any]:
        """Probes the integration endpoint and returns connectivity status."""
        return await IntegrationHealthCheckService.probe_integration(
            session, integration_id
        )
