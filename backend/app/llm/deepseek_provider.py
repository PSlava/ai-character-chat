import asyncio
from typing import AsyncIterator
import httpx
from openai import AsyncOpenAI
from app.llm.base import BaseLLMProvider, LLMMessage, LLMConfig

TIMEOUT = 60  # DeepSeek-reasoner can be slow


class DeepSeekProvider(BaseLLMProvider):
    def __init__(self, api_key: str, proxy_url: str | None = None):
        kwargs: dict = {
            "api_key": api_key,
            "base_url": "https://api.deepseek.com/v1",
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
            model=config.model or "deepseek-chat",
            messages=api_messages,
            max_tokens=config.max_tokens,
            temperature=config.temperature,
            top_p=config.top_p,
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta:
                text = delta.content or getattr(delta, "reasoning_content", None)
                if text:
                    yield text

    async def generate(
        self,
        messages: list[LLMMessage],
        config: LLMConfig,
    ) -> str:
        api_messages = [{"role": m.role, "content": m.content} for m in messages]
        response = await asyncio.wait_for(
            self.client.chat.completions.create(
                model=config.model or "deepseek-chat",
                messages=api_messages,
                max_tokens=config.max_tokens,
                temperature=config.temperature,
                top_p=config.top_p,
            ),
            timeout=TIMEOUT,
        )
        msg = response.choices[0].message if response.choices else None
        content = msg.content if msg else None
        # deepseek-reasoner puts response in reasoning_content
        if not content and msg:
            content = getattr(msg, "reasoning_content", None)
        if not content:
            raise RuntimeError("DeepSeek returned empty response")
        return content
