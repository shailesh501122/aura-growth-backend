"""
Conversation models – unified inbox for Gmail threads and Instagram DMs.
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin


class Conversation(Base, UUIDMixin, TimestampMixin):
    """A unified conversation (Gmail thread or Instagram DM thread)."""

    __tablename__ = "conversations"

    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    channel: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # gmail | instagram
    external_id: Mapped[str | None] = mapped_column(
        String(500), nullable=True, index=True
    )  # Gmail thread ID or IG conversation ID
    subject: Mapped[str | None] = mapped_column(String(500), nullable=True)
    participant: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )  # Other party's email or IG username
    participant_avatar: Mapped[str | None] = mapped_column(String(500), nullable=True)
    last_message_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    is_read: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # ── Relationships ────────────────────────────────────────────────────
    messages = relationship(
        "Message", back_populates="conversation", cascade="all, delete-orphan",
        order_by="Message.created_at",
    )

    def __repr__(self) -> str:
        return f"<Conversation {self.channel}:{self.participant}>"


class Message(Base, UUIDMixin):
    """A single message within a conversation."""

    __tablename__ = "messages"

    conversation_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    direction: Mapped[str] = mapped_column(
        String(10), nullable=False
    )  # inbound | outbound
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    sender: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="sent"
    )  # sent | delivered | read | failed
    automation_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("automations.id", ondelete="SET NULL"),
        nullable=True,
    )
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # ── Relationships ────────────────────────────────────────────────────
    conversation = relationship("Conversation", back_populates="messages")

    def __repr__(self) -> str:
        return f"<Message {self.direction} {self.status}>"
