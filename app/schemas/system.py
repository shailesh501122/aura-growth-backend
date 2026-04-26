"""
System schemas – logs, feature flags, and system settings.
"""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ApiLogResponse(BaseModel):
    id: uuid.UUID
    method: str
    path: str
    status_code: int
    user_id: uuid.UUID | None = None
    ip_address: str | None = None
    duration_ms: int | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ApiLogListResponse(BaseModel):
    success: bool = True
    data: list[ApiLogResponse]
    total: int
    page: int
    page_size: int


class WebhookLogResponse(BaseModel):
    id: uuid.UUID
    source: str
    event_type: str | None = None
    payload: dict[str, Any] | None = None
    status: str
    error_message: str | None = None
    processed_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class WebhookLogListResponse(BaseModel):
    success: bool = True
    data: list[WebhookLogResponse]
    total: int
    page: int
    page_size: int


class FeatureFlagResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    is_enabled: bool
    description: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SystemSettingResponse(BaseModel):
    id: uuid.UUID
    key: str
    value: str | None = None
    category: str
    description: str | None = None
    updated_at: datetime

    model_config = {"from_attributes": True}


class SystemSettingUpdateRequest(BaseModel):
    value: str | None = None
