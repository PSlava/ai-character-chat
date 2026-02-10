from typing import AsyncIterator
import httpx
from openai import AsyncOpenAI
from app.llm.base import BaseLLMProvider, LLMMessage, LLMConfig


class OpenAIProvider(BaseLLMProvider):
    def __init__(self, api_key: str, proxy_url: str | None = None):
        kwargs: dict = {"api_key": api_key}
        if proxy_url:
            kwargs["http_client"] = httpx.AsyncClient(proxy=proxy_url)
        self.client = AsyncOpenAI(**kwargs)

    async def generate_stream(
        self,
        messages: list[LLMMessage],
        config: LLMConfig,
    ) -> AsyncIterator[str]:
        api_messages = [{"role": m.role, "content": m.content} for m in messages]

        stream = await self.client.chat.completions.create(
            model=config.model or "gpt-4o",
            messages=api_messages,
            max_tokens=config.max_tokens,
            temperature=config.temperature,
            top_p=config.top_p,
            frequency_penalty=config.frequency_penalty,
            presence_penalty=config.presence_penalty,
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                yield delta.content

    async def generate(
        self,
        messages: list[LLMMessage],
        config: LLMConfig,
    ) -> str:
        api_messages = [{"role": m.role, "content": m.content} for m in messages]

        response = await self.client.chat.completions.create(
            model=config.model or "gpt-4o",
            messages=api_messages,
            max_tokens=config.max_tokens,
            temperature=config.temperature,
            top_p=config.top_p,
            frequency_penalty=config.frequency_penalty,
            presence_penalty=config.presence_penalty,
        )
        return response.choices[0].message.content
