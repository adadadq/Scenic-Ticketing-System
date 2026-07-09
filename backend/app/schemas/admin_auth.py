from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AdminLoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=128)

    model_config = ConfigDict(extra="forbid")

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        username = value.strip()
        if not username:
            raise ValueError("invalid username")
        return username


class AdminProfileUpdateRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    current_password: str = Field(alias="currentPassword", min_length=1, max_length=128)
    new_password: str | None = Field(default=None, alias="newPassword", min_length=6, max_length=128)

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        username = value.strip()
        if not username:
            raise ValueError("invalid username")
        return username


class AdminMeDTO(BaseModel):
    admin_user_id: int = Field(alias="adminUserId")
    username: str
    display_name: str = Field(alias="displayName")
    role: Literal["SUPER_ADMIN", "OPERATOR"]

    model_config = ConfigDict(populate_by_name=True)
