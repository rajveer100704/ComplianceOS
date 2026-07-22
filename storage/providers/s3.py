import logging
from typing import Dict, Any, Optional
from storage.base import StorageProvider

logger = logging.getLogger("storage_s3")


class S3StorageProvider(StorageProvider):
    """AWS S3 Object Storage Provider implementation."""

    def __init__(
        self,
        bucket_name: str,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        region_name: str = "us-east-1",
    ):
        self.bucket_name = bucket_name
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.region_name = region_name
        self._boto_client = None

    def _get_client(self):
        if self._boto_client is None:
            try:
                import boto3
                from botocore.config import Config

                self._boto_client = boto3.client(
                    "s3",
                    aws_access_key_id=self.aws_access_key_id,
                    aws_secret_access_key=self.aws_secret_access_key,
                    region_name=self.region_name,
                    config=Config(signature_version="s3v4"),
                )
            except ImportError:
                logger.warning(
                    "boto3 package not installed. Operating in mock presigned URL mode for S3."
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
                "upload_url": f"https://{self.bucket_name}.s3.{self.region_name}.amazonaws.com/{object_key}?mock_upload_sig=1",
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
            return f"https://{self.bucket_name}.s3.{self.region_name}.amazonaws.com/{object_key}?mock_download_sig=1"

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
            logger.error(f"Failed to delete S3 object '{object_key}': {str(e)}")
            return False
