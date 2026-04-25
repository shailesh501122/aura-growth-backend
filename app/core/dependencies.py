"""
FastAPI dependency injection utilities.
"""

from typing import Annotated

from fastapi import Depends, Header
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import decode_token
from app.db.session import get_db_session
from app.models.user import User


async def get_db(
    session: AsyncSession = Depends(get_db_session),
) -> AsyncSession:
    """Alias dependency for database session."""
    return session


async def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
    db: AsyncSession = Depends(get_db_session),
) -> User:
    """
    Extract and validate JWT from Authorization header.
    Returns the authenticated User model instance.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise UnauthorizedError("Missing or invalid authorization header")

    token = authorization.split(" ", 1)[1]

    try:
        payload = decode_token(token)
    except JWTError:
        raise UnauthorizedError("Invalid or expired token")

    if payload.get("type") != "access":
        raise UnauthorizedError("Invalid token type")

    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedError("Invalid token payload")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise UnauthorizedError("User not found")

    if not user.is_active:
        raise ForbiddenError("Account is deactivated")

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Ensure the current user is active."""
    if not current_user.is_active:
        raise ForbiddenError("Account is deactivated")
    return current_user


async def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Ensure the current user has admin role."""
    if current_user.role != "admin":
        raise ForbiddenError("Admin access required")
    return current_user
