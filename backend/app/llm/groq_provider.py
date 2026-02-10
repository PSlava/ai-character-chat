from typing import AsyncIterator
import httpx
from openai import AsyncOpenAI
from app.llm.base import BaseLLMProvider, LLMMessage, LLMConfig
from app.llm.thinking_filter import ThinkingFilter, strip_thinking
from app.llm.groq_models import get_fallback_models, refresh_models, is_cache_stale
from app.llm import model_cooldown

TIMEOUT = 25
PROVIDER = "groq"


class GroqProvider(BaseLLMProvider):
    def __init__(self, api_key: str, proxy_url: str | None = None):
        kwargs: dict = {
            "api_key": api_key,
            "base_url": "https://api.groq.com/openai/v1",
            "timeout": TIMEOUT,
        }
        if proxy_url:
            kwargs["http_client"] = httpx.AsyncClient(proxy=proxy_url, timeout=TIMEOUT)
        self.client = AsyncOpenAI(**kwargs)

    async def ensure_models_loaded(self):
        """Refresh model list from API if cache is stale."""
        if is_cache_stale():
            await refresh_models(self.client)

    async def generate_stream(
        self,
        messages: list[LLMMessage],
        config: LLMConfig,
    ) -> AsyncIterator[str]:
        await self.ensure_models_loaded()
        models = self._get_models_to_try(config.model, nsfw=config.content_rating == "nsfw")
        errors: list[tuple[str, str]] = []
        api_messages = [{"role": m.role, "content": m.content} for m in messages]

        for model in models:
            self.last_model_used = model
            try:
                stream = await self.client.chat.completions.create(
                    model=model,
                    messages=api_messages,
                    max_tokens=config.max_tokens,
                    temperature=config.temperature,
                    top_p=config.top_p,
                    frequency_penalty=config.frequency_penalty,
                    presence_penalty=config.presence_penalty,
                    stream=True,
                )
                has_content = False
                thinking_filter = ThinkingFilter()
                async for chunk in stream:
                    delta = chunk.choices[0].delta if chunk.choices else None
                    if delta and delta.content:
                        clean = thinking_filter.process(delta.content)
                        if clean:
                            has_content = True
                            yield clean
                if not has_content:
                    raise RuntimeError("Модель вернула пустой ответ")
                return
            except Exception as e:
                model_cooldown.mark_failed(PROVIDER, model)
                reason = self._extract_reason(e)
                errors.append((model, reason))
                if self._is_retryable(e):
                    continue
                raise RuntimeError(self._format_errors(errors))

        raise RuntimeError(self._format_errors(errors))

    async def generate(
        self,
        messages: list[LLMMessage],
        config: LLMConfig,
    ) -> str:
        await self.ensure_models_loaded()
        models = self._get_models_to_try(config.model, nsfw=config.content_rating == "nsfw")
        errors: list[tuple[str, str]] = []
        api_messages = [{"role": m.role, "content": m.content} for m in messages]

        for model in models:
            self.last_model_used = model
            try:
                response = await self.client.chat.completions.create(
                    model=model,
                    messages=api_messages,
                    max_tokens=config.max_tokens,
                    temperature=config.temperature,
                    top_p=config.top_p,
                    frequency_penalty=config.frequency_penalty,
                    presence_penalty=config.presence_penalty,
                )
                content = response.choices[0].message.content if response.choices else None
                if not content:
                    raise RuntimeError("Модель вернула пустой ответ")
                return strip_thinking(content)
            except Exception as e:
                model_cooldown.mark_failed(PROVIDER, model)
                reason = self._extract_reason(e)
                errors.append((model, reason))
                if self._is_retryable(e):
                    continue
                raise RuntimeError(self._format_errors(errors))

        raise RuntimeError(self._format_errors(errors))

    def _get_models_to_try(self, preferred: str, nsfw: bool = False) -> list[str]:
        fallbacks = get_fallback_models(limit=3, nsfw=nsfw)
        if preferred:
            # Preferred first, then fallbacks (in case preferred is deprecated)
            others = [m for m in fallbacks if m != preferred]
            return [preferred] + others
        available = model_cooldown.filter_available(PROVIDER, fallbacks)
        return available or fallbacks[:1]

    @staticmethod
    def _extract_reason(e: Exception) -> str:
        try:
            body = getattr(e, "body", None)
            if body and isinstance(body, dict):
                msg = body.get("error", body).get("message", "")
                if msg:
                    return msg[:150]
        except Exception:
            pass
        err = str(e)
        return err[:150] + "..." if len(err) > 150 else err

    @staticmethod
    def _is_retryable(e: Exception) -> bool:
        err = str(e)
        return any(s in err for s in ("429", "402", "404", "пустой", "rate")) or "limit" in err.lower()

    @staticmethod
    def _format_errors(errors: list[tuple[str, str]]) -> str:
        lines = ["Groq — все модели недоступны:"]
        for model, reason in errors:
            short = model.split("/")[-1] if "/" in model else model
            lines.append(f"  • {short}: {reason}")
        return "\n".join(lines)
