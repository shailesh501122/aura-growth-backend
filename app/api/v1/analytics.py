"""
Analytics API routes – dashboard stats and activity logs.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.analytics import DashboardStats
from app.services import analytics_service

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/dashboard", response_model=DashboardStats)
async def dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stats = await analytics_service.get_dashboard_stats(db, current_user.id)
    return DashboardStats(**stats)


@router.get("/emails")
async def email_activity(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    logs, total = await analytics_service.get_email_activity(db, current_user.id, page, page_size)
    return {"success": True, "data": logs, "total": total, "page": page, "page_size": page_size}


@router.get("/instagram")
async def dm_activity(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    logs, total = await analytics_service.get_dm_activity(db, current_user.id, page, page_size)
    return {"success": True, "data": logs, "total": total, "page": page, "page_size": page_size}


@router.get("/links")
async def link_analytics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = await analytics_service.get_link_analytics(db, current_user.id)
    return {"success": True, "data": data}


@router.get("/automations")
async def automation_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = await analytics_service.get_automation_stats(db, current_user.id)
    return {"success": True, "data": data}
