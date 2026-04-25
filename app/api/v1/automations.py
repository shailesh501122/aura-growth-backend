"""
Automations API routes – CRUD for email and Instagram automations.
"""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.automation import (
    AutomationCreate,
    AutomationListResponse,
    AutomationLogResponse,
    AutomationResponse,
    AutomationUpdate,
)
from app.services import automation_service

router = APIRouter(prefix="/automations", tags=["Automations"])


@router.get("/", response_model=AutomationListResponse)
async def list_automations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    automations = await automation_service.list_automations(db, current_user.id)
    return AutomationListResponse(
        data=[AutomationResponse.model_validate(a) for a in automations],
        total=len(automations),
    )


@router.post("/", response_model=AutomationResponse, status_code=201)
async def create_automation(
    body: AutomationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    automation = await automation_service.create_automation(db, current_user.id, body.model_dump())
    return AutomationResponse.model_validate(automation)


@router.get("/{automation_id}", response_model=AutomationResponse)
async def get_automation(
    automation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    automation = await automation_service.get_automation(db, automation_id, current_user.id)
    return AutomationResponse.model_validate(automation)


@router.put("/{automation_id}", response_model=AutomationResponse)
async def update_automation(
    automation_id: uuid.UUID,
    body: AutomationUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    automation = await automation_service.update_automation(
        db, automation_id, current_user.id, body.model_dump(exclude_unset=True)
    )
    return AutomationResponse.model_validate(automation)


@router.delete("/{automation_id}")
async def delete_automation(
    automation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await automation_service.delete_automation(db, automation_id, current_user.id)
    return {"success": True, "message": "Automation deleted"}


@router.post("/{automation_id}/toggle", response_model=AutomationResponse)
async def toggle_automation(
    automation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    automation = await automation_service.toggle_automation(db, automation_id, current_user.id)
    return AutomationResponse.model_validate(automation)


@router.get("/{automation_id}/logs")
async def get_automation_logs(
    automation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    logs, total = await automation_service.get_automation_logs(db, automation_id, current_user.id, page, page_size)
    return {
        "success": True,
        "data": [AutomationLogResponse.model_validate(l) for l in logs],
        "total": total,
        "page": page,
        "page_size": page_size,
    }
