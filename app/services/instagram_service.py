"""
Instagram service – Meta Graph API integration for Instagram Business accounts.
Handles OAuth, DM sending, and webhook processing for comment-triggered DMs.
"""

import logging
from datetime import datetime, timezone

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import BadRequestError, NotFoundError, RateLimitError
from app.models.analytics import DmLog
from app.models.automation import Automation, AutomationLog, AutomationRule
from app.models.instagram_account import InstagramAccount

logger = logging.getLogger("auragrowth")

META_GRAPH_URL = "https://graph.facebook.com/v21.0"
META_AUTH_URL = "https://www.facebook.com/v21.0/dialog/oauth"
META_TOKEN_URL = f"{META_GRAPH_URL}/oauth/access_token"


def get_instagram_auth_url(state: str | None = None) -> str:
    """Build Meta OAuth URL for Instagram Business login."""
    scopes = "instagram_basic,instagram_manage_messages,instagram_manage_comments,pages_show_list,pages_messaging"
    params = {
        "client_id": settings.META_APP_ID,
        "redirect_uri": settings.INSTAGRAM_REDIRECT_URI,
        "scope": scopes,
        "response_type": "code",
        "state": state or "ig_connect",
    }
    return META_AUTH_URL + "?" + "&".join(f"{k}={v}" for k, v in params.items())


async def exchange_instagram_code(db: AsyncSession, user_id, code: str) -> InstagramAccount:
    """Exchange OAuth code for tokens and create Instagram account record."""
    async with httpx.AsyncClient() as client:
        # Get short-lived token
        resp = await client.get(META_TOKEN_URL, params={
            "client_id": settings.META_APP_ID,
            "client_secret": settings.META_APP_SECRET,
            "redirect_uri": settings.INSTAGRAM_REDIRECT_URI,
            "code": code,
        })
        if resp.status_code != 200:
            raise BadRequestError(f"Meta token exchange failed: {resp.text}")
        short_token = resp.json()["access_token"]

        # Exchange for long-lived token
        ll_resp = await client.get(META_TOKEN_URL, params={
            "grant_type": "fb_exchange_token",
            "client_id": settings.META_APP_ID,
            "client_secret": settings.META_APP_SECRET,
            "fb_exchange_token": short_token,
        })
        ll_data = ll_resp.json()
        long_token = ll_data.get("access_token", short_token)
        expires_in = ll_data.get("expires_in", 5184000)

        # Get pages
        pages_resp = await client.get(f"{META_GRAPH_URL}/me/accounts", params={"access_token": long_token})
        pages = pages_resp.json().get("data", [])
        if not pages:
            raise BadRequestError("No Facebook Pages found. Instagram Business account requires a linked Page.")
        page = pages[0]
        page_id = page["id"]
        page_token = page["access_token"]

        # Get Instagram Business Account ID
        ig_resp = await client.get(
            f"{META_GRAPH_URL}/{page_id}",
            params={"fields": "instagram_business_account", "access_token": page_token},
        )
        ig_data = ig_resp.json()
        ig_account = ig_data.get("instagram_business_account")
        if not ig_account:
            raise BadRequestError("No Instagram Business account linked to this Page.")
        ig_user_id = ig_account["id"]

        # Get IG username
        profile_resp = await client.get(
            f"{META_GRAPH_URL}/{ig_user_id}",
            params={"fields": "username", "access_token": page_token},
        )
        username = profile_resp.json().get("username", "unknown")

    account = InstagramAccount(
        user_id=user_id,
        instagram_user_id=ig_user_id,
        username=username,
        access_token=long_token,
        token_expiry=datetime.now(timezone.utc),
        page_id=page_id,
        page_access_token=page_token,
        is_active=True,
    )
    db.add(account)
    await db.flush()
    logger.info(f"Instagram account connected: @{username}")
    return account


async def get_instagram_account(db: AsyncSession, user_id) -> InstagramAccount:
    result = await db.execute(
        select(InstagramAccount).where(InstagramAccount.user_id == user_id, InstagramAccount.is_active == True)
    )
    account = result.scalar_one_or_none()
    if not account:
        raise NotFoundError("Instagram account")
    return account


async def send_instagram_dm(account: InstagramAccount, recipient_id: str, message: str) -> dict:
    """Send a DM to an Instagram user using the Instagram Messaging API."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{META_GRAPH_URL}/{account.instagram_user_id}/messages",
            headers={"Content-Type": "application/json"},
            params={"access_token": account.page_access_token},
            json={
                "recipient": {"id": recipient_id},
                "message": {"text": message},
            },
        )
        if resp.status_code == 429:
            raise RateLimitError("Instagram DM rate limit exceeded")
        if resp.status_code != 200:
            logger.error(f"IG DM failed: {resp.text}")
            raise BadRequestError(f"Failed to send DM: {resp.text}")
        return resp.json()


async def process_comment_webhook(db: AsyncSession, webhook_data: dict) -> None:
    """
    Process Instagram comment webhook:
    1. Extract comment text and commenter ID
    2. Find matching automations with ig_comment_keyword rules
    3. Send DM if keyword matches
    """
    try:
        entry = webhook_data.get("entry", [])
        for e in entry:
            changes = e.get("changes", [])
            for change in changes:
                if change.get("field") != "comments":
                    continue
                value = change.get("value", {})
                comment_text = value.get("text", "")
                commenter_id = value.get("from", {}).get("id", "")
                media_id = value.get("media", {}).get("id", "")
                ig_user_id = str(e.get("id", ""))

                if not comment_text or not commenter_id:
                    continue

                # Find the Instagram account
                result = await db.execute(
                    select(InstagramAccount).where(
                        InstagramAccount.instagram_user_id == ig_user_id,
                        InstagramAccount.is_active == True,
                    )
                )
                ig_account = result.scalar_one_or_none()
                if not ig_account:
                    continue

                # Find active automations for this user with ig_comment_keyword rules
                auto_result = await db.execute(
                    select(Automation).where(
                        Automation.user_id == ig_account.user_id,
                        Automation.type.in_(["ig_comment_dm", "ig_keyword_dm"]),
                        Automation.is_active == True,
                    )
                )
                automations = auto_result.scalars().all()

                for automation in automations:
                    rules_result = await db.execute(
                        select(AutomationRule).where(AutomationRule.automation_id == automation.id)
                    )
                    rules = rules_result.scalars().all()

                    for rule in rules:
                        keyword = rule.condition_value
                        text_to_check = comment_text if rule.case_sensitive else comment_text.lower()
                        keyword_to_check = keyword if rule.case_sensitive else keyword.lower()

                        if keyword_to_check in text_to_check:
                            # Keyword matched! Send DM
                            action_config = automation.action_config or {}
                            dm_message = action_config.get("message", f"Thanks for your comment! Here's your link.")

                            try:
                                await send_instagram_dm(ig_account, commenter_id, dm_message)
                                status = "success"
                                error = None
                            except Exception as ex:
                                status = "failed"
                                error = str(ex)

                            # Log the automation execution
                            log = AutomationLog(
                                automation_id=automation.id,
                                trigger_source=f"comment:{media_id}",
                                trigger_data={"comment_text": comment_text, "commenter_id": commenter_id},
                                action_taken=f"Sent DM: {dm_message[:100]}",
                                status=status,
                                error_message=error,
                            )
                            db.add(log)

                            # Log DM
                            dm_log = DmLog(
                                user_id=ig_account.user_id,
                                instagram_account_id=ig_account.id,
                                recipient_ig_id=commenter_id,
                                message_text=dm_message,
                                trigger_type="comment_keyword",
                                trigger_data={"keyword": keyword, "comment": comment_text},
                                status=status,
                                automation_id=automation.id,
                                error_message=error,
                            )
                            db.add(dm_log)
                            break  # One DM per comment per automation

                await db.flush()

    except Exception as e:
        logger.error(f"Error processing IG comment webhook: {e}")
