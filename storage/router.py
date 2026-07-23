from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Dict, Any

from auth.dependencies import SecurityContext, require_permission
from auth.enums import Permission
from storage.service import StorageService

router = APIRouter()


class PresignedUploadRequest(BaseModel):
    project_id: str = Field(..., description="Project ID scope")
    filename: str = Field(..., description="Target upload filename")
    content_type: str = Field(
        default="application/pdf", description="MIME content type"
    )
    expires_in: int = Field(
        default=300, ge=60, le=3600, description="Expiration in seconds"
    )


class PresignedDownloadRequest(BaseModel):
    object_key: str = Field(..., description="Storage object key")
    expires_in: int = Field(
        default=3600, ge=60, le=86400, description="Expiration in seconds"
    )


@router.post(
    "/{org_id}/storage/presigned-upload",
    summary="Generate presigned upload URL",
    response_model=Dict[str, Any],
)
async def generate_presigned_upload_url(
    org_id: str,
    payload: PresignedUploadRequest,
    context: SecurityContext = Depends(require_permission(Permission.REPORTS_WRITE)),
):
    """Generates a presigned upload URL for direct browser S3/R2 file upload."""
    if context.organization and context.organization.id != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cross-tenant access forbidden",
        )

    storage_service = StorageService()
    return storage_service.create_upload_presigned_url(
        organization_id=org_id,
        project_id=payload.project_id,
        filename=payload.filename,
        content_type=payload.content_type,
        expires_in=payload.expires_in,
    )


@router.post(
    "/{org_id}/storage/presigned-download",
    summary="Generate presigned download URL",
    response_model=Dict[str, str],
)
async def generate_presigned_download_url(
    org_id: str,
    payload: PresignedDownloadRequest,
    context: SecurityContext = Depends(require_permission(Permission.REPORTS_READ)),
):
    """Generates a presigned download URL for secure S3/R2 file retrieval."""
    if context.organization and context.organization.id != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cross-tenant access forbidden",
        )

    # Ensure object_key starts with the requesting organization_id (tenant boundary enforcement)
    if not payload.object_key.startswith(f"{org_id}/"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant object key mismatch",
        )

    storage_service = StorageService()
    download_url = storage_service.create_download_presigned_url(
        object_key=payload.object_key,
        expires_in=payload.expires_in,
    )
    return {"download_url": download_url, "object_key": payload.object_key}
