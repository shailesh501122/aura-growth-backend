"""
Support schemas – tickets and replies.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class TicketCreateRequest(BaseModel):
    subject: str = Field(..., min_length=1, max_length=500)
    description: str = Field(..., min_length=1)
    priority: str = Field(default="medium", pattern=r"^(low|medium|high|urgent)$")
    category: str | None = Field(default="general", pattern=r"^(billing|technical|account|general)$")


class TicketReplyRequest(BaseModel):
    message: str = Field(..., min_length=1)


class TicketStatusUpdateRequest(BaseModel):
    status: str = Field(..., pattern=r"^(open|in_progress|resolved|closed)$")


class TicketReplyResponse(BaseModel):
    id: uuid.UUID
    ticket_id: uuid.UUID
    user_id: uuid.UUID
    message: str
    is_admin_reply: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TicketResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    subject: str
    description: str
    status: str
    priority: str
    category: str | None = None
    assigned_to: uuid.UUID | None = None
    replies: list[TicketReplyResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TicketListResponse(BaseModel):
    success: bool = True
    data: list[TicketResponse]
    total: int
    page: int
    page_size: int
