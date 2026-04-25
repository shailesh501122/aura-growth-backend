"""
Automation service – CRUD and execution engine for email + Instagram automations.
"""

import logging
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.automation import Automation, AutomationLog, AutomationRule

logger = logging.getLogger("auragrowth")


async def create_automation(
    db: AsyncSession, user_id: uuid.UUID, data: dict
) -> Automation:
    automation = Automation(
        user_id=user_id,
        name=data["name"],
        description=data.get("description"),
        type=data["type"],
        trigger_config=data.get("trigger_config"),
        action_config=data.get("action_config"),
        is_active=True,
    )
    db.add(automation)
    await db.flush()

    for rule_data in data.get("rules", []):
        rule = AutomationRule(
            automation_id=automation.id,
            condition_type=rule_data["condition_type"],
            condition_value=rule_data["condition_value"],
            case_sensitive=rule_data.get("case_sensitive", False),
        )
        db.add(rule)
    await db.flush()

    result = await db.execute(
        select(Automation).options(selectinload(Automation.rules)).where(Automation.id == automation.id)
    )
    return result.scalar_one()


async def get_automation(db: AsyncSession, automation_id: uuid.UUID, user_id: uuid.UUID) -> Automation:
    result = await db.execute(
        select(Automation).options(selectinload(Automation.rules)).where(Automation.id == automation_id)
    )
    automation = result.scalar_one_or_none()
    if not automation:
        raise NotFoundError("Automation")
    if automation.user_id != user_id:
        raise ForbiddenError("Not your automation")
    return automation


async def list_automations(db: AsyncSession, user_id: uuid.UUID) -> list[Automation]:
    result = await db.execute(
        select(Automation).options(selectinload(Automation.rules))
        .where(Automation.user_id == user_id)
        .order_by(Automation.created_at.desc())
    )
    return list(result.scalars().all())


async def update_automation(db: AsyncSession, automation_id: uuid.UUID, user_id: uuid.UUID, data: dict) -> Automation:
    automation = await get_automation(db, automation_id, user_id)
    for field in ["name", "description", "is_active", "trigger_config", "action_config"]:
        if field in data and data[field] is not None:
            setattr(automation, field, data[field])

    if "rules" in data and data["rules"] is not None:
        # Replace rules
        for rule in automation.rules:
            await db.delete(rule)
        await db.flush()
        for rule_data in data["rules"]:
            rule = AutomationRule(
                automation_id=automation.id,
                condition_type=rule_data["condition_type"],
                condition_value=rule_data["condition_value"],
                case_sensitive=rule_data.get("case_sensitive", False),
            )
            db.add(rule)

    await db.flush()
    result = await db.execute(
        select(Automation).options(selectinload(Automation.rules)).where(Automation.id == automation.id)
    )
    return result.scalar_one()


async def delete_automation(db: AsyncSession, automation_id: uuid.UUID, user_id: uuid.UUID) -> None:
    automation = await get_automation(db, automation_id, user_id)
    await db.delete(automation)
    await db.flush()


async def toggle_automation(db: AsyncSession, automation_id: uuid.UUID, user_id: uuid.UUID) -> Automation:
    automation = await get_automation(db, automation_id, user_id)
    automation.is_active = not automation.is_active
    await db.flush()
    return automation


async def get_automation_logs(db: AsyncSession, automation_id: uuid.UUID, user_id: uuid.UUID, page: int = 1, page_size: int = 20):
    await get_automation(db, automation_id, user_id)  # Auth check
    query = select(AutomationLog).where(AutomationLog.automation_id == automation_id).order_by(AutomationLog.created_at.desc())
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    logs = list((await db.execute(query.offset((page - 1) * page_size).limit(page_size))).scalars().all())
    return logs, total
