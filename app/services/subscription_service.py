"""
Subscription service – plan management, user subscriptions, and usage tracking.
"""

import logging
import uuid
from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, NotFoundError
from app.models.subscription import Plan, UsageTracking, UserSubscription

logger = logging.getLogger("auragrowth")


async def seed_default_plans(db: AsyncSession) -> None:
    """Seed default plans if none exist."""
    result = await db.execute(select(Plan))
    if result.scalars().first():
        return
    defaults = [
        Plan(name="Free", slug="free", price_monthly=0, emails_per_month=50, dm_automations=1, max_automations=2, max_bio_pages=1, features={"ai_replies": False}),
        Plan(name="Starter", slug="starter", price_monthly=9.99, emails_per_month=500, dm_automations=5, max_automations=10, max_bio_pages=3, features={"ai_replies": True}),
        Plan(name="Pro", slug="pro", price_monthly=29.99, emails_per_month=5000, dm_automations=50, max_automations=50, max_bio_pages=10, features={"ai_replies": True, "priority_support": True}),
        Plan(name="Agency", slug="agency", price_monthly=99.99, emails_per_month=50000, dm_automations=500, max_automations=500, max_bio_pages=100, features={"ai_replies": True, "priority_support": True, "white_label": True}),
    ]
    for p in defaults:
        db.add(p)
    await db.flush()
    logger.info("Default plans seeded")


async def list_plans(db: AsyncSession) -> list[Plan]:
    result = await db.execute(select(Plan).where(Plan.is_active == True).order_by(Plan.price_monthly))
    return list(result.scalars().all())


async def get_plan(db: AsyncSession, plan_id: uuid.UUID) -> Plan:
    result = await db.execute(select(Plan).where(Plan.id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise NotFoundError("Plan")
    return plan


async def subscribe_user(db: AsyncSession, user_id: uuid.UUID, plan_id: uuid.UUID) -> UserSubscription:
    plan = await get_plan(db, plan_id)
    # Check existing subscription
    result = await db.execute(select(UserSubscription).where(UserSubscription.user_id == user_id))
    existing = result.scalar_one_or_none()
    if existing:
        existing.plan_id = plan_id
        existing.status = "active"
        existing.started_at = datetime.now(timezone.utc)
        await db.flush()
        return existing

    sub = UserSubscription(user_id=user_id, plan_id=plan_id, status="active", started_at=datetime.now(timezone.utc))
    db.add(sub)
    await db.flush()
    return sub


async def get_user_subscription(db: AsyncSession, user_id: uuid.UUID) -> UserSubscription | None:
    result = await db.execute(
        select(UserSubscription).where(UserSubscription.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def cancel_subscription(db: AsyncSession, user_id: uuid.UUID) -> UserSubscription:
    result = await db.execute(select(UserSubscription).where(UserSubscription.user_id == user_id))
    sub = result.scalar_one_or_none()
    if not sub:
        raise NotFoundError("Subscription")
    sub.status = "cancelled"
    await db.flush()
    return sub


async def get_usage(db: AsyncSession, user_id: uuid.UUID) -> UsageTracking:
    current_month = date.today().replace(day=1)
    result = await db.execute(
        select(UsageTracking).where(UsageTracking.user_id == user_id, UsageTracking.month == current_month)
    )
    usage = result.scalar_one_or_none()
    if not usage:
        usage = UsageTracking(user_id=user_id, month=current_month)
        db.add(usage)
        await db.flush()
    return usage


async def increment_usage(db: AsyncSession, user_id: uuid.UUID, field: str, amount: int = 1) -> None:
    usage = await get_usage(db, user_id)
    current = getattr(usage, field, 0)
    setattr(usage, field, current + amount)
    await db.flush()
