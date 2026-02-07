from pydantic import BaseModel


class CreateChatRequest(BaseModel):
    character_id: str
    model: str | None = None  # override character's preferred model


class SendMessageRequest(BaseModel):
    content: str
