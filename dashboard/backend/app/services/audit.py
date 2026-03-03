"""Audit logging service for compliance tracking."""

import logging
from typing import Any

from app.models.audit import AuditLog
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


async def log_action(
    session: AsyncSession,
    action: str,
    *,
    user_id: int | None = None,
    username: str | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    detail: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> AuditLog:
    """Record an audit log entry."""
    entry = AuditLog(
        user_id=user_id,
        username=username,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        detail=detail,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    session.add(entry)
    await session.flush()
    return entry


def _extract_request_info(request: Any) -> dict:
    """Extract IP and user-agent from a FastAPI Request."""
    ip = None
    ua = None
    if request:
        ip = getattr(request.client, "host", None) if request.client else None
        ua = request.headers.get("user-agent", "")[:512] if hasattr(request, "headers") else None
    return {"ip_address": ip, "user_agent": ua}
