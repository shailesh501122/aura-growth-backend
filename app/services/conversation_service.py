"""
Conversation service – unified inbox for Gmail and Instagram conversations.
"""

import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.conversation import Conversation, Message

logger = logging.getLogger("auragrowth")


async def create_or_get_conversation(
    db: AsyncSession, user_id: uuid.UUID, channel: str,
    external_id: str | None = None, participant: str | None = None,
    subject: str | None = None,
) -> Conversation:
    """Find an existing conversation or create a new one."""
    if external_id:
        result = await db.execute(
            select(Conversation).where(
                Conversation.user_id == user_id,
                Conversation.external_id == external_id,
            )
        )
        conv = result.scalar_one_or_none()
        if conv:
            return conv

    conv = Conversation(
        user_id=user_id,
        channel=channel,
        external_id=external_id,
        participant=participant,
        subject=subject,
        last_message_at=datetime.now(timezone.utc),
    )
    db.add(conv)
    await db.flush()
    return conv


async def add_message(
    db: AsyncSession, conversation_id: uuid.UUID,
    direction: str, content: str, sender: str | None = None,
    status: str = "sent", automation_id: uuid.UUID | None = None,
) -> Message:
    """Add a message to a conversation and update last_message_at."""
    msg = Message(
        conversation_id=conversation_id,
        direction=direction,
        content=content,
        sender=sender,
        status=status,
        automation_id=automation_id,
    )
    db.add(msg)

    # Update conversation timestamp
    result = await db.execute(select(Conversation).where(Conversation.id == conversation_id))
    conv = result.scalar_one_or_none()
    if conv:
        conv.last_message_at = datetime.now(timezone.utc)
        if direction == "inbound":
            conv.is_read = False

    await db.flush()
    return msg


async def list_conversations(
    db: AsyncSession, user_id: uuid.UUID,
    page: int = 1, page_size: int = 20,
    channel_filter: str | None = None,
) -> tuple[list[Conversation], int]:
    """List conversations for a user."""
    query = select(Conversation).where(Conversation.user_id == user_id)
    if channel_filter:
        query = query.where(Conversation.channel == channel_filter)

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    query = query.order_by(Conversation.last_message_at.desc().nullslast()).offset((page - 1) * page_size).limit(page_size)
    convs = list((await db.execute(query)).scalars().all())
    return convs, total


async def get_conversation_messages(
    db: AsyncSession, conversation_id: uuid.UUID, user_id: uuid.UUID,
    page: int = 1, page_size: int = 50,
) -> tuple[list[Message], int]:
    """Get messages for a conversation (with ownership check)."""
    result = await db.execute(select(Conversation).where(Conversation.id == conversation_id))
    conv = result.scalar_one_or_none()
    if not conv:
        raise NotFoundError("Conversation")
    if conv.user_id != user_id:
        raise ForbiddenError("Not your conversation")

    # Mark as read
    conv.is_read = True

    query = select(Message).where(Message.conversation_id == conversation_id)
    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    query = query.order_by(Message.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    messages = list((await db.execute(query)).scalars().all())
    await db.flush()
    return messages, total
