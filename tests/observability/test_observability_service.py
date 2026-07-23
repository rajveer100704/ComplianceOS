import pytest
from fastapi import FastAPI
from observability import ObservabilityService
from config.settings import Settings


def test_observability_service_initialization():
    """Test facade initialization with custom settings."""
    app = FastAPI()
    custom_settings = Settings(
        LOG_LEVEL="DEBUG",
        TRACING_ENABLED=False,
        PROMETHEUS_METRICS_ENABLED=True,
    )
    service = ObservabilityService(custom_settings)
    service.initialize(app)
    assert service.config.LOG_LEVEL == "DEBUG"
