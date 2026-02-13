"""Email notification service for scan events."""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def send_scan_notification(
    host_name: str,
    scanner: str,
    status: str,
    score: int | None = None,
    passed: int = 0,
    failed: int = 0,
    error_message: str | None = None,
) -> bool:
    """Send email notification about scan completion or failure."""
    to_email = settings.notification_email
    if not to_email or not settings.smtp_user or not settings.smtp_password:
        logger.warning("Email notification skipped: SMTP not configured")
        return False

    subject = f"[Test-Hard] Scan {status}: {scanner} on {host_name}"

    if status == "completed":
        body = (
            f"Scan completed successfully.\n\n"
            f"Host: {host_name}\n"
            f"Scanner: {scanner}\n"
            f"Score: {score}\n"
            f"Passed: {passed}\n"
            f"Failed: {failed}\n"
        )
        html = (
            f"<h2>Scan Completed</h2>"
            f"<table style='border-collapse:collapse;'>"
            f"<tr><td style='padding:4px 12px;font-weight:bold;'>Host</td><td style='padding:4px 12px;'>{host_name}</td></tr>"
            f"<tr><td style='padding:4px 12px;font-weight:bold;'>Scanner</td><td style='padding:4px 12px;'>{scanner}</td></tr>"
            f"<tr><td style='padding:4px 12px;font-weight:bold;'>Score</td><td style='padding:4px 12px;'>{score}</td></tr>"
            f"<tr><td style='padding:4px 12px;font-weight:bold;'>Passed</td><td style='padding:4px 12px;color:green;'>{passed}</td></tr>"
            f"<tr><td style='padding:4px 12px;font-weight:bold;'>Failed</td><td style='padding:4px 12px;color:red;'>{failed}</td></tr>"
            f"</table>"
        )
    else:
        body = (
            f"Scan failed.\n\n"
            f"Host: {host_name}\n"
            f"Scanner: {scanner}\n"
            f"Error: {error_message or 'Unknown error'}\n"
        )
        html = (
            f"<h2 style='color:red;'>Scan Failed</h2>"
            f"<table style='border-collapse:collapse;'>"
            f"<tr><td style='padding:4px 12px;font-weight:bold;'>Host</td><td style='padding:4px 12px;'>{host_name}</td></tr>"
            f"<tr><td style='padding:4px 12px;font-weight:bold;'>Scanner</td><td style='padding:4px 12px;'>{scanner}</td></tr>"
            f"<tr><td style='padding:4px 12px;font-weight:bold;'>Error</td><td style='padding:4px 12px;color:red;'>{error_message or 'Unknown error'}</td></tr>"
            f"</table>"
        )

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.smtp_from or settings.smtp_user
        msg["To"] = to_email

        msg.attach(MIMEText(body, "plain"))
        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.starttls()
            server.login(settings.smtp_user, settings.smtp_password)
            server.sendmail(msg["From"], [to_email], msg.as_string())

        logger.info(f"Notification email sent to {to_email} for {scanner} scan on {host_name}")
        return True
    except Exception as e:
        logger.error(f"Failed to send notification email: {e}")
        return False
