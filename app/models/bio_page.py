"""
Link-in-bio models – bio pages and links with click tracking.
"""

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin


class BioPage(Base, UUIDMixin, TimestampMixin):
    """A user's link-in-bio page."""

    __tablename__ = "bio_pages"

    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    slug: Mapped[str] = mapped_column(
        String(100), unique=True, index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    theme: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    is_published: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )

    # ── Relationships ────────────────────────────────────────────────────
    user = relationship("User", back_populates="bio_pages")
    links = relationship(
        "BioLink", back_populates="page", cascade="all, delete-orphan",
        order_by="BioLink.position",
    )

    def __repr__(self) -> str:
        return f"<BioPage /{self.slug}>"


class BioLink(Base, UUIDMixin, TimestampMixin):
    """A link on a bio page."""

    __tablename__ = "bio_links"

    page_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("bio_pages.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(String(2000), nullable=False)
    icon: Mapped[str | None] = mapped_column(String(100), nullable=True)
    position: Mapped[int] = mapped_column(Integer, default=0)
    click_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

    # ── Relationships ────────────────────────────────────────────────────
    page = relationship("BioPage", back_populates="links")

    def __repr__(self) -> str:
        return f"<BioLink {self.title}>"
