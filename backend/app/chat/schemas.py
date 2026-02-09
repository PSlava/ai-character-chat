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
