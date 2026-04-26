"""
Support service – user support ticket management.
"""

import logging
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.support import SupportTicket, TicketReply

logger = logging.getLogger("auragrowth")


async def create_ticket(
    db: AsyncSession, user_id: uuid.UUID,
    subject: str, description: str,
    priority: str = "medium", category: str | None = "general",
) -> SupportTicket:
    """Create a new support ticket."""
    ticket = SupportTicket(
        user_id=user_id,
        subject=subject,
        description=description,
        priority=priority,
        category=category,
        status="open",
    )
    db.add(ticket)
    await db.flush()
    logger.info(f"Support ticket created: {ticket.id}")
    return ticket


async def get_ticket(
    db: AsyncSession, ticket_id: uuid.UUID, user_id: uuid.UUID | None = None,
) -> SupportTicket:
    """Get ticket with replies. If user_id is provided, verify ownership."""
    result = await db.execute(
        select(SupportTicket).options(selectinload(SupportTicket.replies))
        .where(SupportTicket.id == ticket_id)
    )
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise NotFoundError("Support ticket")
    if user_id and ticket.user_id != user_id:
        raise ForbiddenError("Not your ticket")
    return ticket


async def list_user_tickets(
    db: AsyncSession, user_id: uuid.UUID,
    page: int = 1, page_size: int = 20,
) -> tuple[list[SupportTicket], int]:
    """List tickets for a specific user."""
    query = select(SupportTicket).where(SupportTicket.user_id == user_id).order_by(SupportTicket.created_at.desc())
    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0
    tickets = list((await db.execute(
        query.options(selectinload(SupportTicket.replies))
        .offset((page - 1) * page_size).limit(page_size)
    )).scalars().all())
    return tickets, total


async def list_all_tickets(
    db: AsyncSession, page: int = 1, page_size: int = 20,
    status_filter: str | None = None, priority_filter: str | None = None,
) -> tuple[list[SupportTicket], int]:
    """Admin: list all tickets with filters."""
    query = select(SupportTicket).order_by(SupportTicket.created_at.desc())
    if status_filter:
        query = query.where(SupportTicket.status == status_filter)
    if priority_filter:
        query = query.where(SupportTicket.priority == priority_filter)

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0
    tickets = list((await db.execute(
        query.options(selectinload(SupportTicket.replies))
        .offset((page - 1) * page_size).limit(page_size)
    )).scalars().all())
    return tickets, total


async def add_reply(
    db: AsyncSession, ticket_id: uuid.UUID, user_id: uuid.UUID,
    message: str, is_admin: bool = False,
) -> TicketReply:
    """Add a reply to a ticket."""
    result = await db.execute(select(SupportTicket).where(SupportTicket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise NotFoundError("Support ticket")

    reply = TicketReply(
        ticket_id=ticket_id,
        user_id=user_id,
        message=message,
        is_admin_reply=is_admin,
    )
    db.add(reply)

    # Auto-update ticket status
    if is_admin and ticket.status == "open":
        ticket.status = "in_progress"

    await db.flush()
    return reply


async def update_ticket_status(
    db: AsyncSession, ticket_id: uuid.UUID, status: str,
) -> SupportTicket:
    """Admin: update ticket status."""
    result = await db.execute(select(SupportTicket).where(SupportTicket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise NotFoundError("Support ticket")
    ticket.status = status
    await db.flush()
    return ticket
