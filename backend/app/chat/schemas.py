from pydantic import BaseModel, Field


class CreateChatRequest(BaseModel):
    character_id: str = Field(max_length=100)
    model: str | None = Field(default=None, max_length=200)


class SendMessageRequest(BaseModel):
    content: str = Field(max_length=20000)
    model: str | None = Field(default=None, max_length=200)
    temperature: float | None = Field(default=None, ge=0, le=2)
    top_p: float | None = Field(default=None, ge=0, le=1)
    top_k: int | None = Field(default=None, ge=0, le=200)
    frequency_penalty: float | None = Field(default=None, ge=0, le=2)
    presence_penalty: float | None = Field(default=None, ge=0, le=2)
    max_tokens: int | None = Field(default=None, ge=128, le=8192)
    context_limit: int | None = Field(default=None, ge=0, le=128000)
    language: str | None = Field(default=None, max_length=10)
