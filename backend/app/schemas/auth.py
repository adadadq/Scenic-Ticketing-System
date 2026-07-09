import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


PHONE_RE = re.compile(r"^1[3-9]\d{9}$")
USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{3,32}$")


def normalize_phone(value: str) -> str:
    phone = value.strip()
    if not PHONE_RE.fullmatch(phone):
        raise ValueError("invalid phone")
    return phone


class VisitorLoginRequest(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=6, max_length=72)

    model_config = ConfigDict(extra="forbid")

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        username = value.strip()
        if not USERNAME_RE.fullmatch(username):
            raise ValueError("invalid username")
        return username


class VisitorRegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=6, max_length=72)
    phone: str = Field(min_length=11, max_length=11)

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        username = value.strip()
        if not USERNAME_RE.fullmatch(username):
            raise ValueError("invalid username")
        return username

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        return normalize_phone(value)


class VisitorMeDTO(BaseModel):
    visitor_id: int = Field(alias="visitorId")
    visitor_name: str = Field(alias="visitorName")
    phone: str
    visitor_scope: str = Field(alias="visitorScope")
    is_registered: bool = Field(alias="isRegistered")

    model_config = {"populate_by_name": True}


class CsrfPayloadDTO(BaseModel):
    header_name: str = Field(alias="headerName")

    model_config = {"populate_by_name": True}


class LogoutPayloadDTO(BaseModel):
    logged_out: Literal[True] = Field(alias="loggedOut")

    model_config = {"populate_by_name": True}
