import asyncio
from typing import AsyncIterator
import httpx
from openai import AsyncOpenAI
from app.llm.base import BaseLLMProvider, LLMMessage, LLMConfig, LLMResult

TIMEOUT = 60


class XAIProvider(BaseLLMProvider):
    """Grok models via xAI OpenAI-compatible API."""

    def __init__(self, api_key: str, proxy_url: str | None = None):
        kwargs: dict = {
            "api_key": api_key,
            "base_url": "https://api.x.ai/v1",
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
        stream = await self.client.chat.completions.create(
            model=config.model or "grok-3-mini",
            messages=api_messages,
            max_tokens=config.max_tokens,
            temperature=config.temperature,
            top_p=config.top_p,
            stream=True,
        )
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
        response = await asyncio.wait_for(
            self.client.chat.completions.create(
                model=config.model or "grok-3-mini",
                messages=api_messages,
                max_tokens=config.max_tokens,
                temperature=config.temperature,
                top_p=config.top_p,
                # xAI does not support frequency/presence penalty
            ),
            timeout=TIMEOUT,
        )
        msg = response.choices[0].message if response.choices else None
        content = msg.content if msg else None
        if not content:
            raise RuntimeError("xAI/Grok returned empty response")
        usage = getattr(response, "usage", None)
        return LLMResult(
            content=content,
            prompt_tokens=getattr(usage, "prompt_tokens", 0) or 0,
            completion_tokens=getattr(usage, "completion_tokens", 0) or 0,
            model=config.model or "grok-3-mini",
        )
