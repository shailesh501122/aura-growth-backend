"""
Admin API routes – comprehensive admin panel with all modules.
Dashboard, Users, Subscriptions, Revenue, Automations, Gmail/Instagram Activity,
Inbox Monitor, Logs, Support, and System Settings.
"""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, require_admin
from app.models.user import User
from app.schemas.admin import (
    AdminActivityStats,
    AdminAutomationListResponse,
    AdminDashboardStats,
    AdminRevenueStats,
    AdminSubscriptionListResponse,
    AdminUserDetail,
)
from app.schemas.subscription import PlanCreate, PlanResponse, PlanUpdate
from app.schemas.support import (
    TicketListResponse,
    TicketReplyRequest,
    TicketReplyResponse,
    TicketResponse,
    TicketStatusUpdateRequest,
)
from app.schemas.system import (
    ApiLogListResponse,
    ApiLogResponse,
    FeatureFlagResponse,
    SystemSettingResponse,
    SystemSettingUpdateRequest,
    WebhookLogListResponse,
    WebhookLogResponse,
)
from app.schemas.transaction import TransactionListResponse, TransactionResponse
from app.schemas.user import AdminUserUpdate, UserListResponse, UserResponse
from app.services import admin_service, subscription_service, support_service, user_service

router = APIRouter(prefix="/admin", tags=["Admin"])


# ═════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ═════════════════════════════════════════════════════════════════════════

@router.get("/dashboard", response_model=AdminDashboardStats)
async def dashboard_stats(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get comprehensive admin dashboard statistics."""
    return await admin_service.get_dashboard_stats(db)


# Keep legacy /stats endpoint for backward compatibility
@router.get("/stats")
async def platform_stats_legacy(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Legacy stats endpoint – returns same data as /dashboard."""
    stats = await admin_service.get_dashboard_stats(db)
    return {"success": True, "data": stats}


# ═════════════════════════════════════════════════════════════════════════
# USERS
# ═════════════════════════════════════════════════════════════════════════

@router.get("/users", response_model=UserListResponse)
async def list_users(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None),
):
    """List all users with search and pagination."""
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
    """Get a user by ID."""
    user = await user_service.get_user_by_id(db, user_id)
    return UserResponse.model_validate(user)


@router.get("/users/{user_id}/detail", response_model=AdminUserDetail)
async def get_user_detail(
    user_id: uuid.UUID,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get detailed user info including usage, automations, social accounts."""
    return await admin_service.get_user_detail(db, user_id)


@router.put("/users/{user_id}/toggle-active", response_model=UserResponse)
async def toggle_active(
    user_id: uuid.UUID,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Suspend or activate a user."""
    user = await user_service.toggle_user_active(db, user_id)
    return UserResponse.model_validate(user)


@router.put("/users/{user_id}/role", response_model=UserResponse)
async def update_role(
    user_id: uuid.UUID,
    body: AdminUserUpdate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update a user's role (admin/user)."""
    user = await user_service.update_user_role(db, user_id, body.role)
    return UserResponse.model_validate(user)


# ═════════════════════════════════════════════════════════════════════════
# PLANS
# ═════════════════════════════════════════════════════════════════════════

@router.get("/plans", response_model=list[PlanResponse])
async def list_plans(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all subscription plans."""
    plans = await subscription_service.list_plans(db)
    return [PlanResponse.model_validate(p) for p in plans]


@router.post("/plans", response_model=PlanResponse, status_code=201)
async def create_plan(
    body: PlanCreate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create a new subscription plan."""
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
    """Update a subscription plan."""
    plan = await subscription_service.get_plan(db, plan_id)
    for k, v in body.model_dump(exclude_unset=True).items():
        if v is not None:
            setattr(plan, k, v)
    await db.flush()
    return PlanResponse.model_validate(plan)


# ═════════════════════════════════════════════════════════════════════════
# SUBSCRIPTIONS
# ═════════════════════════════════════════════════════════════════════════

@router.get("/subscriptions", response_model=AdminSubscriptionListResponse)
async def list_subscriptions(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = Query(None),
    plan: str | None = Query(None),
):
    """List all user subscriptions with filters."""
    data, total = await admin_service.list_all_subscriptions(
        db, page, page_size, status_filter=status, plan_filter=plan
    )
    return AdminSubscriptionListResponse(
        data=data, total=total, page=page, page_size=page_size,
    )


@router.put("/subscriptions/{subscription_id}/plan")
async def change_subscription_plan(
    subscription_id: uuid.UUID,
    plan_id: uuid.UUID = Query(...),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Change a user's subscription plan (upgrade/downgrade)."""
    from sqlalchemy import select
    from app.models.subscription import UserSubscription
    result = await db.execute(select(UserSubscription).where(UserSubscription.id == subscription_id))
    sub = result.scalar_one_or_none()
    if not sub:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("Subscription")
    plan = await subscription_service.get_plan(db, plan_id)
    sub.plan_id = plan_id
    await db.flush()
    return {"success": True, "message": f"Subscription updated to {plan.name}"}


@router.put("/subscriptions/{subscription_id}/cancel")
async def cancel_subscription_admin(
    subscription_id: uuid.UUID,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Admin: cancel a user's subscription."""
    from sqlalchemy import select
    from app.models.subscription import UserSubscription
    result = await db.execute(select(UserSubscription).where(UserSubscription.id == subscription_id))
    sub = result.scalar_one_or_none()
    if not sub:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("Subscription")
    sub.status = "cancelled"
    await db.flush()
    return {"success": True, "message": "Subscription cancelled"}


# ═════════════════════════════════════════════════════════════════════════
# REVENUE
# ═════════════════════════════════════════════════════════════════════════

@router.get("/revenue", response_model=AdminRevenueStats)
async def revenue_overview(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get revenue overview with MRR, growth, and plan distribution."""
    return await admin_service.get_revenue_stats(db)


@router.get("/transactions", response_model=TransactionListResponse)
async def list_transactions(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = Query(None),
):
    """List all transactions with pagination and filters."""
    rows, total = await admin_service.list_transactions(db, page, page_size, status_filter=status)
    return TransactionListResponse(
        data=[TransactionResponse.model_validate(t) for t in rows],
        total=total, page=page, page_size=page_size,
    )


# ═════════════════════════════════════════════════════════════════════════
# AUTOMATIONS
# ═════════════════════════════════════════════════════════════════════════

@router.get("/automations", response_model=AdminAutomationListResponse)
async def list_automations(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    type: str | None = Query(None),
    active_only: bool = Query(False),
):
    """List all automations across the platform."""
    data, total = await admin_service.list_all_automations(
        db, page, page_size, type_filter=type, active_only=active_only,
    )
    return AdminAutomationListResponse(data=data, total=total, page=page, page_size=page_size)


@router.get("/automations/{automation_id}/logs")
async def get_automation_logs(
    automation_id: uuid.UUID,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """Get execution logs for a specific automation."""
    from sqlalchemy import func, select
    from app.models.automation import AutomationLog
    from app.schemas.automation import AutomationLogResponse

    query = select(AutomationLog).where(AutomationLog.automation_id == automation_id).order_by(AutomationLog.created_at.desc())
    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0
    logs = list((await db.execute(query.offset((page - 1) * page_size).limit(page_size))).scalars().all())
    return {
        "success": True,
        "data": [AutomationLogResponse.model_validate(l) for l in logs],
        "total": total, "page": page, "page_size": page_size,
    }


@router.put("/automations/{automation_id}/toggle")
async def toggle_automation(
    automation_id: uuid.UUID,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Admin force-toggle an automation on/off."""
    auto = await admin_service.admin_toggle_automation(db, automation_id)
    return {"success": True, "is_active": auto.is_active, "message": f"Automation {'activated' if auto.is_active else 'deactivated'}"}


# ═════════════════════════════════════════════════════════════════════════
# GMAIL ACTIVITY
# ═════════════════════════════════════════════════════════════════════════

@router.get("/gmail/activity", response_model=AdminActivityStats)
async def gmail_activity(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Platform-wide Gmail email statistics."""
    return await admin_service.get_gmail_activity(db)


@router.get("/gmail/logs")
async def gmail_logs(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = Query(None),
):
    """Email log entries with status filter."""
    rows, total = await admin_service.list_email_logs(db, page, page_size, status_filter=status)
    return {"success": True, "data": rows, "total": total, "page": page, "page_size": page_size}


# ═════════════════════════════════════════════════════════════════════════
# INSTAGRAM ACTIVITY
# ═════════════════════════════════════════════════════════════════════════

@router.get("/instagram/activity", response_model=AdminActivityStats)
async def instagram_activity(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Platform-wide Instagram DM statistics."""
    return await admin_service.get_instagram_activity(db)


@router.get("/instagram/logs")
async def instagram_logs(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = Query(None),
):
    """DM log entries with status filter."""
    rows, total = await admin_service.list_dm_logs(db, page, page_size, status_filter=status)
    return {"success": True, "data": rows, "total": total, "page": page, "page_size": page_size}


# ═════════════════════════════════════════════════════════════════════════
# INBOX MONITOR
# ═════════════════════════════════════════════════════════════════════════

@router.get("/inbox/conversations")
async def inbox_conversations(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    channel: str | None = Query(None),
):
    """Read-only view of all conversations across the platform."""
    data, total = await admin_service.list_all_conversations(db, page, page_size, channel_filter=channel)
    return {"success": True, "data": data, "total": total, "page": page, "page_size": page_size}


# ═════════════════════════════════════════════════════════════════════════
# LOGS & MONITORING
# ═════════════════════════════════════════════════════════════════════════

@router.get("/logs/api", response_model=ApiLogListResponse)
async def api_logs(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    method: str | None = Query(None),
):
    """API request logs with method filter."""
    rows, total = await admin_service.list_api_logs(db, page, page_size, method_filter=method)
    return ApiLogListResponse(
        data=[ApiLogResponse.model_validate(r) for r in rows],
        total=total, page=page, page_size=page_size,
    )


@router.get("/logs/errors", response_model=ApiLogListResponse)
async def error_logs(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """API error logs (4xx/5xx responses only)."""
    rows, total = await admin_service.list_api_logs(db, page, page_size, min_status=400)
    return ApiLogListResponse(
        data=[ApiLogResponse.model_validate(r) for r in rows],
        total=total, page=page, page_size=page_size,
    )


@router.get("/logs/webhooks", response_model=WebhookLogListResponse)
async def webhook_logs(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    source: str | None = Query(None),
):
    """Webhook processing logs with source filter."""
    rows, total = await admin_service.list_webhook_logs(db, page, page_size, source_filter=source)
    return WebhookLogListResponse(
        data=[WebhookLogResponse.model_validate(r) for r in rows],
        total=total, page=page, page_size=page_size,
    )


# ═════════════════════════════════════════════════════════════════════════
# SUPPORT
# ═════════════════════════════════════════════════════════════════════════

@router.get("/support/tickets", response_model=TicketListResponse)
async def list_support_tickets(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = Query(None),
    priority: str | None = Query(None),
):
    """List all support tickets with filters."""
    tickets, total = await support_service.list_all_tickets(
        db, page, page_size, status_filter=status, priority_filter=priority,
    )
    return TicketListResponse(
        data=[TicketResponse.model_validate(t) for t in tickets],
        total=total, page=page, page_size=page_size,
    )


@router.get("/support/tickets/{ticket_id}", response_model=TicketResponse)
async def get_support_ticket(
    ticket_id: uuid.UUID,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get a support ticket with all replies."""
    ticket = await support_service.get_ticket(db, ticket_id)
    return TicketResponse.model_validate(ticket)


@router.post("/support/tickets/{ticket_id}/reply", response_model=TicketReplyResponse)
async def reply_to_ticket(
    ticket_id: uuid.UUID,
    body: TicketReplyRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Admin reply on a support ticket."""
    reply = await support_service.add_reply(
        db, ticket_id, user_id=admin.id, message=body.message, is_admin=True,
    )
    return TicketReplyResponse.model_validate(reply)


@router.put("/support/tickets/{ticket_id}/status", response_model=TicketResponse)
async def update_ticket_status(
    ticket_id: uuid.UUID,
    body: TicketStatusUpdateRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update a support ticket status."""
    ticket = await support_service.update_ticket_status(db, ticket_id, body.status)
    return TicketResponse.model_validate(ticket)


# ═════════════════════════════════════════════════════════════════════════
# SYSTEM SETTINGS & FEATURE FLAGS
# ═════════════════════════════════════════════════════════════════════════

@router.get("/settings", response_model=list[SystemSettingResponse])
async def list_settings(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    category: str | None = Query(None),
):
    """List all system settings."""
    settings = await admin_service.list_system_settings(db, category=category)
    return [SystemSettingResponse.model_validate(s) for s in settings]


@router.put("/settings/{key}", response_model=SystemSettingResponse)
async def update_setting(
    key: str,
    body: SystemSettingUpdateRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update a system setting value."""
    setting = await admin_service.update_system_setting(db, key, body.value)
    return SystemSettingResponse.model_validate(setting)


@router.get("/settings/features", response_model=list[FeatureFlagResponse])
async def list_feature_flags(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all feature flags."""
    flags = await admin_service.list_feature_flags(db)
    return [FeatureFlagResponse.model_validate(f) for f in flags]


@router.put("/settings/features/{slug}", response_model=FeatureFlagResponse)
async def toggle_feature_flag(
    slug: str,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Toggle a feature flag on/off."""
    flag = await admin_service.toggle_feature_flag(db, slug)
    return FeatureFlagResponse.model_validate(flag)
