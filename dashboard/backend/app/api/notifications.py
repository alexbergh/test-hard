"""Notification settings and test endpoints."""

from app.api.deps import CurrentUser, DbSession
from app.config import get_settings
from app.services.notifications import send_scan_notification
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()
settings = get_settings()


class NotificationSettings(BaseModel):
    """Current notification settings (read-only from env)."""
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_from: str
    notification_email: str
    configured: bool


class NotificationEmailUpdate(BaseModel):
    """Update notification email at runtime."""
    email: str


@router.get("/settings")
async def get_notification_settings(current_user: CurrentUser) -> NotificationSettings:
    """Get current notification settings."""
    return NotificationSettings(
        smtp_host=settings.smtp_host,
        smtp_port=settings.smtp_port,
        smtp_user=settings.smtp_user,
        smtp_from=settings.smtp_from or settings.smtp_user,
        notification_email=settings.notification_email,
        configured=bool(settings.smtp_user and settings.smtp_password),
    )


@router.post("/test")
async def test_notification(current_user: CurrentUser) -> dict:
    """Send a test notification email."""
    if not settings.notification_email:
        raise HTTPException(status_code=400, detail="Notification email not configured")
    if not settings.smtp_user or not settings.smtp_password:
        raise HTTPException(status_code=400, detail="SMTP credentials not configured")

    success = send_scan_notification(
        host_name="test-host",
        scanner="test",
        status="completed",
        score=100,
        passed=10,
        failed=0,
    )
    if success:
        return {"message": f"Test email sent to {settings.notification_email}"}
    raise HTTPException(status_code=500, detail="Failed to send test email")


@router.put("/email")
async def update_notification_email(
    data: NotificationEmailUpdate,
    current_user: CurrentUser,
) -> dict:
    """Update notification email at runtime."""
    settings.notification_email = data.email
    return {"message": "Notification email updated", "email": data.email}
