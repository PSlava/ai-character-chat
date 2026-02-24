from typing import AsyncIterator
import httpx
from openai import AsyncOpenAI
from app.llm.base import BaseLLMProvider, LLMMessage, LLMConfig, LLMResult
from app.llm.thinking_filter import ThinkingFilter, strip_thinking, has_foreign_chars
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

    def _build_params(self, model: str, api_messages: list, config: LLMConfig, stream: bool = False, flex: bool = False) -> dict:
        """Build common params for chat.completions.create."""
        params = {
            "model": model,
            "messages": api_messages,
            "max_tokens": config.max_tokens,
            "temperature": config.temperature,
            "top_p": config.top_p,
            "frequency_penalty": config.frequency_penalty,
            "presence_penalty": config.presence_penalty,
            "stream": stream,
        }
        if flex:
            params["extra_body"] = {"service_tier": "flex"}
        return params

    async def generate_stream(
        self,
        messages: list[LLMMessage],
        config: LLMConfig,
    ) -> AsyncIterator[str]:
        await self.ensure_models_loaded()
        models = self._get_models_to_try(config.model, nsfw=config.content_rating == "nsfw")
        errors: list[tuple[str, str]] = []
        api_messages = [{"role": m.role, "content": m.content} for m in messages]
        # Try flex first (10x limits), then normal on 498
        tiers = [True, False] if config.use_flex else [False]

        for model in models:
            self.last_model_used = model
            for use_flex in tiers:
                try:
                    params = self._build_params(model, api_messages, config, stream=True, flex=use_flex)
                    stream = await self.client.chat.completions.create(**params)
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
                    if use_flex and self._is_flex_unavailable(e):
                        continue  # retry same model without flex
                    model_cooldown.handle_402_if_applicable(PROVIDER, e)
                    if self._is_not_found(e):
                        model_cooldown.mark_not_found(PROVIDER, model)
                    else:
                        model_cooldown.mark_failed(PROVIDER, model)
                    reason = self._extract_reason(e)
                    errors.append((model, reason))
                    if self._is_retryable(e):
                        break  # try next model
                    raise RuntimeError(self._format_errors(errors))

        raise RuntimeError(self._format_errors(errors))

    async def generate(
        self,
        messages: list[LLMMessage],
        config: LLMConfig,
    ) -> str:
        result = await self.generate_with_usage(messages, config)
        return result.content

    async def generate_with_usage(
        self,
        messages: list[LLMMessage],
        config: LLMConfig,
    ) -> LLMResult:
        await self.ensure_models_loaded()
        models = self._get_models_to_try(config.model, nsfw=config.content_rating == "nsfw")
        errors: list[tuple[str, str]] = []
        api_messages = [{"role": m.role, "content": m.content} for m in messages]
        tiers = [True, False] if config.use_flex else [False]

        for model in models:
            self.last_model_used = model
            for use_flex in tiers:
                try:
                    params = self._build_params(model, api_messages, config, stream=False, flex=use_flex)
                    response = await self.client.chat.completions.create(**params)
                    content = response.choices[0].message.content if response.choices else None
                    if not content:
                        raise RuntimeError("Модель вернула пустой ответ")
                    result = strip_thinking(content)
                    if has_foreign_chars(result):
                        raise RuntimeError(f"CJK/foreign chars in response from {model}")
                    usage = getattr(response, "usage", None)
                    return LLMResult(
                        content=result,
                        prompt_tokens=getattr(usage, "prompt_tokens", 0) or 0,
                        completion_tokens=getattr(usage, "completion_tokens", 0) or 0,
                        model=model,
                    )
                except Exception as e:
                    if use_flex and self._is_flex_unavailable(e):
                        continue  # retry same model without flex
                    model_cooldown.handle_402_if_applicable(PROVIDER, e)
                    if self._is_not_found(e):
                        model_cooldown.mark_not_found(PROVIDER, model)
                    else:
                        model_cooldown.mark_failed(PROVIDER, model)
                    reason = self._extract_reason(e)
                    errors.append((model, reason))
                    if self._is_retryable(e):
                        break  # try next model
                    raise RuntimeError(self._format_errors(errors))

        raise RuntimeError(self._format_errors(errors))

    def _get_models_to_try(self, preferred: str, nsfw: bool = False) -> list[str]:
        fallbacks = get_fallback_models(limit=3, nsfw=nsfw)
        if preferred:
            # Preferred first, then fallbacks (in case preferred is deprecated)
            others = [m for m in fallbacks if m != preferred]
            return [preferred] + others
        available = model_cooldown.filter_available(PROVIDER, fallbacks)
        return available or fallbacks

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
    def _is_flex_unavailable(e: Exception) -> bool:
        """Flex tier returns 498 when capacity is exceeded."""
        err = str(e)
        return "498" in err or "capacity_exceeded" in err.lower()

    @staticmethod
    def _is_not_found(e: Exception) -> bool:
        err = str(e).lower()
        return "404" in str(e) or "does not exist" in err or "not found" in err

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
