from typing import AsyncIterator
import httpx
from openai import AsyncOpenAI, BadRequestError
from app.llm.base import BaseLLMProvider, LLMMessage, LLMConfig, LLMResult
from app.llm.thinking_filter import strip_thinking

CONTENT_MODERATION_MSG = "Qwen отклонил запрос из-за модерации контента. Попробуйте переформулировать сообщение или используйте другую модель (DeepSeek, OpenRouter)."

TIMEOUT = 60


class QwenProvider(BaseLLMProvider):
    def __init__(self, api_key: str, proxy_url: str | None = None):
        kwargs: dict = {
            "api_key": api_key,
            "base_url": "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
            "timeout": TIMEOUT,
        }
        if proxy_url:
            kwargs["http_client"] = httpx.AsyncClient(proxy=proxy_url, timeout=TIMEOUT)
        self.client = AsyncOpenAI(**kwargs)

    async def generate_stream(
        self,
        messages: list[LLMMessage],
        config: LLMConfig,
    ) -> AsyncIterator[str]:
        api_messages = [{"role": m.role, "content": m.content} for m in messages]
        try:
            stream = await self.client.chat.completions.create(
                model=config.model or "qwen3-32b",
                messages=api_messages,
                max_tokens=config.max_tokens,
                temperature=config.temperature,
                top_p=config.top_p,
                frequency_penalty=config.frequency_penalty,
                presence_penalty=config.presence_penalty,
                stream=True,
                extra_body={"enable_thinking": False},
            )
        except BadRequestError as e:
            if "data_inspection_failed" in str(e):
                raise RuntimeError(CONTENT_MODERATION_MSG) from e
            raise
        async for chunk in stream:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta and delta.content:
                yield delta.content

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
        api_messages = [{"role": m.role, "content": m.content} for m in messages]
        try:
            response = await self.client.chat.completions.create(
                model=config.model or "qwen3-32b",
                messages=api_messages,
                max_tokens=config.max_tokens,
                temperature=config.temperature,
                top_p=config.top_p,
                frequency_penalty=config.frequency_penalty,
                presence_penalty=config.presence_penalty,
                extra_body={"enable_thinking": False},
            )
        except BadRequestError as e:
            if "data_inspection_failed" in str(e):
                raise RuntimeError(CONTENT_MODERATION_MSG) from e
            raise
        content = response.choices[0].message.content if response.choices else None
        if not content:
            raise RuntimeError("Qwen returned empty response")
        content = strip_thinking(content)
        usage = getattr(response, "usage", None)
        return LLMResult(
            content=content,
            prompt_tokens=getattr(usage, "prompt_tokens", 0) or 0,
            completion_tokens=getattr(usage, "completion_tokens", 0) or 0,
            model=config.model or "qwen3-32b",
        )
