"""
Analytics schemas – dashboard stats and activity logs.
"""

from datetime import datetime

from pydantic import BaseModel


class DashboardStats(BaseModel):
    total_emails_sent: int = 0
    total_dms_sent: int = 0
    total_link_clicks: int = 0
    total_automations_run: int = 0
    active_automations: int = 0
    bio_pages_count: int = 0


class EmailActivityItem(BaseModel):
    direction: str
    from_email: str | None
    to_email: str | None
    subject: str | None
    status: str
    created_at: datetime


class DmActivityItem(BaseModel):
    recipient_username: str | None
    message_text: str | None
    trigger_type: str | None
    status: str
    created_at: datetime


class LinkClickItem(BaseModel):
    link_title: str | None
    url: str | None
    clicks_today: int = 0
    clicks_total: int = 0


class AutomationStatsItem(BaseModel):
    automation_name: str
    automation_type: str
    total_runs: int = 0
    success_count: int = 0
    failure_count: int = 0


class AnalyticsResponse(BaseModel):
    success: bool = True
    data: DashboardStats | list = []
