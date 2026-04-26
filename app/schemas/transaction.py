"""
Transaction schemas – payment and revenue responses.
"""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class TransactionResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    subscription_id: uuid.UUID | None = None
    amount: float
    currency: str
    type: str
    status: str
    payment_method: str | None = None
    stripe_payment_id: str | None = None
    description: str | None = None
    metadata_json: dict[str, Any] | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class TransactionListResponse(BaseModel):
    success: bool = True
    data: list[TransactionResponse]
    total: int
    page: int
    page_size: int
