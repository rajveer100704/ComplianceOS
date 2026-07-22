import logging
from typing import Dict, Any, Optional
from storage.base import StorageProvider

logger = logging.getLogger("storage_r2")


class R2StorageProvider(StorageProvider):
    """Cloudflare R2 S3-Compatible Object Storage Provider implementation."""

    def __init__(
        self,
        bucket_name: str,
        account_id: str,
        access_key_id: Optional[str] = None,
        secret_access_key: Optional[str] = None,
    ):
        self.bucket_name = bucket_name
        self.account_id = account_id
        self.access_key_id = access_key_id
        self.secret_access_key = secret_access_key
        self.endpoint_url = f"https://{account_id}.r2.cloudflarestorage.com"
        self._boto_client = None

    def _get_client(self):
        if self._boto_client is None:
            try:
                import boto3
                from botocore.config import Config

                self._boto_client = boto3.client(
                    "s3",
                    endpoint_url=self.endpoint_url,
                    aws_access_key_id=self.access_key_id,
                    aws_secret_access_key=self.secret_access_key,
                    region_name="auto",
                    config=Config(signature_version="s3v4"),
                )
            except ImportError:
                logger.warning(
                    "boto3 package not installed. Operating in mock presigned URL mode for R2."
                )
                self._boto_client = "MOCK"
        return self._boto_client

    def generate_presigned_upload_url(
        self,
        object_key: str,
        content_type: str = "application/pdf",
        expires_in: int = 300,
    ) -> Dict[str, Any]:
        client = self._get_client()
        if client == "MOCK":
            return {
                "upload_url": f"{self.endpoint_url}/{self.bucket_name}/{object_key}?mock_r2_upload_sig=1",
                "object_key": object_key,
                "expires_in": expires_in,
                "headers": {"Content-Type": content_type},
            }

        url = client.generate_presigned_url(
            ClientMethod="put_object",
            Params={
                "Bucket": self.bucket_name,
                "Key": object_key,
                "ContentType": content_type,
            },
            ExpiresIn=expires_in,
        )
        return {
            "upload_url": url,
            "object_key": object_key,
            "expires_in": expires_in,
            "headers": {"Content-Type": content_type},
        }

    def generate_presigned_download_url(
        self, object_key: str, expires_in: int = 3600
    ) -> str:
        client = self._get_client()
        if client == "MOCK":
            return f"{self.endpoint_url}/{self.bucket_name}/{object_key}?mock_r2_download_sig=1"

        return client.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": self.bucket_name, "Key": object_key},
            ExpiresIn=expires_in,
        )

    def delete_file(self, object_key: str) -> bool:
        client = self._get_client()
        if client == "MOCK":
            return True
        try:
            client.delete_object(Bucket=self.bucket_name, Key=object_key)
            return True
        except Exception as e:
            logger.error(f"Failed to delete R2 object '{object_key}': {str(e)}")
            return False
