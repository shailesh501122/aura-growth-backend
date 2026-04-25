"""
Analytics service – dashboard stats, activity logs, and performance metrics.
"""

import logging
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analytics import ClickEvent, DmLog, EmailLog
from app.models.automation import Automation, AutomationLog
from app.models.bio_page import BioLink, BioPage

logger = logging.getLogger("auragrowth")


async def get_dashboard_stats(db: AsyncSession, user_id: uuid.UUID) -> dict:
    emails_sent = (await db.execute(
        select(func.count()).where(EmailLog.user_id == user_id)
    )).scalar() or 0

    dms_sent = (await db.execute(
        select(func.count()).where(DmLog.user_id == user_id)
    )).scalar() or 0

    # Total link clicks across all user's bio pages
    user_links_q = select(BioLink.id).join(BioPage).where(BioPage.user_id == user_id)
    total_clicks = (await db.execute(
        select(func.count()).where(ClickEvent.link_id.in_(user_links_q))
    )).scalar() or 0

    automations_run = (await db.execute(
        select(func.count()).select_from(AutomationLog).join(Automation).where(Automation.user_id == user_id)
    )).scalar() or 0

    active_automations = (await db.execute(
        select(func.count()).where(Automation.user_id == user_id, Automation.is_active == True)
    )).scalar() or 0

    bio_count = (await db.execute(
        select(func.count()).where(BioPage.user_id == user_id)
    )).scalar() or 0

    return {
        "total_emails_sent": emails_sent,
        "total_dms_sent": dms_sent,
        "total_link_clicks": total_clicks,
        "total_automations_run": automations_run,
        "active_automations": active_automations,
        "bio_pages_count": bio_count,
    }


async def get_email_activity(db: AsyncSession, user_id: uuid.UUID, page: int = 1, page_size: int = 20):
    query = select(EmailLog).where(EmailLog.user_id == user_id).order_by(EmailLog.created_at.desc())
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    logs = list((await db.execute(query.offset((page - 1) * page_size).limit(page_size))).scalars().all())
    return logs, total


async def get_dm_activity(db: AsyncSession, user_id: uuid.UUID, page: int = 1, page_size: int = 20):
    query = select(DmLog).where(DmLog.user_id == user_id).order_by(DmLog.created_at.desc())
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    logs = list((await db.execute(query.offset((page - 1) * page_size).limit(page_size))).scalars().all())
    return logs, total


async def get_link_analytics(db: AsyncSession, user_id: uuid.UUID):
    result = await db.execute(
        select(BioLink.id, BioLink.title, BioLink.url, BioLink.click_count)
        .join(BioPage).where(BioPage.user_id == user_id)
        .order_by(BioLink.click_count.desc())
    )
    return [{"link_id": str(r[0]), "title": r[1], "url": r[2], "clicks_total": r[3]} for r in result.all()]


async def get_automation_stats(db: AsyncSession, user_id: uuid.UUID):
    result = await db.execute(
        select(
            Automation.name, Automation.type,
            func.count(AutomationLog.id).label("total_runs"),
            func.count(AutomationLog.id).filter(AutomationLog.status == "success").label("success_count"),
            func.count(AutomationLog.id).filter(AutomationLog.status == "failed").label("failure_count"),
        )
        .outerjoin(AutomationLog)
        .where(Automation.user_id == user_id)
        .group_by(Automation.id, Automation.name, Automation.type)
    )
    return [
        {"automation_name": r[0], "automation_type": r[1], "total_runs": r[2], "success_count": r[3], "failure_count": r[4]}
        for r in result.all()
    ]
