"""
Automation models – automations, rules, and execution logs.
Supports both email auto-reply and Instagram DM automation.
"""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin


class Automation(Base, UUIDMixin, TimestampMixin):
    """
    An automation owned by a user.
    Types: email_auto_reply, ig_comment_dm, ig_keyword_dm
    """

    __tablename__ = "automations"

    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # email_auto_reply | ig_comment_dm | ig_keyword_dm
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    trigger_config: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    action_config: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # ── Relationships ────────────────────────────────────────────────────
    user = relationship("User", back_populates="automations")
    rules = relationship(
        "AutomationRule", back_populates="automation", cascade="all, delete-orphan"
    )
    logs = relationship(
        "AutomationLog", back_populates="automation", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Automation {self.name} ({self.type})>"


class AutomationRule(Base, UUIDMixin, TimestampMixin):
    """
    A condition rule attached to an automation.
    Condition types: keyword_subject, keyword_body, sender_match, ig_comment_keyword
    """

    __tablename__ = "automation_rules"

    automation_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("automations.id", ondelete="CASCADE"),
        nullable=False,
    )
    condition_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # keyword_subject | keyword_body | sender_match | ig_comment_keyword
    condition_value: Mapped[str] = mapped_column(String(500), nullable=False)
    case_sensitive: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )

    # ── Relationships ────────────────────────────────────────────────────
    automation = relationship("Automation", back_populates="rules")

    def __repr__(self) -> str:
        return f"<AutomationRule {self.condition_type}: {self.condition_value}>"


class AutomationLog(Base, UUIDMixin):
    """Log entry for each automation execution."""

    __tablename__ = "automation_logs"

    automation_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("automations.id", ondelete="CASCADE"),
        nullable=False,
    )
    trigger_source: Mapped[str | None] = mapped_column(String(500), nullable=True)
    trigger_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    action_taken: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending"
    )  # success | failed | pending
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # ── Relationships ────────────────────────────────────────────────────
    automation = relationship("Automation", back_populates="logs")

    def __repr__(self) -> str:
        return f"<AutomationLog {self.status}>"
