from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, Any, Optional
from datetime import datetime
from database.models.enums import (
    IntegrationProvider,
    IntegrationHealthStatus,
)


class IntegrationCreate(BaseModel):
    provider: IntegrationProvider = Field(..., description="Provider enum")
    name: str = Field(
        ..., min_length=2, max_length=100, description="Friendly display name"
    )
    secret: Optional[str] = Field(
        None, description="Primary secret or webhook URL (encrypted at rest)"
    )
    access_token: Optional[str] = Field(None, description="OAuth Access Token")
    refresh_token: Optional[str] = Field(None, description="OAuth Refresh Token")
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Non-secret metadata JSON"
    )
    is_active: bool = Field(default=True, description="Enable status")


class IntegrationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    secret: Optional[str] = Field(None, description="New secret or webhook URL")
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class IntegrationRotateSecretRequest(BaseModel):
    new_secret: str = Field(..., min_length=1, description="New secret or token value")


class IntegrationRuntimeStateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    health_status: IntegrationHealthStatus
    last_success_at: Optional[datetime] = None
    last_failure_at: Optional[datetime] = None
    consecutive_failures: int = 0
    last_error_message: Optional[str] = None
    next_retry_at: Optional[datetime] = None
    last_probe_duration_ms: Optional[int] = None
    updated_at: datetime


class IntegrationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    provider: IntegrationProvider
    name: str
    credential_version: int
    rotated_at: Optional[datetime] = None
    rotated_by: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    runtime_state: Optional[IntegrationRuntimeStateResponse] = None
