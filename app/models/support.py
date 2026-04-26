"""
Support models – tickets and replies for the support system.
"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin


class SupportTicket(Base, UUIDMixin, TimestampMixin):
    """A user support ticket."""

    __tablename__ = "support_tickets"

    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    subject: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="open"
    )  # open | in_progress | resolved | closed
    priority: Mapped[str] = mapped_column(
        String(20), nullable=False, default="medium"
    )  # low | medium | high | urgent
    category: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # billing | technical | account | general
    assigned_to: Mapped[str | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # ── Relationships ────────────────────────────────────────────────────
    replies = relationship(
        "TicketReply", back_populates="ticket", cascade="all, delete-orphan",
        order_by="TicketReply.created_at",
    )

    def __repr__(self) -> str:
        return f"<SupportTicket {self.status}: {self.subject[:50]}>"


class TicketReply(Base, UUIDMixin):
    """A reply on a support ticket (from user or admin)."""

    __tablename__ = "ticket_replies"

    ticket_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("support_tickets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_admin_reply: Mapped[bool] = mapped_column(
        default=False, server_default="false"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # ── Relationships ────────────────────────────────────────────────────
    ticket = relationship("SupportTicket", back_populates="replies")

    def __repr__(self) -> str:
        return f"<TicketReply {'admin' if self.is_admin_reply else 'user'}>"
