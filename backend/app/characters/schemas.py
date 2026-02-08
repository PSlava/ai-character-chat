from pydantic import BaseModel


class CharacterCreate(BaseModel):
    name: str
    tagline: str | None = None
    avatar_url: str | None = None
    personality: str
    scenario: str | None = None
    greeting_message: str
    example_dialogues: str | None = None
    content_rating: str = "sfw"
    system_prompt_suffix: str | None = None
    tags: list[str] = []
    is_public: bool = True
    preferred_model: str = "claude"


class GenerateFromStoryRequest(BaseModel):
    story_text: str
    character_name: str | None = None
    preferred_model: str = "claude"
    content_rating: str = "sfw"


class CharacterUpdate(BaseModel):
    name: str | None = None
    tagline: str | None = None
    avatar_url: str | None = None
    personality: str | None = None
    scenario: str | None = None
    greeting_message: str | None = None
    example_dialogues: str | None = None
    content_rating: str | None = None
    system_prompt_suffix: str | None = None
    tags: list[str] | None = None
    is_public: bool | None = None
    preferred_model: str | None = None
