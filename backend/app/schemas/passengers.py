from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.auth import normalize_phone


class PassengerTemplateRequest(BaseModel):
    passenger_name: str = Field(alias="passengerName", min_length=2, max_length=50)
    id_type: str = Field(default="ID_CARD", alias="idType", min_length=1, max_length=20)
    id_number: str = Field(alias="idNumber", min_length=6, max_length=50)
    phone: str = Field(min_length=11, max_length=11)

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    @field_validator("passenger_name", "id_type", "id_number")
    @classmethod
    def validate_text(cls, value: str) -> str:
        text = value.strip()
        if not text:
            raise ValueError("invalid passenger text")
        return text

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        return normalize_phone(value)


class PassengerTemplateDTO(BaseModel):
    template_id: int = Field(alias="templateId")
    passenger_name: str = Field(alias="passengerName")
    id_type: str = Field(alias="idType")
    id_number: str = Field(alias="idNumber")
    phone: str

    model_config = ConfigDict(populate_by_name=True)
