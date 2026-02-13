from pydantic import BaseModel, Field


class CreateReportRequest(BaseModel):
    reason: str = Field(max_length=50)
    details: str | None = Field(default=None, max_length=2000)


class UpdateReportRequest(BaseModel):
    status: str = Field(max_length=20)
