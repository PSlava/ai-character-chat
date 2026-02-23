from abc import ABC, abstractmethod
from typing import AsyncIterator
from dataclasses import dataclass


@dataclass
class LLMMessage:
    role: str  # "system" | "user" | "assistant"
    content: str


@dataclass
class LLMConfig:
    model: str
    temperature: float = 0.8
    max_tokens: int = 1024
    top_p: float = 0.95
    top_k: int = 0  # 0 = disabled
    frequency_penalty: float = 0.3
    presence_penalty: float = 0.3
    min_p: float = 0.0  # 0 = disabled. When > 0, top_p should be 1.0
    content_rating: str = "sfw"  # "sfw" | "moderate" | "nsfw"
    use_flex: bool = False  # Groq Flex tier (10x rate limits, same price)


@dataclass
class LLMResult:
    content: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    model: str = ""


class BaseLLMProvider(ABC):
    @abstractmethod
    async def generate_stream(
        self,
        messages: list[LLMMessage],
        config: LLMConfig,
    ) -> AsyncIterator[str]:
        """Yield text chunks as they arrive from the LLM."""
        ...

    @abstractmethod
    async def generate(
        self,
        messages: list[LLMMessage],
        config: LLMConfig,
    ) -> str:
        """Return the complete response."""
        ...

    async def generate_with_usage(
        self,
        messages: list[LLMMessage],
        config: LLMConfig,
    ) -> LLMResult:
        """Return complete response with token usage. Override in providers that support it."""
        content = await self.generate(messages, config)
        return LLMResult(content=content)
