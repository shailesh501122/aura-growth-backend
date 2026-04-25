"""
User model – supports both email/password and Google OAuth registration.
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin


class User(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "users"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    password: Mapped[str | None] = mapped_column(String(255), nullable=True)
    google_id: Mapped[str | None] = mapped_column(
        String(255), unique=True, nullable=True, index=True
    )
    role: Mapped[str] = mapped_column(
        String(20), nullable=False, default="user", server_default="user"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # ── Relationships ────────────────────────────────────────────────────
    gmail_accounts = relationship(
        "GmailAccount", back_populates="user", cascade="all, delete-orphan"
    )
    instagram_accounts = relationship(
        "InstagramAccount", back_populates="user", cascade="all, delete-orphan"
    )
    automations = relationship(
        "Automation", back_populates="user", cascade="all, delete-orphan"
    )
    bio_pages = relationship(
        "BioPage", back_populates="user", cascade="all, delete-orphan"
    )
    subscription = relationship(
        "UserSubscription", back_populates="user", uselist=False
    )
    usage_records = relationship(
        "UsageTracking", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User {self.email}>"
