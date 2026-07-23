import json
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from auth.dependencies import (
    SecurityContext,
    require_permission,
    get_db_session,
)
from auth.enums import Permission
from integrations.schemas import (
    IntegrationCreate,
    IntegrationUpdate,
    IntegrationRotateSecretRequest,
    IntegrationResponse,
    IntegrationRuntimeStateResponse,
)
from integrations.services.integration_service import IntegrationService

router = APIRouter()


def _format_integration_response(integration) -> IntegrationResponse:
    metadata = {}
    if integration.metadata_json:
        try:
            metadata = json.loads(integration.metadata_json)
        except Exception:
            metadata = {}

    runtime_state = None
    if integration.runtime_state:
        runtime_state = IntegrationRuntimeStateResponse.model_validate(
            integration.runtime_state
        )

    return IntegrationResponse(
        id=integration.id,
        organization_id=integration.organization_id,
        provider=integration.provider,
        name=integration.name,
        credential_version=integration.credential_version,
        rotated_at=integration.rotated_at,
        rotated_by=integration.rotated_by,
        metadata=metadata,
        is_active=integration.is_active,
        created_at=integration.created_at,
        updated_at=integration.updated_at,
        runtime_state=runtime_state,
    )


@router.post(
    "/{org_id}/integrations",
    summary="Configure third-party integration",
    response_model=IntegrationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_integration(
    org_id: str,
    payload: IntegrationCreate,
    context: SecurityContext = Depends(
        require_permission(Permission.ORGANIZATIONS_WRITE)
    ),
    db: AsyncSession = Depends(get_db_session),
):
    if context.organization and context.organization.id != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cross-tenant access forbidden",
        )

    integration = await IntegrationService.create_integration(db, org_id, payload)
    return _format_integration_response(integration)


@router.get(
    "/{org_id}/integrations",
    summary="List organization integrations",
    response_model=List[IntegrationResponse],
)
async def list_integrations(
    org_id: str,
    active_only: bool = True,
    context: SecurityContext = Depends(
        require_permission(Permission.ORGANIZATIONS_READ)
    ),
    db: AsyncSession = Depends(get_db_session),
):
    if context.organization and context.organization.id != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cross-tenant access forbidden",
        )

    integrations = await IntegrationService.list_integrations(
        db, org_id, active_only=active_only
    )
    return [_format_integration_response(i) for i in integrations]


@router.get(
    "/{org_id}/integrations/{id}",
    summary="Get integration details",
    response_model=IntegrationResponse,
)
async def get_integration(
    org_id: str,
    id: str,
    context: SecurityContext = Depends(
        require_permission(Permission.ORGANIZATIONS_READ)
    ),
    db: AsyncSession = Depends(get_db_session),
):
    integration = await IntegrationService.get_integration(db, id)
    if not integration or integration.organization_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Integration not found"
        )

    return _format_integration_response(integration)


@router.patch(
    "/{org_id}/integrations/{id}",
    summary="Update integration configuration",
    response_model=IntegrationResponse,
)
async def update_integration(
    org_id: str,
    id: str,
    payload: IntegrationUpdate,
    context: SecurityContext = Depends(
        require_permission(Permission.ORGANIZATIONS_WRITE)
    ),
    db: AsyncSession = Depends(get_db_session),
):
    existing = await IntegrationService.get_integration(db, id)
    if not existing or existing.organization_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Integration not found"
        )

    updated = await IntegrationService.update_integration(
        db, id, payload, user_id=context.user.id if context.user else None
    )
    return _format_integration_response(updated)


@router.delete(
    "/{org_id}/integrations/{id}",
    summary="Delete integration",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_integration(
    org_id: str,
    id: str,
    context: SecurityContext = Depends(
        require_permission(Permission.ORGANIZATIONS_WRITE)
    ),
    db: AsyncSession = Depends(get_db_session),
):
    existing = await IntegrationService.get_integration(db, id)
    if not existing or existing.organization_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Integration not found"
        )

    await IntegrationService.delete_integration(db, id)
    return None


@router.post(
    "/{org_id}/integrations/{id}/test",
    summary="Test integration connection",
    response_model=Dict[str, Any],
)
async def test_integration_connection(
    org_id: str,
    id: str,
    context: SecurityContext = Depends(
        require_permission(Permission.ORGANIZATIONS_WRITE)
    ),
    db: AsyncSession = Depends(get_db_session),
):
    existing = await IntegrationService.get_integration(db, id)
    if not existing or existing.organization_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Integration not found"
        )

    return await IntegrationService.test_connection(db, id)


@router.post(
    "/{org_id}/integrations/{id}/rotate-secret",
    summary="Rotate integration secret credential",
    response_model=IntegrationResponse,
)
async def rotate_integration_secret(
    org_id: str,
    id: str,
    payload: IntegrationRotateSecretRequest,
    context: SecurityContext = Depends(
        require_permission(Permission.ORGANIZATIONS_WRITE)
    ),
    db: AsyncSession = Depends(get_db_session),
):
    existing = await IntegrationService.get_integration(db, id)
    if not existing or existing.organization_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Integration not found"
        )

    updated = await IntegrationService.rotate_secret(
        db,
        id,
        payload.new_secret,
        user_id=context.user.id if context.user else None,
    )
    return _format_integration_response(updated)


@router.get(
    "/{org_id}/integrations/{id}/health",
    summary="Get operational health metrics",
    response_model=IntegrationRuntimeStateResponse,
)
async def get_integration_health(
    org_id: str,
    id: str,
    context: SecurityContext = Depends(
        require_permission(Permission.ORGANIZATIONS_READ)
    ),
    db: AsyncSession = Depends(get_db_session),
):
    existing = await IntegrationService.get_integration(db, id)
    if not existing or existing.organization_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Integration not found"
        )

    if not existing.runtime_state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Runtime state not initialized",
        )

    return IntegrationRuntimeStateResponse.model_validate(existing.runtime_state)
