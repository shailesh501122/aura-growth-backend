"""
Automation schemas – CRUD, rules, and logs.
"""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class AutomationRuleCreate(BaseModel):
    condition_type: str = Field(
        ...,
        description="keyword_subject | keyword_body | sender_match | ig_comment_keyword",
    )
    condition_value: str = Field(..., min_length=1, max_length=500)
    case_sensitive: bool = False


class AutomationRuleResponse(BaseModel):
    id: uuid.UUID
    condition_type: str
    condition_value: str
    case_sensitive: bool

    model_config = {"from_attributes": True}


class AutomationCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    type: str = Field(
        ...,
        description="email_auto_reply | ig_comment_dm | ig_keyword_dm",
    )
    trigger_config: dict[str, Any] | None = None
    action_config: dict[str, Any] | None = None
    rules: list[AutomationRuleCreate] = []


class AutomationUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    is_active: bool | None = None
    trigger_config: dict[str, Any] | None = None
    action_config: dict[str, Any] | None = None
    rules: list[AutomationRuleCreate] | None = None


class AutomationResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    type: str
    is_active: bool
    trigger_config: dict[str, Any] | None
    action_config: dict[str, Any] | None
    rules: list[AutomationRuleResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AutomationLogResponse(BaseModel):
    id: uuid.UUID
    automation_id: uuid.UUID
    trigger_source: str | None
    trigger_data: dict[str, Any] | None
    action_taken: str | None
    status: str
    error_message: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class AutomationListResponse(BaseModel):
    success: bool = True
    data: list[AutomationResponse]
    total: int = 0
