import os
import uuid
import logging
from typing import Dict, Any, Optional
from storage.base import StorageProvider
from storage.providers.s3 import S3StorageProvider
from storage.providers.r2 import R2StorageProvider

logger = logging.getLogger("storage_service")


class StorageService:
    """High-level storage service managing tenant-isolated object keys and presigned URL generation."""

    def __init__(self, provider: Optional[StorageProvider] = None):
        if provider is None:
            bucket = os.getenv("STORAGE_BUCKET_NAME", "compliance-os-assets")
            provider_type = os.getenv("STORAGE_PROVIDER", "s3").lower()
            if provider_type == "r2":
                account_id = os.getenv("R2_ACCOUNT_ID", "mock_r2_account")
                provider = R2StorageProvider(bucket_name=bucket, account_id=account_id)
            else:
                provider = S3StorageProvider(bucket_name=bucket)
        self.provider = provider

    @staticmethod
    def build_object_key(organization_id: str, project_id: str, filename: str) -> str:
        """Constructs tenant-isolated storage path: /{org_id}/{project_id}/{uuid}_{filename}."""
        safe_filename = filename.replace(" ", "_")
        unique_prefix = str(uuid.uuid4())[:8]
        return f"{organization_id}/{project_id}/{unique_prefix}_{safe_filename}"

    def create_upload_presigned_url(
        self,
        organization_id: str,
        project_id: str,
        filename: str,
        content_type: str = "application/pdf",
        expires_in: int = 300,
    ) -> Dict[str, Any]:
        """Generates presigned upload URL with tenant-isolated object key."""
        object_key = self.build_object_key(organization_id, project_id, filename)
        return self.provider.generate_presigned_upload_url(
            object_key=object_key,
            content_type=content_type,
            expires_in=expires_in,
        )

    def create_download_presigned_url(
        self, object_key: str, expires_in: int = 3600
    ) -> str:
        """Generates secure presigned download URL."""
        return self.provider.generate_presigned_download_url(
            object_key=object_key, expires_in=expires_in
        )

    def delete_object(self, object_key: str) -> bool:
        """Deletes object from storage."""
        return self.provider.delete_file(object_key)
