from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AdminSystemSettingLogDTO(BaseModel):
    created_at: datetime = Field(alias="createdAt")
    operator_display_name: str = Field(alias="operatorDisplayName")
    operator_username: str = Field(alias="operatorUsername")
    action: str
    source_ip: str | None = Field(default=None, alias="sourceIp")

    model_config = ConfigDict(populate_by_name=True)


class AdminSystemSettingsDTO(BaseModel):
    scenic_name: str = Field(alias="scenicName")
    service_time_start: str = Field(alias="serviceTimeStart")
    service_time_end: str = Field(alias="serviceTimeEnd")
    ticket_time_start: str = Field(alias="ticketTimeStart")
    ticket_time_end: str = Field(alias="ticketTimeEnd")
    check_in_time_start: str = Field(alias="checkInTimeStart")
    check_in_time_end: str = Field(alias="checkInTimeEnd")
    per_order_limit: int = Field(alias="perOrderLimit")
    session_ttl_minutes: int = Field(alias="sessionTtlMinutes")
    csrf_enabled: bool = Field(alias="csrfEnabled")
    login_guard_enabled: bool = Field(alias="loginGuardEnabled")
    sms_enabled: bool = Field(alias="smsEnabled")
    mail_enabled: bool = Field(alias="mailEnabled")
    refund_enabled: bool = Field(alias="refundEnabled")
    stock_enabled: bool = Field(alias="stockEnabled")
    audit_retention_days: int = Field(alias="auditRetentionDays")
    last_backup_label: str = Field(alias="lastBackupLabel")
    updated_at: datetime | None = Field(default=None, alias="updatedAt")
    recent_logs: list[AdminSystemSettingLogDTO] = Field(default_factory=list, alias="recentLogs")

    model_config = ConfigDict(populate_by_name=True)


class AdminSystemSettingsUpdateRequest(BaseModel):
    scenic_name: str | None = Field(default=None, alias="scenicName", min_length=1, max_length=100)
    service_time_start: str | None = Field(default=None, alias="serviceTimeStart", pattern=r"^\d{2}:\d{2}$")
    service_time_end: str | None = Field(default=None, alias="serviceTimeEnd", pattern=r"^\d{2}:\d{2}$")
    ticket_time_start: str | None = Field(default=None, alias="ticketTimeStart", pattern=r"^\d{2}:\d{2}$")
    ticket_time_end: str | None = Field(default=None, alias="ticketTimeEnd", pattern=r"^\d{2}:\d{2}$")
    check_in_time_start: str | None = Field(default=None, alias="checkInTimeStart", pattern=r"^\d{2}:\d{2}$")
    check_in_time_end: str | None = Field(default=None, alias="checkInTimeEnd", pattern=r"^\d{2}:\d{2}$")
    per_order_limit: int | None = Field(default=None, alias="perOrderLimit", ge=1, le=50)
    session_ttl_minutes: int | None = Field(default=None, alias="sessionTtlMinutes", ge=5, le=480)
    csrf_enabled: bool | None = Field(default=None, alias="csrfEnabled")
    login_guard_enabled: bool | None = Field(default=None, alias="loginGuardEnabled")
    sms_enabled: bool | None = Field(default=None, alias="smsEnabled")
    mail_enabled: bool | None = Field(default=None, alias="mailEnabled")
    refund_enabled: bool | None = Field(default=None, alias="refundEnabled")
    stock_enabled: bool | None = Field(default=None, alias="stockEnabled")
    audit_retention_days: int | None = Field(default=None, alias="auditRetentionDays", ge=30, le=365)

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    @field_validator("scenic_name")
    @classmethod
    def validate_scenic_name(cls, value: str | None) -> str | None:
        if value is None:
            return value
        name = value.strip()
        if not name:
            raise ValueError("invalid scenic name")
        return name

    @field_validator(
        "service_time_start",
        "service_time_end",
        "ticket_time_start",
        "ticket_time_end",
        "check_in_time_start",
        "check_in_time_end",
    )
    @classmethod
    def validate_time(cls, value: str | None) -> str | None:
        if value is None:
            return value
        datetime.strptime(value, "%H:%M")
        return value
