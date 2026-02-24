from typing import AsyncIterator
import httpx
import anthropic
from app.llm.base import BaseLLMProvider, LLMMessage, LLMConfig, LLMResult

DEFAULT_MODEL = "claude-sonnet-4-6"


class AnthropicProvider(BaseLLMProvider):
    def __init__(self, api_key: str, proxy_url: str | None = None):
        kwargs: dict = {"api_key": api_key}
        if proxy_url:
            kwargs["http_client"] = httpx.AsyncClient(proxy=proxy_url)
        self.client = anthropic.AsyncAnthropic(**kwargs)

    @staticmethod
    def _prepare(messages: list[LLMMessage]) -> tuple[list[dict], list[dict]]:
        """Split messages into system content blocks (with cache_control) and API messages."""
        system_blocks: list[dict] = []
        api_messages: list[dict] = []
        for msg in messages:
            if msg.role == "system":
                system_blocks.append({
                    "type": "text",
                    "text": msg.content,
                    "cache_control": {"type": "ephemeral"},
                })
            else:
                api_messages.append({"role": msg.role, "content": msg.content})
        return system_blocks, api_messages

    async def generate_stream(
        self,
        messages: list[LLMMessage],
        config: LLMConfig,
    ) -> AsyncIterator[str]:
        system_blocks, api_messages = self._prepare(messages)

        kwargs: dict = {
            "model": config.model or DEFAULT_MODEL,
            "max_tokens": config.max_tokens,
            "messages": api_messages,
        }
        if system_blocks:
            kwargs["system"] = system_blocks
        # Anthropic API: temperature and top_p cannot both be specified
        if config.top_p is not None:
            kwargs["top_p"] = config.top_p
        else:
            kwargs["temperature"] = config.temperature

        async with self.client.messages.stream(**kwargs) as stream:
            async for text in stream.text_stream:
                yield text

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
        system_blocks, api_messages = self._prepare(messages)

        kwargs: dict = {
            "model": config.model or DEFAULT_MODEL,
            "max_tokens": config.max_tokens,
            "messages": api_messages,
        }
        if system_blocks:
            kwargs["system"] = system_blocks
        # Anthropic API: temperature and top_p cannot both be specified
        if config.top_p is not None:
            kwargs["top_p"] = config.top_p
        else:
            kwargs["temperature"] = config.temperature

        response = await self.client.messages.create(**kwargs)
        usage = getattr(response, "usage", None)
        return LLMResult(
            content=response.content[0].text,
            prompt_tokens=getattr(usage, "input_tokens", 0) or 0,
            completion_tokens=getattr(usage, "output_tokens", 0) or 0,
            model=config.model or DEFAULT_MODEL,
        )
