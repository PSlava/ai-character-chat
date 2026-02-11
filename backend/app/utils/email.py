"""Async email sender with dev-mode console fallback."""
import logging
import aiosmtplib
from email.message import EmailMessage
from app.config import settings

logger = logging.getLogger(__name__)


def _smtp_configured() -> bool:
    return bool(settings.smtp_host and settings.smtp_from_email)


async def send_reset_email(to_email: str, reset_url: str) -> None:
    """Send a password reset email, or log to console in dev mode."""
    if not _smtp_configured():
        logger.warning(
            "SMTP not configured. Reset link for %s:\n\n  %s\n",
            to_email,
            reset_url,
        )
        return

    msg = EmailMessage()
    msg["Subject"] = "Password Reset — SweetSin"
    msg["From"] = settings.smtp_from_email
    msg["To"] = to_email
    msg.set_content(
        f"You requested a password reset.\n\n"
        f"Click the link below to set a new password (valid for 1 hour):\n\n"
        f"  {reset_url}\n\n"
        f"If you did not request this, ignore this email.\n"
    )

    await aiosmtplib.send(
        msg,
        hostname=settings.smtp_host,
        port=settings.smtp_port,
        username=settings.smtp_user,
        password=settings.smtp_password,
        start_tls=True,
    )
