from typing import AsyncIterator
import httpx
import anthropic
from app.llm.base import BaseLLMProvider, LLMMessage, LLMConfig


class AnthropicProvider(BaseLLMProvider):
    def __init__(self, api_key: str, proxy_url: str | None = None):
        kwargs: dict = {"api_key": api_key}
        if proxy_url:
            kwargs["http_client"] = httpx.AsyncClient(proxy=proxy_url)
        self.client = anthropic.AsyncAnthropic(**kwargs)

    async def generate_stream(
        self,
        messages: list[LLMMessage],
        config: LLMConfig,
    ) -> AsyncIterator[str]:
        system_prompt = ""
        api_messages = []
        for msg in messages:
            if msg.role == "system":
                system_prompt = msg.content
            else:
                api_messages.append({"role": msg.role, "content": msg.content})

        async with self.client.messages.stream(
            model=config.model or "claude-sonnet-4-5-20250929",
            max_tokens=config.max_tokens,
            temperature=config.temperature,
            top_p=config.top_p,
            system=system_prompt,
            messages=api_messages,
        ) as stream:
            async for text in stream.text_stream:
                yield text

    async def generate(
        self,
        messages: list[LLMMessage],
        config: LLMConfig,
    ) -> str:
        system_prompt = ""
        api_messages = []
        for msg in messages:
            if msg.role == "system":
                system_prompt = msg.content
            else:
                api_messages.append({"role": msg.role, "content": msg.content})

        response = await self.client.messages.create(
            model=config.model or "claude-sonnet-4-5-20250929",
            max_tokens=config.max_tokens,
            temperature=config.temperature,
            top_p=config.top_p,
            system=system_prompt,
            messages=api_messages,
        )
        return response.content[0].text
