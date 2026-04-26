"""
Admin schemas – dashboard stats and admin-specific responses.
"""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class AdminDashboardStats(BaseModel):
    """Complete admin dashboard statistics."""
    total_users: int = 0
    active_users: int = 0
    new_users_today: int = 0
    new_users_this_week: int = 0
    new_users_this_month: int = 0
    total_subscriptions: int = 0
    active_subscriptions: int = 0
    mrr: float = 0.0
    total_revenue: float = 0.0
    total_emails_sent: int = 0
    total_dms_sent: int = 0
    total_automations: int = 0
    active_automations: int = 0
    total_bio_pages: int = 0
    total_support_tickets: int = 0
    open_tickets: int = 0


class AdminUserDetail(BaseModel):
    """Detailed user view for admin panel."""
    id: uuid.UUID
    name: str
    email: str
    role: str
    is_active: bool
    avatar_url: str | None = None
    google_id: str | None = None
    created_at: datetime
    updated_at: datetime
    # Aggregated data
    subscription_plan: str | None = None
    subscription_status: str | None = None
    total_automations: int = 0
    active_automations: int = 0
    total_emails_sent: int = 0
    total_dms_sent: int = 0
    bio_pages_count: int = 0
    gmail_connected: bool = False
    instagram_connected: bool = False


class AdminSubscriptionResponse(BaseModel):
    """Admin view of a user's subscription."""
    id: uuid.UUID
    user_id: uuid.UUID
    user_name: str
    user_email: str
    plan_name: str
    plan_slug: str
    plan_price: float
    status: str
    started_at: datetime
    expires_at: datetime | None = None


class AdminSubscriptionListResponse(BaseModel):
    success: bool = True
    data: list[AdminSubscriptionResponse]
    total: int
    page: int
    page_size: int


class AdminRevenueStats(BaseModel):
    """Revenue overview for admin panel."""
    total_revenue: float = 0.0
    mrr: float = 0.0
    revenue_this_month: float = 0.0
    revenue_last_month: float = 0.0
    revenue_growth_pct: float = 0.0
    total_transactions: int = 0
    plan_distribution: list[dict[str, Any]] = []
    monthly_revenue: list[dict[str, Any]] = []


class AdminAutomationOverview(BaseModel):
    """Admin view of an automation."""
    id: uuid.UUID
    user_id: uuid.UUID
    user_email: str
    name: str
    type: str
    is_active: bool
    total_runs: int = 0
    success_count: int = 0
    failure_count: int = 0
    created_at: datetime


class AdminAutomationListResponse(BaseModel):
    success: bool = True
    data: list[AdminAutomationOverview]
    total: int
    page: int
    page_size: int


class AdminActivityStats(BaseModel):
    """Platform-wide activity statistics."""
    total_count: int = 0
    success_count: int = 0
    failed_count: int = 0
    today_count: int = 0
    this_week_count: int = 0
    this_month_count: int = 0


class AdminInboxOverview(BaseModel):
    """Admin view of conversations."""
    id: uuid.UUID
    user_id: uuid.UUID
    user_email: str
    channel: str
    participant: str | None = None
    subject: str | None = None
    last_message_at: datetime | None = None
    message_count: int = 0
    is_read: bool = False
