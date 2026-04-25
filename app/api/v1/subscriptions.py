"""
Subscriptions API routes – plans, subscribe, usage tracking.
"""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.subscription import PlanResponse, SubscriptionResponse, UsageResponse
from app.services import subscription_service

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])


@router.get("/plans", response_model=list[PlanResponse])
async def list_plans(db: AsyncSession = Depends(get_db)):
    plans = await subscription_service.list_plans(db)
    return [PlanResponse.model_validate(p) for p in plans]


@router.get("/my-subscription")
async def get_my_subscription(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    sub = await subscription_service.get_user_subscription(db, current_user.id)
    if not sub:
        return {"success": True, "data": None, "message": "No active subscription"}
    # Load plan
    plan = await subscription_service.get_plan(db, sub.plan_id)
    return {
        "success": True,
        "data": {
            "id": str(sub.id),
            "plan": PlanResponse.model_validate(plan).model_dump(),
            "status": sub.status,
            "started_at": sub.started_at.isoformat(),
            "expires_at": sub.expires_at.isoformat() if sub.expires_at else None,
        },
    }


@router.post("/subscribe/{plan_id}")
async def subscribe(
    plan_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    sub = await subscription_service.subscribe_user(db, current_user.id, plan_id)
    return {"success": True, "message": "Subscribed successfully", "subscription_id": str(sub.id)}


@router.post("/cancel")
async def cancel(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await subscription_service.cancel_subscription(db, current_user.id)
    return {"success": True, "message": "Subscription cancelled"}


@router.get("/usage", response_model=UsageResponse)
async def get_usage(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    usage = await subscription_service.get_usage(db, current_user.id)
    sub = await subscription_service.get_user_subscription(db, current_user.id)
    plan = await subscription_service.get_plan(db, sub.plan_id) if sub else None
    return UsageResponse(
        emails_sent=usage.emails_sent,
        emails_limit=plan.emails_per_month if plan else 0,
        dms_sent=usage.dms_sent,
        dms_limit=plan.dm_automations if plan else 0,
        automations_run=usage.automations_run,
        automations_limit=plan.max_automations if plan else 0,
    )
