from pydantic import BaseModel, Field


class PageViewRequest(BaseModel):
    path: str = Field(max_length=500)
    referrer: str | None = Field(None, max_length=1000)
