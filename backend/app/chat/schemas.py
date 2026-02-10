from pydantic import BaseModel


class CreateChatRequest(BaseModel):
    character_id: str
    model: str | None = None  # override character's preferred model


class SendMessageRequest(BaseModel):
    content: str
    model: str | None = None  # override model for this chat
    temperature: float | None = None
    top_p: float | None = None
    top_k: int | None = None
    frequency_penalty: float | None = None
    presence_penalty: float | None = None
    max_tokens: int | None = None
    context_limit: int | None = None  # context window in tokens (4000/8000/16000/0=unlimited)
    language: str | None = None
