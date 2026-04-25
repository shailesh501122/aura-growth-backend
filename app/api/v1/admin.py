"""
Admin API routes – user management, plan management, logs.
"""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, require_admin
from app.models.user import User
from app.schemas.subscription import PlanCreate, PlanResponse, PlanUpdate
from app.schemas.user import AdminUserUpdate, UserListResponse, UserResponse
from app.services import subscription_service, user_service

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/users", response_model=UserListResponse)
async def list_users(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None),
):
    users, total = await user_service.list_users(db, page, page_size, search)
    total_pages = (total + page_size - 1) // page_size
    return UserListResponse(
        data=[UserResponse.model_validate(u) for u in users],
        total=total, page=page, page_size=page_size, total_pages=total_pages,
    )


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: uuid.UUID,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    user = await user_service.get_user_by_id(db, user_id)
    return UserResponse.model_validate(user)


@router.put("/users/{user_id}/toggle-active", response_model=UserResponse)
async def toggle_active(
    user_id: uuid.UUID,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    user = await user_service.toggle_user_active(db, user_id)
    return UserResponse.model_validate(user)


@router.put("/users/{user_id}/role", response_model=UserResponse)
async def update_role(
    user_id: uuid.UUID,
    body: AdminUserUpdate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    user = await user_service.update_user_role(db, user_id, body.role)
    return UserResponse.model_validate(user)


@router.get("/plans", response_model=list[PlanResponse])
async def list_plans(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    plans = await subscription_service.list_plans(db)
    return [PlanResponse.model_validate(p) for p in plans]


@router.post("/plans", response_model=PlanResponse, status_code=201)
async def create_plan(
    body: PlanCreate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    from app.models.subscription import Plan
    plan = Plan(**body.model_dump())
    db.add(plan)
    await db.flush()
    return PlanResponse.model_validate(plan)


@router.put("/plans/{plan_id}", response_model=PlanResponse)
async def update_plan(
    plan_id: uuid.UUID,
    body: PlanUpdate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    plan = await subscription_service.get_plan(db, plan_id)
    for k, v in body.model_dump(exclude_unset=True).items():
        if v is not None:
            setattr(plan, k, v)
    await db.flush()
    return PlanResponse.model_validate(plan)


@router.get("/stats")
async def platform_stats(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import func, select
    from app.models.automation import Automation, AutomationLog
    from app.models.bio_page import BioPage

    total_users = (await db.execute(select(func.count(User.id)))).scalar() or 0
    active_users = (await db.execute(select(func.count(User.id)).where(User.is_active == True))).scalar() or 0
    total_automations = (await db.execute(select(func.count(Automation.id)))).scalar() or 0
    total_bio_pages = (await db.execute(select(func.count(BioPage.id)))).scalar() or 0
    total_logs = (await db.execute(select(func.count(AutomationLog.id)))).scalar() or 0

    return {
        "success": True,
        "data": {
            "total_users": total_users,
            "active_users": active_users,
            "total_automations": total_automations,
            "total_bio_pages": total_bio_pages,
            "total_automation_logs": total_logs,
        },
    }
