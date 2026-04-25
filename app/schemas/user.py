"""
User schemas – CRUD responses and admin operations.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserResponse(BaseModel):
    id: uuid.UUID
    name: str
    email: str
    role: str
    is_active: bool
    avatar_url: str | None = None
    google_id: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserUpdateRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    avatar_url: str | None = None


class UserListResponse(BaseModel):
    success: bool = True
    data: list[UserResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)


class AdminUserUpdate(BaseModel):
    is_active: bool | None = None
    role: str | None = None
