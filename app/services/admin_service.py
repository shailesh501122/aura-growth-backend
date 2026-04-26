"""
Admin service – comprehensive admin business logic for all dashboard modules.
"""

import logging
import uuid
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func, select, and_, case
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundError
from app.models.analytics import ClickEvent, DmLog, EmailLog
from app.models.automation import Automation, AutomationLog
from app.models.bio_page import BioPage
from app.models.conversation import Conversation, Message
from app.models.gmail_account import GmailAccount
from app.models.instagram_account import InstagramAccount
from app.models.subscription import Plan, UserSubscription, UsageTracking
from app.models.support import SupportTicket, TicketReply
from app.models.system import ApiLog, FeatureFlag, SystemSetting, WebhookLog
from app.models.transaction import Transaction
from app.models.user import User

logger = logging.getLogger("auragrowth")


# ── Dashboard ────────────────────────────────────────────────────────────

async def get_dashboard_stats(db: AsyncSession) -> dict:
    """Get comprehensive platform statistics for the admin dashboard."""
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=today_start.weekday())
    month_start = today_start.replace(day=1)

    total_users = (await db.execute(select(func.count(User.id)))).scalar() or 0
    active_users = (await db.execute(
        select(func.count(User.id)).where(User.is_active == True)
    )).scalar() or 0
    new_today = (await db.execute(
        select(func.count(User.id)).where(User.created_at >= today_start)
    )).scalar() or 0
    new_week = (await db.execute(
        select(func.count(User.id)).where(User.created_at >= week_start)
    )).scalar() or 0
    new_month = (await db.execute(
        select(func.count(User.id)).where(User.created_at >= month_start)
    )).scalar() or 0

    # Subscriptions
    total_subs = (await db.execute(select(func.count(UserSubscription.id)))).scalar() or 0
    active_subs = (await db.execute(
        select(func.count(UserSubscription.id)).where(UserSubscription.status == "active")
    )).scalar() or 0

    # MRR: sum of monthly prices for all active subscriptions
    mrr_result = await db.execute(
        select(func.coalesce(func.sum(Plan.price_monthly), 0))
        .select_from(UserSubscription)
        .join(Plan, UserSubscription.plan_id == Plan.id)
        .where(UserSubscription.status == "active")
    )
    mrr = float(mrr_result.scalar() or 0)

    # Revenue
    total_revenue = float((await db.execute(
        select(func.coalesce(func.sum(Transaction.amount), 0))
        .where(Transaction.status == "completed")
    )).scalar() or 0)

    # Activity counts
    total_emails = (await db.execute(select(func.count(EmailLog.id)))).scalar() or 0
    total_dms = (await db.execute(select(func.count(DmLog.id)))).scalar() or 0

    # Automations
    total_automations = (await db.execute(select(func.count(Automation.id)))).scalar() or 0
    active_automations = (await db.execute(
        select(func.count(Automation.id)).where(Automation.is_active == True)
    )).scalar() or 0

    # Bio pages
    total_bio = (await db.execute(select(func.count(BioPage.id)))).scalar() or 0

    # Support
    total_tickets = (await db.execute(select(func.count(SupportTicket.id)))).scalar() or 0
    open_tickets = (await db.execute(
        select(func.count(SupportTicket.id)).where(SupportTicket.status.in_(["open", "in_progress"]))
    )).scalar() or 0

    return {
        "total_users": total_users,
        "active_users": active_users,
        "new_users_today": new_today,
        "new_users_this_week": new_week,
        "new_users_this_month": new_month,
        "total_subscriptions": total_subs,
        "active_subscriptions": active_subs,
        "mrr": mrr,
        "total_revenue": total_revenue,
        "total_emails_sent": total_emails,
        "total_dms_sent": total_dms,
        "total_automations": total_automations,
        "active_automations": active_automations,
        "total_bio_pages": total_bio,
        "total_support_tickets": total_tickets,
        "open_tickets": open_tickets,
    }


# ── User Detail ──────────────────────────────────────────────────────────

async def get_user_detail(db: AsyncSession, user_id: uuid.UUID) -> dict:
    """Get comprehensive user detail for admin panel."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundError("User")

    # Subscription
    sub_result = await db.execute(
        select(UserSubscription).options(selectinload(UserSubscription.plan))
        .where(UserSubscription.user_id == user_id)
    )
    sub = sub_result.scalar_one_or_none()

    # Counts
    total_auto = (await db.execute(
        select(func.count(Automation.id)).where(Automation.user_id == user_id)
    )).scalar() or 0
    active_auto = (await db.execute(
        select(func.count(Automation.id)).where(Automation.user_id == user_id, Automation.is_active == True)
    )).scalar() or 0
    emails = (await db.execute(
        select(func.count(EmailLog.id)).where(EmailLog.user_id == user_id)
    )).scalar() or 0
    dms = (await db.execute(
        select(func.count(DmLog.id)).where(DmLog.user_id == user_id)
    )).scalar() or 0
    bios = (await db.execute(
        select(func.count(BioPage.id)).where(BioPage.user_id == user_id)
    )).scalar() or 0
    gmail = (await db.execute(
        select(func.count(GmailAccount.id)).where(GmailAccount.user_id == user_id, GmailAccount.is_active == True)
    )).scalar() or 0
    ig = (await db.execute(
        select(func.count(InstagramAccount.id)).where(InstagramAccount.user_id == user_id, InstagramAccount.is_active == True)
    )).scalar() or 0

    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active,
        "avatar_url": user.avatar_url,
        "google_id": user.google_id,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
        "subscription_plan": sub.plan.name if sub and sub.plan else None,
        "subscription_status": sub.status if sub else None,
        "total_automations": total_auto,
        "active_automations": active_auto,
        "total_emails_sent": emails,
        "total_dms_sent": dms,
        "bio_pages_count": bios,
        "gmail_connected": gmail > 0,
        "instagram_connected": ig > 0,
    }


# ── Subscriptions ────────────────────────────────────────────────────────

async def list_all_subscriptions(
    db: AsyncSession, page: int = 1, page_size: int = 20,
    status_filter: str | None = None, plan_filter: str | None = None,
) -> tuple[list[dict], int]:
    """List all subscriptions with user and plan details."""
    query = (
        select(UserSubscription, User.name, User.email, Plan.name, Plan.slug, Plan.price_monthly)
        .join(User, UserSubscription.user_id == User.id)
        .join(Plan, UserSubscription.plan_id == Plan.id)
    )
    if status_filter:
        query = query.where(UserSubscription.status == status_filter)
    if plan_filter:
        query = query.where(Plan.slug == plan_filter)

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    query = query.order_by(UserSubscription.started_at.desc()).offset((page - 1) * page_size).limit(page_size)
    rows = (await db.execute(query)).all()

    data = []
    for sub, user_name, user_email, plan_name, plan_slug, plan_price in rows:
        data.append({
            "id": sub.id,
            "user_id": sub.user_id,
            "user_name": user_name,
            "user_email": user_email,
            "plan_name": plan_name,
            "plan_slug": plan_slug,
            "plan_price": float(plan_price),
            "status": sub.status,
            "started_at": sub.started_at,
            "expires_at": sub.expires_at,
        })
    return data, total


# ── Revenue ──────────────────────────────────────────────────────────────

async def get_revenue_stats(db: AsyncSession) -> dict:
    """Get comprehensive revenue statistics."""
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_month_start = (month_start - timedelta(days=1)).replace(day=1)

    total_revenue = float((await db.execute(
        select(func.coalesce(func.sum(Transaction.amount), 0))
        .where(Transaction.status == "completed", Transaction.type == "payment")
    )).scalar() or 0)

    revenue_this_month = float((await db.execute(
        select(func.coalesce(func.sum(Transaction.amount), 0))
        .where(Transaction.status == "completed", Transaction.type == "payment", Transaction.created_at >= month_start)
    )).scalar() or 0)

    revenue_last_month = float((await db.execute(
        select(func.coalesce(func.sum(Transaction.amount), 0))
        .where(
            Transaction.status == "completed", Transaction.type == "payment",
            Transaction.created_at >= last_month_start, Transaction.created_at < month_start,
        )
    )).scalar() or 0)

    mrr_result = await db.execute(
        select(func.coalesce(func.sum(Plan.price_monthly), 0))
        .select_from(UserSubscription)
        .join(Plan, UserSubscription.plan_id == Plan.id)
        .where(UserSubscription.status == "active")
    )
    mrr = float(mrr_result.scalar() or 0)

    growth = 0.0
    if revenue_last_month > 0:
        growth = round(((revenue_this_month - revenue_last_month) / revenue_last_month) * 100, 1)

    total_txns = (await db.execute(select(func.count(Transaction.id)))).scalar() or 0

    # Plan distribution
    plan_dist_result = await db.execute(
        select(Plan.name, Plan.slug, func.count(UserSubscription.id))
        .select_from(UserSubscription)
        .join(Plan, UserSubscription.plan_id == Plan.id)
        .where(UserSubscription.status == "active")
        .group_by(Plan.name, Plan.slug)
    )
    plan_distribution = [
        {"plan": name, "slug": slug, "count": count}
        for name, slug, count in plan_dist_result.all()
    ]

    return {
        "total_revenue": total_revenue,
        "mrr": mrr,
        "revenue_this_month": revenue_this_month,
        "revenue_last_month": revenue_last_month,
        "revenue_growth_pct": growth,
        "total_transactions": total_txns,
        "plan_distribution": plan_distribution,
    }


async def list_transactions(
    db: AsyncSession, page: int = 1, page_size: int = 20,
    status_filter: str | None = None,
) -> tuple[list, int]:
    """List all transactions with pagination."""
    query = select(Transaction).order_by(Transaction.created_at.desc())
    if status_filter:
        query = query.where(Transaction.status == status_filter)

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0
    rows = list((await db.execute(
        query.offset((page - 1) * page_size).limit(page_size)
    )).scalars().all())
    return rows, total


# ── Automations ──────────────────────────────────────────────────────────

async def list_all_automations(
    db: AsyncSession, page: int = 1, page_size: int = 20,
    type_filter: str | None = None, active_only: bool = False,
) -> tuple[list[dict], int]:
    """List all automations across the platform with user info and stats."""
    base = (
        select(
            Automation.id, Automation.user_id, Automation.name, Automation.type,
            Automation.is_active, Automation.created_at,
            User.email.label("user_email"),
            func.count(AutomationLog.id).label("total_runs"),
            func.count(case((AutomationLog.status == "success", 1))).label("success_count"),
            func.count(case((AutomationLog.status == "failed", 1))).label("failure_count"),
        )
        .join(User, Automation.user_id == User.id)
        .outerjoin(AutomationLog, Automation.id == AutomationLog.automation_id)
        .group_by(Automation.id, User.email)
    )
    if type_filter:
        base = base.where(Automation.type == type_filter)
    if active_only:
        base = base.where(Automation.is_active == True)

    count_q = select(func.count()).select_from(
        select(Automation.id).join(User, Automation.user_id == User.id)
        .where(*([Automation.type == type_filter] if type_filter else []))
        .where(*([Automation.is_active == True] if active_only else []))
        .subquery()
    )
    total = (await db.execute(count_q)).scalar() or 0

    base = base.order_by(Automation.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    rows = (await db.execute(base)).all()

    data = []
    for row in rows:
        data.append({
            "id": row.id,
            "user_id": row.user_id,
            "user_email": row.user_email,
            "name": row.name,
            "type": row.type,
            "is_active": row.is_active,
            "total_runs": row.total_runs,
            "success_count": row.success_count,
            "failure_count": row.failure_count,
            "created_at": row.created_at,
        })
    return data, total


async def admin_toggle_automation(db: AsyncSession, automation_id: uuid.UUID) -> Automation:
    """Admin force-toggle an automation."""
    result = await db.execute(select(Automation).where(Automation.id == automation_id))
    auto = result.scalar_one_or_none()
    if not auto:
        raise NotFoundError("Automation")
    auto.is_active = not auto.is_active
    await db.flush()
    return auto


# ── Gmail Activity ───────────────────────────────────────────────────────

async def get_gmail_activity(db: AsyncSession) -> dict:
    """Platform-wide Gmail email statistics."""
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=today_start.weekday())
    month_start = today_start.replace(day=1)

    total = (await db.execute(select(func.count(EmailLog.id)))).scalar() or 0
    sent = (await db.execute(select(func.count(EmailLog.id)).where(EmailLog.status == "sent"))).scalar() or 0
    failed = (await db.execute(select(func.count(EmailLog.id)).where(EmailLog.status == "failed"))).scalar() or 0
    today = (await db.execute(select(func.count(EmailLog.id)).where(EmailLog.created_at >= today_start))).scalar() or 0
    week = (await db.execute(select(func.count(EmailLog.id)).where(EmailLog.created_at >= week_start))).scalar() or 0
    month = (await db.execute(select(func.count(EmailLog.id)).where(EmailLog.created_at >= month_start))).scalar() or 0

    return {
        "total_count": total, "success_count": sent, "failed_count": failed,
        "today_count": today, "this_week_count": week, "this_month_count": month,
    }


async def list_email_logs(
    db: AsyncSession, page: int = 1, page_size: int = 20,
    status_filter: str | None = None,
) -> tuple[list, int]:
    query = select(EmailLog).order_by(EmailLog.created_at.desc())
    if status_filter:
        query = query.where(EmailLog.status == status_filter)
    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0
    rows = list((await db.execute(query.offset((page - 1) * page_size).limit(page_size))).scalars().all())
    return rows, total


# ── Instagram Activity ───────────────────────────────────────────────────

async def get_instagram_activity(db: AsyncSession) -> dict:
    """Platform-wide Instagram DM statistics."""
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=today_start.weekday())
    month_start = today_start.replace(day=1)

    total = (await db.execute(select(func.count(DmLog.id)))).scalar() or 0
    sent = (await db.execute(select(func.count(DmLog.id)).where(DmLog.status == "sent"))).scalar() or 0
    failed = (await db.execute(select(func.count(DmLog.id)).where(DmLog.status == "failed"))).scalar() or 0
    today = (await db.execute(select(func.count(DmLog.id)).where(DmLog.created_at >= today_start))).scalar() or 0
    week = (await db.execute(select(func.count(DmLog.id)).where(DmLog.created_at >= week_start))).scalar() or 0
    month = (await db.execute(select(func.count(DmLog.id)).where(DmLog.created_at >= month_start))).scalar() or 0

    return {
        "total_count": total, "success_count": sent, "failed_count": failed,
        "today_count": today, "this_week_count": week, "this_month_count": month,
    }


async def list_dm_logs(
    db: AsyncSession, page: int = 1, page_size: int = 20,
    status_filter: str | None = None,
) -> tuple[list, int]:
    query = select(DmLog).order_by(DmLog.created_at.desc())
    if status_filter:
        query = query.where(DmLog.status == status_filter)
    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0
    rows = list((await db.execute(query.offset((page - 1) * page_size).limit(page_size))).scalars().all())
    return rows, total


# ── Inbox Monitor ────────────────────────────────────────────────────────

async def list_all_conversations(
    db: AsyncSession, page: int = 1, page_size: int = 20,
    channel_filter: str | None = None,
) -> tuple[list[dict], int]:
    """Admin read-only view of all conversations."""
    base = (
        select(
            Conversation.id, Conversation.user_id, Conversation.channel,
            Conversation.participant, Conversation.subject,
            Conversation.last_message_at, Conversation.is_read,
            User.email.label("user_email"),
            func.count(Message.id).label("message_count"),
        )
        .join(User, Conversation.user_id == User.id)
        .outerjoin(Message, Conversation.id == Message.conversation_id)
        .group_by(Conversation.id, User.email)
    )
    if channel_filter:
        base = base.where(Conversation.channel == channel_filter)

    count_q = select(func.count(Conversation.id))
    if channel_filter:
        count_q = count_q.where(Conversation.channel == channel_filter)
    total = (await db.execute(count_q)).scalar() or 0

    base = base.order_by(Conversation.last_message_at.desc().nullslast()).offset((page - 1) * page_size).limit(page_size)
    rows = (await db.execute(base)).all()

    data = []
    for row in rows:
        data.append({
            "id": row.id,
            "user_id": row.user_id,
            "user_email": row.user_email,
            "channel": row.channel,
            "participant": row.participant,
            "subject": row.subject,
            "last_message_at": row.last_message_at,
            "message_count": row.message_count,
            "is_read": row.is_read,
        })
    return data, total


# ── Logs & Monitoring ────────────────────────────────────────────────────

async def list_api_logs(
    db: AsyncSession, page: int = 1, page_size: int = 20,
    method_filter: str | None = None, min_status: int | None = None,
) -> tuple[list, int]:
    query = select(ApiLog).order_by(ApiLog.created_at.desc())
    if method_filter:
        query = query.where(ApiLog.method == method_filter.upper())
    if min_status:
        query = query.where(ApiLog.status_code >= min_status)
    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0
    rows = list((await db.execute(query.offset((page - 1) * page_size).limit(page_size))).scalars().all())
    return rows, total


async def list_webhook_logs(
    db: AsyncSession, page: int = 1, page_size: int = 20,
    source_filter: str | None = None,
) -> tuple[list, int]:
    query = select(WebhookLog).order_by(WebhookLog.created_at.desc())
    if source_filter:
        query = query.where(WebhookLog.source == source_filter)
    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0
    rows = list((await db.execute(query.offset((page - 1) * page_size).limit(page_size))).scalars().all())
    return rows, total


# ── System Settings & Feature Flags ──────────────────────────────────────

async def list_system_settings(db: AsyncSession, category: str | None = None) -> list:
    query = select(SystemSetting).order_by(SystemSetting.category, SystemSetting.key)
    if category:
        query = query.where(SystemSetting.category == category)
    return list((await db.execute(query)).scalars().all())


async def update_system_setting(db: AsyncSession, key: str, value: str | None) -> SystemSetting:
    result = await db.execute(select(SystemSetting).where(SystemSetting.key == key))
    setting = result.scalar_one_or_none()
    if not setting:
        raise NotFoundError("SystemSetting")
    setting.value = value
    await db.flush()
    return setting


async def list_feature_flags(db: AsyncSession) -> list:
    return list((await db.execute(select(FeatureFlag).order_by(FeatureFlag.slug))).scalars().all())


async def toggle_feature_flag(db: AsyncSession, slug: str) -> FeatureFlag:
    result = await db.execute(select(FeatureFlag).where(FeatureFlag.slug == slug))
    flag = result.scalar_one_or_none()
    if not flag:
        raise NotFoundError("FeatureFlag")
    flag.is_enabled = not flag.is_enabled
    await db.flush()
    return flag


# ── Seed Defaults ────────────────────────────────────────────────────────

async def seed_system_defaults(db: AsyncSession) -> None:
    """Seed default system settings and feature flags if they don't exist."""
    # Feature flags
    existing_flags = (await db.execute(select(func.count(FeatureFlag.id)))).scalar() or 0
    if existing_flags == 0:
        defaults = [
            FeatureFlag(name="AI Email Replies", slug="ai_email_replies", is_enabled=True, description="Enable AI-powered email reply generation"),
            FeatureFlag(name="AI DM Replies", slug="ai_dm_replies", is_enabled=True, description="Enable AI-powered Instagram DM replies"),
            FeatureFlag(name="Instagram Automation", slug="ig_automation", is_enabled=True, description="Enable Instagram DM automation"),
            FeatureFlag(name="Gmail Integration", slug="gmail_integration", is_enabled=True, description="Enable Gmail API integration"),
            FeatureFlag(name="User Registration", slug="user_registration", is_enabled=True, description="Allow new user signups"),
            FeatureFlag(name="Bio Pages", slug="bio_pages", is_enabled=True, description="Enable link-in-bio pages"),
        ]
        for f in defaults:
            db.add(f)
        logger.info("Default feature flags seeded")

    # System settings
    existing_settings = (await db.execute(select(func.count(SystemSetting.id)))).scalar() or 0
    if existing_settings == 0:
        defaults = [
            SystemSetting(key="ig_dm_rate_limit_per_day", value="200", category="rate_limits", description="Max Instagram DMs per user per day"),
            SystemSetting(key="email_rate_limit_per_hour", value="50", category="rate_limits", description="Max emails per user per hour"),
            SystemSetting(key="max_automation_rules", value="20", category="rate_limits", description="Max rules per automation"),
            SystemSetting(key="platform_name", value="AuraGrowth", category="general", description="Platform display name"),
            SystemSetting(key="support_email", value="support@auragrowth.com", category="general", description="Support email address"),
            SystemSetting(key="maintenance_mode", value="false", category="general", description="Enable maintenance mode"),
        ]
        for s in defaults:
            db.add(s)
        logger.info("Default system settings seeded")

    await db.flush()
