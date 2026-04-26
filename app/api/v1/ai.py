"""
AI API – AI-powered reply generation and automation suggestions.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.services import ai_service

router = APIRouter(prefix="/ai", tags=["AI"])


class EmailReplyRequest(BaseModel):
    original_subject: str = Field(..., min_length=1)
    original_body: str = Field(..., min_length=1)
    sender_name: str | None = None
    tone: str = Field(default="professional", pattern=r"^(professional|friendly|formal|casual)$")


class DmReplyRequest(BaseModel):
    message_text: str = Field(..., min_length=1)
    context: str | None = None
    tone: str = Field(default="friendly", pattern=r"^(professional|friendly|formal|casual)$")


class SuggestRulesRequest(BaseModel):
    automation_type: str = Field(
        ..., pattern=r"^(email_auto_reply|ig_comment_dm|ig_keyword_dm)$"
    )
    user_description: str | None = None


@router.post("/email-reply")
async def generate_email_reply(
    body: EmailReplyRequest,
    user: User = Depends(get_current_user),
):
    """Generate an AI-powered email reply."""
    return await ai_service.generate_email_reply(
        original_subject=body.original_subject,
        original_body=body.original_body,
        sender_name=body.sender_name,
        tone=body.tone,
    )


@router.post("/dm-reply")
async def generate_dm_reply(
    body: DmReplyRequest,
    user: User = Depends(get_current_user),
):
    """Generate an AI-powered Instagram DM reply."""
    return await ai_service.generate_dm_reply(
        message_text=body.message_text,
        context=body.context,
        tone=body.tone,
    )


@router.post("/suggest-rules")
async def suggest_automation_rules(
    body: SuggestRulesRequest,
    user: User = Depends(get_current_user),
):
    """AI-suggested automation rules based on type and user description."""
    return await ai_service.suggest_automation_rules(
        automation_type=body.automation_type,
        user_description=body.user_description,
    )
