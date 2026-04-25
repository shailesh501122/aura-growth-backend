"""
Subscription schemas – plans and user subscriptions.
"""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class PlanResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    price_monthly: float
    emails_per_month: int
    dm_automations: int
    max_automations: int
    max_bio_pages: int
    features: dict[str, Any] | None
    is_active: bool

    model_config = {"from_attributes": True}


class PlanCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    slug: str = Field(..., min_length=1, max_length=50, pattern=r"^[a-z0-9\-]+$")
    price_monthly: float = Field(..., ge=0)
    emails_per_month: int = Field(default=100, ge=0)
    dm_automations: int = Field(default=1, ge=0)
    max_automations: int = Field(default=3, ge=0)
    max_bio_pages: int = Field(default=1, ge=0)
    features: dict[str, Any] | None = None


class PlanUpdate(BaseModel):
    name: str | None = None
    price_monthly: float | None = None
    emails_per_month: int | None = None
    dm_automations: int | None = None
    max_automations: int | None = None
    max_bio_pages: int | None = None
    features: dict[str, Any] | None = None
    is_active: bool | None = None


class SubscriptionResponse(BaseModel):
    id: uuid.UUID
    plan: PlanResponse
    status: str
    started_at: datetime
    expires_at: datetime | None

    model_config = {"from_attributes": True}


class UsageResponse(BaseModel):
    emails_sent: int = 0
    emails_limit: int = 0
    dms_sent: int = 0
    dms_limit: int = 0
    automations_run: int = 0
    automations_limit: int = 0
