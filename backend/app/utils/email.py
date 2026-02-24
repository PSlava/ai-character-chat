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


async def send_registration_notification(admin_email: str, new_user_email: str, username: str, method: str = "email") -> None:
    """Notify admin about a new user registration."""
    subject = "New Registration — SweetSin"
    text = (
        f"New user registered on SweetSin:\n\n"
        f"  Email:    {new_user_email}\n"
        f"  Username: {username}\n"
        f"  Method:   {method}\n\n"
        f"— SweetSin\n"
    )

    provider = _get_provider()

    if provider == "console":
        logger.info("New registration: %s (%s) via %s", new_user_email, username, method)
        return

    try:
        if provider == "resend":
            await _send_via_resend(admin_email, subject, text)
        else:
            await _send_via_smtp(admin_email, subject, text)
        logger.info("Registration notification sent to %s about %s", admin_email, new_user_email)
    except Exception:
        logger.exception("Failed to send registration notification to %s", admin_email)


async def send_balance_alert(provider: str, error_details: str) -> None:
    """Send immediate alert to all admins when a provider returns 402 (no balance)."""
    admin_str = settings.admin_emails
    if not admin_str:
        logger.warning("No ADMIN_EMAILS configured, cannot send balance alert for %s", provider)
        return

    admin_list = [e.strip() for e in admin_str.split(",") if e.strip()]
    if not admin_list:
        return

    site = settings.site_name
    subject = f"{site} — {provider.upper()} NO BALANCE (402)"
    text = (
        f"Provider '{provider}' returned a 402 (no balance) error.\n\n"
        f"  Error: {error_details[:300]}\n\n"
        f"The provider has been automatically blacklisted for 6 hours.\n"
        f"No requests will be sent to '{provider}' until the blacklist expires "
        f"or you manually re-enable it in Admin > Users page.\n\n"
        f"To re-enable: go to Admin panel, find Provider Status section, "
        f"and toggle '{provider}' back on.\n\n"
        f"-- {site}\n"
    )

    email_provider = _get_provider()
    if email_provider == "console":
        logger.warning("BALANCE ALERT [%s]: %s", provider, error_details[:200])
        return

    for admin_email in admin_list:
        try:
            if email_provider == "resend":
                await _send_via_resend(admin_email, subject, text)
            else:
                await _send_via_smtp(admin_email, subject, text)
            logger.info("Balance alert sent to %s about %s", admin_email, provider)
        except Exception:
            logger.exception("Failed to send balance alert to %s", admin_email)


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
