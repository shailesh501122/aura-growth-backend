"""
Subscription models – plans, user subscriptions, and usage tracking.
"""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin


class Plan(Base, UUIDMixin, TimestampMixin):
    """Subscription plan definition."""

    __tablename__ = "plans"

    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    price_monthly: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False, default=0
    )
    emails_per_month: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    dm_automations: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    max_automations: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    max_bio_pages: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    features: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

    # ── Relationships ────────────────────────────────────────────────────
    subscriptions = relationship("UserSubscription", back_populates="plan")

    def __repr__(self) -> str:
        return f"<Plan {self.name}>"


class UserSubscription(Base, UUIDMixin, TimestampMixin):
    """A user's active subscription."""

    __tablename__ = "user_subscriptions"

    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    plan_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("plans.id", ondelete="RESTRICT"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active"
    )  # active | cancelled | expired
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ── Relationships ────────────────────────────────────────────────────
    user = relationship("User", back_populates="subscription")
    plan = relationship("Plan", back_populates="subscriptions")

    def __repr__(self) -> str:
        return f"<UserSubscription {self.status}>"


class UsageTracking(Base, UUIDMixin):
    """Monthly usage tracking per user for enforcing plan limits."""

    __tablename__ = "usage_tracking"

    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    month: Mapped[datetime] = mapped_column(Date, nullable=False)
    emails_sent: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    dms_sent: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    automations_run: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    # ── Relationships ────────────────────────────────────────────────────
    user = relationship("User", back_populates="usage_records")

    def __repr__(self) -> str:
        return f"<UsageTracking {self.month}>"
