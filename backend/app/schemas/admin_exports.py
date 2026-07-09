from __future__ import annotations

import json
from datetime import datetime
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


ADMIN_EXPORT_JOB_FILTERS_MAX_BYTES = 4096

AdminExportJobType = Literal[
    "ORDER_DETAIL",
    "CHECK_IN_AUDIT",
    "CHECK_IN_FAILURE_AUDIT",
    "REFUND_AUDIT",
    "PAYMENT_RECONCILIATION",
    "PRODUCT_BREAKDOWN",
    "DAILY_TREND",
    "HOURLY_TREND",
    "MONTHLY_TREND",
]
AdminExportJobFileFormat = Literal["CSV", "XLSX"]
AdminExportJobStatus = Literal["PENDING", "RUNNING", "SUCCEEDED", "FAILED"]


def serialized_filters_size(filters: dict[str, Any]) -> int:
    serialized = json.dumps(filters, ensure_ascii=False, separators=(",", ":"), sort_keys=True, default=str)
    return len(serialized.encode("utf-8"))


class AdminExportJobCreateRequest(BaseModel):
    export_type: AdminExportJobType = Field(alias="exportType")
    file_format: AdminExportJobFileFormat = Field(alias="fileFormat")
    filters: dict[str, Any] = Field(
        default_factory=dict,
        description="Export-type-specific filter object. Unknown fields are rejected by the service layer.",
    )

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    @field_validator("filters")
    @classmethod
    def validate_filters(cls, value: dict[str, Any]) -> dict[str, Any]:
        if serialized_filters_size(value) > ADMIN_EXPORT_JOB_FILTERS_MAX_BYTES:
            raise ValueError("filters too large")
        return value


class AdminExportJobDTO(BaseModel):
    job_id: str = Field(alias="jobId")
    export_type: str = Field(alias="exportType")
    file_format: str = Field(alias="fileFormat")
    filters: dict[str, Any]
    status: str
    request_id: str | None = Field(default=None, alias="requestId")
    requested_by_username: str = Field(alias="requestedByUsername")
    requested_by_display_name: str = Field(alias="requestedByDisplayName")
    requested_at: datetime = Field(alias="requestedAt")
    started_at: datetime | None = Field(default=None, alias="startedAt")
    finished_at: datetime | None = Field(default=None, alias="finishedAt")
    file_name: str | None = Field(default=None, alias="fileName")
    error_code: str | None = Field(default=None, alias="errorCode")
    error_message: str | None = Field(default=None, alias="errorMessage")

    model_config = ConfigDict(populate_by_name=True)


class AdminExportJobListDTO(BaseModel):
    items: list[AdminExportJobDTO]
    total: int
    page: int
    page_size: int = Field(alias="pageSize")

    model_config = ConfigDict(populate_by_name=True)


class AdminExportJobAlertEventDTO(BaseModel):
    event_id: int = Field(alias="eventId")
    job_id: str = Field(alias="jobId")
    export_type: str = Field(alias="exportType")
    file_format: str = Field(alias="fileFormat")
    error_code: str = Field(alias="errorCode")
    error_message: str = Field(alias="errorMessage")
    alert_source: str = Field(alias="alertSource")
    created_at: datetime = Field(alias="createdAt")
    occurrence_count: int = Field(alias="occurrenceCount")
    last_seen_at: datetime = Field(alias="lastSeenAt")
    acknowledged_at: datetime | None = Field(default=None, alias="acknowledgedAt")
    acknowledged_by_username: str | None = Field(default=None, alias="acknowledgedByUsername")
    acknowledged_by_display_name: str | None = Field(default=None, alias="acknowledgedByDisplayName")
    acknowledge_note: str | None = Field(default=None, alias="acknowledgeNote")
    closed_at: datetime | None = Field(default=None, alias="closedAt")
    closed_by_username: str | None = Field(default=None, alias="closedByUsername")
    closed_by_display_name: str | None = Field(default=None, alias="closedByDisplayName")
    close_note: str | None = Field(default=None, alias="closeNote")

    model_config = ConfigDict(populate_by_name=True)


class AdminExportJobAlertEventAcknowledgeRequest(BaseModel):
    note: Annotated[str, Field(json_schema_extra={"maxLength": 200})] | None = None

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class AdminExportJobAlertEventCloseRequest(BaseModel):
    note: Annotated[str, Field(json_schema_extra={"maxLength": 200})] | None = None

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class AdminExportJobAlertEventDeleteDTO(BaseModel):
    event_id: int = Field(alias="eventId")
    deleted: bool

    model_config = ConfigDict(populate_by_name=True)


class AdminExportJobAlertEventBatchDeleteRequest(BaseModel):
    event_ids: Annotated[
        list[Annotated[int, Field(ge=1)]],
        Field(alias="eventIds", min_length=1, max_length=100, json_schema_extra={"uniqueItems": True}),
    ]

    model_config = ConfigDict(extra="forbid")

    @field_validator("event_ids")
    @classmethod
    def validate_event_ids(cls, value: list[int]) -> list[int]:
        if len(set(value)) != len(value):
            raise ValueError("eventIds must not contain duplicates")
        return value


class AdminExportJobAlertEventBatchAcknowledgeRequest(BaseModel):
    event_ids: Annotated[
        list[Annotated[int, Field(ge=1)]],
        Field(alias="eventIds", min_length=1, max_length=100, json_schema_extra={"uniqueItems": True}),
    ]
    note: Annotated[str, Field(json_schema_extra={"maxLength": 200})] | None = None

    model_config = ConfigDict(extra="forbid")

    @field_validator("event_ids")
    @classmethod
    def validate_event_ids(cls, value: list[int]) -> list[int]:
        if len(set(value)) != len(value):
            raise ValueError("eventIds must not contain duplicates")
        return value


class AdminExportJobAlertEventBatchAcknowledgeResultDTO(BaseModel):
    event_id: int = Field(alias="eventId")
    acknowledged: bool
    code: str | None = None
    message: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class AdminExportJobAlertEventBatchAcknowledgeDTO(BaseModel):
    total_count: int = Field(alias="totalCount")
    success_count: int = Field(alias="successCount")
    failure_count: int = Field(alias="failureCount")
    results: list[AdminExportJobAlertEventBatchAcknowledgeResultDTO]

    model_config = ConfigDict(populate_by_name=True)


class AdminExportJobAlertEventBatchCloseRequest(BaseModel):
    event_ids: Annotated[
        list[Annotated[int, Field(ge=1)]],
        Field(alias="eventIds", min_length=1, max_length=100, json_schema_extra={"uniqueItems": True}),
    ]
    note: Annotated[str, Field(json_schema_extra={"maxLength": 200})] | None = None

    model_config = ConfigDict(extra="forbid")

    @field_validator("event_ids")
    @classmethod
    def validate_event_ids(cls, value: list[int]) -> list[int]:
        if len(set(value)) != len(value):
            raise ValueError("eventIds must not contain duplicates")
        return value


class AdminExportJobAlertEventBatchCloseResultDTO(BaseModel):
    event_id: int = Field(alias="eventId")
    closed: bool
    code: str | None = None
    message: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class AdminExportJobAlertEventBatchCloseDTO(BaseModel):
    total_count: int = Field(alias="totalCount")
    success_count: int = Field(alias="successCount")
    failure_count: int = Field(alias="failureCount")
    results: list[AdminExportJobAlertEventBatchCloseResultDTO]

    model_config = ConfigDict(populate_by_name=True)


class AdminExportJobAlertEventBatchDeleteResultDTO(BaseModel):
    event_id: int = Field(alias="eventId")
    deleted: bool
    code: str | None = None
    message: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class AdminExportJobAlertEventBatchDeleteDTO(BaseModel):
    total_count: int = Field(alias="totalCount")
    success_count: int = Field(alias="successCount")
    failure_count: int = Field(alias="failureCount")
    results: list[AdminExportJobAlertEventBatchDeleteResultDTO]

    model_config = ConfigDict(populate_by_name=True)


class AdminExportJobAlertEventListDTO(BaseModel):
    items: list[AdminExportJobAlertEventDTO]
    total: int
    page: int
    page_size: int = Field(alias="pageSize")

    model_config = ConfigDict(populate_by_name=True)


class AdminExportJobAlertEventSummaryByErrorCodeDTO(BaseModel):
    error_code: str = Field(alias="errorCode")
    total: int
    acknowledged: int
    unacknowledged: int
    closed: int
    open_count: int = Field(alias="open")

    model_config = ConfigDict(populate_by_name=True)


class AdminExportJobAlertEventSummaryDTO(BaseModel):
    total: int
    acknowledged: int
    unacknowledged: int
    closed: int
    open_count: int = Field(alias="open")
    by_error_code: list[AdminExportJobAlertEventSummaryByErrorCodeDTO] = Field(alias="byErrorCode")

    model_config = ConfigDict(populate_by_name=True)
