"""
Bio page service – CRUD for link-in-bio pages and links.
"""

import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.models.analytics import ClickEvent
from app.models.bio_page import BioLink, BioPage

logger = logging.getLogger("auragrowth")


async def create_bio_page(db: AsyncSession, user_id: uuid.UUID, data: dict) -> BioPage:
    existing = await db.execute(select(BioPage).where(BioPage.slug == data["slug"]))
    if existing.scalar_one_or_none():
        raise ConflictError("A bio page with this slug already exists")
    page = BioPage(user_id=user_id, **data)
    db.add(page)
    await db.flush()
    return page


async def get_bio_page(db: AsyncSession, page_id: uuid.UUID, user_id: uuid.UUID) -> BioPage:
    result = await db.execute(
        select(BioPage).options(selectinload(BioPage.links)).where(BioPage.id == page_id)
    )
    page = result.scalar_one_or_none()
    if not page:
        raise NotFoundError("Bio page")
    if page.user_id != user_id:
        raise ForbiddenError("Not your bio page")
    return page


async def get_public_bio_page(db: AsyncSession, slug: str) -> BioPage:
    result = await db.execute(
        select(BioPage).options(selectinload(BioPage.links))
        .where(BioPage.slug == slug, BioPage.is_published == True)
    )
    page = result.scalar_one_or_none()
    if not page:
        raise NotFoundError("Bio page")
    return page


async def list_bio_pages(db: AsyncSession, user_id: uuid.UUID) -> list[BioPage]:
    result = await db.execute(
        select(BioPage).options(selectinload(BioPage.links))
        .where(BioPage.user_id == user_id).order_by(BioPage.created_at.desc())
    )
    return list(result.scalars().all())


async def update_bio_page(db: AsyncSession, page_id: uuid.UUID, user_id: uuid.UUID, data: dict) -> BioPage:
    page = await get_bio_page(db, page_id, user_id)
    for k, v in data.items():
        if v is not None:
            setattr(page, k, v)
    await db.flush()
    return page


async def delete_bio_page(db: AsyncSession, page_id: uuid.UUID, user_id: uuid.UUID) -> None:
    page = await get_bio_page(db, page_id, user_id)
    await db.delete(page)
    await db.flush()


async def add_link(db: AsyncSession, page_id: uuid.UUID, user_id: uuid.UUID, data: dict) -> BioLink:
    await get_bio_page(db, page_id, user_id)
    link = BioLink(page_id=page_id, **data)
    db.add(link)
    await db.flush()
    return link


async def update_link(db: AsyncSession, page_id: uuid.UUID, link_id: uuid.UUID, user_id: uuid.UUID, data: dict) -> BioLink:
    await get_bio_page(db, page_id, user_id)
    result = await db.execute(select(BioLink).where(BioLink.id == link_id, BioLink.page_id == page_id))
    link = result.scalar_one_or_none()
    if not link:
        raise NotFoundError("Link")
    for k, v in data.items():
        if v is not None:
            setattr(link, k, v)
    await db.flush()
    return link


async def delete_link(db: AsyncSession, page_id: uuid.UUID, link_id: uuid.UUID, user_id: uuid.UUID) -> None:
    await get_bio_page(db, page_id, user_id)
    result = await db.execute(select(BioLink).where(BioLink.id == link_id, BioLink.page_id == page_id))
    link = result.scalar_one_or_none()
    if not link:
        raise NotFoundError("Link")
    await db.delete(link)
    await db.flush()


async def track_click(db: AsyncSession, slug: str, link_id: uuid.UUID, ip: str | None = None, ua: str | None = None, referrer: str | None = None) -> None:
    result = await db.execute(select(BioLink).where(BioLink.id == link_id))
    link = result.scalar_one_or_none()
    if not link:
        raise NotFoundError("Link")
    link.click_count += 1
    event = ClickEvent(link_id=link_id, ip_address=ip, user_agent=ua, referrer=referrer)
    db.add(event)
    await db.flush()
