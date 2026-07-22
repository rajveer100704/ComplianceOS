import pytest
from storage.providers.s3 import S3StorageProvider
from storage.providers.r2 import R2StorageProvider
from storage.service import StorageService


class TestStorageProviders:
    def test_s3_presigned_urls(self):
        s3 = S3StorageProvider(bucket_name="my-s3-bucket")
        upload_res = s3.generate_presigned_upload_url(
            object_key="org_1/proj_2/spec.pdf", content_type="application/pdf"
        )
        assert "upload_url" in upload_res
        assert "my-s3-bucket" in upload_res["upload_url"]
        assert upload_res["object_key"] == "org_1/proj_2/spec.pdf"

        download_url = s3.generate_presigned_download_url("org_1/proj_2/spec.pdf")
        assert "my-s3-bucket" in download_url

    def test_r2_presigned_urls(self):
        r2 = R2StorageProvider(bucket_name="my-r2-bucket", account_id="acc_123")
        upload_res = r2.generate_presigned_upload_url(
            object_key="org_1/proj_2/report.pdf"
        )
        assert "upload_url" in upload_res
        assert "acc_123.r2.cloudflarestorage.com" in upload_res["upload_url"]

        download_url = r2.generate_presigned_download_url("org_1/proj_2/report.pdf")
        assert "acc_123.r2.cloudflarestorage.com" in download_url

    def test_storage_service_build_object_key(self):
        key = StorageService.build_object_key("org_abc", "proj_xyz", "my design.pdf")
        assert key.startswith("org_abc/proj_xyz/")
        assert "my_design.pdf" in key
