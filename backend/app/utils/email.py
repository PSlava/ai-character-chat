"""Async email sender: Resend API → SMTP (Gmail etc.) → console fallback."""
import logging
import aiosmtplib
import httpx
from email.message import EmailMessage
from app.config import settings

logger = logging.getLogger(__name__)


def _get_provider() -> str:
    """Determine which email provider to use."""
    if settings.resend_api_key:
        return "resend"
    if settings.smtp_host and settings.smtp_from_email:
        return "smtp"
    return "console"


async def _send_via_resend(to_email: str, subject: str, text: str) -> None:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {settings.resend_api_key}"},
            json={
                "from": settings.resend_from_email,
                "to": [to_email],
                "subject": subject,
                "text": text,
            },
            timeout=10,
        )
        resp.raise_for_status()


async def _send_via_smtp(to_email: str, subject: str, text: str) -> None:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.smtp_from_email
    msg["To"] = to_email
    msg.set_content(text)

    await aiosmtplib.send(
        msg,
        hostname=settings.smtp_host,
        port=settings.smtp_port,
        username=settings.smtp_user,
        password=settings.smtp_password,
        start_tls=True,
    )


async def send_reset_email(to_email: str, reset_url: str) -> None:
    """Send a password reset email via the configured provider."""
    subject = "Password Reset — SweetSin"
    text = (
        f"You requested a password reset.\n\n"
        f"Click the link below to set a new password (valid for 1 hour):\n\n"
        f"  {reset_url}\n\n"
        f"If you did not request this, ignore this email.\n"
    )

    provider = _get_provider()

    if provider == "console":
        logger.warning(
            "Email not configured. Reset link for %s:\n\n  %s\n",
            to_email,
            reset_url,
        )
        return

    if provider == "resend":
        await _send_via_resend(to_email, subject, text)
        logger.info("Reset email sent via Resend to %s", to_email)
    else:
        await _send_via_smtp(to_email, subject, text)
        logger.info("Reset email sent via SMTP to %s", to_email)
