"""
Instagram connected account model – stores Meta API tokens for IG operations.
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin


class InstagramAccount(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "instagram_accounts"

    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    instagram_user_id: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )
    username: Mapped[str] = mapped_column(String(255), nullable=False)
    access_token: Mapped[str] = mapped_column(Text, nullable=False)
    token_expiry: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    page_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    page_access_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

    # ── Relationships ────────────────────────────────────────────────────
    user = relationship("User", back_populates="instagram_accounts")

    def __repr__(self) -> str:
        return f"<InstagramAccount @{self.username}>"
