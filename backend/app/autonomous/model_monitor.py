"""Model monitor — daily check for new/removed/changed models across LLM providers."""

import json
import logging
from datetime import datetime, timezone

import httpx
from sqlalchemy import text

from app.db.session import engine as db_engine
from app.config import settings

logger = logging.getLogger("autonomous.model_monitor")

DB_KEY_PREFIX = "models."


async def check_models() -> bool:
    """Main entry — check all providers for model changes, notify if any."""
    all_changes = {}

    for provider_name in ("groq", "cerebras", "together", "openrouter"):
        try:
            changes = await _check_provider(provider_name)
            if changes:
                all_changes[provider_name] = changes
        except Exception as e:
            logger.warning("Failed to check %s models: %s", provider_name, e)

    if all_changes:
        await _send_notification(all_changes)
        logger.info("Model changes detected in: %s", ", ".join(all_changes.keys()))
    else:
        logger.info("No model changes detected across all providers")

    return True


async def _check_provider(provider_name: str) -> dict | None:
    """Check a single provider for model changes. Returns diff or None."""
    current = await _fetch_models(provider_name)
    if current is None:
        return None

    previous = await _load_previous(provider_name)

    # First run — save baseline silently
    if previous is None:
        await _save_current(provider_name, current)
        logger.info("Baseline saved for %s (%d models)", provider_name, len(current))
        return None

    changes = _diff_models(previous, current)
    await _save_current(provider_name, current)

    if changes["added"] or changes["removed"] or changes["changed"]:
        return changes
    return None


async def _fetch_models(provider_name: str) -> dict | None:
    """Fetch model list from provider API. Returns {model_id: {owned_by, context_window}}."""
    if provider_name == "openrouter":
        return await _fetch_openrouter_models()
    return await _fetch_openai_compatible(provider_name)


async def _fetch_openai_compatible(provider_name: str) -> dict | None:
    """Fetch models via OpenAI-compatible API (Groq, Cerebras, Together)."""
    from app.llm.registry import get_provider

    provider = get_provider(provider_name)
    if not provider:
        logger.debug("Provider %s not configured, skipping", provider_name)
        return None

    try:
        response = await provider.client.models.list()
        result = {}
        for m in response.data:
            result[m.id] = {
                "owned_by": getattr(m, "owned_by", ""),
                "context_window": getattr(m, "context_window", None),
            }
        return result
    except Exception as e:
        logger.warning("Failed to fetch %s models: %s", provider_name, e)
        return None


async def _fetch_openrouter_models() -> dict | None:
    """Fetch free models from OpenRouter API."""
    api_key = settings.openrouter_api_key
    if not api_key:
        logger.debug("OpenRouter API key not set, skipping")
        return None

    try:
        kwargs = {"timeout": 15}
        if settings.proxy_url:
            kwargs["proxy"] = settings.proxy_url
        async with httpx.AsyncClient(**kwargs) as client:
            resp = await client.get(
                "https://openrouter.ai/api/v1/models",
                headers={"Authorization": f"Bearer {api_key}"},
            )
            resp.raise_for_status()
            data = resp.json()

        result = {}
        for m in data.get("data", []):
            model_id = m.get("id", "")
            if not model_id.endswith(":free"):
                continue
            result[model_id] = {
                "owned_by": m.get("architecture", {}).get("instruct_type", ""),
                "context_window": m.get("context_length"),
            }
        return result
    except Exception as e:
        logger.warning("Failed to fetch OpenRouter models: %s", e)
        return None


def _diff_models(previous: dict, current: dict) -> dict:
    """Compare previous and current model lists."""
    prev_ids = set(previous.keys())
    curr_ids = set(current.keys())

    added = sorted(curr_ids - prev_ids)
    removed = sorted(prev_ids - curr_ids)

    changed = []
    for mid in sorted(prev_ids & curr_ids):
        prev = previous[mid]
        curr = current[mid]
        diffs = []
        for field in ("owned_by", "context_window"):
            if prev.get(field) != curr.get(field):
                diffs.append(f"{field}: {prev.get(field)} → {curr.get(field)}")
        if diffs:
            changed.append({"id": mid, "changes": diffs})

    return {"added": added, "removed": removed, "changed": changed}


async def _load_previous(provider_name: str) -> dict | None:
    """Load previous model state from DB."""
    try:
        async with db_engine.connect() as conn:
            result = await conn.execute(
                text("SELECT value FROM prompt_templates WHERE key = :k"),
                {"k": f"{DB_KEY_PREFIX}{provider_name}"},
            )
            row = result.first()
            if row:
                return json.loads(row[0])
    except Exception as e:
        logger.warning("Failed to load previous %s models: %s", provider_name, e)
    return None


async def _save_current(provider_name: str, models: dict):
    """Save current model state to DB."""
    try:
        value = json.dumps(models, ensure_ascii=False)
        async with db_engine.begin() as conn:
            await conn.execute(
                text("""
                    INSERT INTO prompt_templates (key, value, updated_at)
                    VALUES (:k, :v, NOW())
                    ON CONFLICT (key) DO UPDATE SET value = :v, updated_at = NOW()
                """),
                {"k": f"{DB_KEY_PREFIX}{provider_name}", "v": value},
            )
    except Exception as e:
        logger.warning("Failed to save %s models: %s", provider_name, e)


async def _send_notification(all_changes: dict):
    """Send email notification about model changes to all admins."""
    admin_emails = [e.strip() for e in settings.admin_emails.split(",") if e.strip()]
    if not admin_emails:
        logger.info("No admin emails configured, logging changes only")
        return

    from app.utils.email import _get_provider, _send_via_resend, _send_via_smtp

    provider = _get_provider()
    if provider == "console":
        logger.info("Email not configured. Model changes:\n%s", _format_email_body(all_changes))
        return

    subject = "SweetSin — Model Changes Detected"
    body = _format_email_body(all_changes)

    for email in admin_emails:
        try:
            if provider == "resend":
                await _send_via_resend(email, subject, body)
            else:
                await _send_via_smtp(email, subject, body)
            logger.info("Model change notification sent to %s", email)
        except Exception:
            logger.exception("Failed to send model notification to %s", email)


def _format_email_body(all_changes: dict) -> str:
    """Format email body with model changes."""
    lines = [
        "Model changes detected on SweetSin:\n",
        f"Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n",
    ]

    for provider, changes in all_changes.items():
        lines.append(f"\n{'=' * 40}")
        lines.append(f"  {provider.upper()}")
        lines.append(f"{'=' * 40}\n")

        if changes["added"]:
            lines.append("  + NEW MODELS:")
            for mid in changes["added"]:
                lines.append(f"    + {mid}")
            lines.append("")

        if changes["removed"]:
            lines.append("  - REMOVED MODELS:")
            for mid in changes["removed"]:
                lines.append(f"    - {mid}")
            lines.append("")

        if changes["changed"]:
            lines.append("  ~ CHANGED MODELS:")
            for item in changes["changed"]:
                lines.append(f"    ~ {item['id']}")
                for diff in item["changes"]:
                    lines.append(f"      {diff}")
            lines.append("")

    lines.append("\n— SweetSin Model Monitor\n")
    return "\n".join(lines)
