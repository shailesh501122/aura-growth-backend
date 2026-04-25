"""
Gmail service – Gmail API operations via OAuth2.
"""

import logging
import base64
from datetime import datetime, timezone
from email.mime.text import MIMEText

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import BadRequestError, NotFoundError
from app.models.gmail_account import GmailAccount

logger = logging.getLogger("auragrowth")

GMAIL_API_BASE = "https://gmail.googleapis.com/gmail/v1"
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"

GMAIL_SCOPES = "https://www.googleapis.com/auth/gmail.readonly https://www.googleapis.com/auth/gmail.send https://www.googleapis.com/auth/gmail.modify"


def get_gmail_auth_url(state: str | None = None) -> str:
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI.replace("/auth/", "/gmail/"),
        "response_type": "code",
        "scope": GMAIL_SCOPES,
        "access_type": "offline",
        "prompt": "consent",
    }
    if state:
        params["state"] = state
    return GOOGLE_AUTH_URL + "?" + "&".join(f"{k}={v}" for k, v in params.items())


async def exchange_gmail_code(db: AsyncSession, user_id, code: str) -> GmailAccount:
    async with httpx.AsyncClient() as client:
        resp = await client.post(GOOGLE_TOKEN_URL, data={
            "code": code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI.replace("/auth/", "/gmail/"),
            "grant_type": "authorization_code",
        })
        if resp.status_code != 200:
            raise BadRequestError(f"Gmail token exchange failed: {resp.text}")
        token_data = resp.json()

        # Get user email
        profile_resp = await client.get(
            f"{GMAIL_API_BASE}/users/me/profile",
            headers={"Authorization": f"Bearer {token_data['access_token']}"},
        )
        profile = profile_resp.json()

    account = GmailAccount(
        user_id=user_id,
        email=profile.get("emailAddress", ""),
        access_token=token_data["access_token"],
        refresh_token=token_data.get("refresh_token", ""),
        token_expiry=datetime.now(timezone.utc),
        is_active=True,
    )
    db.add(account)
    await db.flush()
    return account


async def refresh_gmail_token(account: GmailAccount) -> str:
    async with httpx.AsyncClient() as client:
        resp = await client.post(GOOGLE_TOKEN_URL, data={
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "refresh_token": account.refresh_token,
            "grant_type": "refresh_token",
        })
        if resp.status_code != 200:
            raise BadRequestError("Failed to refresh Gmail token")
        data = resp.json()
        account.access_token = data["access_token"]
        return data["access_token"]


async def get_gmail_account(db: AsyncSession, user_id) -> GmailAccount:
    result = await db.execute(
        select(GmailAccount).where(GmailAccount.user_id == user_id, GmailAccount.is_active == True)
    )
    account = result.scalar_one_or_none()
    if not account:
        raise NotFoundError("Gmail account")
    return account


async def list_emails(account: GmailAccount, page_token: str | None = None, max_results: int = 20):
    async with httpx.AsyncClient() as client:
        params = {"maxResults": max_results}
        if page_token:
            params["pageToken"] = page_token
        resp = await client.get(
            f"{GMAIL_API_BASE}/users/me/messages",
            headers={"Authorization": f"Bearer {account.access_token}"},
            params=params,
        )
        if resp.status_code == 401:
            new_token = await refresh_gmail_token(account)
            resp = await client.get(
                f"{GMAIL_API_BASE}/users/me/messages",
                headers={"Authorization": f"Bearer {new_token}"},
                params=params,
            )
        return resp.json()


async def get_email_detail(account: GmailAccount, message_id: str):
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{GMAIL_API_BASE}/users/me/messages/{message_id}",
            headers={"Authorization": f"Bearer {account.access_token}"},
            params={"format": "full"},
        )
        if resp.status_code == 401:
            new_token = await refresh_gmail_token(account)
            resp = await client.get(
                f"{GMAIL_API_BASE}/users/me/messages/{message_id}",
                headers={"Authorization": f"Bearer {new_token}"},
                params={"format": "full"},
            )
        return resp.json()


async def send_gmail(account: GmailAccount, to: str, subject: str, body: str, is_html: bool = False):
    mime_type = "html" if is_html else "plain"
    message = MIMEText(body, mime_type)
    message["to"] = to
    message["subject"] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{GMAIL_API_BASE}/users/me/messages/send",
            headers={"Authorization": f"Bearer {account.access_token}", "Content-Type": "application/json"},
            json={"raw": raw},
        )
        if resp.status_code == 401:
            new_token = await refresh_gmail_token(account)
            resp = await client.post(
                f"{GMAIL_API_BASE}/users/me/messages/send",
                headers={"Authorization": f"Bearer {new_token}", "Content-Type": "application/json"},
                json={"raw": raw},
            )
        return resp.json()
