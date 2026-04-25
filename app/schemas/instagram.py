"""
Instagram schemas – account connection and DM operations.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class InstagramAccountResponse(BaseModel):
    id: uuid.UUID
    instagram_user_id: str
    username: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class InstagramConnectResponse(BaseModel):
    success: bool = True
    auth_url: str


class SendDmRequest(BaseModel):
    recipient_id: str = Field(..., description="Instagram-scoped user ID")
    message: str = Field(..., min_length=1, max_length=1000)


class WebhookVerification(BaseModel):
    """Meta webhook verification query params."""
    hub_mode: str = Field(..., alias="hub.mode")
    hub_challenge: str = Field(..., alias="hub.challenge")
    hub_verify_token: str = Field(..., alias="hub.verify_token")


class InstagramCommentWebhook(BaseModel):
    """Parsed Instagram comment webhook event."""
    comment_id: str
    comment_text: str
    commenter_id: str
    commenter_username: str | None = None
    media_id: str
    timestamp: int | None = None
