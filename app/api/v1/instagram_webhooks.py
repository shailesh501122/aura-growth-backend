"""
Instagram Webhooks – Meta webhook verification and comment event processing.
This is the core handler for keyword-triggered Instagram DM automation.
"""

import logging

from fastapi import APIRouter, BackgroundTasks, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import get_db
from app.services import instagram_service

logger = logging.getLogger("auragrowth")

router = APIRouter(prefix="/instagram", tags=["Instagram Webhooks"])


@router.get("/webhook")
async def verify_webhook(
    request: Request,
):
    """
    Meta webhook verification endpoint.
    Meta sends a GET request with hub.mode, hub.challenge, hub.verify_token.
    We must respond with hub.challenge if verify_token matches.
    """
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == settings.META_WEBHOOK_VERIFY_TOKEN:
        logger.info("Webhook verified successfully")
        return int(challenge)

    logger.warning(f"Webhook verification failed: mode={mode}, token={token}")
    return {"error": "Verification failed"}, 403


@router.post("/webhook")
async def handle_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Handle incoming Instagram webhook events.

    Flow for comment-triggered DM:
    1. Instagram user comments on a post/reel with keyword (e.g., "LINK")
    2. Meta sends webhook POST with comment data
    3. We parse the comment, check against active automation rules
    4. If keyword matches, send DM to commenter via Instagram Messaging API
    5. Log the automation execution
    """
    body = await request.json()
    obj = body.get("object")

    logger.info(f"Webhook received: object={obj}")

    if obj == "instagram":
        # Process in background to respond quickly to Meta (must respond < 20s)
        background_tasks.add_task(
            instagram_service.process_comment_webhook, db, body
        )

    return {"status": "ok"}
