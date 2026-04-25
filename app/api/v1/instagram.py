"""
Instagram API routes – connect account, manage profile.
"""

from fastapi import APIRouter, Depends, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.instagram import InstagramAccountResponse, SendDmRequest
from app.services import instagram_service

router = APIRouter(prefix="/instagram", tags=["Instagram"])


@router.get("/connect")
async def connect_instagram(current_user: User = Depends(get_current_user)):
    """Redirect to Meta OAuth for Instagram access."""
    url = instagram_service.get_instagram_auth_url(state=str(current_user.id))
    return RedirectResponse(url=url)


@router.get("/callback")
async def instagram_callback(
    code: str,
    state: str,
    db: AsyncSession = Depends(get_db),
):
    """Handle Meta OAuth callback for Instagram."""
    account = await instagram_service.exchange_instagram_code(db, user_id=state, code=code)
    return {"success": True, "message": "Instagram connected", "username": account.username}


@router.get("/profile", response_model=InstagramAccountResponse)
async def get_instagram_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    account = await instagram_service.get_instagram_account(db, current_user.id)
    return InstagramAccountResponse.model_validate(account)


@router.post("/dm/send")
async def send_dm(
    body: SendDmRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Manually send a DM to an Instagram user."""
    account = await instagram_service.get_instagram_account(db, current_user.id)
    result = await instagram_service.send_instagram_dm(account, body.recipient_id, body.message)
    return {"success": True, "data": result}


@router.delete("/disconnect")
async def disconnect_instagram(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    account = await instagram_service.get_instagram_account(db, current_user.id)
    account.is_active = False
    await db.flush()
    return {"success": True, "message": "Instagram disconnected"}
