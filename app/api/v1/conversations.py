"""
Conversations API – unified inbox for Gmail and Instagram conversations.
"""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.conversation import (
    ConversationListResponse,
    ConversationReplyRequest,
    ConversationResponse,
    MessageResponse,
)
from app.services import conversation_service

router = APIRouter(prefix="/conversations", tags=["Conversations"])


@router.get("", response_model=ConversationListResponse)
async def list_conversations(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    channel: str | None = Query(None),
):
    """List the current user's conversations."""
    convs, total = await conversation_service.list_conversations(
        db, user.id, page, page_size, channel_filter=channel,
    )
    return ConversationListResponse(
        data=[ConversationResponse.model_validate(c) for c in convs],
        total=total, page=page, page_size=page_size,
    )


@router.get("/{conversation_id}/messages")
async def get_messages(
    conversation_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
):
    """Get messages within a conversation."""
    messages, total = await conversation_service.get_conversation_messages(
        db, conversation_id, user.id, page, page_size,
    )
    return {
        "success": True,
        "data": [MessageResponse.model_validate(m) for m in messages],
        "total": total, "page": page, "page_size": page_size,
    }


@router.post("/{conversation_id}/reply", response_model=MessageResponse)
async def reply_to_conversation(
    conversation_id: uuid.UUID,
    body: ConversationReplyRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Send a manual reply in a conversation."""
    # Verify ownership
    from app.models.conversation import Conversation
    from sqlalchemy import select
    from app.core.exceptions import ForbiddenError, NotFoundError

    result = await db.execute(select(Conversation).where(Conversation.id == conversation_id))
    conv = result.scalar_one_or_none()
    if not conv:
        raise NotFoundError("Conversation")
    if conv.user_id != user.id:
        raise ForbiddenError("Not your conversation")

    msg = await conversation_service.add_message(
        db, conversation_id, direction="outbound",
        content=body.content, sender=user.email, status="sent",
    )
    return MessageResponse.model_validate(msg)
