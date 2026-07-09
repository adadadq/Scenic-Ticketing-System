from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class AdminTicketSlotQuotaDTO(BaseModel):
    slot_start_time: str = Field(alias="slotStartTime")
    slot_end_time: str = Field(alias="slotEndTime")
    quota: int = Field(ge=0, le=10000)

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("slot_start_time", "slot_end_time")
    @classmethod
    def validate_time_text(cls, value: str) -> str:
        parts = value.split(":")
        if len(parts) != 2:
            raise ValueError("time must be HH:MM")
        hour, minute = (int(part) for part in parts)
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError("time must be HH:MM")
        return f"{hour:02d}:{minute:02d}"

    @model_validator(mode="after")
    def validate_time_order(self) -> "AdminTicketSlotQuotaDTO":
        if self.slot_start_time >= self.slot_end_time:
            raise ValueError("slotStartTime must be before slotEndTime")
        return self


class AdminTicketDTO(BaseModel):
    id: int
    name: str
    type: str
    route: str
    sale_price: Decimal = Field(alias="salePrice")
    stock: int
    allocated_quota: int = Field(alias="allocatedQuota")
    status: str
    description: str | None = None
    date_from: date | None = Field(default=None, alias="dateFrom")
    date_to: date | None = Field(default=None, alias="dateTo")
    slot_quota: int = Field(alias="slotQuota")
    slot_quotas: list[AdminTicketSlotQuotaDTO] = Field(default_factory=list, alias="slotQuotas")

    model_config = ConfigDict(populate_by_name=True)


class AdminTicketSaveRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    type: str = Field(min_length=1, max_length=50)
    route: str = Field(min_length=1, max_length=100)
    sale_price: Decimal = Field(alias="salePrice", gt=0, max_digits=10, decimal_places=2)
    stock: int = Field(ge=0)
    status: str
    description: str | None = Field(default=None, max_length=255)
    date_from: date | None = Field(default=None, alias="dateFrom")
    date_to: date | None = Field(default=None, alias="dateTo")
    slot_quota: int = Field(default=40, alias="slotQuota", ge=0, le=10000)
    slot_quotas: list[AdminTicketSlotQuotaDTO] | None = Field(default=None, alias="slotQuotas", max_length=12)

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    @field_validator("name", "type", "route", "description")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        if value is None:
            return value
        stripped = value.strip()
        return stripped or None

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        if value not in {"ON_SALE", "OFF_SALE"}:
            raise ValueError("invalid ticket status")
        return value

    @model_validator(mode="after")
    def validate_date_range(self) -> "AdminTicketSaveRequest":
        if bool(self.date_from) != bool(self.date_to):
            raise ValueError("dateFrom and dateTo must be provided together")
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValueError("dateFrom must be before dateTo")
        if self.slot_quotas:
            keys = [(slot.slot_start_time, slot.slot_end_time) for slot in self.slot_quotas]
            if len(keys) != len(set(keys)):
                raise ValueError("slotQuotas must not contain duplicate slots")
        return self
