"""Automatic error detection: captures ERROR/CRITICAL logs and emails admins."""

import asyncio
import logging
import threading
import time
import traceback
from collections import deque
from datetime import datetime, timezone
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Loggers to ignore (prevent infinite recursion)
_IGNORE_LOGGERS = {"app.utils.error_notifier", "app.utils.email"}


@dataclass
class BufferedError:
    timestamp: datetime
    logger_name: str
    level: str
    message: str
    traceback: str | None


class AdminEmailHandler(logging.Handler):
    """Captures ERROR/CRITICAL logs and sends batched email to admins."""

    FLUSH_INTERVAL = 300  # 5 minutes
    MAX_BUFFER = 50
    DEDUP_WINDOW = 300  # 5 min

    def __init__(self):
        super().__init__(level=logging.ERROR)
        self._buffer: deque[BufferedError] = deque(maxlen=self.MAX_BUFFER)
        self._lock = threading.Lock()
        self._recent_hashes: dict[str, float] = {}
        self._flush_task: asyncio.Task | None = None
        self._loop: asyncio.AbstractEventLoop | None = None

    def start(self, loop: asyncio.AbstractEventLoop):
        self._loop = loop
        self._flush_task = loop.create_task(self._periodic_flush())

    def stop(self):
        if self._flush_task:
            self._flush_task.cancel()

    def emit(self, record: logging.LogRecord):
        # Skip self and email logger to prevent recursion
        if record.name in _IGNORE_LOGGERS:
            return

        # Dedup
        msg_hash = f"{record.name}:{record.getMessage()[:200]}"
        now = time.monotonic()
        with self._lock:
            if msg_hash in self._recent_hashes:
                if now - self._recent_hashes[msg_hash] < self.DEDUP_WINDOW:
                    return
            self._recent_hashes[msg_hash] = now
            # Cleanup old hashes
            self._recent_hashes = {
                k: v for k, v in self._recent_hashes.items()
                if now - v < self.DEDUP_WINDOW
            }

        error = BufferedError(
            timestamp=datetime.now(timezone.utc),
            logger_name=record.name,
            level=record.levelname,
            message=record.getMessage(),
            traceback=self._format_traceback(record),
        )

        with self._lock:
            self._buffer.append(error)

        # Immediate flush for CRITICAL
        if record.levelno >= logging.CRITICAL and self._loop:
            self._loop.call_soon_threadsafe(
                lambda: asyncio.ensure_future(self._do_flush())
            )

    async def _periodic_flush(self):
        while True:
            await asyncio.sleep(self.FLUSH_INTERVAL)
            await self._do_flush()

    async def _do_flush(self):
        with self._lock:
            if not self._buffer:
                return
            errors = list(self._buffer)
            self._buffer.clear()

        try:
            await _send_error_digest(errors)
        except Exception:
            logger.warning("Failed to send error digest email", exc_info=True)

    @staticmethod
    def _format_traceback(record: logging.LogRecord) -> str | None:
        if record.exc_info and record.exc_info[1]:
            return "".join(traceback.format_exception(*record.exc_info))
        return None


async def _send_error_digest(errors: list[BufferedError]):
    """Check setting, format, and send error digest to all admins."""
    from app.db.session import engine as db_engine
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy import text as sa_text

    # Check toggle
    try:
        async with AsyncSession(db_engine) as session:
            result = await session.execute(
                sa_text("SELECT value FROM prompt_templates WHERE key = 'setting.notify_errors'")
            )
            row = result.scalar_one_or_none()
            enabled = (row or "true").lower() == "true"
    except Exception:
        enabled = True  # default to enabled

    if not enabled:
        return

    from app.config import settings
    admin_emails = [e.strip() for e in settings.admin_emails.split(",") if e.strip()]
    if not admin_emails:
        return

    from app.utils.email import _get_provider, _send_via_resend, _send_via_smtp
    provider = _get_provider()
    if provider == "console":
        return  # errors already visible in logs

    subject = f"SweetSin — {len(errors)} error(s) detected"
    body = _format_error_email(errors)

    for email in admin_emails:
        try:
            if provider == "resend":
                await _send_via_resend(email, subject, body)
            else:
                await _send_via_smtp(email, subject, body)
        except Exception:
            pass  # silently fail


def _format_error_email(errors: list[BufferedError]) -> str:
    lines = [
        f"Error digest from SweetSin ({len(errors)} error(s))\n",
        f"Time range: {errors[0].timestamp.strftime('%H:%M:%S')} — "
        f"{errors[-1].timestamp.strftime('%H:%M:%S')} UTC\n",
        "=" * 60,
    ]

    for i, err in enumerate(errors, 1):
        lines.append(f"\n[{i}] {err.level} at {err.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        lines.append(f"    Component: {err.logger_name}")
        lines.append(f"    Message: {err.message}")
        if err.traceback:
            tb = err.traceback
            if len(tb) > 2000:
                tb = tb[:2000] + "\n... (truncated)"
            lines.append(f"    Traceback:\n{tb}")
        lines.append("-" * 40)

    lines.append("\n-- SweetSin Error Monitor\n")
    return "\n".join(lines)


# Singleton
handler = AdminEmailHandler()
