"""
Bio Pages API routes – create/manage link-in-bio pages and links.
"""

import uuid

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.bio_page import (
    BioLinkCreate,
    BioLinkResponse,
    BioLinkUpdate,
    BioPageCreate,
    BioPageResponse,
    BioPageUpdate,
    PublicBioPageResponse,
)
from app.services import bio_page_service

router = APIRouter(prefix="/bio", tags=["Link-in-Bio"])


@router.get("/pages", response_model=list[BioPageResponse])
async def list_pages(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    pages = await bio_page_service.list_bio_pages(db, current_user.id)
    return [BioPageResponse.model_validate(p) for p in pages]


@router.post("/pages", response_model=BioPageResponse, status_code=201)
async def create_page(
    body: BioPageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    page = await bio_page_service.create_bio_page(db, current_user.id, body.model_dump())
    return BioPageResponse.model_validate(page)


@router.get("/pages/{page_id}", response_model=BioPageResponse)
async def get_page(
    page_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    page = await bio_page_service.get_bio_page(db, page_id, current_user.id)
    return BioPageResponse.model_validate(page)


@router.put("/pages/{page_id}", response_model=BioPageResponse)
async def update_page(
    page_id: uuid.UUID,
    body: BioPageUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    page = await bio_page_service.update_bio_page(db, page_id, current_user.id, body.model_dump(exclude_unset=True))
    return BioPageResponse.model_validate(page)


@router.delete("/pages/{page_id}")
async def delete_page(
    page_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await bio_page_service.delete_bio_page(db, page_id, current_user.id)
    return {"success": True, "message": "Bio page deleted"}


@router.post("/pages/{page_id}/links", response_model=BioLinkResponse, status_code=201)
async def add_link(
    page_id: uuid.UUID,
    body: BioLinkCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    link = await bio_page_service.add_link(db, page_id, current_user.id, body.model_dump())
    return BioLinkResponse.model_validate(link)


@router.put("/pages/{page_id}/links/{link_id}", response_model=BioLinkResponse)
async def update_link(
    page_id: uuid.UUID,
    link_id: uuid.UUID,
    body: BioLinkUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    link = await bio_page_service.update_link(db, page_id, link_id, current_user.id, body.model_dump(exclude_unset=True))
    return BioLinkResponse.model_validate(link)


@router.delete("/pages/{page_id}/links/{link_id}")
async def delete_link(
    page_id: uuid.UUID,
    link_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await bio_page_service.delete_link(db, page_id, link_id, current_user.id)
    return {"success": True, "message": "Link deleted"}


# ── Public Endpoint (no auth required) ──────────────────────────────────

@router.get("/p/{slug}", response_model=PublicBioPageResponse)
async def get_public_page(slug: str, db: AsyncSession = Depends(get_db)):
    """Public endpoint to view a published bio page."""
    page = await bio_page_service.get_public_bio_page(db, slug)
    return PublicBioPageResponse.model_validate(page)


@router.post("/p/{slug}/click/{link_id}")
async def track_click(
    slug: str,
    link_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Track a click on a bio page link."""
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    ref = request.headers.get("referer")
    await bio_page_service.track_click(db, slug, link_id, ip=ip, ua=ua, referrer=ref)
    return {"success": True}
