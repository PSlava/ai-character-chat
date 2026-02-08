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

        last_error = None
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
                last_error = e
                if self._is_retryable(e):
                    continue
                raise

        if last_error:
            raise last_error

    async def generate(
        self,
        messages: list[LLMMessage],
        config: LLMConfig,
    ) -> str:
        api_messages = [{"role": m.role, "content": m.content} for m in messages]
        models_to_try = self._get_models_to_try(config.model)

        last_error = None
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
                last_error = e
                if self._is_retryable(e):
                    continue
                raise

        raise last_error

    @staticmethod
    def _is_retryable(e: Exception) -> bool:
        err = str(e)
        return "429" in err or "rate" in err.lower() or "404" in err or "No endpoints" in err

    def _get_models_to_try(self, preferred: str) -> list[str]:
        """Return preferred model first, then fallbacks."""
        model = preferred or FALLBACK_MODELS[0]
        models = [model]
        for fb in FALLBACK_MODELS:
            if fb != model:
                models.append(fb)
        return models
