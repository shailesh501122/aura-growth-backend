"""
Auth service – handles registration, login, Google OAuth, and token management.
"""

import logging
import uuid

import httpx
from fastapi import BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import ConflictError, UnauthorizedError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.schemas.auth import TokenResponse
from app.services.email_service import send_welcome_email

logger = logging.getLogger("auragrowth")

# ── Google OAuth URLs ────────────────────────────────────────────────────
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"


async def register_user(
    db: AsyncSession,
    name: str,
    email: str,
    password: str,
    background_tasks: BackgroundTasks,
) -> TokenResponse:
    """
    Register a new user with email + password.
    Sends welcome email as a background task.
    """
    # Check if email already exists
    existing = await db.execute(select(User).where(User.email == email))
    if existing.scalar_one_or_none():
        raise ConflictError("An account with this email already exists")

    # Create user
    user = User(
        id=uuid.uuid4(),
        name=name,
        email=email,
        password=hash_password(password),
        role="user",
        is_active=True,
    )
    db.add(user)
    await db.flush()

    # Send welcome email in background (non-blocking)
    background_tasks.add_task(send_welcome_email, name=name, email=email)
    logger.info(f"New user registered: {email}")

    # Generate tokens
    access_token = create_access_token(subject=str(user.id), extra_claims={"role": user.role})
    refresh_token = create_refresh_token(subject=str(user.id))

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


async def login_user(
    db: AsyncSession,
    email: str,
    password: str,
) -> TokenResponse:
    """Authenticate user with email + password and return JWT tokens."""
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user or not user.password:
        raise UnauthorizedError("Invalid email or password")

    if not verify_password(password, user.password):
        raise UnauthorizedError("Invalid email or password")

    if not user.is_active:
        raise UnauthorizedError("Account is deactivated")

    access_token = create_access_token(subject=str(user.id), extra_claims={"role": user.role})
    refresh_token = create_refresh_token(subject=str(user.id))

    logger.info(f"User logged in: {email}")

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


def get_google_auth_url(state: str | None = None) -> str:
    """Build Google OAuth2 authorization URL."""
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent",
    }
    if state:
        params["state"] = state
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return f"{GOOGLE_AUTH_URL}?{query}"


async def google_oauth_callback(
    db: AsyncSession,
    code: str,
    background_tasks: BackgroundTasks,
) -> TokenResponse:
    """
    Handle Google OAuth callback:
    1. Exchange code for Google tokens
    2. Get user info from Google
    3. Create or find user
    4. Send welcome email if new user
    5. Return JWT tokens
    """
    async with httpx.AsyncClient() as client:
        # Diagnostic logging (Safe: doesn't log the secret itself)
        if not settings.GOOGLE_CLIENT_SECRET:
            logger.error("❌ GOOGLE_CLIENT_SECRET is missing or empty in environment variables!")
        
        # Exchange authorization code for tokens
        token_response = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
        )

        if token_response.status_code != 200:
            logger.error(f"Google token exchange failed: {token_response.text}")
            raise UnauthorizedError("Failed to authenticate with Google")

        token_data = token_response.json()
        google_access_token = token_data["access_token"]

        # Get user info from Google
        userinfo_response = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {google_access_token}"},
        )

        if userinfo_response.status_code != 200:
            raise UnauthorizedError("Failed to get user info from Google")

        userinfo = userinfo_response.json()

    google_id = userinfo["id"]
    email = userinfo["email"]
    name = userinfo.get("name", email.split("@")[0])
    avatar_url = userinfo.get("picture")

    # Check if user exists by google_id or email
    result = await db.execute(
        select(User).where((User.google_id == google_id) | (User.email == email))
    )
    user = result.scalar_one_or_none()

    is_new_user = False

    if not user:
        # Auto-create account for first-time Google login
        user = User(
            id=uuid.uuid4(),
            name=name,
            email=email,
            google_id=google_id,
            avatar_url=avatar_url,
            role="user",
            is_active=True,
        )
        db.add(user)
        await db.flush()
        is_new_user = True
        logger.info(f"New user created via Google OAuth: {email}")
    elif not user.google_id:
        # Link Google account to existing email user
        user.google_id = google_id
        if avatar_url and not user.avatar_url:
            user.avatar_url = avatar_url
        await db.flush()
        logger.info(f"Google account linked to existing user: {email}")

    # Send welcome email for new users
    if is_new_user:
        background_tasks.add_task(send_welcome_email, name=name, email=email)

    # Generate JWT tokens
    access_token = create_access_token(subject=str(user.id), extra_claims={"role": user.role})
    refresh_token = create_refresh_token(subject=str(user.id))

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


async def refresh_access_token(refresh_token_str: str) -> TokenResponse:
    """Validate a refresh token and issue a new access token pair."""
    try:
        payload = decode_token(refresh_token_str)
    except Exception:
        raise UnauthorizedError("Invalid or expired refresh token")

    if payload.get("type") != "refresh":
        raise UnauthorizedError("Invalid token type")

    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedError("Invalid token payload")

    access_token = create_access_token(subject=user_id)
    new_refresh = create_refresh_token(subject=user_id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh,
    )
