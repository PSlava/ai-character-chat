import asyncio
from typing import AsyncIterator
import httpx
from openai import AsyncOpenAI
from app.llm.base import BaseLLMProvider, LLMMessage, LLMConfig
from app.llm.openrouter_models import get_fallback_models

PER_MODEL_TIMEOUT = 20  # seconds per model attempt

# Models that don't support system role — merge into first user message
NO_SYSTEM_ROLE = {"google/gemma-3-27b-it:free", "google/gemma-3-12b-it:free", "google/gemma-3-4b-it:free"}


class OpenRouterProvider(BaseLLMProvider):
    def __init__(self, api_key: str, proxy_url: str | None = None):
        kwargs: dict = {
            "api_key": api_key,
            "base_url": "https://openrouter.ai/api/v1",
            "timeout": PER_MODEL_TIMEOUT,
        }
        if proxy_url:
            kwargs["http_client"] = httpx.AsyncClient(proxy=proxy_url, timeout=PER_MODEL_TIMEOUT)
        self.client = AsyncOpenAI(**kwargs)

    @staticmethod
    def _prepare_messages(messages: list[LLMMessage], model: str) -> list[dict]:
        api_messages = [{"role": m.role, "content": m.content} for m in messages]
        if model in NO_SYSTEM_ROLE:
            system_parts = [m["content"] for m in api_messages if m["role"] == "system"]
            api_messages = [m for m in api_messages if m["role"] != "system"]
            if system_parts and api_messages:
                prefix = "\n\n".join(system_parts)
                api_messages[0]["content"] = f"{prefix}\n\n{api_messages[0]['content']}"
        return api_messages

    async def generate_stream(
        self,
        messages: list[LLMMessage],
        config: LLMConfig,
    ) -> AsyncIterator[str]:
        models_to_try = self._get_models_to_try(config.model)
        errors: list[tuple[str, str]] = []

        for model in models_to_try:
            api_messages = self._prepare_messages(messages, model)
            try:
                stream = await self.client.chat.completions.create(
                    model=model,
                    messages=api_messages,
                    max_tokens=config.max_tokens,
                    temperature=config.temperature,
                    top_p=config.top_p,
                    stream=True,
                )
                async for chunk in stream:
                    if chunk.choices and chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
                return
            except Exception as e:
                reason = self._extract_reason(e)
                errors.append((model.split("/")[-1].replace(":free", ""), reason))
                if self._is_retryable(e):
                    continue
                raise RuntimeError(self._format_errors(errors))

        raise RuntimeError(self._format_errors(errors))

    async def generate(
        self,
        messages: list[LLMMessage],
        config: LLMConfig,
    ) -> str:
        models_to_try = self._get_models_to_try(config.model)
        errors: list[tuple[str, str]] = []

        for model in models_to_try:
            api_messages = self._prepare_messages(messages, model)
            try:
                response = await asyncio.wait_for(
                    self.client.chat.completions.create(
                        model=model,
                        messages=api_messages,
                        max_tokens=config.max_tokens,
                        temperature=config.temperature,
                        top_p=config.top_p,
                    ),
                    timeout=PER_MODEL_TIMEOUT,
                )
                content = response.choices[0].message.content if response.choices else None
                if not content:
                    raise RuntimeError("Модель вернула пустой ответ")
                return content
            except asyncio.TimeoutError:
                errors.append((model.split("/")[-1].replace(":free", ""), "таймаут"))
                continue
            except Exception as e:
                reason = self._extract_reason(e)
                errors.append((model.split("/")[-1].replace(":free", ""), reason))
                if self._is_retryable(e):
                    continue
                raise RuntimeError(self._format_errors(errors))

        raise RuntimeError(self._format_errors(errors))

    @staticmethod
    def _extract_reason(e: Exception) -> str:
        """Extract human-readable reason from OpenRouter error."""
        try:
            body = getattr(e, "body", None)
            if body and isinstance(body, dict):
                error_obj = body.get("error", body)
                msg = error_obj.get("message", "")
                meta = error_obj.get("metadata", {})
                raw = meta.get("raw", "")
                provider = meta.get("provider_name", "")
                if raw and provider:
                    return f"{msg} ({provider})"
                if msg:
                    return msg
        except Exception:
            pass
        err = str(e)
        if len(err) > 150:
            err = err[:150] + "..."
        return err

    @staticmethod
    def _is_retryable(e: Exception) -> bool:
        err = str(e)
        return any(s in err for s in ("429", "402", "404", "No endpoints", "пустой", "Provider returned error", "INVALID_ARGUMENT", "not enabled")) or "rate" in err.lower() or "spend limit" in err.lower()

    @staticmethod
    def _format_errors(errors: list[tuple[str, str]]) -> str:
        lines = ["Все модели недоступны:"]
        for model, reason in errors:
            lines.append(f"  • {model}: {reason}")
        return "\n".join(lines)

    def _get_models_to_try(self, preferred: str) -> list[str]:
        fallbacks = get_fallback_models(limit=3)
        if not preferred:
            return fallbacks
        models = [preferred]
        for fb in fallbacks:
            if fb != preferred and len(models) < 3:
                models.append(fb)
        return models
