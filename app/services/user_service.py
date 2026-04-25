"""
User service – CRUD operations for user management.
"""

import logging
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, NotFoundError
from app.core.security import hash_password, verify_password
from app.models.user import User

logger = logging.getLogger("auragrowth")


async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> User:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundError("User")
    return user


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def update_user_profile(db: AsyncSession, user: User, name: str | None = None, avatar_url: str | None = None) -> User:
    if name is not None:
        user.name = name
    if avatar_url is not None:
        user.avatar_url = avatar_url
    await db.flush()
    return user


async def change_password(db: AsyncSession, user: User, current_password: str, new_password: str) -> None:
    if not user.password:
        raise BadRequestError("Cannot change password for Google OAuth accounts")
    if not verify_password(current_password, user.password):
        raise BadRequestError("Current password is incorrect")
    user.password = hash_password(new_password)
    await db.flush()


async def list_users(db: AsyncSession, page: int = 1, page_size: int = 20, search: str | None = None) -> tuple[list[User], int]:
    query = select(User)
    if search:
        query = query.where((User.name.ilike(f"%{search}%")) | (User.email.ilike(f"%{search}%")))
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0
    query = query.order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    users = list((await db.execute(query)).scalars().all())
    return users, total


async def toggle_user_active(db: AsyncSession, user_id: uuid.UUID) -> User:
    user = await get_user_by_id(db, user_id)
    user.is_active = not user.is_active
    await db.flush()
    return user


async def update_user_role(db: AsyncSession, user_id: uuid.UUID, role: str) -> User:
    if role not in ("admin", "user"):
        raise BadRequestError("Role must be 'admin' or 'user'")
    user = await get_user_by_id(db, user_id)
    user.role = role
    await db.flush()
    return user
