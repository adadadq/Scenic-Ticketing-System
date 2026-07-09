from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AnnouncementDTO(BaseModel):
    title: str
    content: str
    updated_at: datetime = Field(alias="updatedAt")
    operator_display_name: str = Field(alias="operatorDisplayName")

    model_config = ConfigDict(populate_by_name=True)


class AnnouncementPublishRequest(BaseModel):
    title: str = Field(min_length=1, max_length=40)
    content: str = Field(min_length=1, max_length=200)

    @field_validator("title", "content")
    @classmethod
    def strip_text(cls, value: str) -> str:
        text = value.strip()
        if not text:
            raise ValueError("empty announcement")
        return text
