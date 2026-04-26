"""
AI service – generates email/DM replies and suggests automation rules using Google Gemini.
Falls back gracefully if API key is not configured.
"""

import logging
from typing import Optional

import httpx

from app.core.config import settings

logger = logging.getLogger("auragrowth")

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"


async def _call_gemini(prompt: str) -> str | None:
    """Call Google Gemini API and return generated text."""
    api_key = settings.GEMINI_API_KEY
    if not api_key:
        logger.warning("Gemini API key not configured, skipping AI generation")
        return None

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{GEMINI_API_URL}?key={api_key}",
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "temperature": 0.7,
                        "maxOutputTokens": 1024,
                    },
                },
            )
            if resp.status_code != 200:
                logger.error(f"Gemini API error: {resp.status_code} {resp.text[:200]}")
                return None

            data = resp.json()
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "")
            return None
    except Exception as e:
        logger.error(f"Gemini API call failed: {e}")
        return None


async def generate_email_reply(
    original_subject: str,
    original_body: str,
    sender_name: str | None = None,
    tone: str = "professional",
) -> dict:
    """Generate an AI-powered email reply."""
    prompt = f"""You are an AI email assistant. Generate a {tone} reply to the following email.

From: {sender_name or 'Unknown'}
Subject: {original_subject}
Body:
{original_body[:2000]}

Write a concise, helpful reply. Do not include subject line or email headers, just the body text."""

    reply = await _call_gemini(prompt)
    if reply:
        return {"success": True, "reply": reply, "tone": tone}
    return {
        "success": False,
        "reply": None,
        "error": "AI service unavailable. Please configure GEMINI_API_KEY.",
    }


async def generate_dm_reply(
    message_text: str,
    context: str | None = None,
    tone: str = "friendly",
) -> dict:
    """Generate an AI-powered Instagram DM reply."""
    prompt = f"""You are an AI assistant helping manage Instagram DMs. Generate a {tone} reply to this message.

Message: {message_text[:1000]}
{f'Context: {context}' if context else ''}

Write a short, engaging reply suitable for Instagram DM. Keep it under 300 characters."""

    reply = await _call_gemini(prompt)
    if reply:
        return {"success": True, "reply": reply, "tone": tone}
    return {
        "success": False,
        "reply": None,
        "error": "AI service unavailable. Please configure GEMINI_API_KEY.",
    }


async def suggest_automation_rules(
    automation_type: str,
    user_description: str | None = None,
) -> dict:
    """Suggest automation rules based on type and optional user description."""
    type_context = {
        "email_auto_reply": "email automation rules (keyword matching on subject or body)",
        "ig_comment_dm": "Instagram comment-to-DM automation (keyword matching on comments)",
        "ig_keyword_dm": "Instagram keyword DM automation",
    }

    context = type_context.get(automation_type, "automation rules")
    prompt = f"""You are an AI assistant helping set up {context}.

{f'User description: {user_description}' if user_description else 'Suggest popular rules for a typical creator/business.'}

Suggest 3-5 automation rules in JSON format. Each rule should have:
- "condition_type": one of "keyword_subject", "keyword_body", "sender_match", "ig_comment_keyword"
- "condition_value": the keyword or pattern to match
- "case_sensitive": boolean (usually false)
- "description": brief explanation of why this rule is useful

Return ONLY a JSON array, no markdown."""

    reply = await _call_gemini(prompt)
    if reply:
        import json
        try:
            # Try to parse the AI response as JSON
            cleaned = reply.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0]
            rules = json.loads(cleaned)
            return {"success": True, "suggestions": rules}
        except json.JSONDecodeError:
            return {"success": True, "suggestions": [], "raw_response": reply}
    return {
        "success": False,
        "suggestions": [],
        "error": "AI service unavailable. Please configure GEMINI_API_KEY.",
    }
