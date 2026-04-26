"""
Support API – user-facing support ticket system.
"""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.support import (
    TicketCreateRequest,
    TicketListResponse,
    TicketReplyRequest,
    TicketReplyResponse,
    TicketResponse,
)
from app.services import support_service

router = APIRouter(prefix="/support", tags=["Support"])


@router.post("/tickets", response_model=TicketResponse, status_code=201)
async def create_ticket(
    body: TicketCreateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new support ticket."""
    ticket = await support_service.create_ticket(
        db, user_id=user.id,
        subject=body.subject,
        description=body.description,
        priority=body.priority,
        category=body.category,
    )
    return TicketResponse.model_validate(ticket)


@router.get("/tickets", response_model=TicketListResponse)
async def list_my_tickets(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """List the current user's support tickets."""
    tickets, total = await support_service.list_user_tickets(db, user.id, page, page_size)
    return TicketListResponse(
        data=[TicketResponse.model_validate(t) for t in tickets],
        total=total, page=page, page_size=page_size,
    )


@router.get("/tickets/{ticket_id}", response_model=TicketResponse)
async def get_my_ticket(
    ticket_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific ticket (with ownership check)."""
    ticket = await support_service.get_ticket(db, ticket_id, user_id=user.id)
    return TicketResponse.model_validate(ticket)


@router.post("/tickets/{ticket_id}/reply", response_model=TicketReplyResponse)
async def reply_to_ticket(
    ticket_id: uuid.UUID,
    body: TicketReplyRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Reply to a support ticket as a user."""
    # Verify ownership first
    await support_service.get_ticket(db, ticket_id, user_id=user.id)
    reply = await support_service.add_reply(
        db, ticket_id, user_id=user.id, message=body.message, is_admin=False,
    )
    return TicketReplyResponse.model_validate(reply)
