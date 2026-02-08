from typing import AsyncIterator
from google import genai
from google.genai import types
from app.llm.base import BaseLLMProvider, LLMMessage, LLMConfig


class GeminiProvider(BaseLLMProvider):
    def __init__(self, api_key: str, proxy_url: str | None = None):
        self.client = genai.Client(api_key=api_key)

    async def generate_stream(
        self,
        messages: list[LLMMessage],
        config: LLMConfig,
    ) -> AsyncIterator[str]:
        model = config.model or "gemini-2.0-flash"
        system_instruction, contents = self._build_contents(messages)

        gen_config = types.GenerateContentConfig(
            temperature=config.temperature,
            max_output_tokens=config.max_tokens,
            top_p=config.top_p,
            system_instruction=system_instruction,
        )

        async for chunk in self.client.aio.models.generate_content_stream(
            model=model,
            contents=contents,
            config=gen_config,
        ):
            if chunk.text:
                yield chunk.text

    async def generate(
        self,
        messages: list[LLMMessage],
        config: LLMConfig,
    ) -> str:
        model = config.model or "gemini-2.0-flash"
        system_instruction, contents = self._build_contents(messages)

        gen_config = types.GenerateContentConfig(
            temperature=config.temperature,
            max_output_tokens=config.max_tokens,
            top_p=config.top_p,
            system_instruction=system_instruction,
        )

        response = await self.client.aio.models.generate_content(
            model=model,
            contents=contents,
            config=gen_config,
        )
        return response.text

    def _build_contents(self, messages: list[LLMMessage]):
        system_instruction = None
        contents = []
        for msg in messages:
            if msg.role == "system":
                system_instruction = msg.content
            else:
                role = "user" if msg.role == "user" else "model"
                contents.append(types.Content(
                    role=role,
                    parts=[types.Part(text=msg.content)],
                ))
        return system_instruction, contents
