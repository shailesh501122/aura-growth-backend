"""
Conversation schemas – unified inbox responses.
"""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class MessageResponse(BaseModel):
    id: uuid.UUID
    conversation_id: uuid.UUID
    direction: str
    content: str | None
    sender: str | None
    status: str
    automation_id: uuid.UUID | None = None
    metadata_json: dict[str, Any] | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    channel: str
    external_id: str | None = None
    subject: str | None = None
    participant: str | None = None
    participant_avatar: str | None = None
    last_message_at: datetime | None = None
    is_read: bool
    metadata_json: dict[str, Any] | None = None
    messages: list[MessageResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ConversationListResponse(BaseModel):
    success: bool = True
    data: list[ConversationResponse]
    total: int
    page: int
    page_size: int


class ConversationReplyRequest(BaseModel):
    content: str
