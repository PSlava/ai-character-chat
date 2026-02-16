"""Autonomous scheduler — hourly check loop, dispatches daily tasks."""

import asyncio
import logging
from datetime import datetime, timezone, timedelta

from sqlalchemy import text

from app.db.session import engine as db_engine

logger = logging.getLogger("autonomous")
logger.setLevel(logging.INFO)
if not logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("[%(asctime)s] %(name)s %(levelname)s: %(message)s"))
    logger.addHandler(_handler)

# First run delay (let the server warm up)
_STARTUP_DELAY = 5 * 60  # 5 minutes
_CHECK_INTERVAL = 3600  # 1 hour
_TASK_INTERVAL = timedelta(hours=24)


async def _get_last_run(key: str) -> datetime | None:
    """Read last run timestamp from prompt_templates (scheduler.* keys)."""
    try:
        async with db_engine.connect() as conn:
            result = await conn.execute(
                text("SELECT value FROM prompt_templates WHERE key = :k"),
                {"k": f"scheduler.{key}"},
            )
            row = result.first()
            if row:
                return datetime.fromisoformat(row[0])
    except Exception as e:
        logger.warning("Failed to read scheduler state %s: %s", key, e)
    return None


async def _set_last_run(key: str, dt: datetime | None = None):
    """Write last run timestamp to prompt_templates."""
    now = (dt or datetime.now(timezone.utc)).isoformat()
    try:
        async with db_engine.begin() as conn:
            # Upsert
            await conn.execute(
                text("""
                    INSERT INTO prompt_templates (key, value, updated_at)
                    VALUES (:k, :v, NOW())
                    ON CONFLICT (key) DO UPDATE SET value = :v, updated_at = NOW()
                """),
                {"k": f"scheduler.{key}", "v": now},
            )
    except Exception as e:
        logger.warning("Failed to save scheduler state %s: %s", key, e)


def _should_run(last_run: datetime | None) -> bool:
    """Check if enough time has passed since last run."""
    if last_run is None:
        return True
    return datetime.now(timezone.utc) - last_run >= _TASK_INTERVAL


async def run_scheduler():
    """Main scheduler loop. Call via asyncio.create_task() from lifespan."""
    logger.info("Scheduler starting, first check in %d seconds", _STARTUP_DELAY)
    await asyncio.sleep(_STARTUP_DELAY)

    while True:
        try:
            await _run_cycle()
        except Exception:
            logger.exception("Scheduler cycle failed")

        await asyncio.sleep(_CHECK_INTERVAL)


async def _run_cycle():
    """Single scheduler cycle — check each task and run if due."""
    logger.info("Scheduler cycle starting")

    # 1) Character generation
    last_char = await _get_last_run("last_character")
    if _should_run(last_char):
        try:
            from app.autonomous.character_generator import generate_daily_character
            ok = await generate_daily_character()
            if ok:
                await _set_last_run("last_character")
                logger.info("Daily character generated successfully")
            else:
                logger.warning("Daily character generation returned False")
        except Exception:
            logger.exception("Character generation failed")
            # Send email notification to admins
            await _notify_admin_error("Character generation failed")

    # 2) Counter growth
    last_counters = await _get_last_run("last_counters")
    if _should_run(last_counters):
        try:
            from app.autonomous.counter_growth import grow_counters
            await grow_counters()
            await _set_last_run("last_counters")
            logger.info("Counter growth completed")
        except Exception:
            logger.exception("Counter growth failed")

    # 3) Cleanup
    last_cleanup = await _get_last_run("last_cleanup")
    if _should_run(last_cleanup):
        try:
            from app.autonomous.cleanup import run_cleanup
            await run_cleanup()
            await _set_last_run("last_cleanup")
            logger.info("Cleanup completed")
        except Exception:
            logger.exception("Cleanup failed")

    logger.info("Scheduler cycle complete")


async def _notify_admin_error(error_msg: str):
    """Send error notification to all admin emails."""
    try:
        from app.config import settings
        admin_emails = [e.strip() for e in settings.admin_emails.split(",") if e.strip()]
        if not admin_emails:
            return

        from app.utils.email import _get_provider, _send_via_resend, _send_via_smtp
        provider = _get_provider()
        if provider == "console":
            logger.warning("Email not configured. Error: %s", error_msg)
            return

        import traceback
        subject = "SweetSin — Autonomous Task Error"
        body = (
            f"An autonomous task failed on SweetSin:\n\n"
            f"  Error: {error_msg}\n\n"
            f"  Time: {datetime.now(timezone.utc).isoformat()}\n\n"
            f"  Traceback:\n{traceback.format_exc()}\n\n"
            f"— SweetSin Scheduler\n"
        )

        for email in admin_emails:
            try:
                if provider == "resend":
                    await _send_via_resend(email, subject, body)
                else:
                    await _send_via_smtp(email, subject, body)
            except Exception:
                logger.exception("Failed to send error notification to %s", email)
    except Exception:
        logger.exception("_notify_admin_error itself failed")
