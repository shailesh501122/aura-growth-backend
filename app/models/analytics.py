"""
Analytics models – click events, email logs, and DM logs.
"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, UUIDMixin


class ClickEvent(Base, UUIDMixin):
    """Tracks clicks on bio page links."""

    __tablename__ = "click_events"

    link_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("bio_links.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    ip_address: Mapped[str | None] = mapped_column(String(50), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    referrer: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    country: Mapped[str | None] = mapped_column(String(5), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<ClickEvent {self.link_id}>"


class EmailLog(Base, UUIDMixin):
    """Logs email send/receive events."""

    __tablename__ = "email_logs"

    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    direction: Mapped[str] = mapped_column(
        String(10), nullable=False
    )  # inbound | outbound
    from_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    to_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    subject: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="sent"
    )  # sent | failed | received
    automation_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("automations.id", ondelete="SET NULL"),
        nullable=True,
    )
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<EmailLog {self.direction} {self.status}>"


class DmLog(Base, UUIDMixin):
    """Logs Instagram DM events."""

    __tablename__ = "dm_logs"

    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    instagram_account_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("instagram_accounts.id", ondelete="SET NULL"),
        nullable=True,
    )
    recipient_ig_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    recipient_username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    message_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    trigger_type: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # comment_keyword | manual | automation
    trigger_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="sent"
    )  # sent | failed | pending
    automation_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("automations.id", ondelete="SET NULL"),
        nullable=True,
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<DmLog {self.status}>"
