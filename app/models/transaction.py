"""
Transaction model – tracks payments, refunds, and revenue.
"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, UUIDMixin


class Transaction(Base, UUIDMixin):
    """A financial transaction (payment, refund, etc.)."""

    __tablename__ = "transactions"

    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    subscription_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_subscriptions.id", ondelete="SET NULL"),
        nullable=True,
    )
    amount: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False
    )
    currency: Mapped[str] = mapped_column(
        String(3), nullable=False, default="USD"
    )
    type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # payment | refund | credit
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="completed"
    )  # completed | pending | failed
    payment_method: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # stripe | paypal | manual
    stripe_payment_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True, index=True
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<Transaction {self.type} ${self.amount} {self.status}>"
