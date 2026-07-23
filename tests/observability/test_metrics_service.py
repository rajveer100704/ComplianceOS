import pytest
from prometheus_client import CollectorRegistry
from observability.metrics import MetricsService


def test_metrics_service_recording_and_exposition():
    """Test MetricsService records events and exports Prometheus exposition format."""
    registry = CollectorRegistry()
    metrics = MetricsService(registry=registry)

    metrics.record_request("POST", "/api/v1/claims/verify", 200, 0.15)
    metrics.record_retrieval("hybrid", 0.08, cache_hit=True)
    metrics.record_document_upload("s3")
    metrics.record_report_generated("pdf")

    content, content_type = metrics.export_metrics()
    text_content = content.decode("utf-8")

    assert "http_requests_total" in text_content
    assert "retrieval_duration_seconds" in text_content
    assert "documents_uploaded_total" in text_content
    assert "reports_generated_total" in text_content
    assert "text/plain" in content_type
