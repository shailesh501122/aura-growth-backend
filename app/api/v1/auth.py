"""
Auth API routes – registration, login, Google OAuth, token refresh.
"""

from fastapi import APIRouter, BackgroundTasks, Depends, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.auth import AuthResponse, LoginRequest, RefreshTokenRequest, RegisterRequest, TokenResponse
from app.schemas.user import UserResponse
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=AuthResponse)
async def register(
    body: RegisterRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Register a new user with email + password. Sends welcome email."""
    tokens = await auth_service.register_user(
        db=db, name=body.name, email=body.email,
        password=body.password, background_tasks=background_tasks,
    )
    return AuthResponse(message="Registration successful", data=tokens)


@router.post("/login", response_model=AuthResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Login with email + password."""
    tokens = await auth_service.login_user(db=db, email=body.email, password=body.password)
    return AuthResponse(message="Login successful", data=tokens)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(body: RefreshTokenRequest):
    """Refresh access token using a valid refresh token."""
    return await auth_service.refresh_access_token(body.refresh_token)


@router.get("/google/login")
async def google_login(state: str | None = Query(None)):
    """Redirect to Google OAuth2 authorization page."""
    url = auth_service.get_google_auth_url(state=state)
    return RedirectResponse(url=url)


@router.get("/google/callback", response_model=AuthResponse)
async def google_callback(
    code: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    state: str | None = Query(None),
):
    """Handle Google OAuth2 callback. Creates account if first login."""
    tokens = await auth_service.google_oauth_callback(db=db, code=code, background_tasks=background_tasks)
    return AuthResponse(message="Google login successful", data=tokens)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current authenticated user profile."""
    return UserResponse.model_validate(current_user)
