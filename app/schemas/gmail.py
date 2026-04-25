"""
Gmail schemas – account connection and email operations.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class GmailAccountResponse(BaseModel):
    id: uuid.UUID
    email: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class SendEmailRequest(BaseModel):
    to: EmailStr
    subject: str = Field(..., min_length=1, max_length=500)
    body: str = Field(..., min_length=1)
    is_html: bool = False


class EmailResponse(BaseModel):
    id: str
    thread_id: str | None = None
    from_email: str | None = None
    to_email: str | None = None
    subject: str | None = None
    snippet: str | None = None
    body: str | None = None
    date: str | None = None
    is_read: bool = False
    labels: list[str] = []


class EmailListResponse(BaseModel):
    success: bool = True
    data: list[EmailResponse]
    next_page_token: str | None = None
    total_estimate: int = 0
