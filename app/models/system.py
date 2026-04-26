"""
System models – API logs, webhook logs, feature flags, and system settings.
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDMixin


class ApiLog(Base, UUIDMixin):
    """Logs every API request for monitoring and debugging."""

    __tablename__ = "api_logs"

    method: Mapped[str] = mapped_column(String(10), nullable=False)
    path: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    status_code: Mapped[int] = mapped_column(Integer, nullable=False)
    user_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )
    ip_address: Mapped[str | None] = mapped_column(String(50), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    request_body: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    response_summary: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    def __repr__(self) -> str:
        return f"<ApiLog {self.method} {self.path} {self.status_code}>"


class WebhookLog(Base, UUIDMixin):
    """Logs incoming webhook events from Meta, Gmail, Stripe, etc."""

    __tablename__ = "webhook_logs"

    source: Mapped[str] = mapped_column(
        String(30), nullable=False, index=True
    )  # meta | gmail | stripe
    event_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="received"
    )  # received | processed | failed
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<WebhookLog {self.source}:{self.event_type} {self.status}>"


class FeatureFlag(Base, UUIDMixin, TimestampMixin):
    """Feature flags for enabling/disabling platform features."""

    __tablename__ = "feature_flags"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    is_enabled: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true"
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<FeatureFlag {self.slug}: {'ON' if self.is_enabled else 'OFF'}>"


class SystemSetting(Base, UUIDMixin, TimestampMixin):
    """Key-value system configuration settings."""

    __tablename__ = "system_settings"

    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    value: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(
        String(50), nullable=False, default="general"
    )  # general | api_keys | smtp | rate_limits | integrations
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<SystemSetting {self.key}>"
