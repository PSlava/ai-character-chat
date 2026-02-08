from typing import AsyncIterator
import httpx
from openai import AsyncOpenAI
from app.llm.base import BaseLLMProvider, LLMMessage, LLMConfig

FALLBACK_MODELS = [
    "meta-llama/llama-3.3-70b-instruct:free",
    "qwen/qwen3-next-80b-a3b-instruct:free",
    "deepseek/deepseek-r1-0528:free",
    "nousresearch/hermes-3-llama-3.1-405b:free",
    "mistralai/mistral-small-3.1-24b-instruct:free",
    "google/gemma-3-27b-it:free",
]


class OpenRouterProvider(BaseLLMProvider):
    def __init__(self, api_key: str, proxy_url: str | None = None):
        kwargs: dict = {
            "api_key": api_key,
            "base_url": "https://openrouter.ai/api/v1",
        }
        if proxy_url:
            kwargs["http_client"] = httpx.AsyncClient(proxy=proxy_url)
        self.client = AsyncOpenAI(**kwargs)

    async def generate_stream(
        self,
        messages: list[LLMMessage],
        config: LLMConfig,
    ) -> AsyncIterator[str]:
        api_messages = [{"role": m.role, "content": m.content} for m in messages]
        models_to_try = self._get_models_to_try(config.model)
        errors: list[tuple[str, str]] = []

        for model in models_to_try:
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
        api_messages = [{"role": m.role, "content": m.content} for m in messages]
        models_to_try = self._get_models_to_try(config.model)
        errors: list[tuple[str, str]] = []

        for model in models_to_try:
            try:
                response = await self.client.chat.completions.create(
                    model=model,
                    messages=api_messages,
                    max_tokens=config.max_tokens,
                    temperature=config.temperature,
                    top_p=config.top_p,
                )
                return response.choices[0].message.content
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
        err = str(e)
        # Try to find the 'message' field in the error JSON
        import json
        try:
            # OpenAI SDK errors have .body with parsed JSON
            body = getattr(e, "body", None)
            if body and isinstance(body, dict):
                error_obj = body.get("error", body)
                msg = error_obj.get("message", "")
                # Also check metadata.raw for provider-specific errors
                meta = error_obj.get("metadata", {})
                raw = meta.get("raw", "")
                provider = meta.get("provider_name", "")
                if raw and provider:
                    return f"{msg} (провайдер: {provider})"
                if msg:
                    return msg
        except Exception:
            pass
        # Fallback: trim long error strings
        if len(err) > 200:
            err = err[:200] + "..."
        return err

    @staticmethod
    def _is_retryable(e: Exception) -> bool:
        err = str(e)
        return "429" in err or "402" in err or "rate" in err.lower() or "404" in err or "No endpoints" in err or "spend limit" in err.lower()

    @staticmethod
    def _format_errors(errors: list[tuple[str, str]]) -> str:
        """Format per-model errors into a readable message."""
        lines = ["Все модели недоступны:"]
        for model, reason in errors:
            lines.append(f"  • {model}: {reason}")
        return "\n".join(lines)

    def _get_models_to_try(self, preferred: str) -> list[str]:
        """Return preferred model first, then fallbacks."""
        model = preferred or FALLBACK_MODELS[0]
        models = [model]
        for fb in FALLBACK_MODELS:
            if fb != model:
                models.append(fb)
        return models
