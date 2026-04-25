"""
Bio page schemas – pages and links CRUD.
"""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class BioLinkCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    url: str = Field(..., min_length=1, max_length=2000)
    icon: str | None = None
    position: int = 0


class BioLinkUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    url: str | None = Field(None, min_length=1, max_length=2000)
    icon: str | None = None
    position: int | None = None
    is_active: bool | None = None


class BioLinkResponse(BaseModel):
    id: uuid.UUID
    title: str
    url: str
    icon: str | None
    position: int
    click_count: int
    is_active: bool

    model_config = {"from_attributes": True}


class BioPageCreate(BaseModel):
    slug: str = Field(..., min_length=1, max_length=100, pattern=r"^[a-z0-9\-]+$")
    title: str = Field(..., min_length=1, max_length=255)
    bio: str | None = None
    avatar_url: str | None = None
    theme: dict[str, Any] | None = None
    is_published: bool = False


class BioPageUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    bio: str | None = None
    avatar_url: str | None = None
    theme: dict[str, Any] | None = None
    is_published: bool | None = None


class BioPageResponse(BaseModel):
    id: uuid.UUID
    slug: str
    title: str
    bio: str | None
    avatar_url: str | None
    theme: dict[str, Any] | None
    is_published: bool
    links: list[BioLinkResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PublicBioPageResponse(BaseModel):
    """Public-facing bio page (no internal IDs exposed)."""
    slug: str
    title: str
    bio: str | None
    avatar_url: str | None
    theme: dict[str, Any] | None
    links: list[BioLinkResponse] = []
