from pydantic import BaseModel, Field


class PersonaCreate(BaseModel):
    name: str = Field(max_length=50)
    description: str | None = Field(default=None, max_length=2000)
    is_default: bool = False


class PersonaUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=50)
    description: str | None = Field(default=None, max_length=2000)
    is_default: bool | None = None
