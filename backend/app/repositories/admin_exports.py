from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any, Protocol

from psycopg.types.json import Jsonb

from app.core.db import connect_db

ADMIN_EXPORT_JOB_AUTO_RETRY_DELAY_SECONDS = 60


@dataclass(frozen=True)
class AdminExportJobCreateRecord:
    job_id: str
    export_type: str
    file_format: str
    filters: dict[str, Any]
    request_id: str | None
    requested_by_admin_user_id: int
    requested_by_username: str
    requested_by_display_name: str


@dataclass(frozen=True)
class AdminExportJobListFilter:
    export_type: str | None
    file_format: str | None
    status: str | None
    page: int
    page_size: int


@dataclass(frozen=True)
class AdminExportJobRecord:
    job_id: str
    export_type: str
    file_format: str
    filters: dict[str, Any]
    status: str
    request_id: str | None
    requested_by_username: str
    requested_by_display_name: str
    requested_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
    file_name: str | None
    error_code: str | None
    error_message: str | None


@dataclass(frozen=True)
class AdminExportJobFileRecord:
    job_id: str
    file_format: str
    file_name: str
    storage_key: str


@dataclass(frozen=True)
class AdminExportJobCleanupFileRecord:
    job_id: str
    storage_key: str


@dataclass(frozen=True)
class AdminExportJobAlertEventCreateRecord:
    job_id: str
    export_type: str
    file_format: str
    error_code: str
    error_message: str
    alert_source: str


@dataclass(frozen=True)
class AdminExportJobAlertEventListFilter:
    job_id: str | None
    export_type: str | None
    file_format: str | None
    error_code: str | None
    acknowledged: bool | None
    closed: bool | None
    date_from: date | None
    date_to: date | None
    page: int
    page_size: int


@dataclass(frozen=True)
class AdminExportJobAlertEventSummaryFilter:
    export_type: str | None
    file_format: str | None
    closed: bool | None
    date_from: date | None
    date_to: date | None


@dataclass(frozen=True)
class AdminExportJobAlertEventRecord:
    event_id: int
    job_id: str
    export_type: str
    file_format: str
    error_code: str
    error_message: str
    alert_source: str
    created_at: datetime
    acknowledged_at: datetime | None
    acknowledged_by_admin_user_id: int | None
    acknowledged_by_username: str | None
    acknowledged_by_display_name: str | None
    acknowledge_note: str | None
    closed_at: datetime | None = None
    closed_by_admin_user_id: int | None = None
    closed_by_username: str | None = None
    closed_by_display_name: str | None = None
    close_note: str | None = None
    occurrence_count: int = 1
    last_seen_at: datetime | None = None


@dataclass(frozen=True)
class AdminExportJobAlertEventAcknowledgeRecord:
    event_id: int
    acknowledged_by_admin_user_id: int
    acknowledged_by_username: str
    acknowledged_by_display_name: str
    acknowledge_note: str | None


@dataclass(frozen=True)
class AdminExportJobAlertEventCloseRecord:
    event_id: int
    closed_by_admin_user_id: int
    closed_by_username: str
    closed_by_display_name: str
    close_note: str | None


@dataclass(frozen=True)
class AdminExportJobAlertEventDeleteResult:
    found: bool
    closed: bool
    deleted: bool


@dataclass(frozen=True)
class AdminExportJobListRecord:
    items: list[AdminExportJobRecord]
    total: int
    page: int
    page_size: int


@dataclass(frozen=True)
class AdminExportJobRecoveryRecord:
    recovered_count: int
    final_failed_jobs: list[AdminExportJobRecord]


@dataclass(frozen=True)
class AdminExportJobAlertEventListRecord:
    items: list[AdminExportJobAlertEventRecord]
    total: int
    page: int
    page_size: int


@dataclass(frozen=True)
class AdminExportJobAlertEventSummaryByErrorCodeRecord:
    error_code: str
    total: int
    acknowledged: int
    unacknowledged: int
    closed: int
    open_count: int


@dataclass(frozen=True)
class AdminExportJobAlertEventSummaryRecord:
    total: int
    acknowledged: int
    unacknowledged: int
    closed: int
    open_count: int
    by_error_code: list[AdminExportJobAlertEventSummaryByErrorCodeRecord]


class AdminExportJobRepository(Protocol):
    def create_export_job(self, record: AdminExportJobCreateRecord) -> AdminExportJobRecord:
        ...

    def claim_next_pending_job(self) -> AdminExportJobRecord | None:
        ...

    def recover_stale_running_jobs(
        self,
        *,
        timeout_seconds: int,
        error_code: str,
        error_message: str,
    ) -> AdminExportJobRecoveryRecord:
        ...

    def mark_export_job_succeeded(
        self,
        job_id: str,
        *,
        file_name: str,
        storage_key: str,
    ) -> AdminExportJobRecord | None:
        ...

    def mark_export_job_failed(
        self,
        job_id: str,
        *,
        error_code: str,
        error_message: str,
        retryable: bool = False,
    ) -> AdminExportJobRecord | None:
        ...

    def retry_failed_export_job(self, job_id: str) -> AdminExportJobRecord | None:
        ...

    def list_export_jobs(self, filters: AdminExportJobListFilter) -> AdminExportJobListRecord:
        ...

    def get_export_job(self, job_id: str) -> AdminExportJobRecord | None:
        ...

    def get_export_job_file(self, job_id: str) -> AdminExportJobFileRecord | None:
        ...

    def list_succeeded_export_job_files_finished_before(
        self,
        finished_before: datetime,
        *,
        limit: int,
    ) -> list[AdminExportJobCleanupFileRecord]:
        ...

    def clear_export_job_file_metadata(self, job_id: str, *, storage_key: str) -> bool:
        ...

    def create_export_job_alert_event(self, record: AdminExportJobAlertEventCreateRecord) -> None:
        ...

    def list_export_job_alert_events(
        self,
        filters: AdminExportJobAlertEventListFilter,
    ) -> AdminExportJobAlertEventListRecord:
        ...

    def summarize_export_job_alert_events(
        self,
        filters: AdminExportJobAlertEventSummaryFilter,
    ) -> AdminExportJobAlertEventSummaryRecord:
        ...

    def acknowledge_export_job_alert_event(
        self,
        record: AdminExportJobAlertEventAcknowledgeRecord,
    ) -> AdminExportJobAlertEventRecord | None:
        ...

    def close_export_job_alert_event(
        self,
        record: AdminExportJobAlertEventCloseRecord,
    ) -> AdminExportJobAlertEventRecord | None:
        ...

    def reopen_export_job_alert_event(self, event_id: int) -> AdminExportJobAlertEventRecord | None:
        ...

    def delete_closed_export_job_alert_event(self, event_id: int) -> AdminExportJobAlertEventDeleteResult:
        ...


def admin_export_job_from_row(row: dict) -> AdminExportJobRecord:
    return AdminExportJobRecord(
        job_id=row["job_id"],
        export_type=row["export_type"],
        file_format=row["file_format"],
        filters=row["filters"],
        status=row["status"],
        request_id=row.get("request_id"),
        requested_by_username=row["requested_by_username"],
        requested_by_display_name=row["requested_by_display_name"],
        requested_at=row["requested_at"],
        started_at=row["started_at"],
        finished_at=row["finished_at"],
        file_name=row["file_name"],
        error_code=row["error_code"],
        error_message=row["error_message"],
    )


def admin_export_job_alert_event_from_row(row: dict) -> AdminExportJobAlertEventRecord:
    return AdminExportJobAlertEventRecord(
        event_id=row["id"],
        job_id=row["job_id"],
        export_type=row["export_type"],
        file_format=row["file_format"],
        error_code=row["error_code"],
        error_message=row["error_message"],
        alert_source=row["alert_source"],
        created_at=row["created_at"],
        acknowledged_at=row["acknowledged_at"],
        acknowledged_by_admin_user_id=row["acknowledged_by_admin_user_id"],
        acknowledged_by_username=row["acknowledged_by_username"],
        acknowledged_by_display_name=row["acknowledged_by_display_name"],
        acknowledge_note=row["acknowledge_note"],
        closed_at=row.get("closed_at"),
        closed_by_admin_user_id=row.get("closed_by_admin_user_id"),
        closed_by_username=row.get("closed_by_username"),
        closed_by_display_name=row.get("closed_by_display_name"),
        close_note=row.get("close_note"),
        occurrence_count=row.get("occurrence_count", 1),
        last_seen_at=row.get("last_seen_at") or row["created_at"],
    )


class PostgresAdminExportJobRepository:
    def create_export_job(self, record: AdminExportJobCreateRecord) -> AdminExportJobRecord:
        with connect_db() as connection:
            row = connection.execute(
                """
                INSERT INTO admin_export_job (
                    job_id,
                    export_type,
                    file_format,
                    filters,
                    request_id,
                    status,
                    requested_by_admin_user_id,
                    requested_by_username,
                    requested_by_display_name
                )
                VALUES (%s, %s, %s, %s, %s, 'PENDING', %s, %s, %s)
                RETURNING
                    job_id,
                    export_type,
                    file_format,
                    filters,
                    status,
                    request_id,
                    requested_by_username,
                    requested_by_display_name,
                    requested_at,
                    started_at,
                    finished_at,
                    file_name,
                    error_code,
                    error_message
                """,
                (
                    record.job_id,
                    record.export_type,
                    record.file_format,
                    Jsonb(record.filters),
                    record.request_id,
                    record.requested_by_admin_user_id,
                    record.requested_by_username,
                    record.requested_by_display_name,
                ),
            ).fetchone()
        return admin_export_job_from_row(row)

    def claim_next_pending_job(self) -> AdminExportJobRecord | None:
        with connect_db() as connection:
            row = connection.execute(
                """
                UPDATE admin_export_job
                SET
                    status = 'RUNNING',
                    started_at = COALESCE(started_at, CURRENT_TIMESTAMP),
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = (
                    SELECT id
                    FROM admin_export_job
                    WHERE status = 'PENDING'
                        AND (next_attempt_at IS NULL OR next_attempt_at <= CURRENT_TIMESTAMP)
                    ORDER BY requested_at ASC, id ASC
                    FOR UPDATE SKIP LOCKED
                    LIMIT 1
                )
                RETURNING
                    job_id,
                    export_type,
                    file_format,
                    filters,
                    status,
                    request_id,
                    requested_by_username,
                    requested_by_display_name,
                    requested_at,
                    started_at,
                    finished_at,
                    file_name,
                    error_code,
                    error_message
                """,
                (),
            ).fetchone()
        return admin_export_job_from_row(row) if row else None

    def recover_stale_running_jobs(
        self,
        *,
        timeout_seconds: int,
        error_code: str,
        error_message: str,
    ) -> AdminExportJobRecoveryRecord:
        with connect_db() as connection:
            rows = connection.execute(
                """
                UPDATE admin_export_job
                SET
                    status = CASE
                        WHEN retry_count < max_retries THEN 'PENDING'
                        ELSE 'FAILED'
                    END,
                    retry_count = CASE
                        WHEN retry_count < max_retries THEN retry_count + 1
                        ELSE retry_count
                    END,
                    started_at = CASE
                        WHEN retry_count < max_retries THEN NULL
                        ELSE started_at
                    END,
                    finished_at = CASE
                        WHEN retry_count < max_retries THEN NULL
                        ELSE CURRENT_TIMESTAMP
                    END,
                    file_name = CASE
                        WHEN retry_count < max_retries THEN NULL
                        ELSE file_name
                    END,
                    storage_key = CASE
                        WHEN retry_count < max_retries THEN NULL
                        ELSE storage_key
                    END,
                    error_code = CASE
                        WHEN retry_count < max_retries THEN NULL
                        ELSE %s
                    END,
                    error_message = CASE
                        WHEN retry_count < max_retries THEN NULL
                        ELSE %s
                    END,
                    next_attempt_at = NULL,
                    updated_at = CURRENT_TIMESTAMP
                WHERE
                    status = 'RUNNING'
                    AND started_at IS NOT NULL
                    AND started_at < CURRENT_TIMESTAMP - (%s * INTERVAL '1 second')
                RETURNING
                    job_id,
                    export_type,
                    file_format,
                    filters,
                    status,
                    request_id,
                    requested_by_username,
                    requested_by_display_name,
                    requested_at,
                    started_at,
                    finished_at,
                    file_name,
                    error_code,
                    error_message
                """,
                (error_code, error_message, timeout_seconds),
            ).fetchall()
        records = [admin_export_job_from_row(row) for row in rows]
        return AdminExportJobRecoveryRecord(
            recovered_count=len(records),
            final_failed_jobs=[record for record in records if record.status == "FAILED"],
        )

    def mark_export_job_succeeded(
        self,
        job_id: str,
        *,
        file_name: str,
        storage_key: str,
    ) -> AdminExportJobRecord | None:
        with connect_db() as connection:
            row = connection.execute(
                """
                UPDATE admin_export_job
                SET
                    status = 'SUCCEEDED',
                    finished_at = CURRENT_TIMESTAMP,
                    file_name = %s,
                    storage_key = %s,
                    next_attempt_at = NULL,
                    error_code = NULL,
                    error_message = NULL,
                    updated_at = CURRENT_TIMESTAMP
                WHERE job_id = %s AND status = 'RUNNING'
                RETURNING
                    job_id,
                    export_type,
                    file_format,
                    filters,
                    status,
                    request_id,
                    requested_by_username,
                    requested_by_display_name,
                    requested_at,
                    started_at,
                    finished_at,
                    file_name,
                    error_code,
                    error_message
                """,
                (file_name, storage_key, job_id),
            ).fetchone()
            return admin_export_job_from_row(row) if row else None

    def mark_export_job_failed(
        self,
        job_id: str,
        *,
        error_code: str,
        error_message: str,
        retryable: bool = False,
    ) -> AdminExportJobRecord | None:
        with connect_db() as connection:
            row = connection.execute(
                """
                UPDATE admin_export_job
                SET
                    status = CASE
                        WHEN %s AND retry_count < max_retries THEN 'PENDING'
                        ELSE 'FAILED'
                    END,
                    retry_count = CASE
                        WHEN %s AND retry_count < max_retries THEN retry_count + 1
                        ELSE retry_count
                    END,
                    started_at = CASE
                        WHEN %s AND retry_count < max_retries THEN NULL
                        ELSE started_at
                    END,
                    finished_at = CASE
                        WHEN %s AND retry_count < max_retries THEN NULL
                        ELSE CURRENT_TIMESTAMP
                    END,
                    file_name = CASE
                        WHEN %s AND retry_count < max_retries THEN NULL
                        ELSE file_name
                    END,
                    storage_key = CASE
                        WHEN %s AND retry_count < max_retries THEN NULL
                        ELSE storage_key
                    END,
                    error_code = CASE
                        WHEN %s AND retry_count < max_retries THEN NULL
                        ELSE %s
                    END,
                    error_message = CASE
                        WHEN %s AND retry_count < max_retries THEN NULL
                        ELSE %s
                    END,
                    next_attempt_at = CASE
                        WHEN %s AND retry_count < max_retries THEN CURRENT_TIMESTAMP + (%s * INTERVAL '1 second')
                        ELSE NULL
                    END,
                    updated_at = CURRENT_TIMESTAMP
                WHERE job_id = %s AND status = 'RUNNING'
                RETURNING
                    job_id,
                    export_type,
                    file_format,
                    filters,
                    status,
                    request_id,
                    requested_by_username,
                    requested_by_display_name,
                    requested_at,
                    started_at,
                    finished_at,
                    file_name,
                    error_code,
                    error_message
                """,
                (
                    retryable,
                    retryable,
                    retryable,
                    retryable,
                    retryable,
                    retryable,
                    retryable,
                    error_code,
                    retryable,
                    error_message,
                    retryable,
                    ADMIN_EXPORT_JOB_AUTO_RETRY_DELAY_SECONDS,
                    job_id,
                ),
            ).fetchone()
        return admin_export_job_from_row(row) if row else None

    def retry_failed_export_job(self, job_id: str) -> AdminExportJobRecord | None:
        with connect_db() as connection:
            row = connection.execute(
                """
                UPDATE admin_export_job
                SET
                    status = 'PENDING',
                    started_at = NULL,
                    finished_at = NULL,
                    file_name = NULL,
                    storage_key = NULL,
                    error_code = NULL,
                    error_message = NULL,
                    retry_count = 0,
                    next_attempt_at = NULL,
                    updated_at = CURRENT_TIMESTAMP
                WHERE job_id = %s AND status = 'FAILED'
                RETURNING
                    job_id,
                    export_type,
                    file_format,
                    filters,
                    status,
                    request_id,
                    requested_by_username,
                    requested_by_display_name,
                    requested_at,
                    started_at,
                    finished_at,
                    file_name,
                    error_code,
                    error_message
                """,
                (job_id,),
            ).fetchone()
        return admin_export_job_from_row(row) if row else None

    def list_export_jobs(self, filters: AdminExportJobListFilter) -> AdminExportJobListRecord:
        where_clause, params = self._export_job_where_clause(filters)
        limit = filters.page_size
        offset = (filters.page - 1) * filters.page_size

        with connect_db() as connection:
            count_row = connection.execute(
                f"""
                SELECT COUNT(*) AS total
                FROM admin_export_job
                {where_clause}
                """,
                params,
            ).fetchone()
            rows = connection.execute(
                f"""
                SELECT
                    job_id,
                    export_type,
                    file_format,
                    filters,
                    status,
                    request_id,
                    requested_by_username,
                    requested_by_display_name,
                    requested_at,
                    started_at,
                    finished_at,
                    file_name,
                    error_code,
                    error_message
                FROM admin_export_job
                {where_clause}
                ORDER BY requested_at DESC, id DESC
                LIMIT %s OFFSET %s
                """,
                params + (limit, offset),
            ).fetchall()

        return AdminExportJobListRecord(
            items=[admin_export_job_from_row(row) for row in rows],
            total=count_row["total"] if count_row else 0,
            page=filters.page,
            page_size=filters.page_size,
        )

    def get_export_job(self, job_id: str) -> AdminExportJobRecord | None:
        with connect_db() as connection:
            row = connection.execute(
                """
                SELECT
                    job_id,
                    export_type,
                    file_format,
                    filters,
                    status,
                    request_id,
                    requested_by_username,
                    requested_by_display_name,
                    requested_at,
                    started_at,
                    finished_at,
                    file_name,
                    error_code,
                    error_message
                FROM admin_export_job
                WHERE job_id = %s
                """,
                (job_id,),
            ).fetchone()
        return admin_export_job_from_row(row) if row else None

    def get_export_job_file(self, job_id: str) -> AdminExportJobFileRecord | None:
        with connect_db() as connection:
            row = connection.execute(
                """
                SELECT
                    job_id,
                    file_format,
                    file_name,
                    storage_key
                FROM admin_export_job
                WHERE
                    job_id = %s
                    AND status = 'SUCCEEDED'
                    AND file_name IS NOT NULL
                    AND storage_key IS NOT NULL
                """,
                (job_id,),
            ).fetchone()
        if row is None:
            return None
        return AdminExportJobFileRecord(
            job_id=row["job_id"],
            file_format=row["file_format"],
            file_name=row["file_name"],
            storage_key=row["storage_key"],
        )

    def list_succeeded_export_job_files_finished_before(
        self,
        finished_before: datetime,
        *,
        limit: int,
    ) -> list[AdminExportJobCleanupFileRecord]:
        with connect_db() as connection:
            rows = connection.execute(
                """
                SELECT
                    job_id,
                    storage_key
                FROM admin_export_job
                WHERE
                    status = 'SUCCEEDED'
                    AND finished_at IS NOT NULL
                    AND finished_at < %s
                    AND storage_key IS NOT NULL
                ORDER BY finished_at ASC, id ASC
                LIMIT %s
                """,
                (finished_before, limit),
            ).fetchall()
        return [
            AdminExportJobCleanupFileRecord(
                job_id=row["job_id"],
                storage_key=row["storage_key"],
            )
            for row in rows
        ]

    def clear_export_job_file_metadata(self, job_id: str, *, storage_key: str) -> bool:
        with connect_db() as connection:
            row = connection.execute(
                """
                UPDATE admin_export_job
                SET
                    file_name = NULL,
                    storage_key = NULL,
                    updated_at = CURRENT_TIMESTAMP
                WHERE
                    job_id = %s
                    AND status = 'SUCCEEDED'
                    AND storage_key = %s
                RETURNING job_id
                """,
                (job_id, storage_key),
            ).fetchone()
        return row is not None

    def create_export_job_alert_event(self, record: AdminExportJobAlertEventCreateRecord) -> None:
        with connect_db() as connection:
            connection.execute(
                """
                INSERT INTO admin_export_job_alert_event (
                    job_id,
                    export_type,
                    file_format,
                    error_code,
                    error_message,
                    alert_source,
                    occurrence_count,
                    last_seen_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, 1, CURRENT_TIMESTAMP)
                ON CONFLICT (job_id, error_code, alert_source)
                    WHERE closed_at IS NULL
                DO UPDATE
                SET
                    occurrence_count = admin_export_job_alert_event.occurrence_count + 1,
                    last_seen_at = CURRENT_TIMESTAMP,
                    error_message = EXCLUDED.error_message
                """,
                (
                    record.job_id,
                    record.export_type,
                    record.file_format,
                    record.error_code,
                    record.error_message,
                    record.alert_source,
                ),
            )

    def list_export_job_alert_events(
        self,
        filters: AdminExportJobAlertEventListFilter,
    ) -> AdminExportJobAlertEventListRecord:
        where_clause, params = self._export_job_alert_event_where_clause(filters)
        limit = filters.page_size
        offset = (filters.page - 1) * filters.page_size

        with connect_db() as connection:
            count_row = connection.execute(
                f"""
                SELECT COUNT(*) AS total
                FROM admin_export_job_alert_event
                {where_clause}
                """,
                params,
            ).fetchone()
            rows = connection.execute(
                f"""
                SELECT
                    id,
                    job_id,
                    export_type,
                    file_format,
                    error_code,
                    error_message,
                    alert_source,
                    created_at,
                    acknowledged_at,
                    acknowledged_by_admin_user_id,
                    acknowledged_by_username,
                    acknowledged_by_display_name,
                    acknowledge_note,
                    closed_at,
                    closed_by_admin_user_id,
                    closed_by_username,
                    closed_by_display_name,
                    close_note,
                    occurrence_count,
                    last_seen_at
                FROM admin_export_job_alert_event
                {where_clause}
                ORDER BY created_at DESC, id DESC
                LIMIT %s OFFSET %s
                """,
                params + (limit, offset),
            ).fetchall()

        return AdminExportJobAlertEventListRecord(
            items=[admin_export_job_alert_event_from_row(row) for row in rows],
            total=count_row["total"] if count_row else 0,
            page=filters.page,
            page_size=filters.page_size,
        )

    def summarize_export_job_alert_events(
        self,
        filters: AdminExportJobAlertEventSummaryFilter,
    ) -> AdminExportJobAlertEventSummaryRecord:
        where_clause, params = self._export_job_alert_event_summary_where_clause(filters)

        with connect_db() as connection:
            summary_row = connection.execute(
                f"""
                SELECT
                    COUNT(*) AS total,
                    COUNT(*) FILTER (WHERE acknowledged_at IS NOT NULL) AS acknowledged,
                    COUNT(*) FILTER (WHERE acknowledged_at IS NULL) AS unacknowledged,
                    COUNT(*) FILTER (WHERE closed_at IS NOT NULL) AS closed,
                    COUNT(*) FILTER (WHERE closed_at IS NULL) AS open_count
                FROM admin_export_job_alert_event
                {where_clause}
                """,
                params,
            ).fetchone()
            error_rows = connection.execute(
                f"""
                SELECT
                    error_code,
                    COUNT(*) AS total,
                    COUNT(*) FILTER (WHERE acknowledged_at IS NOT NULL) AS acknowledged,
                    COUNT(*) FILTER (WHERE acknowledged_at IS NULL) AS unacknowledged,
                    COUNT(*) FILTER (WHERE closed_at IS NOT NULL) AS closed,
                    COUNT(*) FILTER (WHERE closed_at IS NULL) AS open_count
                FROM admin_export_job_alert_event
                {where_clause}
                GROUP BY error_code
                ORDER BY total DESC, error_code ASC
                """,
                params,
            ).fetchall()

        return AdminExportJobAlertEventSummaryRecord(
            total=summary_row["total"] if summary_row else 0,
            acknowledged=summary_row["acknowledged"] if summary_row else 0,
            unacknowledged=summary_row["unacknowledged"] if summary_row else 0,
            closed=summary_row["closed"] if summary_row else 0,
            open_count=summary_row["open_count"] if summary_row else 0,
            by_error_code=[
                AdminExportJobAlertEventSummaryByErrorCodeRecord(
                    error_code=row["error_code"],
                    total=row["total"],
                    acknowledged=row["acknowledged"],
                    unacknowledged=row["unacknowledged"],
                    closed=row["closed"],
                    open_count=row["open_count"],
                )
                for row in error_rows
            ],
        )

    def acknowledge_export_job_alert_event(
        self,
        record: AdminExportJobAlertEventAcknowledgeRecord,
    ) -> AdminExportJobAlertEventRecord | None:
        with connect_db() as connection:
            row = connection.execute(
                """
                UPDATE admin_export_job_alert_event
                SET
                    acknowledged_at = CASE
                        WHEN acknowledged_at IS NULL THEN CURRENT_TIMESTAMP
                        ELSE acknowledged_at
                    END,
                    acknowledged_by_admin_user_id = CASE
                        WHEN acknowledged_at IS NULL THEN %s
                        ELSE acknowledged_by_admin_user_id
                    END,
                    acknowledged_by_username = CASE
                        WHEN acknowledged_at IS NULL THEN %s
                        ELSE acknowledged_by_username
                    END,
                    acknowledged_by_display_name = CASE
                        WHEN acknowledged_at IS NULL THEN %s
                        ELSE acknowledged_by_display_name
                    END,
                    acknowledge_note = CASE
                        WHEN acknowledged_at IS NULL THEN %s
                        ELSE acknowledge_note
                    END
                WHERE id = %s
                RETURNING
                    id,
                    job_id,
                    export_type,
                    file_format,
                    error_code,
                    error_message,
                    alert_source,
                    created_at,
                    acknowledged_at,
                    acknowledged_by_admin_user_id,
                    acknowledged_by_username,
                    acknowledged_by_display_name,
                    acknowledge_note,
                    closed_at,
                    closed_by_admin_user_id,
                    closed_by_username,
                    closed_by_display_name,
                    close_note,
                    occurrence_count,
                    last_seen_at
                """,
                (
                    record.acknowledged_by_admin_user_id,
                    record.acknowledged_by_username,
                    record.acknowledged_by_display_name,
                    record.acknowledge_note,
                    record.event_id,
                ),
            ).fetchone()
        return admin_export_job_alert_event_from_row(row) if row else None

    def close_export_job_alert_event(
        self,
        record: AdminExportJobAlertEventCloseRecord,
    ) -> AdminExportJobAlertEventRecord | None:
        with connect_db() as connection:
            row = connection.execute(
                """
                UPDATE admin_export_job_alert_event
                SET
                    closed_at = CASE
                        WHEN closed_at IS NULL THEN CURRENT_TIMESTAMP
                        ELSE closed_at
                    END,
                    closed_by_admin_user_id = CASE
                        WHEN closed_at IS NULL THEN %s
                        ELSE closed_by_admin_user_id
                    END,
                    closed_by_username = CASE
                        WHEN closed_at IS NULL THEN %s
                        ELSE closed_by_username
                    END,
                    closed_by_display_name = CASE
                        WHEN closed_at IS NULL THEN %s
                        ELSE closed_by_display_name
                    END,
                    close_note = CASE
                        WHEN closed_at IS NULL THEN %s
                        ELSE close_note
                    END
                WHERE id = %s
                RETURNING
                    id,
                    job_id,
                    export_type,
                    file_format,
                    error_code,
                    error_message,
                    alert_source,
                    created_at,
                    acknowledged_at,
                    acknowledged_by_admin_user_id,
                    acknowledged_by_username,
                    acknowledged_by_display_name,
                    acknowledge_note,
                    closed_at,
                    closed_by_admin_user_id,
                    closed_by_username,
                    closed_by_display_name,
                    close_note,
                    occurrence_count,
                    last_seen_at
                """,
                (
                    record.closed_by_admin_user_id,
                    record.closed_by_username,
                    record.closed_by_display_name,
                    record.close_note,
                    record.event_id,
                ),
            ).fetchone()
        return admin_export_job_alert_event_from_row(row) if row else None

    def reopen_export_job_alert_event(self, event_id: int) -> AdminExportJobAlertEventRecord | None:
        with connect_db() as connection:
            row = connection.execute(
                """
                WITH target AS (
                    SELECT
                        id,
                        job_id,
                        error_code,
                        alert_source
                    FROM admin_export_job_alert_event
                    WHERE id = %s
                ),
                existing_open AS (
                    SELECT
                        event.id,
                        event.job_id,
                        event.export_type,
                        event.file_format,
                        event.error_code,
                        event.error_message,
                        event.alert_source,
                        event.created_at,
                        event.acknowledged_at,
                        event.acknowledged_by_admin_user_id,
                        event.acknowledged_by_username,
                        event.acknowledged_by_display_name,
                        event.acknowledge_note,
                        event.closed_at,
                        event.closed_by_admin_user_id,
                        event.closed_by_username,
                        event.closed_by_display_name,
                        event.close_note,
                        event.occurrence_count,
                        event.last_seen_at
                    FROM admin_export_job_alert_event event
                    JOIN target
                        ON event.job_id = target.job_id
                        AND event.error_code = target.error_code
                        AND event.alert_source = target.alert_source
                    WHERE event.closed_at IS NULL
                        AND event.id <> target.id
                    ORDER BY event.created_at DESC, event.id DESC
                    LIMIT 1
                ),
                reopened AS (
                    UPDATE admin_export_job_alert_event
                    SET
                        closed_at = NULL,
                        closed_by_admin_user_id = NULL,
                        closed_by_username = NULL,
                        closed_by_display_name = NULL,
                        close_note = NULL
                    WHERE id = %s
                        AND NOT EXISTS (SELECT 1 FROM existing_open)
                    RETURNING
                        id,
                        job_id,
                        export_type,
                        file_format,
                        error_code,
                        error_message,
                        alert_source,
                        created_at,
                        acknowledged_at,
                        acknowledged_by_admin_user_id,
                        acknowledged_by_username,
                        acknowledged_by_display_name,
                        acknowledge_note,
                        closed_at,
                        closed_by_admin_user_id,
                        closed_by_username,
                        closed_by_display_name,
                        close_note,
                        occurrence_count,
                        last_seen_at
                )
                SELECT *
                FROM reopened
                UNION ALL
                SELECT *
                FROM existing_open
                LIMIT 1
                """,
                (event_id, event_id),
            ).fetchone()
        return admin_export_job_alert_event_from_row(row) if row else None

    def delete_closed_export_job_alert_event(self, event_id: int) -> AdminExportJobAlertEventDeleteResult:
        with connect_db() as connection:
            row = connection.execute(
                """
                WITH target AS (
                    SELECT
                        id,
                        closed_at
                    FROM admin_export_job_alert_event
                    WHERE id = %s
                ),
                deleted AS (
                    DELETE FROM admin_export_job_alert_event
                    WHERE
                        id = %s
                        AND closed_at IS NOT NULL
                    RETURNING id
                )
                SELECT
                    EXISTS (SELECT 1 FROM target) AS found,
                    EXISTS (SELECT 1 FROM target WHERE closed_at IS NOT NULL) AS closed,
                    EXISTS (SELECT 1 FROM deleted) AS deleted
                """,
                (event_id, event_id),
            ).fetchone()
        if row is None:
            return AdminExportJobAlertEventDeleteResult(found=False, closed=False, deleted=False)
        return AdminExportJobAlertEventDeleteResult(
            found=row["found"],
            closed=row["closed"],
            deleted=row["deleted"],
        )

    @staticmethod
    def _export_job_where_clause(filters: AdminExportJobListFilter) -> tuple[str, tuple[object, ...]]:
        clauses: list[str] = []
        params: list[object] = []

        if filters.export_type:
            clauses.append("export_type = %s")
            params.append(filters.export_type)
        if filters.file_format:
            clauses.append("file_format = %s")
            params.append(filters.file_format)
        if filters.status:
            clauses.append("status = %s")
            params.append(filters.status)

        if not clauses:
            return "", ()
        return "WHERE " + " AND ".join(clauses), tuple(params)

    @staticmethod
    def _export_job_alert_event_where_clause(
        filters: AdminExportJobAlertEventListFilter,
    ) -> tuple[str, tuple[object, ...]]:
        clauses: list[str] = []
        params: list[object] = []

        if filters.job_id:
            clauses.append("job_id = %s")
            params.append(filters.job_id)
        if filters.export_type:
            clauses.append("export_type = %s")
            params.append(filters.export_type)
        if filters.file_format:
            clauses.append("file_format = %s")
            params.append(filters.file_format)
        if filters.error_code:
            clauses.append("error_code = %s")
            params.append(filters.error_code)
        if filters.acknowledged is True:
            clauses.append("acknowledged_at IS NOT NULL")
        if filters.acknowledged is False:
            clauses.append("acknowledged_at IS NULL")
        if filters.closed is True:
            clauses.append("closed_at IS NOT NULL")
        if filters.closed is False:
            clauses.append("closed_at IS NULL")
        if filters.date_from:
            clauses.append("created_at >= %s")
            params.append(filters.date_from)
        if filters.date_to:
            clauses.append("created_at < %s")
            params.append(filters.date_to + timedelta(days=1))

        if not clauses:
            return "", ()
        return "WHERE " + " AND ".join(clauses), tuple(params)

    @staticmethod
    def _export_job_alert_event_summary_where_clause(
        filters: AdminExportJobAlertEventSummaryFilter,
    ) -> tuple[str, tuple[object, ...]]:
        clauses: list[str] = []
        params: list[object] = []

        if filters.export_type:
            clauses.append("export_type = %s")
            params.append(filters.export_type)
        if filters.file_format:
            clauses.append("file_format = %s")
            params.append(filters.file_format)
        if filters.closed is True:
            clauses.append("closed_at IS NOT NULL")
        if filters.closed is False:
            clauses.append("closed_at IS NULL")
        if filters.date_from:
            clauses.append("created_at >= %s")
            params.append(filters.date_from)
        if filters.date_to:
            clauses.append("created_at < %s")
            params.append(filters.date_to + timedelta(days=1))

        if not clauses:
            return "", ()
        return "WHERE " + " AND ".join(clauses), tuple(params)


def get_admin_export_job_repository() -> AdminExportJobRepository:
    return PostgresAdminExportJobRepository()
