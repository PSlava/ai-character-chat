from pydantic import BaseModel, Field


class CharacterCreate(BaseModel):
    name: str = Field(max_length=100)
    tagline: str | None = Field(default=None, max_length=300)
    avatar_url: str | None = Field(default=None, max_length=2000)
    personality: str = Field(max_length=10000)
    appearance: str | None = Field(default=None, max_length=5000)
    scenario: str | None = Field(default=None, max_length=5000)
    greeting_message: str = Field(max_length=5000)
    example_dialogues: str | None = Field(default=None, max_length=10000)
    content_rating: str = Field(default="sfw", max_length=20)
    system_prompt_suffix: str | None = Field(default=None, max_length=5000)
    tags: list[str] = Field(default_factory=list, max_length=20)
    structured_tags: list[str] = Field(default_factory=list, max_length=50)
    is_public: bool = True
    preferred_model: str = Field(default="qwen", max_length=200)
    max_tokens: int = Field(default=2048, ge=128, le=8192)
    response_length: str = Field(default="long", max_length=20)


class GenerateFromStoryRequest(BaseModel):
    story_text: str = Field(max_length=50000)
    character_name: str | None = Field(default=None, max_length=100)
    preferred_model: str = Field(default="qwen", max_length=200)
    content_rating: str = Field(default="sfw", max_length=20)
    extra_instructions: str | None = Field(default=None, max_length=2000)


class CharacterUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=100)
    tagline: str | None = Field(default=None, max_length=300)
    avatar_url: str | None = Field(default=None, max_length=2000)
    personality: str | None = Field(default=None, max_length=10000)
    appearance: str | None = Field(default=None, max_length=5000)
    scenario: str | None = Field(default=None, max_length=5000)
    greeting_message: str | None = Field(default=None, max_length=5000)
    example_dialogues: str | None = Field(default=None, max_length=10000)
    content_rating: str | None = Field(default=None, max_length=20)
    system_prompt_suffix: str | None = Field(default=None, max_length=5000)
    tags: list[str] | None = Field(default=None, max_length=20)
    structured_tags: list[str] | None = Field(default=None, max_length=50)
    is_public: bool | None = None
    preferred_model: str | None = Field(default=None, max_length=200)
    max_tokens: int | None = Field(default=None, ge=128, le=8192)
    response_length: str | None = Field(default=None, max_length=20)
