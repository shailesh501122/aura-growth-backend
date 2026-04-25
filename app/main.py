"""
AuraGrowth SaaS Backend – FastAPI Application Entry Point.

A unified platform for link-in-bio pages, Gmail automation,
and Instagram DM automation powered by Meta API.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router as v1_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.db.session import engine
from app.services.subscription_service import seed_default_plans
from app.db.session import async_session_factory

logger = logging.getLogger("auragrowth")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown events."""
    logger.info(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"📊 Environment: {settings.ENVIRONMENT}")

    # Seed default subscription plans
    async with async_session_factory() as session:
        try:
            await seed_default_plans(session)
            await session.commit()
        except Exception as e:
            logger.warning(f"Plan seeding skipped: {e}")

    yield

    # Shutdown
    logger.info("🛑 Shutting down...")
    await engine.dispose()


def create_app() -> FastAPI:
    """Application factory."""
    app = FastAPI(
        title=settings.APP_NAME,
        description=(
            "AuraGrowth SaaS Backend – Link-in-bio pages, Gmail automation, "
            "and Instagram DM automation with AI-powered workflows."
        ),
        version=settings.APP_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # ── CORS Middleware ──────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Exception Handlers ───────────────────────────────────────────────
    register_exception_handlers(app)

    # ── Routers ──────────────────────────────────────────────────────────
    app.include_router(v1_router)

    # ── Health Check ─────────────────────────────────────────────────────
    @app.get("/health", tags=["Health"])
    async def health_check():
        return {
            "status": "healthy",
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
        }

    # ── Root ─────────────────────────────────────────────────────────────
    @app.get("/", include_in_schema=False)
    async def root():
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/docs")

    return app


app = create_app()
