from abc import ABC, abstractmethod
from typing import Dict, Any


class StorageProvider(ABC):
    """Abstract base contract for Cloud Object Storage infrastructure providers (S3, Cloudflare R2)."""

    @abstractmethod
    def generate_presigned_upload_url(
        self,
        object_key: str,
        content_type: str = "application/pdf",
        expires_in: int = 300,
    ) -> Dict[str, Any]:
        """Generates a presigned URL for direct browser file upload (HTTP PUT)."""
        pass

    @abstractmethod
    def generate_presigned_download_url(
        self, object_key: str, expires_in: int = 3600
    ) -> str:
        """Generates a presigned URL for secure file download (HTTP GET)."""
        pass

    @abstractmethod
    def delete_file(self, object_key: str) -> bool:
        """Deletes an object from cloud storage."""
        pass
