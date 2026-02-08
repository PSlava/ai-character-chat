from app.llm.base import BaseLLMProvider
from app.llm.anthropic_provider import AnthropicProvider
from app.llm.openai_provider import OpenAIProvider
from app.llm.gemini_provider import GeminiProvider

_providers: dict[str, BaseLLMProvider] = {}


def init_providers(
    anthropic_key: str | None,
    openai_key: str | None,
    gemini_key: str | None = None,
):
    if anthropic_key:
        _providers["claude"] = AnthropicProvider(api_key=anthropic_key)
    if openai_key:
        _providers["openai"] = OpenAIProvider(api_key=openai_key)
    if gemini_key:
        _providers["gemini"] = GeminiProvider(api_key=gemini_key)


def get_provider(name: str) -> BaseLLMProvider:
    if name not in _providers:
        available = list(_providers.keys())
        raise ValueError(
            f"Provider '{name}' not configured. Available: {available}"
        )
    return _providers[name]


def get_available_providers() -> list[str]:
    return list(_providers.keys())
