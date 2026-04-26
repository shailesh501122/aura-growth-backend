"""
Middleware – request logging for API monitoring and debugging.
"""

import logging
import time
import uuid
from datetime import datetime, timezone

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

logger = logging.getLogger("auragrowth")

# Paths to skip logging (health checks, docs, static)
SKIP_PATHS = {"/health", "/docs", "/redoc", "/openapi.json", "/favicon.ico", "/"}


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Logs every API request to the database for admin monitoring.
    Captures: method, path, status, duration, user_id, IP, user-agent.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Skip non-API paths
        if request.url.path in SKIP_PATHS:
            return await call_next(request)

        start_time = time.perf_counter()
        response = await call_next(request)
        duration_ms = int((time.perf_counter() - start_time) * 1000)

        # Extract user ID from JWT if present (non-blocking)
        user_id = None
        try:
            auth_header = request.headers.get("authorization", "")
            if auth_header.startswith("Bearer "):
                from app.core.security import decode_token
                payload = decode_token(auth_header.split(" ", 1)[1])
                user_id_str = payload.get("sub")
                if user_id_str:
                    user_id = uuid.UUID(user_id_str)
        except Exception:
            pass  # Don't break the request if JWT parsing fails

        # Log to database asynchronously (best-effort, non-blocking)
        try:
            from app.db.session import async_session_factory
            from app.models.system import ApiLog

            async with async_session_factory() as session:
                log_entry = ApiLog(
                    method=request.method,
                    path=str(request.url.path)[:500],
                    status_code=response.status_code,
                    user_id=user_id,
                    ip_address=request.client.host if request.client else None,
                    user_agent=request.headers.get("user-agent", "")[:500],
                    duration_ms=duration_ms,
                )
                session.add(log_entry)
                await session.commit()
        except Exception as e:
            # Never let logging break the actual request
            logger.debug(f"API log write failed: {e}")

        return response
