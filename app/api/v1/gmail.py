"""
Gmail API routes – connect Gmail, list/send emails.
"""

from fastapi import APIRouter, Depends, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.gmail import GmailAccountResponse, SendEmailRequest
from app.services import gmail_service

router = APIRouter(prefix="/gmail", tags=["Gmail"])


@router.get("/connect")
async def connect_gmail(current_user: User = Depends(get_current_user)):
    """Redirect to Google OAuth for Gmail access."""
    url = gmail_service.get_gmail_auth_url(state=str(current_user.id))
    return RedirectResponse(url=url)


@router.get("/callback")
async def gmail_callback(
    code: str,
    state: str,
    db: AsyncSession = Depends(get_db),
):
    """Handle Gmail OAuth callback."""
    account = await gmail_service.exchange_gmail_code(db, user_id=state, code=code)
    return {"success": True, "message": "Gmail connected", "email": account.email}


@router.get("/account", response_model=GmailAccountResponse)
async def get_gmail_account(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    account = await gmail_service.get_gmail_account(db, current_user.id)
    return GmailAccountResponse.model_validate(account)


@router.get("/emails")
async def list_emails(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    page_token: str | None = Query(None),
    max_results: int = Query(20, ge=1, le=100),
):
    account = await gmail_service.get_gmail_account(db, current_user.id)
    return await gmail_service.list_emails(account, page_token=page_token, max_results=max_results)


@router.get("/emails/{message_id}")
async def get_email(
    message_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    account = await gmail_service.get_gmail_account(db, current_user.id)
    return await gmail_service.get_email_detail(account, message_id)


@router.post("/emails/send")
async def send_email(
    body: SendEmailRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    account = await gmail_service.get_gmail_account(db, current_user.id)
    result = await gmail_service.send_gmail(account, to=body.to, subject=body.subject, body=body.body, is_html=body.is_html)
    return {"success": True, "data": result}


@router.delete("/disconnect")
async def disconnect_gmail(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    account = await gmail_service.get_gmail_account(db, current_user.id)
    account.is_active = False
    await db.flush()
    return {"success": True, "message": "Gmail disconnected"}
