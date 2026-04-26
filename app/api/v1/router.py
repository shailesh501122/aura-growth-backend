"""
Main v1 API router – aggregates all endpoint routers.
"""

from fastapi import APIRouter

from app.api.v1 import (
    admin,
    ai,
    analytics,
    auth,
    automations,
    bio_pages,
    conversations,
    gmail,
    instagram,
    instagram_webhooks,
    subscriptions,
    support,
    users,
)

router = APIRouter(prefix="/api/v1")

router.include_router(auth.router)
router.include_router(users.router)
router.include_router(gmail.router)
router.include_router(instagram.router)
router.include_router(instagram_webhooks.router)
router.include_router(automations.router)
router.include_router(bio_pages.router)
router.include_router(subscriptions.router)
router.include_router(analytics.router)
router.include_router(conversations.router)
router.include_router(support.router)
router.include_router(ai.router)
router.include_router(admin.router)
