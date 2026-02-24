from app.llm.base import BaseLLMProvider
from app.llm.openai_provider import OpenAIProvider
from app.llm.gemini_provider import GeminiProvider
from app.llm.openrouter_provider import OpenRouterProvider
from app.llm.deepseek_provider import DeepSeekProvider
from app.llm.qwen_provider import QwenProvider
from app.llm.groq_provider import GroqProvider
from app.llm.cerebras_provider import CerebrasProvider
from app.llm.anthropic_provider import AnthropicProvider
from app.llm.together_provider import TogetherProvider
from app.llm import model_cooldown

_providers: dict[str, BaseLLMProvider] = {}


def init_providers(
    openai_key: str | None,
    gemini_key: str | None = None,
    anthropic_key: str | None = None,
    openrouter_key: str | None = None,
    deepseek_key: str | None = None,
    qwen_key: str | None = None,
    groq_key: str | None = None,
    cerebras_key: str | None = None,
    together_key: str | None = None,
    proxy_url: str | None = None,
):
    if anthropic_key:
        _providers["claude"] = AnthropicProvider(api_key=anthropic_key, proxy_url=proxy_url)
    if openai_key:
        _providers["openai"] = OpenAIProvider(api_key=openai_key, proxy_url=proxy_url)
    if gemini_key:
        _providers["gemini"] = GeminiProvider(api_key=gemini_key, proxy_url=proxy_url)
    if openrouter_key:
        _providers["openrouter"] = OpenRouterProvider(api_key=openrouter_key, proxy_url=proxy_url)
    if deepseek_key:
        _providers["deepseek"] = DeepSeekProvider(api_key=deepseek_key, proxy_url=proxy_url)
    if qwen_key:
        _providers["qwen"] = QwenProvider(api_key=qwen_key, proxy_url=proxy_url)
    if groq_key:
        _providers["groq"] = GroqProvider(api_key=groq_key, proxy_url=proxy_url)
    if cerebras_key:
        _providers["cerebras"] = CerebrasProvider(api_key=cerebras_key, proxy_url=proxy_url)
    if together_key:
        _providers["together"] = TogetherProvider(api_key=together_key, proxy_url=proxy_url)


def get_provider(name: str) -> BaseLLMProvider:
    if name not in _providers:
        available = list(_providers.keys())
        raise ValueError(
            f"Provider '{name}' not configured. Available: {available}"
        )
    if not model_cooldown.is_provider_available(name):
        raise ValueError(f"Provider '{name}' is unavailable (blacklisted or disabled)")
    return _providers[name]


def get_available_providers() -> list[str]:
    return list(_providers.keys())
