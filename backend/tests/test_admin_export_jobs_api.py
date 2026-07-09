from dataclasses import replace
from datetime import UTC, date, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from fastapi.testclient import TestClient
import pytest

import app.repositories.admin_exports as admin_export_repository_module
import app.services.admin_exports as admin_export_service_module
from app.core.errors import AppError
from app.main import create_app
from app.repositories.admin_exports import (
    AdminExportJobAlertEventAcknowledgeRecord,
    AdminExportJobAlertEventCloseRecord,
    AdminExportJobAlertEventCreateRecord,
    AdminExportJobAlertEventDeleteResult,
    AdminExportJobAlertEventListFilter,
    AdminExportJobAlertEventListRecord,
    AdminExportJobAlertEventRecord,
    AdminExportJobAlertEventSummaryByErrorCodeRecord,
    AdminExportJobAlertEventSummaryFilter,
    AdminExportJobAlertEventSummaryRecord,
    AdminExportJobCreateRecord,
    AdminExportJobCleanupFileRecord,
    AdminExportJobFileRecord,
    AdminExportJobListFilter,
    AdminExportJobListRecord,
    AdminExportJobRecord,
    AdminExportJobRecoveryRecord,
    PostgresAdminExportJobRepository,
    get_admin_export_job_repository,
)
from app.repositories.auth import get_auth_repository
from app.services.admin_exports import (
    AdminExportFileStorage,
    AdminExportJobService,
    AdminExportJobWorkerService,
    get_admin_export_file_storage,
)

from test_admin_auth_api import FakeAuthRepository, admin_login_payload, seed_enabled_admin
from test_auth_api import csrf_headers


REQUESTED_AT = datetime(2026, 7, 1, 9, 30, tzinfo=UTC)
STARTED_AT = datetime(2026, 7, 1, 9, 35, tzinfo=UTC)
FINISHED_AT = datetime(2026, 7, 1, 9, 40, tzinfo=UTC)
NEXT_ATTEMPT_AT = datetime(2026, 7, 1, 9, 41, tzinfo=UTC)


def export_job_record(
    *,
    job_id: str = "11111111-1111-4111-8111-111111111111",
    export_type: str = "ORDER_DETAIL",
    file_format: str = "CSV",
    filters: dict[str, Any] | None = None,
    status: str = "PENDING",
    request_id: str | None = "export-request",
    requested_at: datetime = REQUESTED_AT,
    started_at: datetime | None = None,
    finished_at: datetime | None = None,
    file_name: str | None = None,
    error_code: str | None = None,
    error_message: str | None = None,
) -> AdminExportJobRecord:
    return AdminExportJobRecord(
        job_id=job_id,
        export_type=export_type,
        file_format=file_format,
        filters=filters or {"dateFrom": "2026-07-01"},
        status=status,
        request_id=request_id,
        requested_by_username="admin",
        requested_by_display_name="演示管理员",
        requested_at=requested_at,
        started_at=started_at,
        finished_at=finished_at,
        file_name=file_name,
        error_code=error_code,
        error_message=error_message,
    )


class FakeAdminExportJobRepository:
    def __init__(self):
        self.created_records: list[AdminExportJobCreateRecord] = []
        self.last_filters: AdminExportJobListFilter | None = None
        self.last_alert_event_filters: AdminExportJobAlertEventListFilter | None = None
        self.last_alert_event_summary_filters: AdminExportJobAlertEventSummaryFilter | None = None
        self.last_alert_event_acknowledge: AdminExportJobAlertEventAcknowledgeRecord | None = None
        self.last_alert_event_close: AdminExportJobAlertEventCloseRecord | None = None
        self.last_alert_event_reopen: int | None = None
        self.last_alert_event_delete: int | None = None
        self.recover_stale_running_calls: list[tuple[int, str, str]] = []
        self.alert_events: list[AdminExportJobAlertEventCreateRecord] = []
        self.alert_event_records: list[AdminExportJobAlertEventRecord] = []
        self.succeeded_storage_keys: dict[str, str] = {}
        self.retry_counts: dict[str, int] = {}
        self.max_retries: dict[str, int] = {}
        self.next_attempt_ats: dict[str, datetime] = {}
        self.stale_running_job_ids: set[str] = set()
        self.jobs: dict[str, AdminExportJobRecord] = {
            "11111111-1111-4111-8111-111111111111": export_job_record(),
        }

    def create_export_job(self, record: AdminExportJobCreateRecord) -> AdminExportJobRecord:
        self.created_records.append(record)
        job = export_job_record(
            job_id=record.job_id,
            export_type=record.export_type,
            file_format=record.file_format,
            filters=record.filters,
            request_id=record.request_id,
        )
        self.jobs[job.job_id] = job
        return job

    def recover_stale_running_jobs(
        self,
        *,
        timeout_seconds: int,
        error_code: str,
        error_message: str,
    ) -> AdminExportJobRecoveryRecord:
        self.recover_stale_running_calls.append((timeout_seconds, error_code, error_message))
        recovered = 0
        final_failed_jobs: list[AdminExportJobRecord] = []
        for job_id, job in list(self.jobs.items()):
            if job_id not in self.stale_running_job_ids or job.status != "RUNNING" or job.started_at is None:
                continue
            retry_count = self.retry_counts.get(job_id, 0)
            max_retries = self.max_retries.get(job_id, 1)
            if retry_count < max_retries:
                self.retry_counts[job_id] = retry_count + 1
                self.next_attempt_ats.pop(job_id, None)
                self.jobs[job_id] = replace(
                    job,
                    status="PENDING",
                    started_at=None,
                    finished_at=None,
                    file_name=None,
                    error_code=None,
                    error_message=None,
                )
            else:
                self.next_attempt_ats.pop(job_id, None)
                failed_job = replace(
                    job,
                    status="FAILED",
                    finished_at=FINISHED_AT,
                    error_code=error_code,
                    error_message=error_message,
                )
                self.jobs[job_id] = failed_job
                final_failed_jobs.append(failed_job)
            recovered += 1
            self.stale_running_job_ids.discard(job_id)
        return AdminExportJobRecoveryRecord(recovered_count=recovered, final_failed_jobs=final_failed_jobs)

    def claim_next_pending_job(self) -> AdminExportJobRecord | None:
        pending_jobs = sorted(
            [
                job
                for job in self.jobs.values()
                if job.status == "PENDING" and job.job_id not in self.next_attempt_ats
            ],
            key=lambda job: (job.requested_at, job.job_id),
        )
        if not pending_jobs:
            return None
        job = replace(pending_jobs[0], status="RUNNING", started_at=STARTED_AT)
        self.jobs[job.job_id] = job
        return job

    def mark_export_job_succeeded(
        self,
        job_id: str,
        *,
        file_name: str,
        storage_key: str,
    ) -> AdminExportJobRecord | None:
        job = self.jobs.get(job_id)
        if job is None or job.status != "RUNNING":
            return None
        self.succeeded_storage_keys[job_id] = storage_key
        self.next_attempt_ats.pop(job_id, None)
        job = replace(
            job,
            status="SUCCEEDED",
            finished_at=FINISHED_AT,
            file_name=file_name,
            error_code=None,
            error_message=None,
        )
        self.jobs[job_id] = job
        return job

    def mark_export_job_failed(
        self,
        job_id: str,
        *,
        error_code: str,
        error_message: str,
        retryable: bool = False,
    ) -> AdminExportJobRecord | None:
        job = self.jobs.get(job_id)
        if job is None or job.status != "RUNNING":
            return None
        retry_count = self.retry_counts.get(job_id, 0)
        max_retries = self.max_retries.get(job_id, 1)
        if retryable and retry_count < max_retries:
            self.retry_counts[job_id] = retry_count + 1
            self.next_attempt_ats[job_id] = NEXT_ATTEMPT_AT
            job = replace(
                job,
                status="PENDING",
                started_at=None,
                finished_at=None,
                file_name=None,
                error_code=None,
                error_message=None,
            )
            self.jobs[job_id] = job
            return job
        job = replace(
            job,
            status="FAILED",
            finished_at=FINISHED_AT,
            error_code=error_code,
            error_message=error_message,
        )
        self.next_attempt_ats.pop(job_id, None)
        self.jobs[job_id] = job
        return job

    def retry_failed_export_job(self, job_id: str) -> AdminExportJobRecord | None:
        job = self.jobs.get(job_id)
        if job is None or job.status != "FAILED":
            return None
        self.succeeded_storage_keys.pop(job_id, None)
        self.retry_counts[job_id] = 0
        self.next_attempt_ats.pop(job_id, None)
        job = replace(
            job,
            status="PENDING",
            started_at=None,
            finished_at=None,
            file_name=None,
            error_code=None,
            error_message=None,
        )
        self.jobs[job_id] = job
        return job

    def list_export_jobs(self, filters: AdminExportJobListFilter) -> AdminExportJobListRecord:
        self.last_filters = filters
        items = [
            job
            for job in self.jobs.values()
            if (filters.export_type is None or job.export_type == filters.export_type)
            and (filters.file_format is None or job.file_format == filters.file_format)
            and (filters.status is None or job.status == filters.status)
        ]
        return AdminExportJobListRecord(
            items=items,
            total=len(items),
            page=filters.page,
            page_size=filters.page_size,
        )

    def get_export_job(self, job_id: str) -> AdminExportJobRecord | None:
        return self.jobs.get(job_id)

    def get_export_job_file(self, job_id: str) -> AdminExportJobFileRecord | None:
        job = self.jobs.get(job_id)
        storage_key = self.succeeded_storage_keys.get(job_id)
        if job is None or job.status != "SUCCEEDED" or job.file_name is None or storage_key is None:
            return None
        return AdminExportJobFileRecord(
            job_id=job.job_id,
            file_format=job.file_format,
            file_name=job.file_name,
            storage_key=storage_key,
        )

    def list_succeeded_export_job_files_finished_before(
        self,
        finished_before: datetime,
        *,
        limit: int,
    ) -> list[AdminExportJobCleanupFileRecord]:
        candidates = [
            AdminExportJobCleanupFileRecord(job_id=job.job_id, storage_key=self.succeeded_storage_keys[job.job_id])
            for job in self.jobs.values()
            if job.status == "SUCCEEDED"
            and job.finished_at is not None
            and job.finished_at < finished_before
            and job.job_id in self.succeeded_storage_keys
        ]
        return candidates[:limit]

    def clear_export_job_file_metadata(self, job_id: str, *, storage_key: str) -> bool:
        job = self.jobs.get(job_id)
        if job is None or job.status != "SUCCEEDED" or self.succeeded_storage_keys.get(job_id) != storage_key:
            return False
        self.succeeded_storage_keys.pop(job_id, None)
        self.jobs[job_id] = replace(job, file_name=None)
        return True

    def create_export_job_alert_event(self, record: AdminExportJobAlertEventCreateRecord) -> None:
        for index, event in enumerate(self.alert_event_records):
            if (
                event.job_id == record.job_id
                and event.error_code == record.error_code
                and event.alert_source == record.alert_source
                and event.closed_at is None
            ):
                self.alert_event_records[index] = replace(
                    event,
                    error_message=record.error_message,
                    occurrence_count=event.occurrence_count + 1,
                    last_seen_at=FINISHED_AT,
                )
                return
        self.alert_events.append(record)
        self.alert_event_records.append(
            AdminExportJobAlertEventRecord(
                event_id=len(self.alert_event_records) + 1,
                job_id=record.job_id,
                export_type=record.export_type,
                file_format=record.file_format,
                error_code=record.error_code,
                error_message=record.error_message,
                alert_source=record.alert_source,
                created_at=FINISHED_AT,
                acknowledged_at=None,
                acknowledged_by_admin_user_id=None,
                acknowledged_by_username=None,
                acknowledged_by_display_name=None,
                acknowledge_note=None,
                occurrence_count=1,
                last_seen_at=FINISHED_AT,
            )
        )

    def list_export_job_alert_events(
        self,
        filters: AdminExportJobAlertEventListFilter,
    ) -> AdminExportJobAlertEventListRecord:
        self.last_alert_event_filters = filters
        items = [
            event
            for event in self.alert_event_records
            if (filters.job_id is None or event.job_id == filters.job_id)
            and (filters.export_type is None or event.export_type == filters.export_type)
            and (filters.file_format is None or event.file_format == filters.file_format)
            and (filters.error_code is None or event.error_code == filters.error_code)
            and (filters.acknowledged is None or (event.acknowledged_at is not None) == filters.acknowledged)
            and (filters.closed is None or (event.closed_at is not None) == filters.closed)
            and (filters.date_from is None or event.created_at.date() >= filters.date_from)
            and (filters.date_to is None or event.created_at.date() <= filters.date_to)
        ]
        return AdminExportJobAlertEventListRecord(
            items=items,
            total=len(items),
            page=filters.page,
            page_size=filters.page_size,
        )

    def summarize_export_job_alert_events(
        self,
        filters: AdminExportJobAlertEventSummaryFilter,
    ) -> AdminExportJobAlertEventSummaryRecord:
        self.last_alert_event_summary_filters = filters
        items = [
            event
            for event in self.alert_event_records
            if (filters.export_type is None or event.export_type == filters.export_type)
            and (filters.file_format is None or event.file_format == filters.file_format)
            and (filters.closed is None or (event.closed_at is not None) == filters.closed)
            and (filters.date_from is None or event.created_at.date() >= filters.date_from)
            and (filters.date_to is None or event.created_at.date() <= filters.date_to)
        ]
        by_error_code: dict[str, list[AdminExportJobAlertEventRecord]] = {}
        for event in items:
            by_error_code.setdefault(event.error_code, []).append(event)
        return AdminExportJobAlertEventSummaryRecord(
            total=len(items),
            acknowledged=sum(1 for event in items if event.acknowledged_at is not None),
            unacknowledged=sum(1 for event in items if event.acknowledged_at is None),
            closed=sum(1 for event in items if event.closed_at is not None),
            open_count=sum(1 for event in items if event.closed_at is None),
            by_error_code=[
                AdminExportJobAlertEventSummaryByErrorCodeRecord(
                    error_code=error_code,
                    total=len(error_items),
                    acknowledged=sum(1 for event in error_items if event.acknowledged_at is not None),
                    unacknowledged=sum(1 for event in error_items if event.acknowledged_at is None),
                    closed=sum(1 for event in error_items if event.closed_at is not None),
                    open_count=sum(1 for event in error_items if event.closed_at is None),
                )
                for error_code, error_items in sorted(
                    by_error_code.items(),
                    key=lambda item: (-len(item[1]), item[0]),
                )
            ],
        )

    def acknowledge_export_job_alert_event(
        self,
        record: AdminExportJobAlertEventAcknowledgeRecord,
    ) -> AdminExportJobAlertEventRecord | None:
        self.last_alert_event_acknowledge = record
        for index, event in enumerate(self.alert_event_records):
            if event.event_id != record.event_id:
                continue
            if event.acknowledged_at is not None:
                return event
            acknowledged = replace(
                event,
                acknowledged_at=FINISHED_AT,
                acknowledged_by_admin_user_id=record.acknowledged_by_admin_user_id,
                acknowledged_by_username=record.acknowledged_by_username,
                acknowledged_by_display_name=record.acknowledged_by_display_name,
                acknowledge_note=record.acknowledge_note,
            )
            self.alert_event_records[index] = acknowledged
            return acknowledged
        return None

    def close_export_job_alert_event(
        self,
        record: AdminExportJobAlertEventCloseRecord,
    ) -> AdminExportJobAlertEventRecord | None:
        self.last_alert_event_close = record
        for index, event in enumerate(self.alert_event_records):
            if event.event_id != record.event_id:
                continue
            if event.closed_at is not None:
                return event
            closed = replace(
                event,
                closed_at=FINISHED_AT,
                closed_by_admin_user_id=record.closed_by_admin_user_id,
                closed_by_username=record.closed_by_username,
                closed_by_display_name=record.closed_by_display_name,
                close_note=record.close_note,
            )
            self.alert_event_records[index] = closed
            return closed
        return None

    def reopen_export_job_alert_event(self, event_id: int) -> AdminExportJobAlertEventRecord | None:
        self.last_alert_event_reopen = event_id
        for index, event in enumerate(self.alert_event_records):
            if event.event_id != event_id:
                continue
            existing_open = next(
                (
                    existing
                    for existing in self.alert_event_records
                    if existing.event_id != event.event_id
                    and existing.job_id == event.job_id
                    and existing.error_code == event.error_code
                    and existing.alert_source == event.alert_source
                    and existing.closed_at is None
                ),
                None,
            )
            if existing_open is not None:
                return existing_open
            reopened = replace(
                event,
                closed_at=None,
                closed_by_admin_user_id=None,
                closed_by_username=None,
                closed_by_display_name=None,
                close_note=None,
            )
            self.alert_event_records[index] = reopened
            return reopened
        return None

    def delete_closed_export_job_alert_event(self, event_id: int) -> AdminExportJobAlertEventDeleteResult:
        self.last_alert_event_delete = event_id
        for index, event in enumerate(self.alert_event_records):
            if event.event_id != event_id:
                continue
            if event.closed_at is None:
                return AdminExportJobAlertEventDeleteResult(found=True, closed=False, deleted=False)
            del self.alert_event_records[index]
            return AdminExportJobAlertEventDeleteResult(found=True, closed=True, deleted=True)
        return AdminExportJobAlertEventDeleteResult(found=False, closed=False, deleted=False)


class FakeAdminExportFileStorage:
    def __init__(self):
        self.files: dict[str, bytes] = {}

    def read_file(self, storage_key: str) -> bytes:
        if storage_key not in self.files:
            raise AppError(404, "ADMIN_EXPORT_FILE_NOT_FOUND", "导出文件不存在")
        return self.files[storage_key]

    def write_file(self, storage_key: str, content: bytes) -> None:
        if ".." in storage_key:
            raise AppError(404, "ADMIN_EXPORT_FILE_NOT_FOUND", "导出文件不存在")
        self.files[storage_key] = content

    def delete_file(self, storage_key: str) -> bool:
        if ".." in storage_key:
            raise AppError(404, "ADMIN_EXPORT_FILE_NOT_FOUND", "导出文件不存在")
        if storage_key not in self.files:
            return False
        del self.files[storage_key]
        return True


class FakeAdminReportService:
    def __init__(self):
        self.order_detail_csv_calls: list[tuple[date | None, date | None]] = []
        self.order_detail_xlsx_calls: list[tuple[date | None, date | None]] = []
        self.payment_reconciliation_csv_calls: list[tuple[date | None, date | None]] = []
        self.payment_reconciliation_xlsx_calls: list[tuple[date | None, date | None]] = []
        self.product_breakdown_csv_calls: list[tuple[date | None, date | None]] = []
        self.product_breakdown_xlsx_calls: list[tuple[date | None, date | None]] = []
        self.daily_trend_csv_calls: list[tuple[date | None, date | None, bool]] = []
        self.daily_trend_xlsx_calls: list[tuple[date | None, date | None, bool]] = []
        self.hourly_trend_csv_calls: list[tuple[date | None, date | None, bool]] = []
        self.hourly_trend_xlsx_calls: list[tuple[date | None, date | None, bool]] = []
        self.monthly_trend_csv_calls: list[tuple[date | None, date | None, bool]] = []
        self.monthly_trend_xlsx_calls: list[tuple[date | None, date | None, bool]] = []

    def export_order_detail_csv_for_worker(self, date_from: date | None, date_to: date | None) -> str:
        self.order_detail_csv_calls.append((date_from, date_to))
        return "\ufefforderNo,buyerName\nO-1,张三\n"

    def export_order_detail_xlsx_for_worker(self, date_from: date | None, date_to: date | None) -> bytes:
        self.order_detail_xlsx_calls.append((date_from, date_to))
        return b"PK\x03\x04fake-order-xlsx"

    def export_payment_reconciliation_csv_for_worker(self, date_from: date | None, date_to: date | None) -> str:
        self.payment_reconciliation_csv_calls.append((date_from, date_to))
        return "\ufeffdateFrom,dateTo,reconciled\n2026-07-01,2026-07-31,true\n"

    def export_payment_reconciliation_xlsx_for_worker(self, date_from: date | None, date_to: date | None) -> bytes:
        self.payment_reconciliation_xlsx_calls.append((date_from, date_to))
        return b"PK\x03\x04fake-payment-reconciliation-xlsx"

    def export_product_breakdown_csv_for_worker(self, date_from: date | None, date_to: date | None) -> str:
        self.product_breakdown_csv_calls.append((date_from, date_to))
        return "\ufeffproductId,ticketTypeId,netPaidAmount\nP-1,T-1,128.00\n"

    def export_product_breakdown_xlsx_for_worker(self, date_from: date | None, date_to: date | None) -> bytes:
        self.product_breakdown_xlsx_calls.append((date_from, date_to))
        return b"PK\x03\x04fake-product-breakdown-xlsx"

    def export_daily_trend_csv_for_worker(
        self,
        date_from: date | None,
        date_to: date | None,
        include_empty: bool = False,
    ) -> str:
        self.daily_trend_csv_calls.append((date_from, date_to, include_empty))
        return "\ufeffreportDate,orderCount\n2026-07-01,2\n"

    def export_daily_trend_xlsx_for_worker(
        self,
        date_from: date | None,
        date_to: date | None,
        include_empty: bool = False,
    ) -> bytes:
        self.daily_trend_xlsx_calls.append((date_from, date_to, include_empty))
        return b"PK\x03\x04fake-daily-trend-xlsx"

    def export_hourly_trend_csv_for_worker(
        self,
        date_from: date | None,
        date_to: date | None,
        include_empty: bool = False,
    ) -> str:
        self.hourly_trend_csv_calls.append((date_from, date_to, include_empty))
        return "\ufeffreportHour,orderCount\n2026-07-01T08:00:00,2\n"

    def export_hourly_trend_xlsx_for_worker(
        self,
        date_from: date | None,
        date_to: date | None,
        include_empty: bool = False,
    ) -> bytes:
        self.hourly_trend_xlsx_calls.append((date_from, date_to, include_empty))
        return b"PK\x03\x04fake-hourly-trend-xlsx"

    def export_monthly_trend_csv_for_worker(
        self,
        date_from: date | None,
        date_to: date | None,
        include_empty: bool = False,
    ) -> str:
        self.monthly_trend_csv_calls.append((date_from, date_to, include_empty))
        return "\ufeffreportMonth,orderCount\n2026-07,2\n"

    def export_monthly_trend_xlsx_for_worker(
        self,
        date_from: date | None,
        date_to: date | None,
        include_empty: bool = False,
    ) -> bytes:
        self.monthly_trend_xlsx_calls.append((date_from, date_to, include_empty))
        return b"PK\x03\x04fake-monthly-trend-xlsx"

    @staticmethod
    def order_export_filename(date_from: date | None, date_to: date | None) -> str:
        start = date_from.strftime("%Y%m%d") if date_from else "start"
        end = date_to.strftime("%Y%m%d") if date_to else "end"
        return f"admin-orders-{start}-{end}.csv"

    @staticmethod
    def order_export_xlsx_filename(date_from: date | None, date_to: date | None) -> str:
        start = date_from.strftime("%Y%m%d") if date_from else "start"
        end = date_to.strftime("%Y%m%d") if date_to else "end"
        return f"admin-orders-{start}-{end}.xlsx"

    @staticmethod
    def product_breakdown_export_filename(date_from: date | None, date_to: date | None) -> str:
        start = date_from.strftime("%Y%m%d") if date_from else "start"
        end = date_to.strftime("%Y%m%d") if date_to else "end"
        return f"admin-product-breakdown-{start}-{end}.csv"

    @staticmethod
    def payment_reconciliation_export_filename(date_from: date | None, date_to: date | None) -> str:
        start = date_from.strftime("%Y%m%d") if date_from else "start"
        end = date_to.strftime("%Y%m%d") if date_to else "end"
        return f"admin-payment-reconciliation-{start}-{end}.csv"

    @staticmethod
    def payment_reconciliation_export_xlsx_filename(date_from: date | None, date_to: date | None) -> str:
        start = date_from.strftime("%Y%m%d") if date_from else "start"
        end = date_to.strftime("%Y%m%d") if date_to else "end"
        return f"admin-payment-reconciliation-{start}-{end}.xlsx"

    @staticmethod
    def product_breakdown_export_xlsx_filename(date_from: date | None, date_to: date | None) -> str:
        start = date_from.strftime("%Y%m%d") if date_from else "start"
        end = date_to.strftime("%Y%m%d") if date_to else "end"
        return f"admin-product-breakdown-{start}-{end}.xlsx"

    @staticmethod
    def trend_export_filename(trend: str, date_from: date | None, date_to: date | None) -> str:
        start = date_from.strftime("%Y%m%d") if date_from else "start"
        end = date_to.strftime("%Y%m%d") if date_to else "end"
        return f"admin-{trend}-trend-{start}-{end}.csv"

    @staticmethod
    def trend_export_xlsx_filename(trend: str, date_from: date | None, date_to: date | None) -> str:
        start = date_from.strftime("%Y%m%d") if date_from else "start"
        end = date_to.strftime("%Y%m%d") if date_to else "end"
        return f"admin-{trend}-trend-{start}-{end}.xlsx"


class FakeAdminCheckInService:
    def __init__(self):
        self.check_in_audit_csv_calls: list[
            tuple[str | None, str | None, str | None, str | None, date | None, date | None]
        ] = []
        self.check_in_audit_xlsx_calls: list[
            tuple[str | None, str | None, str | None, str | None, date | None, date | None]
        ] = []
        self.check_in_failure_audit_csv_calls: list[
            tuple[str | None, str | None, str | None, date | None, date | None]
        ] = []
        self.check_in_failure_audit_xlsx_calls: list[
            tuple[str | None, str | None, str | None, date | None, date | None]
        ] = []

    def export_check_in_audit_logs_csv_for_worker(
        self,
        ticket_code: str | None,
        order_no: str | None,
        operator_username: str | None,
        reason: str | None,
        date_from: date | None,
        date_to: date | None,
    ) -> str:
        self.check_in_audit_csv_calls.append((ticket_code, order_no, operator_username, reason, date_from, date_to))
        return "\ufeffticketCode,action\nT-1,CHECK_IN\n"

    def export_check_in_audit_logs_xlsx_for_worker(
        self,
        ticket_code: str | None,
        order_no: str | None,
        operator_username: str | None,
        reason: str | None,
        date_from: date | None,
        date_to: date | None,
    ) -> bytes:
        self.check_in_audit_xlsx_calls.append((ticket_code, order_no, operator_username, reason, date_from, date_to))
        return b"PK\x03\x04fake-check-in-audit-xlsx"

    def export_check_in_failure_audit_logs_csv_for_worker(
        self,
        ticket_code: str | None,
        failure_code: str | None,
        operator_username: str | None,
        date_from: date | None,
        date_to: date | None,
    ) -> str:
        self.check_in_failure_audit_csv_calls.append(
            (ticket_code, failure_code, operator_username, date_from, date_to)
        )
        return "\ufeffticketCode,failureCode\nT-404,TICKET_NOT_FOUND\n"

    def export_check_in_failure_audit_logs_xlsx_for_worker(
        self,
        ticket_code: str | None,
        failure_code: str | None,
        operator_username: str | None,
        date_from: date | None,
        date_to: date | None,
    ) -> bytes:
        self.check_in_failure_audit_xlsx_calls.append(
            (ticket_code, failure_code, operator_username, date_from, date_to)
        )
        return b"PK\x03\x04fake-check-in-failure-audit-xlsx"

    @staticmethod
    def check_in_audit_log_export_filename(date_from: date | None, date_to: date | None) -> str:
        start = date_from.strftime("%Y%m%d") if date_from else "start"
        end = date_to.strftime("%Y%m%d") if date_to else "end"
        return f"admin-check-in-logs-{start}-{end}.csv"

    @staticmethod
    def check_in_audit_log_export_xlsx_filename(date_from: date | None, date_to: date | None) -> str:
        start = date_from.strftime("%Y%m%d") if date_from else "start"
        end = date_to.strftime("%Y%m%d") if date_to else "end"
        return f"admin-check-in-logs-{start}-{end}.xlsx"

    @staticmethod
    def check_in_failure_audit_log_export_filename(date_from: date | None, date_to: date | None) -> str:
        start = date_from.strftime("%Y%m%d") if date_from else "start"
        end = date_to.strftime("%Y%m%d") if date_to else "end"
        return f"admin-check-in-failure-logs-{start}-{end}.csv"

    @staticmethod
    def check_in_failure_audit_log_export_xlsx_filename(date_from: date | None, date_to: date | None) -> str:
        start = date_from.strftime("%Y%m%d") if date_from else "start"
        end = date_to.strftime("%Y%m%d") if date_to else "end"
        return f"admin-check-in-failure-logs-{start}-{end}.xlsx"


class FakeAdminRefundService:
    def __init__(self):
        self.refund_audit_csv_calls: list[
            tuple[str | None, str | None, str | None, date | None, date | None]
        ] = []
        self.refund_audit_xlsx_calls: list[
            tuple[str | None, str | None, str | None, date | None, date | None]
        ] = []

    def export_refund_audit_logs_csv_for_worker(
        self,
        refund_type: str | None,
        order_no: str | None,
        operator_username: str | None,
        date_from: date | None,
        date_to: date | None,
    ) -> str:
        self.refund_audit_csv_calls.append((refund_type, order_no, operator_username, date_from, date_to))
        return "\ufefforderNo,refundType\nO-1,FULL\n"

    def export_refund_audit_logs_xlsx_for_worker(
        self,
        refund_type: str | None,
        order_no: str | None,
        operator_username: str | None,
        date_from: date | None,
        date_to: date | None,
    ) -> bytes:
        self.refund_audit_xlsx_calls.append((refund_type, order_no, operator_username, date_from, date_to))
        return b"PK\x03\x04fake-refund-audit-xlsx"

    @staticmethod
    def refund_audit_log_export_filename(date_from: date | None, date_to: date | None) -> str:
        start = date_from.strftime("%Y%m%d") if date_from else "start"
        end = date_to.strftime("%Y%m%d") if date_to else "end"
        return f"admin-refund-logs-{start}-{end}.csv"

    @staticmethod
    def refund_audit_log_export_xlsx_filename(date_from: date | None, date_to: date | None) -> str:
        start = date_from.strftime("%Y%m%d") if date_from else "start"
        end = date_to.strftime("%Y%m%d") if date_to else "end"
        return f"admin-refund-logs-{start}-{end}.xlsx"


def build_client(
    auth_repo: FakeAuthRepository,
    export_repo: FakeAdminExportJobRepository,
    file_storage: FakeAdminExportFileStorage | None = None,
) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_auth_repository] = lambda: auth_repo
    app.dependency_overrides[get_admin_export_job_repository] = lambda: export_repo
    if file_storage is not None:
        app.dependency_overrides[get_admin_export_file_storage] = lambda: file_storage
    return TestClient(app)


def login_admin(client: TestClient, auth_repo: FakeAuthRepository) -> None:
    seed_enabled_admin(auth_repo)
    response = client.post(
        "/api/admin/auth/login",
        json=admin_login_payload(),
        headers=csrf_headers(client),
    )
    assert response.status_code == 200


def login_visitor(client: TestClient) -> None:
    response = client.post(
        "/api/auth/visitor/register",
        json={"username": "demo_visitor", "password": "Visitor123", "phone": "13911112222"},
        headers=csrf_headers(client),
    )
    assert response.status_code == 200


def test_admin_can_create_export_job_with_csrf():
    auth_repo = FakeAuthRepository()
    export_repo = FakeAdminExportJobRepository()
    client = build_client(auth_repo, export_repo)
    login_admin(client, auth_repo)

    response = client.post(
        "/api/admin/export-jobs",
        json={
            "exportType": "ORDER_DETAIL",
            "fileFormat": "CSV",
            "filters": {"dateFrom": "2026-07-01", "dateTo": "2026-07-31"},
        },
        headers=csrf_headers(client),
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["jobId"]
    assert data["exportType"] == "ORDER_DETAIL"
    assert data["fileFormat"] == "CSV"
    assert data["filters"] == {"dateFrom": "2026-07-01", "dateTo": "2026-07-31"}
    assert data["status"] == "PENDING"
    assert data["requestId"] == response.json()["request_id"]
    assert data["requestedByUsername"] == "admin"
    assert data["requestedByDisplayName"] == "演示管理员"
    assert "storageKey" not in data
    assert "requestedByAdminUserId" not in data

    created = export_repo.created_records[0]
    assert created.export_type == "ORDER_DETAIL"
    assert created.file_format == "CSV"
    assert created.filters == {"dateFrom": "2026-07-01", "dateTo": "2026-07-31"}
    assert created.request_id == response.json()["request_id"]
    assert created.requested_by_admin_user_id == 1


def test_export_job_filters_are_whitelisted_and_normalized():
    auth_repo = FakeAuthRepository()
    export_repo = FakeAdminExportJobRepository()
    client = build_client(auth_repo, export_repo)
    login_admin(client, auth_repo)
    headers = csrf_headers(client)

    check_in_audit = client.post(
        "/api/admin/export-jobs",
        json={
            "exportType": "CHECK_IN_AUDIT",
            "fileFormat": "XLSX",
            "filters": {
                "ticketCode": " TICKET-1 ",
                "orderNo": " O-1 ",
                "operatorUsername": " admin ",
                "reason": " 误核销 ",
                "dateFrom": "2026-07-01",
                "dateTo": "2026-07-31",
            },
        },
        headers=headers,
    )
    failure_audit = client.post(
        "/api/admin/export-jobs",
        json={
            "exportType": "CHECK_IN_FAILURE_AUDIT",
            "fileFormat": "CSV",
            "filters": {"failureCode": "ticket_not_found", "ticketCode": " T-404 "},
        },
        headers=headers,
    )
    refund_audit = client.post(
        "/api/admin/export-jobs",
        json={
            "exportType": "REFUND_AUDIT",
            "fileFormat": "CSV",
            "filters": {"refundType": "partial", "orderNo": " O-REFUND "},
        },
        headers=headers,
    )
    payment_reconciliation = client.post(
        "/api/admin/export-jobs",
        json={
            "exportType": "PAYMENT_RECONCILIATION",
            "fileFormat": "CSV",
            "filters": {"dateFrom": "2026-07-01", "dateTo": "2026-07-31"},
        },
        headers=headers,
    )
    daily_trend = client.post(
        "/api/admin/export-jobs",
        json={
            "exportType": "DAILY_TREND",
            "fileFormat": "XLSX",
            "filters": {"dateFrom": "2026-07-01", "dateTo": "2026-07-03", "includeEmpty": "true"},
        },
        headers=headers,
    )

    assert check_in_audit.status_code == 200
    assert failure_audit.status_code == 200
    assert refund_audit.status_code == 200
    assert payment_reconciliation.status_code == 200
    assert daily_trend.status_code == 200
    assert export_repo.created_records[-5].filters == {
        "dateFrom": "2026-07-01",
        "dateTo": "2026-07-31",
        "ticketCode": "TICKET-1",
        "orderNo": "O-1",
        "operatorUsername": "admin",
        "reason": "误核销",
    }
    assert export_repo.created_records[-4].filters == {
        "ticketCode": "T-404",
        "failureCode": "TICKET_NOT_FOUND",
    }
    assert export_repo.created_records[-3].filters == {
        "orderNo": "O-REFUND",
        "refundType": "PARTIAL",
    }
    assert export_repo.created_records[-2].filters == {
        "dateFrom": "2026-07-01",
        "dateTo": "2026-07-31",
    }
    assert export_repo.created_records[-1].filters == {
        "dateFrom": "2026-07-01",
        "dateTo": "2026-07-03",
        "includeEmpty": True,
    }
    assert check_in_audit.json()["data"]["filters"] == {
        "dateFrom": "2026-07-01",
        "dateTo": "2026-07-31",
        "ticketCode": "***",
        "orderNo": "***",
        "operatorUsername": "***",
        "reason": "***",
    }
    assert failure_audit.json()["data"]["filters"] == {
        "ticketCode": "***",
        "failureCode": "TICKET_NOT_FOUND",
    }
    assert refund_audit.json()["data"]["filters"] == {
        "orderNo": "***",
        "refundType": "PARTIAL",
    }
    assert payment_reconciliation.json()["data"]["filters"] == {
        "dateFrom": "2026-07-01",
        "dateTo": "2026-07-31",
    }
    assert daily_trend.json()["data"]["filters"]["includeEmpty"] is True


def test_export_job_api_redacts_sensitive_filter_values_without_affecting_worker_filters():
    auth_repo = FakeAuthRepository()
    export_repo = FakeAdminExportJobRepository()
    export_repo.jobs = {
        "sensitive-filters": export_job_record(
            job_id="sensitive-filters",
            export_type="CHECK_IN_AUDIT",
            filters={
                "ticketCode": "TICKET-SECRET",
                "orderNo": "ORDER-SECRET",
                "operatorUsername": "admin-secret",
                "reason": "误核销原因",
                "dateFrom": "2026-07-01",
                "dateTo": "2026-07-31",
            },
        )
    }
    client = build_client(auth_repo, export_repo)
    login_admin(client, auth_repo)

    list_response = client.get("/api/admin/export-jobs", params={"exportType": "CHECK_IN_AUDIT"})
    detail_response = client.get("/api/admin/export-jobs/sensitive-filters")
    claimed_job = AdminExportJobService(export_repo, SimpleNamespace()).claim_next_pending_job()

    expected_public_filters = {
        "ticketCode": "***",
        "orderNo": "***",
        "operatorUsername": "***",
        "reason": "***",
        "dateFrom": "2026-07-01",
        "dateTo": "2026-07-31",
    }
    assert list_response.status_code == 200
    assert list_response.json()["data"]["items"][0]["filters"] == expected_public_filters
    assert detail_response.status_code == 200
    assert detail_response.json()["data"]["filters"] == expected_public_filters
    assert claimed_job is not None
    assert claimed_job.filters["ticketCode"] == "TICKET-SECRET"
    assert claimed_job.filters["orderNo"] == "ORDER-SECRET"
    assert claimed_job.filters["operatorUsername"] == "admin-secret"
    assert claimed_job.filters["reason"] == "误核销原因"


def test_export_job_worker_state_transitions_are_internal_and_guarded():
    auth_repo = FakeAuthRepository()
    export_repo = FakeAdminExportJobRepository()
    export_repo.jobs = {
        "later": export_job_record(job_id="later", requested_at=datetime(2026, 7, 1, 10, tzinfo=UTC)),
        "earlier": export_job_record(job_id="earlier", requested_at=datetime(2026, 7, 1, 8, tzinfo=UTC)),
        "running": export_job_record(
            job_id="running",
            status="RUNNING",
            requested_at=datetime(2026, 7, 1, 7, tzinfo=UTC),
            started_at=STARTED_AT,
        ),
    }
    service = AdminExportJobService(export_repo, auth_repo)

    claimed = service.claim_next_pending_job()
    succeeded = service.mark_export_job_succeeded(
        " earlier ",
        file_name=" export.csv ",
        storage_key=" private/exports/export.csv ",
    )
    failed = service.mark_export_job_failed(
        " running ",
        error_code=" WORKER_ERROR ",
        error_message=" transient failure ",
    )
    no_pending_after_later = service.claim_next_pending_job()
    no_pending = service.claim_next_pending_job()

    assert claimed is not None
    assert claimed.job_id == "earlier"
    assert claimed.status == "RUNNING"
    assert succeeded is not None
    assert succeeded.status == "SUCCEEDED"
    assert succeeded.file_name == "export.csv"
    assert succeeded.error_code is None
    assert "storageKey" not in succeeded.model_dump(by_alias=True)
    assert export_repo.succeeded_storage_keys["earlier"] == "private/exports/export.csv"
    assert failed is not None
    assert failed.status == "FAILED"
    assert failed.error_code == "WORKER_ERROR"
    assert failed.error_message == "transient failure"
    assert no_pending_after_later is not None
    assert no_pending_after_later.job_id == "later"
    assert no_pending_after_later.status == "RUNNING"
    assert no_pending is None
    assert service.mark_export_job_succeeded(
        "earlier",
        file_name="again.csv",
        storage_key="private/again.csv",
    ) is None


def test_export_job_worker_marks_interrupted_running_job_failed():
    export_repo = FakeAdminExportJobRepository()
    export_repo.jobs = {"interrupt-job": export_job_record(job_id="interrupt-job")}
    worker_service = AdminExportJobWorkerService(
        AdminExportJobService(export_repo, FakeAuthRepository()),
        FakeAdminReportService(),
        FakeAdminCheckInService(),
        FakeAdminRefundService(),
        FakeAdminExportFileStorage(),
    )

    def interrupt_running_job(_job):
        raise KeyboardInterrupt()

    worker_service.process_running_job = interrupt_running_job

    try:
        worker_service.process_next_pending_job()
    except KeyboardInterrupt:
        pass
    else:
        raise AssertionError("expected KeyboardInterrupt to be re-raised")

    failed_job = export_repo.jobs["interrupt-job"]
    assert failed_job.status == "FAILED"
    assert failed_job.error_code == "ADMIN_EXPORT_JOB_WORKER_FAILED"
    assert failed_job.error_message == "导出任务处理失败"
    assert export_repo.retry_counts.get("interrupt-job", 0) == 0


def test_export_job_worker_auto_retries_unexpected_failure_once_before_failed():
    export_repo = FakeAdminExportJobRepository()
    export_repo.jobs = {"auto-retry-job": export_job_record(job_id="auto-retry-job")}
    worker_service = AdminExportJobWorkerService(
        AdminExportJobService(export_repo, FakeAuthRepository()),
        FakeAdminReportService(),
        FakeAdminCheckInService(),
        FakeAdminRefundService(),
        FakeAdminExportFileStorage(),
    )

    def crash_running_job(_job):
        raise RuntimeError("temporary filesystem failure")

    worker_service.process_running_job = crash_running_job

    first_result = worker_service.process_next_pending_job()
    retried_job = export_repo.jobs["auto-retry-job"]
    immediate_result = worker_service.process_next_pending_job()

    assert first_result is not None
    assert first_result.job_id == "auto-retry-job"
    assert first_result.status == "PENDING"
    assert first_result.error_code is None
    assert retried_job.status == "PENDING"
    assert retried_job.started_at is None
    assert retried_job.finished_at is None
    assert retried_job.error_code is None
    assert export_repo.retry_counts["auto-retry-job"] == 1
    assert export_repo.next_attempt_ats["auto-retry-job"] == NEXT_ATTEMPT_AT
    assert immediate_result is None

    export_repo.next_attempt_ats.pop("auto-retry-job")
    second_result = worker_service.process_next_pending_job()
    failed_job = export_repo.jobs["auto-retry-job"]

    assert second_result is not None
    assert second_result.status == "FAILED"
    assert second_result.error_code == "ADMIN_EXPORT_JOB_WORKER_FAILED"
    assert second_result.error_message == "导出任务处理失败"
    assert failed_job.status == "FAILED"
    assert failed_job.finished_at == FINISHED_AT
    assert failed_job.error_code == "ADMIN_EXPORT_JOB_WORKER_FAILED"
    assert len(export_repo.alert_events) == 1
    alert_event = export_repo.alert_events[0]
    assert alert_event.job_id == "auto-retry-job"
    assert alert_event.export_type == "ORDER_DETAIL"
    assert alert_event.file_format == "CSV"
    assert alert_event.error_code == "ADMIN_EXPORT_JOB_WORKER_FAILED"
    assert alert_event.error_message == "导出任务处理失败"
    assert alert_event.alert_source == "WORKER_FINAL_FAILURE"
    assert "dateFrom" not in repr(alert_event)
    assert "storage_key" not in repr(alert_event)


def test_export_job_worker_does_not_record_alert_event_for_pending_auto_retry():
    export_repo = FakeAdminExportJobRepository()
    export_repo.jobs = {"auto-retry-job": export_job_record(job_id="auto-retry-job")}
    worker_service = AdminExportJobWorkerService(
        AdminExportJobService(export_repo, FakeAuthRepository()),
        FakeAdminReportService(),
        FakeAdminCheckInService(),
        FakeAdminRefundService(),
        FakeAdminExportFileStorage(),
    )

    def crash_running_job(_job):
        raise RuntimeError("temporary filesystem failure")

    worker_service.process_running_job = crash_running_job

    first_result = worker_service.process_next_pending_job()

    assert first_result is not None
    assert first_result.status == "PENDING"
    assert export_repo.alert_events == []


def test_export_job_alert_event_deduplicates_open_events_but_not_closed_events():
    export_repo = FakeAdminExportJobRepository()
    record = AdminExportJobAlertEventCreateRecord(
        job_id="dedupe-job",
        export_type="ORDER_DETAIL",
        file_format="CSV",
        error_code="ADMIN_EXPORT_JOB_WORKER_FAILED",
        error_message="第一次失败",
        alert_source="WORKER_FINAL_FAILURE",
    )

    export_repo.create_export_job_alert_event(record)
    export_repo.create_export_job_alert_event(
        replace(record, error_message="第二次失败")
    )

    assert len(export_repo.alert_event_records) == 1
    assert export_repo.alert_event_records[0].error_message == "第二次失败"
    assert export_repo.alert_event_records[0].occurrence_count == 2
    assert export_repo.alert_event_records[0].last_seen_at == FINISHED_AT

    export_repo.alert_event_records[0] = replace(export_repo.alert_event_records[0], closed_at=FINISHED_AT)
    export_repo.create_export_job_alert_event(
        replace(record, error_message="关闭后再次失败")
    )

    assert len(export_repo.alert_event_records) == 2
    assert export_repo.alert_event_records[1].error_message == "关闭后再次失败"
    assert export_repo.alert_event_records[1].occurrence_count == 1


def test_export_job_worker_recovers_stale_running_jobs_before_claiming_next_job():
    export_repo = FakeAdminExportJobRepository()
    export_repo.jobs = {
        "stale-running": export_job_record(
            job_id="stale-running",
            status="RUNNING",
            requested_at=datetime(2026, 7, 1, 8, tzinfo=UTC),
            started_at=STARTED_AT,
        ),
        "fresh-pending": export_job_record(
            job_id="fresh-pending",
            requested_at=datetime(2026, 7, 1, 9, tzinfo=UTC),
        ),
    }
    export_repo.stale_running_job_ids.add("stale-running")
    storage = FakeAdminExportFileStorage()
    worker_service = AdminExportJobWorkerService(
        AdminExportJobService(export_repo, FakeAuthRepository()),
        FakeAdminReportService(),
        FakeAdminCheckInService(),
        FakeAdminRefundService(),
        storage,
    )

    result = worker_service.process_next_pending_job()

    assert export_repo.recover_stale_running_calls == [
        (1800, "ADMIN_EXPORT_JOB_WORKER_TIMEOUT", "导出任务处理超时")
    ]
    assert result is not None
    assert result.job_id == "stale-running"
    assert result.status == "SUCCEEDED"
    assert export_repo.jobs["stale-running"].status == "SUCCEEDED"
    assert export_repo.retry_counts["stale-running"] == 1
    assert export_repo.jobs["fresh-pending"].status == "PENDING"
    assert export_repo.alert_events == []
    assert any(key.startswith("export-jobs/stale-running/") for key in storage.files)


def test_export_job_worker_recovers_stale_running_job_to_failed_when_retry_exhausted():
    export_repo = FakeAdminExportJobRepository()
    export_repo.jobs = {
        "stale-running": export_job_record(
            job_id="stale-running",
            status="RUNNING",
            started_at=STARTED_AT,
        )
    }
    export_repo.stale_running_job_ids.add("stale-running")
    export_repo.retry_counts["stale-running"] = 1
    export_repo.max_retries["stale-running"] = 1
    service = AdminExportJobService(export_repo, FakeAuthRepository())

    recovered = service.recover_stale_running_jobs()

    assert recovered == 1
    failed_job = export_repo.jobs["stale-running"]
    assert failed_job.status == "FAILED"
    assert failed_job.error_code == "ADMIN_EXPORT_JOB_WORKER_TIMEOUT"
    assert failed_job.error_message == "导出任务处理超时"
    assert failed_job.finished_at == FINISHED_AT
    assert len(export_repo.alert_events) == 1
    alert_event = export_repo.alert_events[0]
    assert alert_event.job_id == "stale-running"
    assert alert_event.export_type == "ORDER_DETAIL"
    assert alert_event.file_format == "CSV"
    assert alert_event.error_code == "ADMIN_EXPORT_JOB_WORKER_TIMEOUT"
    assert alert_event.error_message == "导出任务处理超时"
    assert alert_event.alert_source == "WORKER_FINAL_FAILURE"
    assert "dateFrom" not in repr(alert_event)
    assert "storage_key" not in repr(alert_event)


def test_admin_can_retry_failed_export_job_with_csrf():
    auth_repo = FakeAuthRepository()
    export_repo = FakeAdminExportJobRepository()
    export_repo.jobs["failed-job"] = export_job_record(
        job_id="failed-job",
        status="FAILED",
        filters={
            "ticketCode": "TICKET-SECRET",
            "orderNo": "ORDER-SECRET",
            "operatorUsername": "admin-secret",
            "reason": "误核销原因",
            "dateFrom": "2026-07-01",
        },
        started_at=STARTED_AT,
        finished_at=FINISHED_AT,
        file_name="stale.csv",
        error_code="ADMIN_EXPORT_JOB_WORKER_FAILED",
        error_message="导出任务处理失败",
    )
    export_repo.succeeded_storage_keys["failed-job"] = "private/stale.csv"
    export_repo.retry_counts["failed-job"] = 1
    export_repo.next_attempt_ats["failed-job"] = NEXT_ATTEMPT_AT
    client = build_client(auth_repo, export_repo)
    login_admin(client, auth_repo)

    response = client.post("/api/admin/export-jobs/failed-job/retry", headers=csrf_headers(client))

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["jobId"] == "failed-job"
    assert data["status"] == "PENDING"
    assert data["filters"] == {
        "ticketCode": "***",
        "orderNo": "***",
        "operatorUsername": "***",
        "reason": "***",
        "dateFrom": "2026-07-01",
    }
    assert "startedAt" not in data
    assert "finishedAt" not in data
    assert "fileName" not in data
    assert "errorCode" not in data
    assert "errorMessage" not in data
    assert "storageKey" not in data
    retried = export_repo.jobs["failed-job"]
    assert retried.status == "PENDING"
    assert retried.started_at is None
    assert retried.finished_at is None
    assert retried.file_name is None
    assert retried.error_code is None
    assert retried.error_message is None
    assert retried.filters["ticketCode"] == "TICKET-SECRET"
    assert retried.filters["orderNo"] == "ORDER-SECRET"
    assert retried.filters["operatorUsername"] == "admin-secret"
    assert retried.filters["reason"] == "误核销原因"
    assert export_repo.retry_counts["failed-job"] == 0
    assert "failed-job" not in export_repo.next_attempt_ats
    assert "failed-job" not in export_repo.succeeded_storage_keys


def test_export_job_retry_rejects_non_failed_and_missing_jobs():
    auth_repo = FakeAuthRepository()
    export_repo = FakeAdminExportJobRepository()
    export_repo.jobs["running-job"] = export_job_record(
        job_id="running-job",
        status="RUNNING",
        started_at=STARTED_AT,
    )
    export_repo.jobs["succeeded-job"] = export_job_record(
        job_id="succeeded-job",
        status="SUCCEEDED",
        started_at=STARTED_AT,
        finished_at=FINISHED_AT,
        file_name="export.csv",
    )
    client = build_client(auth_repo, export_repo)
    login_admin(client, auth_repo)
    headers = csrf_headers(client)

    pending_retry = client.post(
        "/api/admin/export-jobs/11111111-1111-4111-8111-111111111111/retry",
        headers=headers,
    )
    running_retry = client.post("/api/admin/export-jobs/running-job/retry", headers=headers)
    succeeded_retry = client.post("/api/admin/export-jobs/succeeded-job/retry", headers=headers)
    missing_retry = client.post("/api/admin/export-jobs/missing-job/retry", headers=headers)

    assert pending_retry.status_code == 409
    assert pending_retry.json()["code"] == "ADMIN_EXPORT_JOB_RETRY_NOT_ALLOWED"
    assert running_retry.status_code == 409
    assert running_retry.json()["code"] == "ADMIN_EXPORT_JOB_RETRY_NOT_ALLOWED"
    assert succeeded_retry.status_code == 409
    assert succeeded_retry.json()["code"] == "ADMIN_EXPORT_JOB_RETRY_NOT_ALLOWED"
    assert missing_retry.status_code == 404
    assert missing_retry.json()["code"] == "ADMIN_EXPORT_JOB_NOT_FOUND"


def test_export_job_worker_state_inputs_are_length_limited():
    service = AdminExportJobService(FakeAdminExportJobRepository(), FakeAuthRepository())

    invalid_calls = [
        lambda: service.mark_export_job_succeeded(123, file_name="export.csv", storage_key="private/export.csv"),
        lambda: service.mark_export_job_succeeded("", file_name="export.csv", storage_key="private/export.csv"),
        lambda: service.mark_export_job_succeeded("job", file_name=None, storage_key="private/export.csv"),
        lambda: service.mark_export_job_succeeded("job", file_name="x" * 256, storage_key="private/export.csv"),
        lambda: service.mark_export_job_succeeded("job", file_name="export.csv", storage_key="x" * 256),
        lambda: service.mark_export_job_failed("job", error_code="x" * 81, error_message="failed"),
        lambda: service.mark_export_job_failed("job", error_code="WORKER_ERROR", error_message="x" * 501),
    ]

    for call in invalid_calls:
        try:
            call()
        except AppError as exc:
            assert exc.code == "ADMIN_EXPORT_JOB_WORKER_INPUT_INVALID"
        else:
            raise AssertionError("expected worker input validation error")


def test_export_job_worker_generates_order_detail_csv_and_marks_job_succeeded():
    export_repo = FakeAdminExportJobRepository()
    export_repo.jobs = {
        "order-csv-job": export_job_record(
            job_id="order-csv-job",
            filters={"dateFrom": "2026-07-01", "dateTo": "2026-07-31"},
        )
    }
    report_service = FakeAdminReportService()
    check_in_service = FakeAdminCheckInService()
    refund_service = FakeAdminRefundService()
    storage = FakeAdminExportFileStorage()
    worker_service = AdminExportJobWorkerService(
        AdminExportJobService(export_repo, FakeAuthRepository()),
        report_service,
        check_in_service,
        refund_service,
        storage,
    )

    result = worker_service.process_next_pending_job()

    assert result is not None
    assert result.job_id == "order-csv-job"
    assert result.status == "SUCCEEDED"
    assert result.file_name == "admin-orders-20260701-20260731.csv"
    assert result.error_code is None
    assert "storageKey" not in result.model_dump(by_alias=True)
    storage_key = export_repo.succeeded_storage_keys["order-csv-job"]
    assert storage_key == "export-jobs/order-csv-job/admin-orders-20260701-20260731.csv"
    assert storage.files[storage_key] == "\ufefforderNo,buyerName\nO-1,张三\n".encode("utf-8")
    assert report_service.order_detail_csv_calls == [(date(2026, 7, 1), date(2026, 7, 31))]
    assert report_service.order_detail_xlsx_calls == []
    assert check_in_service.check_in_audit_csv_calls == []
    assert check_in_service.check_in_audit_xlsx_calls == []
    assert check_in_service.check_in_failure_audit_csv_calls == []
    assert check_in_service.check_in_failure_audit_xlsx_calls == []


def test_export_job_worker_deletes_generated_file_when_success_mark_returns_none():
    export_repo = FakeAdminExportJobRepository()
    export_repo.jobs = {
        "lost-running-job": export_job_record(
            job_id="lost-running-job",
            status="FAILED",
            started_at=STARTED_AT,
        )
    }
    storage = FakeAdminExportFileStorage()
    worker_service = AdminExportJobWorkerService(
        AdminExportJobService(export_repo, FakeAuthRepository()),
        FakeAdminReportService(),
        FakeAdminCheckInService(),
        FakeAdminRefundService(),
        storage,
    )
    job = AdminExportJobService.to_export_job_dto(
        export_job_record(job_id="lost-running-job", status="RUNNING", started_at=STARTED_AT)
    )

    result = worker_service.write_file_and_mark_succeeded(
        job,
        file_name="orphan.csv",
        content=b"temporary export",
    )

    assert result is None
    assert storage.files == {}
    assert "lost-running-job" not in export_repo.succeeded_storage_keys


def test_export_job_worker_deletes_generated_file_when_success_mark_raises():
    class RaisingAdminExportJobService(AdminExportJobService):
        def mark_export_job_succeeded(self, *_args, **_kwargs):
            raise RuntimeError("database write failed")

    export_repo = FakeAdminExportJobRepository()
    storage = FakeAdminExportFileStorage()
    worker_service = AdminExportJobWorkerService(
        RaisingAdminExportJobService(export_repo, FakeAuthRepository()),
        FakeAdminReportService(),
        FakeAdminCheckInService(),
        FakeAdminRefundService(),
        storage,
    )
    job = AdminExportJobService.to_export_job_dto(
        export_job_record(job_id="raise-mark-job", status="RUNNING", started_at=STARTED_AT)
    )

    with pytest.raises(RuntimeError, match="database write failed"):
        worker_service.write_file_and_mark_succeeded(
            job,
            file_name="orphan.csv",
            content=b"temporary export",
        )

    assert storage.files == {}


def test_export_job_worker_generates_order_detail_xlsx_and_marks_job_succeeded():
    export_repo = FakeAdminExportJobRepository()
    export_repo.jobs = {
        "order-xlsx-job": export_job_record(
            job_id="order-xlsx-job",
            file_format="XLSX",
            filters={"dateFrom": "2026-07-01", "dateTo": "2026-07-31"},
        )
    }
    report_service = FakeAdminReportService()
    check_in_service = FakeAdminCheckInService()
    refund_service = FakeAdminRefundService()
    storage = FakeAdminExportFileStorage()
    worker_service = AdminExportJobWorkerService(
        AdminExportJobService(export_repo, FakeAuthRepository()),
        report_service,
        check_in_service,
        refund_service,
        storage,
    )

    result = worker_service.process_next_pending_job()

    assert result is not None
    assert result.job_id == "order-xlsx-job"
    assert result.status == "SUCCEEDED"
    assert result.file_name == "admin-orders-20260701-20260731.xlsx"
    assert result.error_code is None
    assert "storageKey" not in result.model_dump(by_alias=True)
    storage_key = export_repo.succeeded_storage_keys["order-xlsx-job"]
    assert storage_key == "export-jobs/order-xlsx-job/admin-orders-20260701-20260731.xlsx"
    assert storage.files[storage_key] == b"PK\x03\x04fake-order-xlsx"
    assert report_service.order_detail_csv_calls == []
    assert report_service.order_detail_xlsx_calls == [(date(2026, 7, 1), date(2026, 7, 31))]
    assert check_in_service.check_in_audit_csv_calls == []
    assert check_in_service.check_in_audit_xlsx_calls == []
    assert check_in_service.check_in_failure_audit_csv_calls == []
    assert check_in_service.check_in_failure_audit_xlsx_calls == []


def test_export_job_worker_generates_check_in_audit_csv_and_marks_job_succeeded():
    export_repo = FakeAdminExportJobRepository()
    export_repo.jobs = {
        "check-in-audit-csv-job": export_job_record(
            job_id="check-in-audit-csv-job",
            export_type="CHECK_IN_AUDIT",
            filters={
                "ticketCode": "T-1",
                "orderNo": "O-1",
                "operatorUsername": "admin",
                "reason": "误核销",
                "dateFrom": "2026-07-01",
                "dateTo": "2026-07-31",
            },
        )
    }
    report_service = FakeAdminReportService()
    check_in_service = FakeAdminCheckInService()
    refund_service = FakeAdminRefundService()
    storage = FakeAdminExportFileStorage()
    worker_service = AdminExportJobWorkerService(
        AdminExportJobService(export_repo, FakeAuthRepository()),
        report_service,
        check_in_service,
        refund_service,
        storage,
    )

    result = worker_service.process_next_pending_job()

    assert result is not None
    assert result.job_id == "check-in-audit-csv-job"
    assert result.status == "SUCCEEDED"
    assert result.file_name == "admin-check-in-logs-20260701-20260731.csv"
    assert result.error_code is None
    assert "storageKey" not in result.model_dump(by_alias=True)
    storage_key = export_repo.succeeded_storage_keys["check-in-audit-csv-job"]
    assert storage_key == "export-jobs/check-in-audit-csv-job/admin-check-in-logs-20260701-20260731.csv"
    assert storage.files[storage_key] == "\ufeffticketCode,action\nT-1,CHECK_IN\n".encode("utf-8")
    assert report_service.order_detail_csv_calls == []
    assert report_service.order_detail_xlsx_calls == []
    assert check_in_service.check_in_audit_csv_calls == [
        ("T-1", "O-1", "admin", "误核销", date(2026, 7, 1), date(2026, 7, 31))
    ]
    assert check_in_service.check_in_audit_xlsx_calls == []
    assert check_in_service.check_in_failure_audit_csv_calls == []
    assert check_in_service.check_in_failure_audit_xlsx_calls == []


def test_export_job_worker_generates_check_in_audit_xlsx_and_marks_job_succeeded():
    export_repo = FakeAdminExportJobRepository()
    export_repo.jobs = {
        "check-in-audit-xlsx-job": export_job_record(
            job_id="check-in-audit-xlsx-job",
            export_type="CHECK_IN_AUDIT",
            file_format="XLSX",
            filters={
                "ticketCode": "T-1",
                "orderNo": "O-1",
                "operatorUsername": "admin",
                "reason": "误核销",
                "dateFrom": "2026-07-01",
                "dateTo": "2026-07-31",
            },
        )
    }
    report_service = FakeAdminReportService()
    check_in_service = FakeAdminCheckInService()
    refund_service = FakeAdminRefundService()
    storage = FakeAdminExportFileStorage()
    worker_service = AdminExportJobWorkerService(
        AdminExportJobService(export_repo, FakeAuthRepository()),
        report_service,
        check_in_service,
        refund_service,
        storage,
    )

    result = worker_service.process_next_pending_job()

    assert result is not None
    assert result.job_id == "check-in-audit-xlsx-job"
    assert result.status == "SUCCEEDED"
    assert result.file_name == "admin-check-in-logs-20260701-20260731.xlsx"
    assert result.error_code is None
    assert "storageKey" not in result.model_dump(by_alias=True)
    storage_key = export_repo.succeeded_storage_keys["check-in-audit-xlsx-job"]
    assert storage_key == "export-jobs/check-in-audit-xlsx-job/admin-check-in-logs-20260701-20260731.xlsx"
    assert storage.files[storage_key] == b"PK\x03\x04fake-check-in-audit-xlsx"
    assert report_service.order_detail_csv_calls == []
    assert report_service.order_detail_xlsx_calls == []
    assert check_in_service.check_in_audit_csv_calls == []
    assert check_in_service.check_in_audit_xlsx_calls == [
        ("T-1", "O-1", "admin", "误核销", date(2026, 7, 1), date(2026, 7, 31))
    ]
    assert check_in_service.check_in_failure_audit_csv_calls == []
    assert check_in_service.check_in_failure_audit_xlsx_calls == []


def test_export_job_worker_generates_check_in_failure_audit_csv_and_marks_job_succeeded():
    export_repo = FakeAdminExportJobRepository()
    export_repo.jobs = {
        "check-in-failure-audit-csv-job": export_job_record(
            job_id="check-in-failure-audit-csv-job",
            export_type="CHECK_IN_FAILURE_AUDIT",
            filters={
                "ticketCode": "T-404",
                "failureCode": "TICKET_NOT_FOUND",
                "operatorUsername": "admin",
                "dateFrom": "2026-07-01",
                "dateTo": "2026-07-31",
            },
        )
    }
    report_service = FakeAdminReportService()
    check_in_service = FakeAdminCheckInService()
    refund_service = FakeAdminRefundService()
    storage = FakeAdminExportFileStorage()
    worker_service = AdminExportJobWorkerService(
        AdminExportJobService(export_repo, FakeAuthRepository()),
        report_service,
        check_in_service,
        refund_service,
        storage,
    )

    result = worker_service.process_next_pending_job()

    assert result is not None
    assert result.job_id == "check-in-failure-audit-csv-job"
    assert result.status == "SUCCEEDED"
    assert result.file_name == "admin-check-in-failure-logs-20260701-20260731.csv"
    assert result.error_code is None
    assert "storageKey" not in result.model_dump(by_alias=True)
    storage_key = export_repo.succeeded_storage_keys["check-in-failure-audit-csv-job"]
    assert storage_key == (
        "export-jobs/check-in-failure-audit-csv-job/"
        "admin-check-in-failure-logs-20260701-20260731.csv"
    )
    assert storage.files[storage_key] == "\ufeffticketCode,failureCode\nT-404,TICKET_NOT_FOUND\n".encode("utf-8")
    assert report_service.order_detail_csv_calls == []
    assert report_service.order_detail_xlsx_calls == []
    assert check_in_service.check_in_audit_csv_calls == []
    assert check_in_service.check_in_audit_xlsx_calls == []
    assert check_in_service.check_in_failure_audit_csv_calls == [
        ("T-404", "TICKET_NOT_FOUND", "admin", date(2026, 7, 1), date(2026, 7, 31))
    ]
    assert check_in_service.check_in_failure_audit_xlsx_calls == []


def test_export_job_worker_generates_check_in_failure_audit_xlsx_and_marks_job_succeeded():
    export_repo = FakeAdminExportJobRepository()
    export_repo.jobs = {
        "check-in-failure-audit-xlsx-job": export_job_record(
            job_id="check-in-failure-audit-xlsx-job",
            export_type="CHECK_IN_FAILURE_AUDIT",
            file_format="XLSX",
            filters={
                "ticketCode": "T-404",
                "failureCode": "TICKET_NOT_FOUND",
                "operatorUsername": "admin",
                "dateFrom": "2026-07-01",
                "dateTo": "2026-07-31",
            },
        )
    }
    report_service = FakeAdminReportService()
    check_in_service = FakeAdminCheckInService()
    refund_service = FakeAdminRefundService()
    storage = FakeAdminExportFileStorage()
    worker_service = AdminExportJobWorkerService(
        AdminExportJobService(export_repo, FakeAuthRepository()),
        report_service,
        check_in_service,
        refund_service,
        storage,
    )

    result = worker_service.process_next_pending_job()

    assert result is not None
    assert result.job_id == "check-in-failure-audit-xlsx-job"
    assert result.status == "SUCCEEDED"
    assert result.file_name == "admin-check-in-failure-logs-20260701-20260731.xlsx"
    assert result.error_code is None
    assert "storageKey" not in result.model_dump(by_alias=True)
    storage_key = export_repo.succeeded_storage_keys["check-in-failure-audit-xlsx-job"]
    assert storage_key == (
        "export-jobs/check-in-failure-audit-xlsx-job/"
        "admin-check-in-failure-logs-20260701-20260731.xlsx"
    )
    assert storage.files[storage_key] == b"PK\x03\x04fake-check-in-failure-audit-xlsx"
    assert report_service.order_detail_csv_calls == []
    assert report_service.order_detail_xlsx_calls == []
    assert check_in_service.check_in_audit_csv_calls == []
    assert check_in_service.check_in_audit_xlsx_calls == []
    assert check_in_service.check_in_failure_audit_csv_calls == []
    assert check_in_service.check_in_failure_audit_xlsx_calls == [
        ("T-404", "TICKET_NOT_FOUND", "admin", date(2026, 7, 1), date(2026, 7, 31))
    ]
    assert refund_service.refund_audit_csv_calls == []


def test_export_job_worker_generates_refund_audit_csv_and_marks_job_succeeded():
    export_repo = FakeAdminExportJobRepository()
    export_repo.jobs = {
        "refund-audit-csv-job": export_job_record(
            job_id="refund-audit-csv-job",
            export_type="REFUND_AUDIT",
            filters={
                "refundType": "FULL",
                "orderNo": "O-1",
                "operatorUsername": "admin",
                "dateFrom": "2026-07-01",
                "dateTo": "2026-07-31",
            },
        )
    }
    report_service = FakeAdminReportService()
    check_in_service = FakeAdminCheckInService()
    refund_service = FakeAdminRefundService()
    storage = FakeAdminExportFileStorage()
    worker_service = AdminExportJobWorkerService(
        AdminExportJobService(export_repo, FakeAuthRepository()),
        report_service,
        check_in_service,
        refund_service,
        storage,
    )

    result = worker_service.process_next_pending_job()

    assert result is not None
    assert result.job_id == "refund-audit-csv-job"
    assert result.status == "SUCCEEDED"
    assert result.file_name == "admin-refund-logs-20260701-20260731.csv"
    assert result.error_code is None
    assert "storageKey" not in result.model_dump(by_alias=True)
    storage_key = export_repo.succeeded_storage_keys["refund-audit-csv-job"]
    assert storage_key == "export-jobs/refund-audit-csv-job/admin-refund-logs-20260701-20260731.csv"
    assert storage.files[storage_key] == "\ufefforderNo,refundType\nO-1,FULL\n".encode("utf-8")
    assert report_service.order_detail_csv_calls == []
    assert report_service.order_detail_xlsx_calls == []
    assert check_in_service.check_in_audit_csv_calls == []
    assert check_in_service.check_in_audit_xlsx_calls == []
    assert check_in_service.check_in_failure_audit_csv_calls == []
    assert check_in_service.check_in_failure_audit_xlsx_calls == []
    assert refund_service.refund_audit_csv_calls == [
        ("FULL", "O-1", "admin", date(2026, 7, 1), date(2026, 7, 31))
    ]
    assert refund_service.refund_audit_xlsx_calls == []


def test_export_job_worker_generates_refund_audit_xlsx_and_marks_job_succeeded():
    export_repo = FakeAdminExportJobRepository()
    export_repo.jobs = {
        "refund-audit-xlsx-job": export_job_record(
            job_id="refund-audit-xlsx-job",
            export_type="REFUND_AUDIT",
            file_format="XLSX",
            filters={
                "refundType": "PARTIAL",
                "orderNo": "O-2",
                "operatorUsername": "admin",
                "dateFrom": "2026-07-01",
                "dateTo": "2026-07-31",
            },
        )
    }
    report_service = FakeAdminReportService()
    check_in_service = FakeAdminCheckInService()
    refund_service = FakeAdminRefundService()
    storage = FakeAdminExportFileStorage()
    worker_service = AdminExportJobWorkerService(
        AdminExportJobService(export_repo, FakeAuthRepository()),
        report_service,
        check_in_service,
        refund_service,
        storage,
    )

    result = worker_service.process_next_pending_job()

    assert result is not None
    assert result.job_id == "refund-audit-xlsx-job"
    assert result.status == "SUCCEEDED"
    assert result.file_name == "admin-refund-logs-20260701-20260731.xlsx"
    assert result.error_code is None
    assert "storageKey" not in result.model_dump(by_alias=True)
    storage_key = export_repo.succeeded_storage_keys["refund-audit-xlsx-job"]
    assert storage_key == "export-jobs/refund-audit-xlsx-job/admin-refund-logs-20260701-20260731.xlsx"
    assert storage.files[storage_key] == b"PK\x03\x04fake-refund-audit-xlsx"
    assert report_service.order_detail_csv_calls == []
    assert report_service.order_detail_xlsx_calls == []
    assert check_in_service.check_in_audit_csv_calls == []
    assert check_in_service.check_in_audit_xlsx_calls == []
    assert check_in_service.check_in_failure_audit_csv_calls == []
    assert check_in_service.check_in_failure_audit_xlsx_calls == []
    assert refund_service.refund_audit_csv_calls == []
    assert refund_service.refund_audit_xlsx_calls == [
        ("PARTIAL", "O-2", "admin", date(2026, 7, 1), date(2026, 7, 31))
    ]


def test_export_job_worker_generates_product_breakdown_csv_and_marks_job_succeeded():
    export_repo = FakeAdminExportJobRepository()
    export_repo.jobs = {
        "product-breakdown-csv-job": export_job_record(
            job_id="product-breakdown-csv-job",
            export_type="PRODUCT_BREAKDOWN",
            file_format="CSV",
            filters={
                "dateFrom": "2026-07-01",
                "dateTo": "2026-07-31",
            },
        )
    }
    report_service = FakeAdminReportService()
    check_in_service = FakeAdminCheckInService()
    refund_service = FakeAdminRefundService()
    storage = FakeAdminExportFileStorage()
    worker_service = AdminExportJobWorkerService(
        AdminExportJobService(export_repo, FakeAuthRepository()),
        report_service,
        check_in_service,
        refund_service,
        storage,
    )

    result = worker_service.process_next_pending_job()

    assert result is not None
    assert result.job_id == "product-breakdown-csv-job"
    assert result.status == "SUCCEEDED"
    assert result.file_name == "admin-product-breakdown-20260701-20260731.csv"
    assert result.error_code is None
    assert "storageKey" not in result.model_dump(by_alias=True)
    storage_key = export_repo.succeeded_storage_keys["product-breakdown-csv-job"]
    assert storage_key == (
        "export-jobs/product-breakdown-csv-job/"
        "admin-product-breakdown-20260701-20260731.csv"
    )
    assert storage.files[storage_key] == (
        "\ufeffproductId,ticketTypeId,netPaidAmount\nP-1,T-1,128.00\n".encode("utf-8")
    )
    assert report_service.order_detail_csv_calls == []
    assert report_service.order_detail_xlsx_calls == []
    assert report_service.product_breakdown_csv_calls == [(date(2026, 7, 1), date(2026, 7, 31))]
    assert report_service.product_breakdown_xlsx_calls == []
    assert check_in_service.check_in_audit_csv_calls == []
    assert check_in_service.check_in_audit_xlsx_calls == []
    assert check_in_service.check_in_failure_audit_csv_calls == []
    assert check_in_service.check_in_failure_audit_xlsx_calls == []
    assert refund_service.refund_audit_csv_calls == []
    assert refund_service.refund_audit_xlsx_calls == []


def test_export_job_worker_generates_payment_reconciliation_csv_and_marks_job_succeeded():
    export_repo = FakeAdminExportJobRepository()
    export_repo.jobs = {
        "payment-reconciliation-csv-job": export_job_record(
            job_id="payment-reconciliation-csv-job",
            export_type="PAYMENT_RECONCILIATION",
            file_format="CSV",
            filters={
                "dateFrom": "2026-07-01",
                "dateTo": "2026-07-31",
            },
        )
    }
    report_service = FakeAdminReportService()
    check_in_service = FakeAdminCheckInService()
    refund_service = FakeAdminRefundService()
    storage = FakeAdminExportFileStorage()
    worker_service = AdminExportJobWorkerService(
        AdminExportJobService(export_repo, FakeAuthRepository()),
        report_service,
        check_in_service,
        refund_service,
        storage,
    )

    result = worker_service.process_next_pending_job()

    assert result is not None
    assert result.job_id == "payment-reconciliation-csv-job"
    assert result.status == "SUCCEEDED"
    assert result.file_name == "admin-payment-reconciliation-20260701-20260731.csv"
    assert result.error_code is None
    assert "storageKey" not in result.model_dump(by_alias=True)
    storage_key = export_repo.succeeded_storage_keys["payment-reconciliation-csv-job"]
    assert storage_key == (
        "export-jobs/payment-reconciliation-csv-job/"
        "admin-payment-reconciliation-20260701-20260731.csv"
    )
    assert storage.files[storage_key] == (
        "\ufeffdateFrom,dateTo,reconciled\n2026-07-01,2026-07-31,true\n".encode("utf-8")
    )
    assert report_service.order_detail_csv_calls == []
    assert report_service.order_detail_xlsx_calls == []
    assert report_service.payment_reconciliation_csv_calls == [(date(2026, 7, 1), date(2026, 7, 31))]
    assert report_service.payment_reconciliation_xlsx_calls == []
    assert report_service.product_breakdown_csv_calls == []
    assert report_service.product_breakdown_xlsx_calls == []
    assert check_in_service.check_in_audit_csv_calls == []
    assert check_in_service.check_in_audit_xlsx_calls == []
    assert check_in_service.check_in_failure_audit_csv_calls == []
    assert check_in_service.check_in_failure_audit_xlsx_calls == []
    assert refund_service.refund_audit_csv_calls == []
    assert refund_service.refund_audit_xlsx_calls == []


def test_export_job_worker_generates_product_breakdown_xlsx_and_marks_job_succeeded():
    export_repo = FakeAdminExportJobRepository()
    export_repo.jobs = {
        "product-breakdown-xlsx-job": export_job_record(
            job_id="product-breakdown-xlsx-job",
            export_type="PRODUCT_BREAKDOWN",
            file_format="XLSX",
            filters={
                "dateFrom": "2026-07-01",
                "dateTo": "2026-07-31",
            },
        )
    }
    report_service = FakeAdminReportService()
    check_in_service = FakeAdminCheckInService()
    refund_service = FakeAdminRefundService()
    storage = FakeAdminExportFileStorage()
    worker_service = AdminExportJobWorkerService(
        AdminExportJobService(export_repo, FakeAuthRepository()),
        report_service,
        check_in_service,
        refund_service,
        storage,
    )

    result = worker_service.process_next_pending_job()

    assert result is not None
    assert result.job_id == "product-breakdown-xlsx-job"
    assert result.status == "SUCCEEDED"
    assert result.file_name == "admin-product-breakdown-20260701-20260731.xlsx"
    assert result.error_code is None
    assert "storageKey" not in result.model_dump(by_alias=True)
    storage_key = export_repo.succeeded_storage_keys["product-breakdown-xlsx-job"]
    assert storage_key == (
        "export-jobs/product-breakdown-xlsx-job/"
        "admin-product-breakdown-20260701-20260731.xlsx"
    )
    assert storage.files[storage_key] == b"PK\x03\x04fake-product-breakdown-xlsx"
    assert report_service.order_detail_csv_calls == []
    assert report_service.order_detail_xlsx_calls == []
    assert report_service.product_breakdown_csv_calls == []
    assert report_service.product_breakdown_xlsx_calls == [(date(2026, 7, 1), date(2026, 7, 31))]
    assert check_in_service.check_in_audit_csv_calls == []
    assert check_in_service.check_in_audit_xlsx_calls == []
    assert check_in_service.check_in_failure_audit_csv_calls == []
    assert check_in_service.check_in_failure_audit_xlsx_calls == []
    assert refund_service.refund_audit_csv_calls == []
    assert refund_service.refund_audit_xlsx_calls == []


def test_export_job_worker_generates_daily_trend_csv_and_marks_job_succeeded():
    export_repo = FakeAdminExportJobRepository()
    export_repo.jobs = {
        "daily-trend-csv-job": export_job_record(
            job_id="daily-trend-csv-job",
            export_type="DAILY_TREND",
            file_format="CSV",
            filters={
                "dateFrom": "2026-07-01",
                "dateTo": "2026-07-31",
                "includeEmpty": True,
            },
        )
    }
    report_service = FakeAdminReportService()
    check_in_service = FakeAdminCheckInService()
    refund_service = FakeAdminRefundService()
    storage = FakeAdminExportFileStorage()
    worker_service = AdminExportJobWorkerService(
        AdminExportJobService(export_repo, FakeAuthRepository()),
        report_service,
        check_in_service,
        refund_service,
        storage,
    )

    result = worker_service.process_next_pending_job()

    assert result is not None
    assert result.job_id == "daily-trend-csv-job"
    assert result.status == "SUCCEEDED"
    assert result.file_name == "admin-daily-trend-20260701-20260731.csv"
    assert result.error_code is None
    assert "storageKey" not in result.model_dump(by_alias=True)
    storage_key = export_repo.succeeded_storage_keys["daily-trend-csv-job"]
    assert storage_key == (
        "export-jobs/daily-trend-csv-job/"
        "admin-daily-trend-20260701-20260731.csv"
    )
    assert storage.files[storage_key] == (
        "\ufeffreportDate,orderCount\n2026-07-01,2\n".encode("utf-8")
    )
    assert report_service.order_detail_csv_calls == []
    assert report_service.order_detail_xlsx_calls == []
    assert report_service.product_breakdown_csv_calls == []
    assert report_service.product_breakdown_xlsx_calls == []
    assert report_service.daily_trend_csv_calls == [(date(2026, 7, 1), date(2026, 7, 31), True)]
    assert report_service.daily_trend_xlsx_calls == []
    assert report_service.hourly_trend_csv_calls == []
    assert report_service.hourly_trend_xlsx_calls == []
    assert report_service.monthly_trend_csv_calls == []
    assert report_service.monthly_trend_xlsx_calls == []
    assert check_in_service.check_in_audit_csv_calls == []
    assert check_in_service.check_in_audit_xlsx_calls == []
    assert check_in_service.check_in_failure_audit_csv_calls == []
    assert check_in_service.check_in_failure_audit_xlsx_calls == []
    assert refund_service.refund_audit_csv_calls == []
    assert refund_service.refund_audit_xlsx_calls == []


def test_export_job_worker_generates_daily_trend_xlsx_and_marks_job_succeeded():
    export_repo = FakeAdminExportJobRepository()
    export_repo.jobs = {
        "daily-trend-xlsx-job": export_job_record(
            job_id="daily-trend-xlsx-job",
            export_type="DAILY_TREND",
            file_format="XLSX",
            filters={
                "dateFrom": "2026-07-01",
                "dateTo": "2026-07-31",
                "includeEmpty": True,
            },
        )
    }
    report_service = FakeAdminReportService()
    check_in_service = FakeAdminCheckInService()
    refund_service = FakeAdminRefundService()
    storage = FakeAdminExportFileStorage()
    worker_service = AdminExportJobWorkerService(
        AdminExportJobService(export_repo, FakeAuthRepository()),
        report_service,
        check_in_service,
        refund_service,
        storage,
    )

    result = worker_service.process_next_pending_job()

    assert result is not None
    assert result.job_id == "daily-trend-xlsx-job"
    assert result.status == "SUCCEEDED"
    assert result.file_name == "admin-daily-trend-20260701-20260731.xlsx"
    assert result.error_code is None
    assert "storageKey" not in result.model_dump(by_alias=True)
    storage_key = export_repo.succeeded_storage_keys["daily-trend-xlsx-job"]
    assert storage_key == (
        "export-jobs/daily-trend-xlsx-job/"
        "admin-daily-trend-20260701-20260731.xlsx"
    )
    assert storage.files[storage_key] == b"PK\x03\x04fake-daily-trend-xlsx"
    assert report_service.order_detail_csv_calls == []
    assert report_service.order_detail_xlsx_calls == []
    assert report_service.product_breakdown_csv_calls == []
    assert report_service.product_breakdown_xlsx_calls == []
    assert report_service.daily_trend_csv_calls == []
    assert report_service.daily_trend_xlsx_calls == [(date(2026, 7, 1), date(2026, 7, 31), True)]
    assert report_service.hourly_trend_csv_calls == []
    assert report_service.hourly_trend_xlsx_calls == []
    assert check_in_service.check_in_audit_csv_calls == []
    assert check_in_service.check_in_audit_xlsx_calls == []
    assert check_in_service.check_in_failure_audit_csv_calls == []
    assert check_in_service.check_in_failure_audit_xlsx_calls == []
    assert refund_service.refund_audit_csv_calls == []
    assert refund_service.refund_audit_xlsx_calls == []


def test_export_job_worker_generates_hourly_trend_csv_and_marks_job_succeeded():
    export_repo = FakeAdminExportJobRepository()
    export_repo.jobs = {
        "hourly-trend-csv-job": export_job_record(
            job_id="hourly-trend-csv-job",
            export_type="HOURLY_TREND",
            file_format="CSV",
            filters={
                "dateFrom": "2026-07-01",
                "dateTo": "2026-07-03",
                "includeEmpty": True,
            },
        )
    }
    report_service = FakeAdminReportService()
    check_in_service = FakeAdminCheckInService()
    refund_service = FakeAdminRefundService()
    storage = FakeAdminExportFileStorage()
    worker_service = AdminExportJobWorkerService(
        AdminExportJobService(export_repo, FakeAuthRepository()),
        report_service,
        check_in_service,
        refund_service,
        storage,
    )

    result = worker_service.process_next_pending_job()

    assert result is not None
    assert result.job_id == "hourly-trend-csv-job"
    assert result.status == "SUCCEEDED"
    assert result.file_name == "admin-hourly-trend-20260701-20260703.csv"
    assert result.error_code is None
    assert "storageKey" not in result.model_dump(by_alias=True)
    storage_key = export_repo.succeeded_storage_keys["hourly-trend-csv-job"]
    assert storage_key == (
        "export-jobs/hourly-trend-csv-job/"
        "admin-hourly-trend-20260701-20260703.csv"
    )
    assert storage.files[storage_key] == (
        "\ufeffreportHour,orderCount\n2026-07-01T08:00:00,2\n".encode("utf-8")
    )
    assert report_service.order_detail_csv_calls == []
    assert report_service.order_detail_xlsx_calls == []
    assert report_service.product_breakdown_csv_calls == []
    assert report_service.product_breakdown_xlsx_calls == []
    assert report_service.daily_trend_csv_calls == []
    assert report_service.daily_trend_xlsx_calls == []
    assert report_service.hourly_trend_csv_calls == [(date(2026, 7, 1), date(2026, 7, 3), True)]
    assert report_service.hourly_trend_xlsx_calls == []
    assert report_service.monthly_trend_csv_calls == []
    assert check_in_service.check_in_audit_csv_calls == []
    assert check_in_service.check_in_audit_xlsx_calls == []
    assert check_in_service.check_in_failure_audit_csv_calls == []
    assert check_in_service.check_in_failure_audit_xlsx_calls == []
    assert refund_service.refund_audit_csv_calls == []
    assert refund_service.refund_audit_xlsx_calls == []


def test_export_job_worker_generates_hourly_trend_xlsx_and_marks_job_succeeded():
    export_repo = FakeAdminExportJobRepository()
    export_repo.jobs = {
        "hourly-trend-xlsx-job": export_job_record(
            job_id="hourly-trend-xlsx-job",
            export_type="HOURLY_TREND",
            file_format="XLSX",
            filters={
                "dateFrom": "2026-07-01",
                "dateTo": "2026-07-03",
                "includeEmpty": True,
            },
        )
    }
    report_service = FakeAdminReportService()
    check_in_service = FakeAdminCheckInService()
    refund_service = FakeAdminRefundService()
    storage = FakeAdminExportFileStorage()
    worker_service = AdminExportJobWorkerService(
        AdminExportJobService(export_repo, FakeAuthRepository()),
        report_service,
        check_in_service,
        refund_service,
        storage,
    )

    result = worker_service.process_next_pending_job()

    assert result is not None
    assert result.job_id == "hourly-trend-xlsx-job"
    assert result.status == "SUCCEEDED"
    assert result.file_name == "admin-hourly-trend-20260701-20260703.xlsx"
    assert result.error_code is None
    assert "storageKey" not in result.model_dump(by_alias=True)
    storage_key = export_repo.succeeded_storage_keys["hourly-trend-xlsx-job"]
    assert storage_key == (
        "export-jobs/hourly-trend-xlsx-job/"
        "admin-hourly-trend-20260701-20260703.xlsx"
    )
    assert storage.files[storage_key] == b"PK\x03\x04fake-hourly-trend-xlsx"
    assert report_service.order_detail_csv_calls == []
    assert report_service.order_detail_xlsx_calls == []
    assert report_service.product_breakdown_csv_calls == []
    assert report_service.product_breakdown_xlsx_calls == []
    assert report_service.daily_trend_csv_calls == []
    assert report_service.daily_trend_xlsx_calls == []
    assert report_service.hourly_trend_csv_calls == []
    assert report_service.hourly_trend_xlsx_calls == [(date(2026, 7, 1), date(2026, 7, 3), True)]
    assert report_service.monthly_trend_csv_calls == []
    assert check_in_service.check_in_audit_csv_calls == []
    assert check_in_service.check_in_audit_xlsx_calls == []
    assert check_in_service.check_in_failure_audit_csv_calls == []
    assert check_in_service.check_in_failure_audit_xlsx_calls == []
    assert refund_service.refund_audit_csv_calls == []
    assert refund_service.refund_audit_xlsx_calls == []


def test_export_job_worker_generates_monthly_trend_csv_and_marks_job_succeeded():
    export_repo = FakeAdminExportJobRepository()
    export_repo.jobs = {
        "monthly-trend-csv-job": export_job_record(
            job_id="monthly-trend-csv-job",
            export_type="MONTHLY_TREND",
            file_format="CSV",
            filters={
                "dateFrom": "2026-07-01",
                "dateTo": "2026-09-30",
                "includeEmpty": True,
            },
        )
    }
    report_service = FakeAdminReportService()
    check_in_service = FakeAdminCheckInService()
    refund_service = FakeAdminRefundService()
    storage = FakeAdminExportFileStorage()
    worker_service = AdminExportJobWorkerService(
        AdminExportJobService(export_repo, FakeAuthRepository()),
        report_service,
        check_in_service,
        refund_service,
        storage,
    )

    result = worker_service.process_next_pending_job()

    assert result is not None
    assert result.job_id == "monthly-trend-csv-job"
    assert result.status == "SUCCEEDED"
    assert result.file_name == "admin-monthly-trend-20260701-20260930.csv"
    assert result.error_code is None
    assert "storageKey" not in result.model_dump(by_alias=True)
    storage_key = export_repo.succeeded_storage_keys["monthly-trend-csv-job"]
    assert storage_key == (
        "export-jobs/monthly-trend-csv-job/"
        "admin-monthly-trend-20260701-20260930.csv"
    )
    assert storage.files[storage_key] == (
        "\ufeffreportMonth,orderCount\n2026-07,2\n".encode("utf-8")
    )
    assert report_service.order_detail_csv_calls == []
    assert report_service.order_detail_xlsx_calls == []
    assert report_service.product_breakdown_csv_calls == []
    assert report_service.product_breakdown_xlsx_calls == []
    assert report_service.daily_trend_csv_calls == []
    assert report_service.daily_trend_xlsx_calls == []
    assert report_service.hourly_trend_csv_calls == []
    assert report_service.hourly_trend_xlsx_calls == []
    assert report_service.monthly_trend_csv_calls == [(date(2026, 7, 1), date(2026, 9, 30), True)]
    assert report_service.monthly_trend_xlsx_calls == []
    assert check_in_service.check_in_audit_csv_calls == []
    assert check_in_service.check_in_audit_xlsx_calls == []
    assert check_in_service.check_in_failure_audit_csv_calls == []
    assert check_in_service.check_in_failure_audit_xlsx_calls == []
    assert refund_service.refund_audit_csv_calls == []
    assert refund_service.refund_audit_xlsx_calls == []


def test_export_job_worker_generates_monthly_trend_xlsx_and_marks_job_succeeded():
    export_repo = FakeAdminExportJobRepository()
    export_repo.jobs = {
        "monthly-trend-xlsx-job": export_job_record(
            job_id="monthly-trend-xlsx-job",
            export_type="MONTHLY_TREND",
            file_format="XLSX",
            filters={
                "dateFrom": "2026-07-01",
                "dateTo": "2026-09-30",
                "includeEmpty": True,
            },
        )
    }
    report_service = FakeAdminReportService()
    check_in_service = FakeAdminCheckInService()
    refund_service = FakeAdminRefundService()
    storage = FakeAdminExportFileStorage()
    worker_service = AdminExportJobWorkerService(
        AdminExportJobService(export_repo, FakeAuthRepository()),
        report_service,
        check_in_service,
        refund_service,
        storage,
    )

    result = worker_service.process_next_pending_job()

    assert result is not None
    assert result.job_id == "monthly-trend-xlsx-job"
    assert result.status == "SUCCEEDED"
    assert result.file_name == "admin-monthly-trend-20260701-20260930.xlsx"
    assert result.error_code is None
    assert "storageKey" not in result.model_dump(by_alias=True)
    storage_key = export_repo.succeeded_storage_keys["monthly-trend-xlsx-job"]
    assert storage_key == (
        "export-jobs/monthly-trend-xlsx-job/"
        "admin-monthly-trend-20260701-20260930.xlsx"
    )
    assert storage.files[storage_key] == b"PK\x03\x04fake-monthly-trend-xlsx"
    assert report_service.order_detail_csv_calls == []
    assert report_service.order_detail_xlsx_calls == []
    assert report_service.product_breakdown_csv_calls == []
    assert report_service.product_breakdown_xlsx_calls == []
    assert report_service.daily_trend_csv_calls == []
    assert report_service.daily_trend_xlsx_calls == []
    assert report_service.hourly_trend_csv_calls == []
    assert report_service.hourly_trend_xlsx_calls == []
    assert report_service.monthly_trend_csv_calls == []
    assert report_service.monthly_trend_xlsx_calls == [(date(2026, 7, 1), date(2026, 9, 30), True)]
    assert check_in_service.check_in_audit_csv_calls == []
    assert check_in_service.check_in_audit_xlsx_calls == []
    assert check_in_service.check_in_failure_audit_csv_calls == []
    assert check_in_service.check_in_failure_audit_xlsx_calls == []
    assert refund_service.refund_audit_csv_calls == []
    assert refund_service.refund_audit_xlsx_calls == []


def test_export_job_worker_marks_unsupported_jobs_failed():
    export_repo = FakeAdminExportJobRepository()
    export_repo.jobs = {
        "unsupported-job": export_job_record(
            job_id="unsupported-job",
            export_type="UNKNOWN_EXPORT",
            file_format="CSV",
        )
    }
    report_service = FakeAdminReportService()
    check_in_service = FakeAdminCheckInService()
    refund_service = FakeAdminRefundService()
    storage = FakeAdminExportFileStorage()
    worker_service = AdminExportJobWorkerService(
        AdminExportJobService(export_repo, FakeAuthRepository()),
        report_service,
        check_in_service,
        refund_service,
        storage,
    )

    result = worker_service.process_next_pending_job()

    assert result is not None
    assert result.job_id == "unsupported-job"
    assert result.status == "FAILED"
    assert result.error_code == "ADMIN_EXPORT_JOB_UNSUPPORTED"
    assert result.error_message == "暂不支持该异步导出类型或格式"
    assert export_repo.retry_counts.get("unsupported-job", 0) == 0
    assert len(export_repo.alert_events) == 1
    alert_event = export_repo.alert_events[0]
    assert alert_event.job_id == "unsupported-job"
    assert alert_event.export_type == "UNKNOWN_EXPORT"
    assert alert_event.file_format == "CSV"
    assert alert_event.error_code == "ADMIN_EXPORT_JOB_UNSUPPORTED"
    assert alert_event.error_message == "暂不支持该异步导出类型或格式"
    assert alert_event.alert_source == "WORKER_FINAL_FAILURE"
    assert "dateFrom" not in repr(alert_event)
    assert "storage_key" not in repr(alert_event)
    assert report_service.order_detail_csv_calls == []
    assert report_service.order_detail_xlsx_calls == []
    assert report_service.payment_reconciliation_csv_calls == []
    assert report_service.payment_reconciliation_xlsx_calls == []
    assert report_service.product_breakdown_csv_calls == []
    assert report_service.product_breakdown_xlsx_calls == []
    assert report_service.daily_trend_csv_calls == []
    assert report_service.daily_trend_xlsx_calls == []
    assert report_service.hourly_trend_csv_calls == []
    assert report_service.hourly_trend_xlsx_calls == []
    assert report_service.monthly_trend_csv_calls == []
    assert report_service.monthly_trend_xlsx_calls == []
    assert check_in_service.check_in_audit_csv_calls == []
    assert check_in_service.check_in_audit_xlsx_calls == []
    assert check_in_service.check_in_failure_audit_csv_calls == []
    assert check_in_service.check_in_failure_audit_xlsx_calls == []
    assert refund_service.refund_audit_csv_calls == []
    assert refund_service.refund_audit_xlsx_calls == []
    assert storage.files == {}


def test_export_job_worker_generates_payment_reconciliation_xlsx_and_marks_job_succeeded():
    export_repo = FakeAdminExportJobRepository()
    export_repo.jobs = {
        "payment-reconciliation-xlsx-job": export_job_record(
            job_id="payment-reconciliation-xlsx-job",
            export_type="PAYMENT_RECONCILIATION",
            file_format="XLSX",
            filters={
                "dateFrom": "2026-07-01",
                "dateTo": "2026-07-31",
            },
        )
    }
    report_service = FakeAdminReportService()
    check_in_service = FakeAdminCheckInService()
    refund_service = FakeAdminRefundService()
    storage = FakeAdminExportFileStorage()
    worker_service = AdminExportJobWorkerService(
        AdminExportJobService(export_repo, FakeAuthRepository()),
        report_service,
        check_in_service,
        refund_service,
        storage,
    )

    result = worker_service.process_next_pending_job()

    assert result is not None
    assert result.job_id == "payment-reconciliation-xlsx-job"
    assert result.status == "SUCCEEDED"
    assert result.file_name == "admin-payment-reconciliation-20260701-20260731.xlsx"
    assert result.error_code is None
    assert "storageKey" not in result.model_dump(by_alias=True)
    storage_key = export_repo.succeeded_storage_keys["payment-reconciliation-xlsx-job"]
    assert storage_key == (
        "export-jobs/payment-reconciliation-xlsx-job/"
        "admin-payment-reconciliation-20260701-20260731.xlsx"
    )
    assert storage.files[storage_key] == b"PK\x03\x04fake-payment-reconciliation-xlsx"
    assert report_service.payment_reconciliation_csv_calls == []
    assert report_service.payment_reconciliation_xlsx_calls == [(date(2026, 7, 1), date(2026, 7, 31))]
    assert report_service.product_breakdown_csv_calls == []
    assert report_service.product_breakdown_xlsx_calls == []
    assert check_in_service.check_in_audit_csv_calls == []
    assert check_in_service.check_in_audit_xlsx_calls == []
    assert check_in_service.check_in_failure_audit_csv_calls == []
    assert check_in_service.check_in_failure_audit_xlsx_calls == []
    assert refund_service.refund_audit_csv_calls == []
    assert refund_service.refund_audit_xlsx_calls == []


def assert_daily_trend_csv_invalid_filters_fail(filters: dict[str, Any]) -> None:
    export_repo = FakeAdminExportJobRepository()
    export_repo.jobs = {
        "daily-trend-csv-job": export_job_record(
            job_id="daily-trend-csv-job",
            export_type="DAILY_TREND",
            file_format="CSV",
            filters=filters,
        )
    }
    report_service = FakeAdminReportService()
    check_in_service = FakeAdminCheckInService()
    refund_service = FakeAdminRefundService()
    storage = FakeAdminExportFileStorage()
    worker_service = AdminExportJobWorkerService(
        AdminExportJobService(export_repo, FakeAuthRepository()),
        report_service,
        check_in_service,
        refund_service,
        storage,
    )

    result = worker_service.process_next_pending_job()

    assert result is not None
    assert result.job_id == "daily-trend-csv-job"
    assert result.status == "FAILED"
    assert result.error_code == "ADMIN_EXPORT_JOB_FILTERS_INVALID"
    assert result.error_message == "导出任务筛选条件不合法"
    assert report_service.order_detail_csv_calls == []
    assert report_service.order_detail_xlsx_calls == []
    assert report_service.product_breakdown_csv_calls == []
    assert report_service.product_breakdown_xlsx_calls == []
    assert report_service.daily_trend_csv_calls == []
    assert report_service.daily_trend_xlsx_calls == []
    assert report_service.hourly_trend_csv_calls == []
    assert report_service.hourly_trend_xlsx_calls == []
    assert report_service.monthly_trend_csv_calls == []
    assert check_in_service.check_in_audit_csv_calls == []
    assert check_in_service.check_in_audit_xlsx_calls == []
    assert check_in_service.check_in_failure_audit_csv_calls == []
    assert check_in_service.check_in_failure_audit_xlsx_calls == []
    assert refund_service.refund_audit_csv_calls == []
    assert refund_service.refund_audit_xlsx_calls == []
    assert storage.files == {}


def test_export_job_worker_marks_daily_trend_csv_non_normalized_date_filter_failed():
    assert_daily_trend_csv_invalid_filters_fail(
        {
            "dateFrom": "20260701",
            "dateTo": "2026-07-31",
            "includeEmpty": True,
        }
    )


def test_export_job_worker_marks_daily_trend_csv_non_bool_include_empty_filter_failed():
    assert_daily_trend_csv_invalid_filters_fail(
        {
            "dateFrom": "2026-07-01",
            "dateTo": "2026-07-31",
            "includeEmpty": "true",
        }
    )


def test_export_job_worker_marks_refund_audit_csv_invalid_filters_failed():
    export_repo = FakeAdminExportJobRepository()
    export_repo.jobs = {
        "refund-audit-csv-job": export_job_record(
            job_id="refund-audit-csv-job",
            export_type="REFUND_AUDIT",
            file_format="CSV",
            filters={"dateFrom": "not-a-date"},
        )
    }
    report_service = FakeAdminReportService()
    check_in_service = FakeAdminCheckInService()
    refund_service = FakeAdminRefundService()
    storage = FakeAdminExportFileStorage()
    worker_service = AdminExportJobWorkerService(
        AdminExportJobService(export_repo, FakeAuthRepository()),
        report_service,
        check_in_service,
        refund_service,
        storage,
    )

    result = worker_service.process_next_pending_job()

    assert result is not None
    assert result.job_id == "refund-audit-csv-job"
    assert result.status == "FAILED"
    assert result.error_code == "ADMIN_EXPORT_JOB_FILTERS_INVALID"
    assert result.error_message == "导出任务筛选条件不合法"
    assert report_service.order_detail_csv_calls == []
    assert report_service.order_detail_xlsx_calls == []
    assert check_in_service.check_in_audit_csv_calls == []
    assert check_in_service.check_in_audit_xlsx_calls == []
    assert check_in_service.check_in_failure_audit_csv_calls == []
    assert check_in_service.check_in_failure_audit_xlsx_calls == []
    assert refund_service.refund_audit_csv_calls == []
    assert refund_service.refund_audit_xlsx_calls == []
    assert storage.files == {}


def test_export_job_worker_returns_none_when_no_pending_job():
    export_repo = FakeAdminExportJobRepository()
    export_repo.jobs = {
        "running": export_job_record(job_id="running", status="RUNNING", started_at=STARTED_AT)
    }
    worker_service = AdminExportJobWorkerService(
        AdminExportJobService(export_repo, FakeAuthRepository()),
        FakeAdminReportService(),
        FakeAdminCheckInService(),
        FakeAdminRefundService(),
        FakeAdminExportFileStorage(),
    )

    assert worker_service.process_next_pending_job() is None


def test_admin_can_list_and_get_export_jobs_without_csrf_header():
    auth_repo = FakeAuthRepository()
    export_repo = FakeAdminExportJobRepository()
    export_repo.jobs["22222222-2222-4222-8222-222222222222"] = export_job_record(
        job_id="22222222-2222-4222-8222-222222222222",
        export_type="DAILY_TREND",
        file_format="XLSX",
        status="RUNNING",
    )
    client = build_client(auth_repo, export_repo)
    login_admin(client, auth_repo)

    list_response = client.get(
        "/api/admin/export-jobs",
        params={
            "exportType": "daily_trend",
            "fileFormat": " xlsx ",
            "status": "running",
            "page": 2,
            "pageSize": 5,
        },
    )
    detail_response = client.get("/api/admin/export-jobs/22222222-2222-4222-8222-222222222222")

    assert list_response.status_code == 200
    assert list_response.json()["data"]["total"] == 1
    assert list_response.json()["data"]["items"][0]["exportType"] == "DAILY_TREND"
    assert export_repo.last_filters == AdminExportJobListFilter(
        export_type="DAILY_TREND",
        file_format="XLSX",
        status="RUNNING",
        page=2,
        page_size=5,
    )
    assert detail_response.status_code == 200
    assert detail_response.json()["data"]["fileFormat"] == "XLSX"


def test_admin_can_list_export_job_alert_events_without_csrf_header():
    auth_repo = FakeAuthRepository()
    export_repo = FakeAdminExportJobRepository()
    export_repo.alert_event_records = [
        AdminExportJobAlertEventRecord(
            event_id=1,
            job_id="alert-job-1",
            export_type="ORDER_DETAIL",
            file_format="CSV",
            error_code="ADMIN_EXPORT_JOB_WORKER_FAILED",
            error_message="导出任务处理失败",
            alert_source="WORKER_FINAL_FAILURE",
            created_at=FINISHED_AT,
            acknowledged_at=None,
            acknowledged_by_admin_user_id=None,
            acknowledged_by_username=None,
            acknowledged_by_display_name=None,
            acknowledge_note=None,
        ),
        AdminExportJobAlertEventRecord(
            event_id=2,
            job_id="alert-job-2",
            export_type="DAILY_TREND",
            file_format="XLSX",
            error_code="ADMIN_EXPORT_JOB_WORKER_TIMEOUT",
            error_message="导出任务处理超时",
            alert_source="WORKER_FINAL_FAILURE",
            created_at=REQUESTED_AT,
            acknowledged_at=FINISHED_AT,
            acknowledged_by_admin_user_id=1,
            acknowledged_by_username="admin",
            acknowledged_by_display_name="演示管理员",
            acknowledge_note="已重跑",
            closed_at=FINISHED_AT,
            closed_by_admin_user_id=1,
            closed_by_username="admin",
            closed_by_display_name="演示管理员",
            close_note="已处理",
        ),
    ]
    client = build_client(auth_repo, export_repo)
    login_admin(client, auth_repo)

    response = client.get(
        "/api/admin/export-job-alert-events",
        params={
            "jobId": " alert-job-1 ",
            "exportType": " order_detail ",
            "fileFormat": " csv ",
            "errorCode": " admin_export_job_worker_failed ",
            "acknowledged": "false",
            "closed": "false",
            "dateFrom": "2026-07-01",
            "dateTo": "2026-07-01",
            "page": 2,
            "pageSize": 5,
        },
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total"] == 1
    assert data["page"] == 2
    assert data["pageSize"] == 5
    assert data["items"] == [
        {
            "eventId": 1,
            "jobId": "alert-job-1",
            "exportType": "ORDER_DETAIL",
            "fileFormat": "CSV",
            "errorCode": "ADMIN_EXPORT_JOB_WORKER_FAILED",
            "errorMessage": "导出任务处理失败",
            "alertSource": "WORKER_FINAL_FAILURE",
            "createdAt": FINISHED_AT.isoformat().replace("+00:00", "Z"),
            "occurrenceCount": 1,
            "lastSeenAt": FINISHED_AT.isoformat().replace("+00:00", "Z"),
        }
    ]
    assert export_repo.last_alert_event_filters == AdminExportJobAlertEventListFilter(
        job_id="alert-job-1",
        export_type="ORDER_DETAIL",
        file_format="CSV",
        error_code="ADMIN_EXPORT_JOB_WORKER_FAILED",
        acknowledged=False,
        closed=False,
        date_from=date(2026, 7, 1),
        date_to=date(2026, 7, 1),
        page=2,
        page_size=5,
    )
    assert "filters" not in response.text
    assert "storageKey" not in response.text
    assert "storage_key" not in response.text
    assert "adminUserId" not in response.text
    assert "closedByAdminUserId" not in response.text


def test_export_job_alert_event_list_rejects_invalid_filters():
    auth_repo = FakeAuthRepository()
    export_repo = FakeAdminExportJobRepository()
    client = build_client(auth_repo, export_repo)
    login_admin(client, auth_repo)

    bad_acknowledged_response = client.get(
        "/api/admin/export-job-alert-events",
        params={"acknowledged": "maybe"},
    )
    bad_closed_response = client.get(
        "/api/admin/export-job-alert-events",
        params={"closed": "maybe"},
    )
    bad_date_response = client.get(
        "/api/admin/export-job-alert-events",
        params={"dateFrom": "2026/07/01"},
    )
    bad_export_type_response = client.get(
        "/api/admin/export-job-alert-events",
        params={"exportType": "unknown"},
    )
    bad_file_format_response = client.get(
        "/api/admin/export-job-alert-events",
        params={"fileFormat": "pdf"},
    )
    reversed_date_response = client.get(
        "/api/admin/export-job-alert-events",
        params={"dateFrom": "2026-07-02", "dateTo": "2026-07-01"},
    )

    assert bad_acknowledged_response.status_code == 422
    assert bad_acknowledged_response.json()["code"] == "ADMIN_EXPORT_JOB_ALERT_EVENT_FILTER_INVALID"
    assert bad_closed_response.status_code == 422
    assert bad_closed_response.json()["code"] == "ADMIN_EXPORT_JOB_ALERT_EVENT_FILTER_INVALID"
    assert bad_date_response.status_code == 422
    assert bad_date_response.json()["code"] == "ADMIN_EXPORT_JOB_ALERT_EVENT_FILTER_INVALID"
    assert bad_export_type_response.status_code == 422
    assert bad_export_type_response.json()["code"] == "ADMIN_EXPORT_JOB_ALERT_EVENT_FILTER_INVALID"
    assert bad_file_format_response.status_code == 422
    assert bad_file_format_response.json()["code"] == "ADMIN_EXPORT_JOB_ALERT_EVENT_FILTER_INVALID"
    assert reversed_date_response.status_code == 422
    assert reversed_date_response.json()["code"] == "ADMIN_EXPORT_JOB_ALERT_EVENT_FILTER_INVALID"


def test_admin_can_summarize_export_job_alert_events_without_csrf_header():
    auth_repo = FakeAuthRepository()
    export_repo = FakeAdminExportJobRepository()
    export_repo.alert_event_records = [
        AdminExportJobAlertEventRecord(
            event_id=1,
            job_id="alert-job-1",
            export_type="ORDER_DETAIL",
            file_format="CSV",
            error_code="ADMIN_EXPORT_JOB_WORKER_FAILED",
            error_message="导出任务处理失败",
            alert_source="WORKER_FINAL_FAILURE",
            created_at=REQUESTED_AT,
            acknowledged_at=None,
            acknowledged_by_admin_user_id=None,
            acknowledged_by_username=None,
            acknowledged_by_display_name=None,
            acknowledge_note=None,
        ),
        AdminExportJobAlertEventRecord(
            event_id=2,
            job_id="alert-job-2",
            export_type="DAILY_TREND",
            file_format="XLSX",
            error_code="ADMIN_EXPORT_JOB_WORKER_FAILED",
            error_message="导出任务处理失败",
            alert_source="WORKER_FINAL_FAILURE",
            created_at=FINISHED_AT,
            acknowledged_at=FINISHED_AT,
            acknowledged_by_admin_user_id=1,
            acknowledged_by_username="admin",
            acknowledged_by_display_name="演示管理员",
            acknowledge_note="已重跑",
            closed_at=FINISHED_AT,
            closed_by_admin_user_id=1,
            closed_by_username="admin",
            closed_by_display_name="演示管理员",
            close_note="已处理",
        ),
        AdminExportJobAlertEventRecord(
            event_id=3,
            job_id="alert-job-3",
            export_type="ORDER_DETAIL",
            file_format="CSV",
            error_code="ADMIN_EXPORT_JOB_WORKER_TIMEOUT",
            error_message="导出任务处理超时",
            alert_source="WORKER_FINAL_FAILURE",
            created_at=datetime(2026, 6, 30, 9, 0, tzinfo=UTC),
            acknowledged_at=None,
            acknowledged_by_admin_user_id=None,
            acknowledged_by_username=None,
            acknowledged_by_display_name=None,
            acknowledge_note=None,
        ),
    ]
    client = build_client(auth_repo, export_repo)
    login_admin(client, auth_repo)

    response = client.get(
        "/api/admin/export-job-alert-events/summary",
        params={
            "exportType": " order_detail ",
            "fileFormat": " csv ",
            "closed": "false",
            "dateFrom": "2026-07-01",
            "dateTo": "2026-07-01",
        },
    )

    assert response.status_code == 200
    assert response.json()["data"] == {
        "total": 1,
        "acknowledged": 0,
        "unacknowledged": 1,
        "closed": 0,
        "open": 1,
        "byErrorCode": [
            {
                "errorCode": "ADMIN_EXPORT_JOB_WORKER_FAILED",
                "total": 1,
                "acknowledged": 0,
                "unacknowledged": 1,
                "closed": 0,
                "open": 1,
            }
        ],
    }
    assert export_repo.last_alert_event_summary_filters == AdminExportJobAlertEventSummaryFilter(
        export_type="ORDER_DETAIL",
        file_format="CSV",
        closed=False,
        date_from=date(2026, 7, 1),
        date_to=date(2026, 7, 1),
    )
    assert "filters" not in response.text
    assert "storageKey" not in response.text
    assert "storage_key" not in response.text


def test_export_job_alert_event_summary_rejects_invalid_filters_and_requires_admin():
    auth_repo = FakeAuthRepository()
    export_repo = FakeAdminExportJobRepository()
    client = build_client(auth_repo, export_repo)

    anonymous_response = client.get(
        "/api/admin/export-job-alert-events/summary",
        params={"dateFrom": "2026-07-01"},
    )
    login_visitor(client)
    visitor_response = client.get(
        "/api/admin/export-job-alert-events/summary",
        params={"dateFrom": "2026-07-01"},
    )
    auth_repo = FakeAuthRepository()
    export_repo = FakeAdminExportJobRepository()
    client = build_client(auth_repo, export_repo)
    login_admin(client, auth_repo)
    bad_date_response = client.get(
        "/api/admin/export-job-alert-events/summary",
        params={"dateFrom": "2026/07/01"},
    )
    bad_closed_response = client.get(
        "/api/admin/export-job-alert-events/summary",
        params={"closed": "maybe"},
    )
    bad_export_type_response = client.get(
        "/api/admin/export-job-alert-events/summary",
        params={"exportType": "unknown"},
    )
    bad_file_format_response = client.get(
        "/api/admin/export-job-alert-events/summary",
        params={"fileFormat": "pdf"},
    )
    reversed_date_response = client.get(
        "/api/admin/export-job-alert-events/summary",
        params={"dateFrom": "2026-07-02", "dateTo": "2026-07-01"},
    )

    assert anonymous_response.status_code == 401
    assert anonymous_response.json()["code"] == "ADMIN_AUTH_REQUIRED"
    assert visitor_response.status_code == 403
    assert visitor_response.json()["code"] == "ADMIN_FORBIDDEN"
    assert bad_date_response.status_code == 422
    assert bad_date_response.json()["code"] == "ADMIN_EXPORT_JOB_ALERT_EVENT_FILTER_INVALID"
    assert bad_closed_response.status_code == 422
    assert bad_closed_response.json()["code"] == "ADMIN_EXPORT_JOB_ALERT_EVENT_FILTER_INVALID"
    assert bad_export_type_response.status_code == 422
    assert bad_export_type_response.json()["code"] == "ADMIN_EXPORT_JOB_ALERT_EVENT_FILTER_INVALID"
    assert bad_file_format_response.status_code == 422
    assert bad_file_format_response.json()["code"] == "ADMIN_EXPORT_JOB_ALERT_EVENT_FILTER_INVALID"
    assert reversed_date_response.status_code == 422
    assert reversed_date_response.json()["code"] == "ADMIN_EXPORT_JOB_ALERT_EVENT_FILTER_INVALID"


def test_admin_can_acknowledge_export_job_alert_event_with_csrf_header():
    auth_repo = FakeAuthRepository()
    export_repo = FakeAdminExportJobRepository()
    export_repo.alert_event_records = [
        AdminExportJobAlertEventRecord(
            event_id=7,
            job_id="alert-job-1",
            export_type="ORDER_DETAIL",
            file_format="CSV",
            error_code="ADMIN_EXPORT_JOB_WORKER_FAILED",
            error_message="导出任务处理失败",
            alert_source="WORKER_FINAL_FAILURE",
            created_at=REQUESTED_AT,
            acknowledged_at=None,
            acknowledged_by_admin_user_id=None,
            acknowledged_by_username=None,
            acknowledged_by_display_name=None,
            acknowledge_note=None,
        )
    ]
    client = build_client(auth_repo, export_repo)
    login_admin(client, auth_repo)

    response = client.post(
        "/api/admin/export-job-alert-events/7/acknowledge",
        json={"note": " 已人工重跑成功 "},
        headers=csrf_headers(client),
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data == {
        "eventId": 7,
        "jobId": "alert-job-1",
        "exportType": "ORDER_DETAIL",
        "fileFormat": "CSV",
        "errorCode": "ADMIN_EXPORT_JOB_WORKER_FAILED",
        "errorMessage": "导出任务处理失败",
        "alertSource": "WORKER_FINAL_FAILURE",
        "createdAt": REQUESTED_AT.isoformat().replace("+00:00", "Z"),
        "occurrenceCount": 1,
        "lastSeenAt": REQUESTED_AT.isoformat().replace("+00:00", "Z"),
        "acknowledgedAt": FINISHED_AT.isoformat().replace("+00:00", "Z"),
        "acknowledgedByUsername": "admin",
        "acknowledgedByDisplayName": "演示管理员",
        "acknowledgeNote": "已人工重跑成功",
    }
    assert export_repo.last_alert_event_acknowledge == AdminExportJobAlertEventAcknowledgeRecord(
        event_id=7,
        acknowledged_by_admin_user_id=1,
        acknowledged_by_username="admin",
        acknowledged_by_display_name="演示管理员",
        acknowledge_note="已人工重跑成功",
    )
    assert "filters" not in response.text
    assert "storageKey" not in response.text
    assert "storage_key" not in response.text


def test_export_job_alert_event_acknowledge_is_first_write_wins():
    auth_repo = FakeAuthRepository()
    export_repo = FakeAdminExportJobRepository()
    export_repo.alert_event_records = [
        AdminExportJobAlertEventRecord(
            event_id=8,
            job_id="alert-job-1",
            export_type="ORDER_DETAIL",
            file_format="CSV",
            error_code="ADMIN_EXPORT_JOB_WORKER_FAILED",
            error_message="导出任务处理失败",
            alert_source="WORKER_FINAL_FAILURE",
            created_at=REQUESTED_AT,
            acknowledged_at=FINISHED_AT,
            acknowledged_by_admin_user_id=1,
            acknowledged_by_username="admin",
            acknowledged_by_display_name="演示管理员",
            acknowledge_note="第一次处理",
        )
    ]
    client = build_client(auth_repo, export_repo)
    login_admin(client, auth_repo)

    response = client.post(
        "/api/admin/export-job-alert-events/8/acknowledge",
        json={"note": "第二次处理"},
        headers=csrf_headers(client),
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["acknowledgedAt"] == FINISHED_AT.isoformat().replace("+00:00", "Z")
    assert data["acknowledgedByUsername"] == "admin"
    assert data["acknowledgeNote"] == "第一次处理"


def test_admin_can_batch_acknowledge_export_job_alert_events_with_per_item_results():
    auth_repo = FakeAuthRepository()
    export_repo = FakeAdminExportJobRepository()
    export_repo.alert_event_records = [
        AdminExportJobAlertEventRecord(
            event_id=31,
            job_id="alert-job-open-1",
            export_type="ORDER_DETAIL",
            file_format="CSV",
            error_code="ADMIN_EXPORT_JOB_WORKER_FAILED",
            error_message="导出任务处理失败",
            alert_source="WORKER_FINAL_FAILURE",
            created_at=REQUESTED_AT,
            acknowledged_at=None,
            acknowledged_by_admin_user_id=None,
            acknowledged_by_username=None,
            acknowledged_by_display_name=None,
            acknowledge_note=None,
        ),
        AdminExportJobAlertEventRecord(
            event_id=32,
            job_id="alert-job-already-acknowledged",
            export_type="ORDER_DETAIL",
            file_format="XLSX",
            error_code="ADMIN_EXPORT_JOB_WORKER_TIMEOUT",
            error_message="导出任务处理超时",
            alert_source="WORKER_FINAL_FAILURE",
            created_at=REQUESTED_AT,
            acknowledged_at=FINISHED_AT,
            acknowledged_by_admin_user_id=1,
            acknowledged_by_username="admin",
            acknowledged_by_display_name="演示管理员",
            acknowledge_note="第一次处理",
        ),
    ]
    client = build_client(auth_repo, export_repo)
    login_admin(client, auth_repo)

    response = client.post(
        "/api/admin/export-job-alert-events/batch-acknowledge",
        json={"eventIds": [31, 32, 404], "note": " 已处理 "},
        headers=csrf_headers(client),
    )

    assert response.status_code == 200
    assert response.json()["data"] == {
        "totalCount": 3,
        "successCount": 2,
        "failureCount": 1,
        "results": [
            {"eventId": 31, "acknowledged": True},
            {"eventId": 32, "acknowledged": True},
            {
                "eventId": 404,
                "acknowledged": False,
                "code": "ADMIN_EXPORT_JOB_ALERT_EVENT_NOT_FOUND",
                "message": "导出任务告警事件不存在",
            },
        ],
    }
    assert export_repo.alert_event_records[0].acknowledged_at == FINISHED_AT
    assert export_repo.alert_event_records[0].acknowledged_by_username == "admin"
    assert export_repo.alert_event_records[0].acknowledge_note == "已处理"
    assert export_repo.alert_event_records[1].acknowledge_note == "第一次处理"
    assert "filters" not in response.text
    assert "storageKey" not in response.text
    assert "storage_key" not in response.text


def test_export_job_alert_event_batch_acknowledge_rejects_duplicate_empty_extra_and_bad_note():
    auth_repo = FakeAuthRepository()
    export_repo = FakeAdminExportJobRepository()
    client = build_client(auth_repo, export_repo)
    login_admin(client, auth_repo)

    duplicate_response = client.post(
        "/api/admin/export-job-alert-events/batch-acknowledge",
        json={"eventIds": [1, 1]},
        headers=csrf_headers(client),
    )
    empty_response = client.post(
        "/api/admin/export-job-alert-events/batch-acknowledge",
        json={"eventIds": []},
        headers=csrf_headers(client),
    )
    extra_response = client.post(
        "/api/admin/export-job-alert-events/batch-acknowledge",
        json={"eventIds": [1], "adminUserId": 1},
        headers=csrf_headers(client),
    )
    snake_case_response = client.post(
        "/api/admin/export-job-alert-events/batch-acknowledge",
        json={"event_ids": [1]},
        headers=csrf_headers(client),
    )
    non_positive_response = client.post(
        "/api/admin/export-job-alert-events/batch-acknowledge",
        json={"eventIds": [0]},
        headers=csrf_headers(client),
    )
    bad_note_response = client.post(
        "/api/admin/export-job-alert-events/batch-acknowledge",
        json={"eventIds": [1], "note": "x" * 201},
        headers=csrf_headers(client),
    )

    assert duplicate_response.status_code == 422
    assert empty_response.status_code == 422
    assert extra_response.status_code == 422
    assert snake_case_response.status_code == 422
    assert non_positive_response.status_code == 422
    assert bad_note_response.status_code == 422
    assert bad_note_response.json()["code"] == "ADMIN_EXPORT_JOB_ALERT_EVENT_ACK_INVALID"
    assert export_repo.alert_event_records == []


def test_admin_can_close_and_reopen_export_job_alert_event_with_csrf_header():
    auth_repo = FakeAuthRepository()
    export_repo = FakeAdminExportJobRepository()
    export_repo.alert_event_records = [
        AdminExportJobAlertEventRecord(
            event_id=11,
            job_id="alert-job-1",
            export_type="ORDER_DETAIL",
            file_format="CSV",
            error_code="ADMIN_EXPORT_JOB_WORKER_FAILED",
            error_message="导出任务处理失败",
            alert_source="WORKER_FINAL_FAILURE",
            created_at=REQUESTED_AT,
            acknowledged_at=None,
            acknowledged_by_admin_user_id=None,
            acknowledged_by_username=None,
            acknowledged_by_display_name=None,
            acknowledge_note=None,
        )
    ]
    client = build_client(auth_repo, export_repo)
    login_admin(client, auth_repo)

    close_response = client.post(
        "/api/admin/export-job-alert-events/11/close",
        json={"note": " 已确认无需继续展示 "},
        headers=csrf_headers(client),
    )
    reopen_response = client.post(
        "/api/admin/export-job-alert-events/11/reopen",
        headers=csrf_headers(client),
    )

    assert close_response.status_code == 200
    close_data = close_response.json()["data"]
    assert close_data["closedAt"] == FINISHED_AT.isoformat().replace("+00:00", "Z")
    assert close_data["closedByUsername"] == "admin"
    assert close_data["closedByDisplayName"] == "演示管理员"
    assert close_data["closeNote"] == "已确认无需继续展示"
    assert export_repo.last_alert_event_close == AdminExportJobAlertEventCloseRecord(
        event_id=11,
        closed_by_admin_user_id=1,
        closed_by_username="admin",
        closed_by_display_name="演示管理员",
        close_note="已确认无需继续展示",
    )
    assert "closedByAdminUserId" not in close_response.text
    assert "filters" not in close_response.text
    assert "storageKey" not in close_response.text
    assert "storage_key" not in close_response.text
    assert reopen_response.status_code == 200
    reopen_data = reopen_response.json()["data"]
    assert "closedAt" not in reopen_data
    assert "closedByUsername" not in reopen_data
    assert "closeNote" not in reopen_data
    assert export_repo.last_alert_event_reopen == 11


def test_admin_can_batch_close_export_job_alert_events_with_per_item_results():
    auth_repo = FakeAuthRepository()
    export_repo = FakeAdminExportJobRepository()
    export_repo.alert_event_records = [
        AdminExportJobAlertEventRecord(
            event_id=41,
            job_id="alert-job-open-1",
            export_type="ORDER_DETAIL",
            file_format="CSV",
            error_code="ADMIN_EXPORT_JOB_WORKER_FAILED",
            error_message="导出任务处理失败",
            alert_source="WORKER_FINAL_FAILURE",
            created_at=REQUESTED_AT,
            acknowledged_at=None,
            acknowledged_by_admin_user_id=None,
            acknowledged_by_username=None,
            acknowledged_by_display_name=None,
            acknowledge_note=None,
        ),
        AdminExportJobAlertEventRecord(
            event_id=42,
            job_id="alert-job-already-closed",
            export_type="ORDER_DETAIL",
            file_format="XLSX",
            error_code="ADMIN_EXPORT_JOB_WORKER_TIMEOUT",
            error_message="导出任务处理超时",
            alert_source="WORKER_FINAL_FAILURE",
            created_at=REQUESTED_AT,
            acknowledged_at=None,
            acknowledged_by_admin_user_id=None,
            acknowledged_by_username=None,
            acknowledged_by_display_name=None,
            acknowledge_note=None,
            closed_at=FINISHED_AT,
            closed_by_admin_user_id=1,
            closed_by_username="admin",
            closed_by_display_name="演示管理员",
            close_note="第一次关闭",
        ),
    ]
    client = build_client(auth_repo, export_repo)
    login_admin(client, auth_repo)

    response = client.post(
        "/api/admin/export-job-alert-events/batch-close",
        json={"eventIds": [41, 42, 404], "note": " 已处理 "},
        headers=csrf_headers(client),
    )

    assert response.status_code == 200
    assert response.json()["data"] == {
        "totalCount": 3,
        "successCount": 2,
        "failureCount": 1,
        "results": [
            {"eventId": 41, "closed": True},
            {"eventId": 42, "closed": True},
            {
                "eventId": 404,
                "closed": False,
                "code": "ADMIN_EXPORT_JOB_ALERT_EVENT_NOT_FOUND",
                "message": "导出任务告警事件不存在",
            },
        ],
    }
    assert export_repo.alert_event_records[0].closed_at == FINISHED_AT
    assert export_repo.alert_event_records[0].closed_by_username == "admin"
    assert export_repo.alert_event_records[0].close_note == "已处理"
    assert export_repo.alert_event_records[1].close_note == "第一次关闭"
    assert "filters" not in response.text
    assert "storageKey" not in response.text
    assert "storage_key" not in response.text


def test_export_job_alert_event_batch_close_rejects_duplicate_empty_extra_and_bad_note():
    auth_repo = FakeAuthRepository()
    export_repo = FakeAdminExportJobRepository()
    client = build_client(auth_repo, export_repo)
    login_admin(client, auth_repo)

    duplicate_response = client.post(
        "/api/admin/export-job-alert-events/batch-close",
        json={"eventIds": [1, 1]},
        headers=csrf_headers(client),
    )
    empty_response = client.post(
        "/api/admin/export-job-alert-events/batch-close",
        json={"eventIds": []},
        headers=csrf_headers(client),
    )
    extra_response = client.post(
        "/api/admin/export-job-alert-events/batch-close",
        json={"eventIds": [1], "adminUserId": 1},
        headers=csrf_headers(client),
    )
    snake_case_response = client.post(
        "/api/admin/export-job-alert-events/batch-close",
        json={"event_ids": [1]},
        headers=csrf_headers(client),
    )
    non_positive_response = client.post(
        "/api/admin/export-job-alert-events/batch-close",
        json={"eventIds": [0]},
        headers=csrf_headers(client),
    )
    too_many_response = client.post(
        "/api/admin/export-job-alert-events/batch-close",
        json={"eventIds": list(range(1, 102))},
        headers=csrf_headers(client),
    )
    bad_note_response = client.post(
        "/api/admin/export-job-alert-events/batch-close",
        json={"eventIds": [1], "note": "x" * 201},
        headers=csrf_headers(client),
    )

    assert duplicate_response.status_code == 422
    assert empty_response.status_code == 422
    assert extra_response.status_code == 422
    assert snake_case_response.status_code == 422
    assert non_positive_response.status_code == 422
    assert too_many_response.status_code == 422
    assert bad_note_response.status_code == 422
    assert bad_note_response.json()["code"] == "ADMIN_EXPORT_JOB_ALERT_EVENT_CLOSE_INVALID"
    assert export_repo.alert_event_records == []


def test_export_job_alert_event_close_is_first_write_wins():
    auth_repo = FakeAuthRepository()
    export_repo = FakeAdminExportJobRepository()
    export_repo.alert_event_records = [
        AdminExportJobAlertEventRecord(
            event_id=12,
            job_id="alert-job-1",
            export_type="ORDER_DETAIL",
            file_format="CSV",
            error_code="ADMIN_EXPORT_JOB_WORKER_FAILED",
            error_message="导出任务处理失败",
            alert_source="WORKER_FINAL_FAILURE",
            created_at=REQUESTED_AT,
            acknowledged_at=None,
            acknowledged_by_admin_user_id=None,
            acknowledged_by_username=None,
            acknowledged_by_display_name=None,
            acknowledge_note=None,
            closed_at=FINISHED_AT,
            closed_by_admin_user_id=1,
            closed_by_username="admin",
            closed_by_display_name="演示管理员",
            close_note="第一次关闭",
        )
    ]
    client = build_client(auth_repo, export_repo)
    login_admin(client, auth_repo)

    response = client.post(
        "/api/admin/export-job-alert-events/12/close",
        json={"note": "第二次关闭"},
        headers=csrf_headers(client),
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["closedAt"] == FINISHED_AT.isoformat().replace("+00:00", "Z")
    assert data["closedByUsername"] == "admin"
    assert data["closeNote"] == "第一次关闭"


def test_export_job_alert_event_reopen_returns_existing_open_duplicate():
    auth_repo = FakeAuthRepository()
    export_repo = FakeAdminExportJobRepository()
    export_repo.alert_event_records = [
        AdminExportJobAlertEventRecord(
            event_id=10,
            job_id="alert-job-duplicate",
            export_type="ORDER_DETAIL",
            file_format="CSV",
            error_code="ADMIN_EXPORT_JOB_WORKER_FAILED",
            error_message="旧告警",
            alert_source="WORKER_FINAL_FAILURE",
            created_at=REQUESTED_AT,
            acknowledged_at=None,
            acknowledged_by_admin_user_id=None,
            acknowledged_by_username=None,
            acknowledged_by_display_name=None,
            acknowledge_note=None,
            closed_at=FINISHED_AT,
            closed_by_admin_user_id=1,
            closed_by_username="admin",
            closed_by_display_name="演示管理员",
            close_note="已关闭",
        ),
        AdminExportJobAlertEventRecord(
            event_id=11,
            job_id="alert-job-duplicate",
            export_type="ORDER_DETAIL",
            file_format="CSV",
            error_code="ADMIN_EXPORT_JOB_WORKER_FAILED",
            error_message="新告警",
            alert_source="WORKER_FINAL_FAILURE",
            created_at=FINISHED_AT,
            acknowledged_at=None,
            acknowledged_by_admin_user_id=None,
            acknowledged_by_username=None,
            acknowledged_by_display_name=None,
            acknowledge_note=None,
            occurrence_count=2,
            last_seen_at=FINISHED_AT,
        ),
    ]
    client = build_client(auth_repo, export_repo)
    login_admin(client, auth_repo)

    response = client.post(
        "/api/admin/export-job-alert-events/10/reopen",
        headers=csrf_headers(client),
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["eventId"] == 11
    assert data["errorMessage"] == "新告警"
    assert data["occurrenceCount"] == 2
    assert data["lastSeenAt"] == FINISHED_AT.isoformat().replace("+00:00", "Z")
    assert export_repo.alert_event_records[0].closed_at == FINISHED_AT
    assert export_repo.alert_event_records[1].closed_at is None


def test_admin_can_delete_closed_export_job_alert_event_with_csrf_header():
    auth_repo = FakeAuthRepository()
    export_repo = FakeAdminExportJobRepository()
    export_repo.alert_event_records = [
        AdminExportJobAlertEventRecord(
            event_id=13,
            job_id="alert-job-closed",
            export_type="ORDER_DETAIL",
            file_format="CSV",
            error_code="ADMIN_EXPORT_JOB_WORKER_FAILED",
            error_message="导出任务处理失败",
            alert_source="WORKER_FINAL_FAILURE",
            created_at=REQUESTED_AT,
            acknowledged_at=None,
            acknowledged_by_admin_user_id=None,
            acknowledged_by_username=None,
            acknowledged_by_display_name=None,
            acknowledge_note=None,
            closed_at=FINISHED_AT,
            closed_by_admin_user_id=1,
            closed_by_username="admin",
            closed_by_display_name="演示管理员",
            close_note="已关闭",
        )
    ]
    client = build_client(auth_repo, export_repo)
    login_admin(client, auth_repo)

    response = client.delete(
        "/api/admin/export-job-alert-events/13",
        headers=csrf_headers(client),
    )

    assert response.status_code == 200
    assert response.json()["data"] == {"eventId": 13, "deleted": True}
    assert export_repo.last_alert_event_delete == 13
    assert export_repo.alert_event_records == []
    assert "filters" not in response.text
    assert "storageKey" not in response.text
    assert "storage_key" not in response.text


def test_admin_can_batch_delete_closed_export_job_alert_events_with_per_item_results():
    auth_repo = FakeAuthRepository()
    export_repo = FakeAdminExportJobRepository()
    export_repo.alert_event_records = [
        AdminExportJobAlertEventRecord(
            event_id=21,
            job_id="alert-job-closed-1",
            export_type="ORDER_DETAIL",
            file_format="CSV",
            error_code="ADMIN_EXPORT_JOB_WORKER_FAILED",
            error_message="导出任务处理失败",
            alert_source="WORKER_FINAL_FAILURE",
            created_at=REQUESTED_AT,
            acknowledged_at=None,
            acknowledged_by_admin_user_id=None,
            acknowledged_by_username=None,
            acknowledged_by_display_name=None,
            acknowledge_note=None,
            closed_at=FINISHED_AT,
            closed_by_admin_user_id=1,
            closed_by_username="admin",
            closed_by_display_name="演示管理员",
            close_note="已关闭",
        ),
        AdminExportJobAlertEventRecord(
            event_id=22,
            job_id="alert-job-open",
            export_type="ORDER_DETAIL",
            file_format="CSV",
            error_code="ADMIN_EXPORT_JOB_WORKER_FAILED",
            error_message="导出任务处理失败",
            alert_source="WORKER_FINAL_FAILURE",
            created_at=REQUESTED_AT,
            acknowledged_at=None,
            acknowledged_by_admin_user_id=None,
            acknowledged_by_username=None,
            acknowledged_by_display_name=None,
            acknowledge_note=None,
        ),
        AdminExportJobAlertEventRecord(
            event_id=23,
            job_id="alert-job-closed-2",
            export_type="ORDER_DETAIL",
            file_format="XLSX",
            error_code="ADMIN_EXPORT_JOB_WORKER_TIMEOUT",
            error_message="导出任务处理超时",
            alert_source="WORKER_FINAL_FAILURE",
            created_at=REQUESTED_AT,
            acknowledged_at=None,
            acknowledged_by_admin_user_id=None,
            acknowledged_by_username=None,
            acknowledged_by_display_name=None,
            acknowledge_note=None,
            closed_at=FINISHED_AT,
            closed_by_admin_user_id=1,
            closed_by_username="admin",
            closed_by_display_name="演示管理员",
            close_note="已关闭",
        ),
    ]
    client = build_client(auth_repo, export_repo)
    login_admin(client, auth_repo)

    response = client.post(
        "/api/admin/export-job-alert-events/batch-delete",
        json={"eventIds": [21, 22, 404, 23]},
        headers=csrf_headers(client),
    )

    assert response.status_code == 200
    assert response.json()["data"] == {
        "totalCount": 4,
        "successCount": 2,
        "failureCount": 2,
        "results": [
            {"eventId": 21, "deleted": True},
            {
                "eventId": 22,
                "deleted": False,
                "code": "ADMIN_EXPORT_JOB_ALERT_EVENT_DELETE_NOT_ALLOWED",
                "message": "只有已关闭的导出任务告警事件可以删除",
            },
            {
                "eventId": 404,
                "deleted": False,
                "code": "ADMIN_EXPORT_JOB_ALERT_EVENT_NOT_FOUND",
                "message": "导出任务告警事件不存在",
            },
            {"eventId": 23, "deleted": True},
        ],
    }
    assert [event.event_id for event in export_repo.alert_event_records] == [22]
    assert "filters" not in response.text
    assert "storageKey" not in response.text
    assert "storage_key" not in response.text


def test_export_job_alert_event_delete_rejects_open_or_missing_event():
    auth_repo = FakeAuthRepository()
    export_repo = FakeAdminExportJobRepository()
    export_repo.alert_event_records = [
        AdminExportJobAlertEventRecord(
            event_id=14,
            job_id="alert-job-open",
            export_type="ORDER_DETAIL",
            file_format="CSV",
            error_code="ADMIN_EXPORT_JOB_WORKER_FAILED",
            error_message="导出任务处理失败",
            alert_source="WORKER_FINAL_FAILURE",
            created_at=REQUESTED_AT,
            acknowledged_at=None,
            acknowledged_by_admin_user_id=None,
            acknowledged_by_username=None,
            acknowledged_by_display_name=None,
            acknowledge_note=None,
        )
    ]
    client = build_client(auth_repo, export_repo)
    login_admin(client, auth_repo)

    open_response = client.delete(
        "/api/admin/export-job-alert-events/14",
        headers=csrf_headers(client),
    )
    missing_response = client.delete(
        "/api/admin/export-job-alert-events/404",
        headers=csrf_headers(client),
    )

    assert open_response.status_code == 409
    assert open_response.json()["code"] == "ADMIN_EXPORT_JOB_ALERT_EVENT_DELETE_NOT_ALLOWED"
    assert missing_response.status_code == 404
    assert missing_response.json()["code"] == "ADMIN_EXPORT_JOB_ALERT_EVENT_NOT_FOUND"
    assert len(export_repo.alert_event_records) == 1


def test_export_job_alert_event_batch_delete_rejects_duplicate_empty_and_extra_fields():
    auth_repo = FakeAuthRepository()
    export_repo = FakeAdminExportJobRepository()
    client = build_client(auth_repo, export_repo)
    login_admin(client, auth_repo)

    duplicate_response = client.post(
        "/api/admin/export-job-alert-events/batch-delete",
        json={"eventIds": [1, 1]},
        headers=csrf_headers(client),
    )
    empty_response = client.post(
        "/api/admin/export-job-alert-events/batch-delete",
        json={"eventIds": []},
        headers=csrf_headers(client),
    )
    extra_response = client.post(
        "/api/admin/export-job-alert-events/batch-delete",
        json={"eventIds": [1], "adminUserId": 1},
        headers=csrf_headers(client),
    )
    snake_case_response = client.post(
        "/api/admin/export-job-alert-events/batch-delete",
        json={"event_ids": [1]},
        headers=csrf_headers(client),
    )
    non_positive_response = client.post(
        "/api/admin/export-job-alert-events/batch-delete",
        json={"eventIds": [0]},
        headers=csrf_headers(client),
    )

    assert duplicate_response.status_code == 422
    assert empty_response.status_code == 422
    assert extra_response.status_code == 422
    assert snake_case_response.status_code == 422
    assert non_positive_response.status_code == 422
    assert export_repo.alert_event_records == []


def test_export_job_alert_event_close_and_reopen_require_admin_and_csrf():
    auth_repo = FakeAuthRepository()
    export_repo = FakeAdminExportJobRepository()
    client = build_client(auth_repo, export_repo)

    anonymous_response = client.post(
        "/api/admin/export-job-alert-events/1/close",
        json={},
        headers=csrf_headers(client),
    )
    login_visitor(client)
    visitor_response = client.post(
        "/api/admin/export-job-alert-events/1/reopen",
        headers=csrf_headers(client),
    )
    auth_repo = FakeAuthRepository()
    export_repo = FakeAdminExportJobRepository()
    client = build_client(auth_repo, export_repo)
    login_admin(client, auth_repo)
    missing_csrf_response = client.post(
        "/api/admin/export-job-alert-events/1/close",
        json={},
    )

    assert anonymous_response.status_code == 401
    assert anonymous_response.json()["code"] == "ADMIN_AUTH_REQUIRED"
    assert visitor_response.status_code == 403
    assert visitor_response.json()["code"] == "ADMIN_FORBIDDEN"
    assert missing_csrf_response.status_code == 403
    assert missing_csrf_response.json()["code"] == "CSRF_INVALID"


def test_export_job_alert_event_batch_close_requires_admin_and_csrf():
    auth_repo = FakeAuthRepository()
    export_repo = FakeAdminExportJobRepository()
    client = build_client(auth_repo, export_repo)

    anonymous_response = client.post(
        "/api/admin/export-job-alert-events/batch-close",
        json={"eventIds": [1], "note": "已处理"},
        headers=csrf_headers(client),
    )
    login_visitor(client)
    visitor_response = client.post(
        "/api/admin/export-job-alert-events/batch-close",
        json={"eventIds": [1], "note": "已处理"},
        headers=csrf_headers(client),
    )
    auth_repo = FakeAuthRepository()
    export_repo = FakeAdminExportJobRepository()
    client = build_client(auth_repo, export_repo)
    login_admin(client, auth_repo)
    missing_csrf_response = client.post(
        "/api/admin/export-job-alert-events/batch-close",
        json={"eventIds": [1], "note": "已处理"},
    )

    assert anonymous_response.status_code == 401
    assert anonymous_response.json()["code"] == "ADMIN_AUTH_REQUIRED"
    assert visitor_response.status_code == 403
    assert visitor_response.json()["code"] == "ADMIN_FORBIDDEN"
    assert missing_csrf_response.status_code == 403
    assert missing_csrf_response.json()["code"] == "CSRF_INVALID"


def test_export_job_alert_event_delete_requires_admin_and_csrf():
    auth_repo = FakeAuthRepository()
    export_repo = FakeAdminExportJobRepository()
    client = build_client(auth_repo, export_repo)

    anonymous_response = client.delete(
        "/api/admin/export-job-alert-events/1",
        headers=csrf_headers(client),
    )
    login_visitor(client)
    visitor_response = client.delete(
        "/api/admin/export-job-alert-events/1",
        headers=csrf_headers(client),
    )
    auth_repo = FakeAuthRepository()
    export_repo = FakeAdminExportJobRepository()
    client = build_client(auth_repo, export_repo)
    login_admin(client, auth_repo)
    missing_csrf_response = client.delete("/api/admin/export-job-alert-events/1")

    assert anonymous_response.status_code == 401
    assert anonymous_response.json()["code"] == "ADMIN_AUTH_REQUIRED"
    assert visitor_response.status_code == 403
    assert visitor_response.json()["code"] == "ADMIN_FORBIDDEN"
    assert missing_csrf_response.status_code == 403
    assert missing_csrf_response.json()["code"] == "CSRF_INVALID"


def test_export_job_alert_event_batch_delete_requires_admin_and_csrf():
    auth_repo = FakeAuthRepository()
    export_repo = FakeAdminExportJobRepository()
    client = build_client(auth_repo, export_repo)

    anonymous_response = client.post(
        "/api/admin/export-job-alert-events/batch-delete",
        json={"eventIds": [1]},
        headers=csrf_headers(client),
    )
    login_visitor(client)
    visitor_response = client.post(
        "/api/admin/export-job-alert-events/batch-delete",
        json={"eventIds": [1]},
        headers=csrf_headers(client),
    )
    auth_repo = FakeAuthRepository()
    export_repo = FakeAdminExportJobRepository()
    client = build_client(auth_repo, export_repo)
    login_admin(client, auth_repo)
    missing_csrf_response = client.post(
        "/api/admin/export-job-alert-events/batch-delete",
        json={"eventIds": [1]},
    )

    assert anonymous_response.status_code == 401
    assert anonymous_response.json()["code"] == "ADMIN_AUTH_REQUIRED"
    assert visitor_response.status_code == 403
    assert visitor_response.json()["code"] == "ADMIN_FORBIDDEN"
    assert missing_csrf_response.status_code == 403
    assert missing_csrf_response.json()["code"] == "CSRF_INVALID"


def test_export_job_alert_event_close_and_reopen_reject_missing_event_and_bad_note():
    auth_repo = FakeAuthRepository()
    export_repo = FakeAdminExportJobRepository()
    client = build_client(auth_repo, export_repo)
    login_admin(client, auth_repo)

    missing_close_response = client.post(
        "/api/admin/export-job-alert-events/404/close",
        json={},
        headers=csrf_headers(client),
    )
    missing_reopen_response = client.post(
        "/api/admin/export-job-alert-events/404/reopen",
        headers=csrf_headers(client),
    )
    bad_note_response = client.post(
        "/api/admin/export-job-alert-events/404/close",
        json={"note": "x" * 201},
        headers=csrf_headers(client),
    )

    assert missing_close_response.status_code == 404
    assert missing_close_response.json()["code"] == "ADMIN_EXPORT_JOB_ALERT_EVENT_NOT_FOUND"
    assert missing_reopen_response.status_code == 404
    assert missing_reopen_response.json()["code"] == "ADMIN_EXPORT_JOB_ALERT_EVENT_NOT_FOUND"
    assert bad_note_response.status_code == 422
    assert bad_note_response.json()["code"] == "ADMIN_EXPORT_JOB_ALERT_EVENT_CLOSE_INVALID"


def test_export_job_alert_event_list_requires_admin_session():
    auth_repo = FakeAuthRepository()
    export_repo = FakeAdminExportJobRepository()
    client = build_client(auth_repo, export_repo)

    anonymous_response = client.get("/api/admin/export-job-alert-events")
    login_visitor(client)
    visitor_response = client.get("/api/admin/export-job-alert-events")

    assert anonymous_response.status_code == 401
    assert anonymous_response.json()["code"] == "ADMIN_AUTH_REQUIRED"
    assert visitor_response.status_code == 403
    assert visitor_response.json()["code"] == "ADMIN_FORBIDDEN"


def test_export_job_alert_event_acknowledge_requires_admin_and_csrf():
    auth_repo = FakeAuthRepository()
    export_repo = FakeAdminExportJobRepository()
    client = build_client(auth_repo, export_repo)

    anonymous_response = client.post(
        "/api/admin/export-job-alert-events/1/acknowledge",
        json={"note": "已处理"},
        headers=csrf_headers(client),
    )
    login_visitor(client)
    visitor_response = client.post(
        "/api/admin/export-job-alert-events/1/acknowledge",
        json={"note": "已处理"},
        headers=csrf_headers(client),
    )
    auth_repo = FakeAuthRepository()
    export_repo = FakeAdminExportJobRepository()
    client = build_client(auth_repo, export_repo)
    login_admin(client, auth_repo)
    no_csrf_response = client.post(
        "/api/admin/export-job-alert-events/1/acknowledge",
        json={"note": "已处理"},
    )

    assert anonymous_response.status_code == 401
    assert anonymous_response.json()["code"] == "ADMIN_AUTH_REQUIRED"
    assert visitor_response.status_code == 403
    assert visitor_response.json()["code"] == "ADMIN_FORBIDDEN"
    assert no_csrf_response.status_code == 403
    assert no_csrf_response.json()["code"] == "CSRF_INVALID"


def test_export_job_alert_event_batch_acknowledge_requires_admin_and_csrf():
    auth_repo = FakeAuthRepository()
    export_repo = FakeAdminExportJobRepository()
    client = build_client(auth_repo, export_repo)

    anonymous_response = client.post(
        "/api/admin/export-job-alert-events/batch-acknowledge",
        json={"eventIds": [1], "note": "已处理"},
        headers=csrf_headers(client),
    )
    login_visitor(client)
    visitor_response = client.post(
        "/api/admin/export-job-alert-events/batch-acknowledge",
        json={"eventIds": [1], "note": "已处理"},
        headers=csrf_headers(client),
    )
    auth_repo = FakeAuthRepository()
    export_repo = FakeAdminExportJobRepository()
    client = build_client(auth_repo, export_repo)
    login_admin(client, auth_repo)
    no_csrf_response = client.post(
        "/api/admin/export-job-alert-events/batch-acknowledge",
        json={"eventIds": [1], "note": "已处理"},
    )

    assert anonymous_response.status_code == 401
    assert anonymous_response.json()["code"] == "ADMIN_AUTH_REQUIRED"
    assert visitor_response.status_code == 403
    assert visitor_response.json()["code"] == "ADMIN_FORBIDDEN"
    assert no_csrf_response.status_code == 403
    assert no_csrf_response.json()["code"] == "CSRF_INVALID"


def test_export_job_alert_event_acknowledge_rejects_missing_event_and_bad_note():
    auth_repo = FakeAuthRepository()
    export_repo = FakeAdminExportJobRepository()
    client = build_client(auth_repo, export_repo)
    login_admin(client, auth_repo)

    missing_response = client.post(
        "/api/admin/export-job-alert-events/404/acknowledge",
        json={"note": "已处理"},
        headers=csrf_headers(client),
    )
    bad_note_response = client.post(
        "/api/admin/export-job-alert-events/404/acknowledge",
        json={"note": "x" * 201},
        headers=csrf_headers(client),
    )

    assert missing_response.status_code == 404
    assert missing_response.json()["code"] == "ADMIN_EXPORT_JOB_ALERT_EVENT_NOT_FOUND"
    assert bad_note_response.status_code == 422
    assert bad_note_response.json()["code"] == "ADMIN_EXPORT_JOB_ALERT_EVENT_ACK_INVALID"


def test_admin_can_download_succeeded_export_job_without_csrf_header():
    auth_repo = FakeAuthRepository()
    export_repo = FakeAdminExportJobRepository()
    file_storage = FakeAdminExportFileStorage()
    export_repo.jobs["download-job"] = export_job_record(
        job_id="download-job",
        file_format="CSV",
        status="SUCCEEDED",
        started_at=STARTED_AT,
        finished_at=FINISHED_AT,
        file_name='admin-orders-"july".csv',
    )
    export_repo.succeeded_storage_keys["download-job"] = "private/admin-orders.csv"
    file_storage.files["private/admin-orders.csv"] = b"orderNo,totalAmount\nO-1,100.00\n"
    client = build_client(auth_repo, export_repo, file_storage)
    login_admin(client, auth_repo)

    response = client.get("/api/admin/export-jobs/download-job/download")

    assert response.status_code == 200
    assert response.content == b"orderNo,totalAmount\nO-1,100.00\n"
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert (
        response.headers["content-disposition"]
        == 'attachment; filename="admin-orders-_july_.csv"; filename*=UTF-8\'\'admin-orders-_july_.csv'
    )
    assert not response.text.startswith("{")


def test_admin_can_download_xlsx_export_job_with_utf8_filename():
    auth_repo = FakeAuthRepository()
    export_repo = FakeAdminExportJobRepository()
    file_storage = FakeAdminExportFileStorage()
    export_repo.jobs["xlsx-download-job"] = export_job_record(
        job_id="xlsx-download-job",
        file_format="XLSX",
        status="SUCCEEDED",
        started_at=STARTED_AT,
        finished_at=FINISHED_AT,
        file_name="订单汇总.xlsx",
    )
    export_repo.succeeded_storage_keys["xlsx-download-job"] = "private/admin-orders.xlsx"
    file_storage.files["private/admin-orders.xlsx"] = b"PK\x03\x04fake-xlsx"
    client = build_client(auth_repo, export_repo, file_storage)
    login_admin(client, auth_repo)

    response = client.get("/api/admin/export-jobs/xlsx-download-job/download")

    assert response.status_code == 200
    assert response.content == b"PK\x03\x04fake-xlsx"
    assert (
        response.headers["content-type"]
        == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    assert (
        response.headers["content-disposition"]
        == "attachment; filename=\"____.xlsx\"; filename*=UTF-8''%E8%AE%A2%E5%8D%95%E6%B1%87%E6%80%BB.xlsx"
    )


def test_export_job_download_requires_admin_and_ready_file():
    auth_repo = FakeAuthRepository()
    export_repo = FakeAdminExportJobRepository()
    file_storage = FakeAdminExportFileStorage()
    client = build_client(auth_repo, export_repo, file_storage)

    anonymous = client.get("/api/admin/export-jobs/11111111-1111-4111-8111-111111111111/download")

    assert anonymous.status_code == 401
    assert anonymous.json()["code"] == "ADMIN_AUTH_REQUIRED"

    login_visitor(client)
    visitor = client.get("/api/admin/export-jobs/11111111-1111-4111-8111-111111111111/download")

    assert visitor.status_code == 403
    assert visitor.json()["code"] == "ADMIN_FORBIDDEN"

    auth_repo = FakeAuthRepository()
    export_repo = FakeAdminExportJobRepository()
    file_storage = FakeAdminExportFileStorage()
    export_repo.jobs["ready-metadata"] = export_job_record(
        job_id="ready-metadata",
        file_format="XLSX",
        status="SUCCEEDED",
        started_at=STARTED_AT,
        finished_at=FINISHED_AT,
        file_name="admin-orders.xlsx",
    )
    export_repo.succeeded_storage_keys["ready-metadata"] = "private/missing.xlsx"
    client = build_client(auth_repo, export_repo, file_storage)
    login_admin(client, auth_repo)

    not_ready = client.get("/api/admin/export-jobs/11111111-1111-4111-8111-111111111111/download")
    missing_file = client.get("/api/admin/export-jobs/ready-metadata/download")

    assert not_ready.status_code == 409
    assert not_ready.json()["code"] == "ADMIN_EXPORT_JOB_FILE_NOT_READY"
    assert missing_file.status_code == 404
    assert missing_file.json()["code"] == "ADMIN_EXPORT_FILE_NOT_FOUND"


def test_export_file_storage_rejects_path_traversal(tmp_path: Path):
    root = tmp_path / "exports"
    safe_dir = root / "private"
    safe_dir.mkdir(parents=True)
    safe_file = safe_dir / "export.csv"
    safe_file.write_bytes(b"ok")
    secret_file = tmp_path / "secret.csv"
    secret_file.write_bytes(b"secret")
    storage = AdminExportFileStorage(root)

    assert storage.read_file("private/export.csv") == b"ok"

    for storage_key in ["../secret.csv", str(secret_file)]:
        try:
            storage.read_file(storage_key)
        except AppError as exc:
            assert exc.status_code == 404
            assert exc.code == "ADMIN_EXPORT_FILE_NOT_FOUND"
        else:
            raise AssertionError("expected traversal storage key to be rejected")


def test_export_file_storage_deletes_files_inside_root(tmp_path: Path):
    root = tmp_path / "exports"
    safe_dir = root / "private"
    safe_dir.mkdir(parents=True)
    safe_file = safe_dir / "export.csv"
    safe_file.write_bytes(b"ok")
    secret_file = tmp_path / "secret.csv"
    secret_file.write_bytes(b"secret")
    symlink_file = safe_dir / "linked-secret.csv"
    symlink_file.symlink_to(secret_file)
    storage = AdminExportFileStorage(root)

    assert storage.delete_file("private/export.csv") is True
    assert not safe_file.exists()
    assert storage.delete_file("private/export.csv") is False

    for storage_key in ["../secret.csv", str(tmp_path / "secret.csv")]:
        try:
            storage.delete_file(storage_key)
        except AppError as exc:
            assert exc.status_code == 404
            assert exc.code == "ADMIN_EXPORT_FILE_NOT_FOUND"
        else:
            raise AssertionError("expected traversal storage key to be rejected")

    try:
        storage.delete_file("private/linked-secret.csv")
    except AppError as exc:
        assert exc.status_code == 404
        assert exc.code == "ADMIN_EXPORT_FILE_NOT_FOUND"
    else:
        raise AssertionError("expected symlink escape to be rejected")
    assert secret_file.read_bytes() == b"secret"
    assert symlink_file.is_symlink()


def test_admin_export_file_storage_factory_uses_local_provider(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(
        admin_export_service_module,
        "get_settings",
        lambda: SimpleNamespace(admin_export_storage_provider="local", admin_export_storage_dir=str(tmp_path)),
    )

    storage = get_admin_export_file_storage()

    assert isinstance(storage, AdminExportFileStorage)
    assert storage.root_dir == tmp_path


def test_admin_export_file_storage_factory_rejects_unsupported_provider(monkeypatch):
    monkeypatch.setattr(
        admin_export_service_module,
        "get_settings",
        lambda: SimpleNamespace(admin_export_storage_provider="s3", admin_export_storage_dir="/tmp/exports"),
    )

    with pytest.raises(AppError) as error:
        get_admin_export_file_storage()

    assert error.value.status_code == 500
    assert error.value.code == "ADMIN_EXPORT_STORAGE_PROVIDER_UNSUPPORTED"


def test_cleanup_old_succeeded_export_job_files_deletes_files_and_clears_metadata():
    export_repo = FakeAdminExportJobRepository()
    export_repo.jobs = {
        "old-file": export_job_record(
            job_id="old-file",
            status="SUCCEEDED",
            started_at=STARTED_AT,
            finished_at=FINISHED_AT,
            file_name="old.csv",
        ),
        "missing-file": export_job_record(
            job_id="missing-file",
            status="SUCCEEDED",
            started_at=STARTED_AT,
            finished_at=FINISHED_AT,
            file_name="missing.csv",
        ),
        "recent-file": export_job_record(
            job_id="recent-file",
            status="SUCCEEDED",
            started_at=STARTED_AT,
            finished_at=datetime(2026, 7, 2, 9, 40, tzinfo=UTC),
            file_name="recent.csv",
        ),
        "failed-file": export_job_record(
            job_id="failed-file",
            status="FAILED",
            started_at=STARTED_AT,
            finished_at=FINISHED_AT,
            file_name="failed.csv",
        ),
    }
    export_repo.succeeded_storage_keys = {
        "old-file": "private/old.csv",
        "missing-file": "private/missing.csv",
        "recent-file": "private/recent.csv",
        "failed-file": "private/failed.csv",
    }
    storage = FakeAdminExportFileStorage()
    storage.files = {
        "private/old.csv": b"old",
        "private/recent.csv": b"recent",
        "private/failed.csv": b"failed",
    }
    service = AdminExportJobService(export_repo, FakeAuthRepository())

    result = service.cleanup_succeeded_export_job_files(
        finished_before=datetime(2026, 7, 2, tzinfo=UTC),
        limit=100,
        storage=storage,
    )

    assert result.scanned == 2
    assert result.files_deleted == 1
    assert result.files_missing == 1
    assert result.metadata_cleared == 2
    assert result.skipped == 0
    assert "private/old.csv" not in storage.files
    assert "private/recent.csv" in storage.files
    assert "private/failed.csv" in storage.files
    assert export_repo.jobs["old-file"].file_name is None
    assert export_repo.jobs["missing-file"].file_name is None
    assert export_repo.jobs["recent-file"].file_name == "recent.csv"
    assert export_repo.jobs["failed-file"].file_name == "failed.csv"
    assert "old-file" not in export_repo.succeeded_storage_keys
    assert "missing-file" not in export_repo.succeeded_storage_keys
    assert export_repo.succeeded_storage_keys["recent-file"] == "private/recent.csv"
    assert export_repo.succeeded_storage_keys["failed-file"] == "private/failed.csv"


def test_cleanup_export_job_files_skips_invalid_storage_keys():
    export_repo = FakeAdminExportJobRepository()
    export_repo.jobs = {
        "unsafe-file": export_job_record(
            job_id="unsafe-file",
            status="SUCCEEDED",
            started_at=STARTED_AT,
            finished_at=FINISHED_AT,
            file_name="unsafe.csv",
        )
    }
    export_repo.succeeded_storage_keys = {"unsafe-file": "../unsafe.csv"}
    storage = FakeAdminExportFileStorage()
    service = AdminExportJobService(export_repo, FakeAuthRepository())

    result = service.cleanup_succeeded_export_job_files(
        finished_before=datetime(2026, 7, 2, tzinfo=UTC),
        limit=100,
        storage=storage,
    )

    assert result.scanned == 1
    assert result.files_deleted == 0
    assert result.files_missing == 0
    assert result.metadata_cleared == 0
    assert result.skipped == 1
    assert export_repo.jobs["unsafe-file"].file_name == "unsafe.csv"
    assert export_repo.succeeded_storage_keys["unsafe-file"] == "../unsafe.csv"


def test_cleanup_export_job_files_rejects_invalid_inputs():
    service = AdminExportJobService(FakeAdminExportJobRepository(), FakeAuthRepository())

    invalid_calls = [
        lambda: service.cleanup_succeeded_export_job_files(
            finished_before="2026-07-02",
            limit=100,
            storage=FakeAdminExportFileStorage(),
        ),
        lambda: service.cleanup_succeeded_export_job_files(
            finished_before=datetime(2026, 7, 2, tzinfo=UTC),
            limit=0,
            storage=FakeAdminExportFileStorage(),
        ),
        lambda: service.cleanup_succeeded_export_job_files(
            finished_before=datetime(2026, 7, 2, tzinfo=UTC),
            limit=1001,
            storage=FakeAdminExportFileStorage(),
        ),
    ]

    for call in invalid_calls:
        try:
            call()
        except AppError as exc:
            assert exc.code == "ADMIN_EXPORT_JOB_CLEANUP_INPUT_INVALID"
        else:
            raise AssertionError("expected cleanup input validation error")


def test_export_job_endpoints_enforce_admin_permissions_and_csrf():
    auth_repo = FakeAuthRepository()
    export_repo = FakeAdminExportJobRepository()
    client = build_client(auth_repo, export_repo)

    anonymous_post = client.post(
        "/api/admin/export-jobs",
        json={"exportType": "ORDER_DETAIL", "fileFormat": "CSV"},
    )
    anonymous_get = client.get("/api/admin/export-jobs")
    anonymous_post_with_csrf = client.post(
        "/api/admin/export-jobs",
        json={"exportType": "ORDER_DETAIL", "fileFormat": "CSV"},
        headers=csrf_headers(client),
    )
    anonymous_retry = client.post("/api/admin/export-jobs/11111111-1111-4111-8111-111111111111/retry")
    anonymous_retry_with_csrf = client.post(
        "/api/admin/export-jobs/11111111-1111-4111-8111-111111111111/retry",
        headers=csrf_headers(client),
    )

    assert anonymous_post.status_code == 403
    assert anonymous_post.json()["code"] == "CSRF_INVALID"
    assert anonymous_get.status_code == 401
    assert anonymous_get.json()["code"] == "ADMIN_AUTH_REQUIRED"
    assert anonymous_post_with_csrf.status_code == 401
    assert anonymous_post_with_csrf.json()["code"] == "ADMIN_AUTH_REQUIRED"
    assert anonymous_retry.status_code == 403
    assert anonymous_retry.json()["code"] == "CSRF_INVALID"
    assert anonymous_retry_with_csrf.status_code == 401
    assert anonymous_retry_with_csrf.json()["code"] == "ADMIN_AUTH_REQUIRED"

    login_visitor(client)
    visitor_headers = csrf_headers(client)
    visitor_post = client.post(
        "/api/admin/export-jobs",
        json={"exportType": "ORDER_DETAIL", "fileFormat": "CSV"},
        headers=visitor_headers,
    )
    visitor_get = client.get("/api/admin/export-jobs")
    visitor_retry = client.post(
        "/api/admin/export-jobs/11111111-1111-4111-8111-111111111111/retry",
        headers=visitor_headers,
    )

    assert visitor_post.status_code == 403
    assert visitor_post.json()["code"] == "ADMIN_FORBIDDEN"
    assert visitor_get.status_code == 403
    assert visitor_get.json()["code"] == "ADMIN_FORBIDDEN"
    assert visitor_retry.status_code == 403
    assert visitor_retry.json()["code"] == "ADMIN_FORBIDDEN"


def test_export_job_validation_and_missing_job_errors():
    auth_repo = FakeAuthRepository()
    export_repo = FakeAdminExportJobRepository()
    client = build_client(auth_repo, export_repo)
    login_admin(client, auth_repo)
    headers = csrf_headers(client)

    extra_field = client.post(
        "/api/admin/export-jobs",
        json={"exportType": "ORDER_DETAIL", "fileFormat": "CSV", "adminUserId": 1},
        headers=headers,
    )
    large_filters = client.post(
        "/api/admin/export-jobs",
        json={"exportType": "ORDER_DETAIL", "fileFormat": "CSV", "filters": {"q": "x" * 5000}},
        headers=headers,
    )
    invalid_type = client.get("/api/admin/export-jobs", params={"exportType": "unknown"})
    invalid_file_format = client.get("/api/admin/export-jobs", params={"fileFormat": "pdf"})
    invalid_status = client.get("/api/admin/export-jobs", params={"status": "done"})
    missing = client.get("/api/admin/export-jobs/missing-job")

    assert extra_field.status_code == 422
    assert extra_field.json()["code"] == "VALIDATION_ERROR"
    assert large_filters.status_code == 422
    assert large_filters.json()["code"] == "VALIDATION_ERROR"
    assert invalid_type.status_code == 422
    assert invalid_type.json()["code"] == "ADMIN_EXPORT_JOB_TYPE_INVALID"
    assert invalid_file_format.status_code == 422
    assert invalid_file_format.json()["code"] == "ADMIN_EXPORT_JOB_FILE_FORMAT_INVALID"
    assert invalid_status.status_code == 422
    assert invalid_status.json()["code"] == "ADMIN_EXPORT_JOB_STATUS_INVALID"
    assert missing.status_code == 404
    assert missing.json()["code"] == "ADMIN_EXPORT_JOB_NOT_FOUND"


def test_export_job_filter_whitelist_rejects_invalid_filters():
    auth_repo = FakeAuthRepository()
    export_repo = FakeAdminExportJobRepository()
    client = build_client(auth_repo, export_repo)
    login_admin(client, auth_repo)
    headers = csrf_headers(client)

    invalid_payloads = [
        {"exportType": "ORDER_DETAIL", "fileFormat": "CSV", "filters": {"adminUserId": 1}},
        {"exportType": "ORDER_DETAIL", "fileFormat": "CSV", "filters": {"includeEmpty": True}},
        {"exportType": "ORDER_DETAIL", "fileFormat": "CSV", "filters": {"dateFrom": "2026-13-01"}},
        {"exportType": "ORDER_DETAIL", "fileFormat": "CSV", "filters": {"dateFrom": "20260701"}},
        {
            "exportType": "PRODUCT_BREAKDOWN",
            "fileFormat": "CSV",
            "filters": {"dateFrom": "2026-08-01", "dateTo": "2026-07-01"},
        },
        {"exportType": "PAYMENT_RECONCILIATION", "fileFormat": "CSV", "filters": {"includeEmpty": True}},
        {
            "exportType": "CHECK_IN_AUDIT",
            "fileFormat": "CSV",
            "filters": {"ticketCode": "x" * 65},
        },
        {
            "exportType": "CHECK_IN_AUDIT",
            "fileFormat": "CSV",
            "filters": {"reason": "误" * 101},
        },
        {
            "exportType": "CHECK_IN_FAILURE_AUDIT",
            "fileFormat": "CSV",
            "filters": {"failureCode": "SQL_ERROR"},
        },
        {"exportType": "REFUND_AUDIT", "fileFormat": "CSV", "filters": {"refundType": "CHARGEBACK"}},
        {"exportType": "DAILY_TREND", "fileFormat": "CSV", "filters": {"includeEmpty": "yes"}},
    ]

    for payload in invalid_payloads:
        response = client.post("/api/admin/export-jobs", json=payload, headers=headers)

        assert response.status_code == 422
        assert response.json()["code"] == "ADMIN_EXPORT_JOB_FILTERS_INVALID"

    assert export_repo.created_records == []


def test_postgres_export_job_repository_uses_parameterized_values(monkeypatch):
    calls: list[tuple[str, tuple[object, ...]]] = []

    class FakeCursor:
        def __init__(self):
            self.last_sql = ""

        def execute(self, sql: str, params: tuple[object, ...]):
            self.last_sql = sql
            calls.append((sql, params))
            return self

        def fetchone(self):
            if "COUNT(*) AS total" in self.last_sql:
                return {"total": 0}
            return {
                "job_id": "job-1",
                "export_type": "ORDER_DETAIL",
                "file_format": "CSV",
                "filters": {"dateFrom": "2026-07-01"},
                "status": "PENDING",
                "request_id": "postgres-request",
                "requested_by_username": "admin",
                "requested_by_display_name": "演示管理员",
                "requested_at": REQUESTED_AT,
                "started_at": None,
                "finished_at": None,
                "file_name": None,
                "storage_key": "private/export.csv",
                "error_code": None,
                "error_message": None,
            }

        def fetchall(self):
            return []

    class FakeConnection:
        def __init__(self):
            self.cursor = FakeCursor()

        def __enter__(self):
            return self.cursor

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr(admin_export_repository_module, "connect_db", lambda: FakeConnection())

    repository = PostgresAdminExportJobRepository()
    repository.create_export_job(
        AdminExportJobCreateRecord(
            job_id="job-1",
            export_type="ORDER_DETAIL",
            file_format="CSV",
            filters={"dateFrom": "2026-07-01"},
            request_id="postgres-create",
            requested_by_admin_user_id=1,
            requested_by_username="admin",
            requested_by_display_name="演示管理员",
        )
    )
    repository.list_export_jobs(
        AdminExportJobListFilter(export_type="ORDER_DETAIL", file_format="CSV", status="PENDING", page=2, page_size=10)
    )
    repository.get_export_job("job-1")
    repository.get_export_job_file("job-1")

    create_sql, create_params = calls[0]
    count_sql, count_params = calls[1]
    list_sql, list_params = calls[2]
    get_sql, get_params = calls[3]
    file_sql, file_params = calls[4]

    assert "job-1" not in create_sql
    assert create_params[:3] == ("job-1", "ORDER_DETAIL", "CSV")
    assert create_params[4] == "postgres-create"
    assert "postgres-create" not in create_sql
    assert "export_type = %s" in count_sql
    assert "file_format = %s" in count_sql
    assert "status = %s" in count_sql
    assert "CSV" not in count_sql
    assert count_params == ("ORDER_DETAIL", "CSV", "PENDING")
    assert "LIMIT %s OFFSET %s" in list_sql
    assert list_params == ("ORDER_DETAIL", "CSV", "PENDING", 10, 10)
    assert "WHERE job_id = %s" in get_sql
    assert get_params == ("job-1",)
    assert "job-1" not in file_sql
    assert "storage_key" in file_sql
    assert "WHERE" in file_sql
    assert "job_id = %s" in file_sql
    assert "status = 'SUCCEEDED'" in file_sql
    assert file_params == ("job-1",)


def test_postgres_export_job_worker_state_uses_locks_and_parameterized_values(monkeypatch):
    calls: list[tuple[str, tuple[object, ...]]] = []

    class FakeCursor:
        def __init__(self):
            self.last_sql = ""
            self.last_params: tuple[object, ...] = ()

        def execute(self, sql: str, params: tuple[object, ...]):
            self.last_sql = sql
            self.last_params = params
            calls.append((sql, params))
            return self

        def fetchone(self):
            if "retry_count < max_retries" in self.last_sql and self.last_params[0] is True:
                status = "PENDING"
                file_name = None
                error_code = None
                error_message = None
                finished_at = None
            elif "retry_count < max_retries" in self.last_sql:
                status = "FAILED"
                file_name = None
                error_code = "WORKER_ERROR"
                error_message = "failed"
                finished_at = FINISHED_AT
            elif "status = 'PENDING'" in self.last_sql and "status = 'FAILED'" in self.last_sql:
                status = "PENDING"
                file_name = None
                error_code = None
                error_message = None
                finished_at = None
            elif "status = 'SUCCEEDED'" in self.last_sql:
                status = "SUCCEEDED"
                file_name = "export.csv"
                error_code = None
                error_message = None
                finished_at = FINISHED_AT
            elif "status = 'FAILED'" in self.last_sql:
                status = "FAILED"
                file_name = None
                error_code = "WORKER_ERROR"
                error_message = "failed"
                finished_at = FINISHED_AT
            else:
                status = "RUNNING"
                file_name = None
                error_code = None
                error_message = None
                finished_at = None
            return {
                "job_id": "job-1",
                "export_type": "ORDER_DETAIL",
                "file_format": "CSV",
                "filters": {"dateFrom": "2026-07-01"},
                "status": status,
                "request_id": "worker-request",
                "requested_by_username": "admin",
                "requested_by_display_name": "演示管理员",
                "requested_at": REQUESTED_AT,
                "started_at": STARTED_AT,
                "finished_at": finished_at,
                "file_name": file_name,
                "error_code": error_code,
                "error_message": error_message,
            }

    class FakeConnection:
        def __init__(self):
            self.cursor = FakeCursor()

        def __enter__(self):
            return self.cursor

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr(admin_export_repository_module, "connect_db", lambda: FakeConnection())

    repository = PostgresAdminExportJobRepository()
    repository.claim_next_pending_job()
    repository.mark_export_job_succeeded(
        "job-1",
        file_name="export.csv",
        storage_key="private/export.csv",
    )
    failed_record = repository.mark_export_job_failed(
        "job-2",
        error_code="WORKER_ERROR",
        error_message="failed",
    )
    retried_record = repository.mark_export_job_failed(
        "job-4",
        error_code="WORKER_ERROR",
        error_message="failed",
        retryable=True,
    )
    repository.retry_failed_export_job("job-3")

    claim_sql, claim_params = calls[0]
    success_sql, success_params = calls[1]
    failure_sql, failure_params = calls[2]
    auto_retry_sql, auto_retry_params = calls[3]
    retry_sql, retry_params = calls[4]

    assert "FOR UPDATE SKIP LOCKED" in claim_sql
    assert "WHERE status = 'PENDING'" in claim_sql
    assert "next_attempt_at IS NULL OR next_attempt_at <= CURRENT_TIMESTAMP" in claim_sql
    assert "status = 'RUNNING'" in claim_sql
    assert claim_params == ()
    assert "job-1" not in success_sql
    assert "private/export.csv" not in success_sql
    assert "next_attempt_at = NULL" in success_sql
    assert "WHERE job_id = %s AND status = 'RUNNING'" in success_sql
    assert success_params == ("export.csv", "private/export.csv", "job-1")
    assert "job-2" not in failure_sql
    assert "failed" not in failure_sql
    assert "WHERE job_id = %s AND status = 'RUNNING'" in failure_sql
    assert "retry_count < max_retries" in failure_sql
    assert "retry_count + 1" in failure_sql
    assert "next_attempt_at = CASE" in failure_sql
    assert "INTERVAL '1 second'" in failure_sql
    assert failed_record is not None
    assert failed_record.status == "FAILED"
    assert failure_params == (
        False,
        False,
        False,
        False,
        False,
        False,
        False,
        "WORKER_ERROR",
        False,
        "failed",
        False,
        60,
        "job-2",
    )
    assert "job-4" not in auto_retry_sql
    assert "failed" not in auto_retry_sql
    assert "WHERE job_id = %s AND status = 'RUNNING'" in auto_retry_sql
    assert retried_record is not None
    assert retried_record.status == "PENDING"
    assert auto_retry_params == (
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        "WORKER_ERROR",
        True,
        "failed",
        True,
        60,
        "job-4",
    )
    assert "job-3" not in retry_sql
    assert "status = 'PENDING'" in retry_sql
    assert "started_at = NULL" in retry_sql
    assert "finished_at = NULL" in retry_sql
    assert "storage_key = NULL" in retry_sql
    assert "error_code = NULL" in retry_sql
    assert "retry_count = 0" in retry_sql
    assert "next_attempt_at = NULL" in retry_sql
    assert "WHERE job_id = %s AND status = 'FAILED'" in retry_sql
    assert retry_params == ("job-3",)


def test_postgres_export_job_success_row_conversion_happens_before_connection_exit(monkeypatch):
    calls: list[tuple[str, tuple[object, ...]]] = []

    class FakeCursor:
        def execute(self, sql, params=()):
            self.last_sql = sql
            self.last_params = params
            calls.append((sql, params))
            return self

        def fetchone(self):
            return {
                "job_id": "job-1",
                "export_type": "ORDER_DETAIL",
                "file_format": "CSV",
                "filters": {},
                "status": "SUCCEEDED",
                "request_id": "worker-request",
                "requested_by_username": "admin",
                "requested_by_display_name": "演示管理员",
                "requested_at": REQUESTED_AT,
                "started_at": STARTED_AT,
                "finished_at": FINISHED_AT,
                "file_name": "export.csv",
                "error_code": None,
                "error_message": None,
            }

    class FakeConnection:
        def __init__(self):
            self.cursor = FakeCursor()
            self.exit_exc_type = None

        def __enter__(self):
            return self.cursor

        def __exit__(self, exc_type, *_args):
            self.exit_exc_type = exc_type
            return False

    connection = FakeConnection()

    def raise_during_row_conversion(_row):
        raise RuntimeError("row conversion failed before commit")

    monkeypatch.setattr(admin_export_repository_module, "connect_db", lambda: connection)
    monkeypatch.setattr(
        admin_export_repository_module,
        "admin_export_job_from_row",
        raise_during_row_conversion,
    )

    repository = PostgresAdminExportJobRepository()

    with pytest.raises(RuntimeError, match="row conversion failed before commit"):
        repository.mark_export_job_succeeded(
            "job-1",
            file_name="export.csv",
            storage_key="private/export.csv",
        )

    success_sql, success_params = calls[0]
    assert "WHERE job_id = %s AND status = 'RUNNING'" in success_sql
    assert success_params == ("export.csv", "private/export.csv", "job-1")
    assert connection.exit_exc_type is RuntimeError


def test_postgres_export_job_recover_stale_running_jobs_uses_parameterized_values(monkeypatch):
    calls: list[tuple[str, tuple[object, ...]]] = []

    class FakeCursor:
        def __init__(self):
            self.last_sql = ""

        def execute(self, sql: str, params: tuple[object, ...]):
            self.last_sql = sql
            calls.append((sql, params))
            return self

        def fetchall(self):
            return [
                {
                    "job_id": "stale-job",
                    "export_type": "ORDER_DETAIL",
                    "file_format": "CSV",
                    "filters": {"dateFrom": "2026-07-01"},
                    "status": "FAILED",
                    "request_id": "stale-request",
                    "requested_by_username": "admin",
                    "requested_by_display_name": "演示管理员",
                    "requested_at": REQUESTED_AT,
                    "started_at": STARTED_AT,
                    "finished_at": FINISHED_AT,
                    "file_name": None,
                    "error_code": "ADMIN_EXPORT_JOB_WORKER_TIMEOUT",
                    "error_message": "导出任务处理超时",
                }
            ]

    class FakeConnection:
        def __init__(self):
            self.cursor = FakeCursor()

        def __enter__(self):
            return self.cursor

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr(admin_export_repository_module, "connect_db", lambda: FakeConnection())

    repository = PostgresAdminExportJobRepository()
    recovered = repository.recover_stale_running_jobs(
        timeout_seconds=1800,
        error_code="ADMIN_EXPORT_JOB_WORKER_TIMEOUT",
        error_message="导出任务处理超时",
    )

    sql, params = calls[0]
    assert recovered.recovered_count == 1
    assert len(recovered.final_failed_jobs) == 1
    assert recovered.final_failed_jobs[0].job_id == "stale-job"
    assert recovered.final_failed_jobs[0].status == "FAILED"
    assert "ADMIN_EXPORT_JOB_WORKER_TIMEOUT" not in sql
    assert "导出任务处理超时" not in sql
    assert "status = 'RUNNING'" in sql
    assert "retry_count < max_retries" in sql
    assert "retry_count + 1" in sql
    assert "status = CASE" in sql
    assert "started_at < CURRENT_TIMESTAMP - (%s * INTERVAL '1 second')" in sql
    assert "next_attempt_at = NULL" in sql
    assert "RETURNING" in sql
    assert "job_id" in sql
    assert "error_message" in sql
    assert params == ("ADMIN_EXPORT_JOB_WORKER_TIMEOUT", "导出任务处理超时", 1800)


def test_postgres_export_job_alert_event_insert_uses_parameterized_values(monkeypatch):
    calls: list[tuple[str, tuple[object, ...]]] = []

    class FakeCursor:
        def execute(self, sql: str, params: tuple[object, ...]):
            calls.append((sql, params))
            return self

        def fetchone(self):
            return None

    class FakeConnection:
        def __init__(self):
            self.cursor = FakeCursor()

        def __enter__(self):
            return self.cursor

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr(admin_export_repository_module, "connect_db", lambda: FakeConnection())

    repository = PostgresAdminExportJobRepository()
    repository.create_export_job_alert_event(
        AdminExportJobAlertEventCreateRecord(
            job_id="job-1",
            export_type="ORDER_DETAIL",
            file_format="CSV",
            error_code="ADMIN_EXPORT_JOB_WORKER_FAILED",
            error_message="导出任务处理失败",
            alert_source="WORKER_FINAL_FAILURE",
        )
    )

    assert len(calls) == 1
    sql, params = calls[0]
    assert "INSERT INTO admin_export_job_alert_event" in sql
    assert "ON CONFLICT (job_id, error_code, alert_source)" in sql
    assert "WHERE closed_at IS NULL" in sql
    assert "DO UPDATE" in sql
    assert "occurrence_count = admin_export_job_alert_event.occurrence_count + 1" in sql
    assert "last_seen_at = CURRENT_TIMESTAMP" in sql
    assert "error_message = EXCLUDED.error_message" in sql
    assert "job-1" not in sql
    assert "ORDER_DETAIL" not in sql
    assert "ADMIN_EXPORT_JOB_WORKER_FAILED" not in sql
    assert "导出任务处理失败" not in sql
    assert params == (
        "job-1",
        "ORDER_DETAIL",
        "CSV",
        "ADMIN_EXPORT_JOB_WORKER_FAILED",
        "导出任务处理失败",
        "WORKER_FINAL_FAILURE",
    )


def test_postgres_export_job_alert_event_upsert_targets_open_unique_index(monkeypatch):
    calls: list[tuple[str, tuple[object, ...]]] = []

    class FakeCursor:
        def execute(self, sql: str, params: tuple[object, ...]):
            calls.append((sql, params))
            return self

    class FakeConnection:
        def __init__(self):
            self.cursor = FakeCursor()

        def __enter__(self):
            return self.cursor

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr(admin_export_repository_module, "connect_db", lambda: FakeConnection())

    repository = PostgresAdminExportJobRepository()
    repository.create_export_job_alert_event(
        AdminExportJobAlertEventCreateRecord(
            job_id="job-1",
            export_type="ORDER_DETAIL",
            file_format="CSV",
            error_code="ADMIN_EXPORT_JOB_WORKER_FAILED",
            error_message="导出任务处理失败",
            alert_source="WORKER_FINAL_FAILURE",
        )
    )

    assert len(calls) == 1
    sql, params = calls[0]
    assert "ON CONFLICT (job_id, error_code, alert_source)" in sql
    assert "WHERE closed_at IS NULL" in sql
    assert "DO UPDATE" in sql
    assert "occurrence_count = admin_export_job_alert_event.occurrence_count + 1" in sql
    assert params == (
        "job-1",
        "ORDER_DETAIL",
        "CSV",
        "ADMIN_EXPORT_JOB_WORKER_FAILED",
        "导出任务处理失败",
        "WORKER_FINAL_FAILURE",
    )


def test_postgres_export_job_alert_event_list_uses_parameterized_values(monkeypatch):
    calls: list[tuple[str, tuple[object, ...]]] = []

    class FakeCursor:
        def execute(self, sql: str, params: tuple[object, ...]):
            calls.append((sql, params))
            return self

        def fetchone(self):
            return {"total": 1}

        def fetchall(self):
            return [
                {
                    "id": 1,
                    "job_id": "job-1",
                    "export_type": "ORDER_DETAIL",
                    "file_format": "CSV",
                    "error_code": "ADMIN_EXPORT_JOB_WORKER_FAILED",
                    "error_message": "导出任务处理失败",
                    "alert_source": "WORKER_FINAL_FAILURE",
                    "created_at": FINISHED_AT,
                    "acknowledged_at": None,
                    "acknowledged_by_admin_user_id": None,
                    "acknowledged_by_username": None,
                    "acknowledged_by_display_name": None,
                    "acknowledge_note": None,
                }
            ]

    class FakeConnection:
        def __init__(self):
            self.cursor = FakeCursor()

        def __enter__(self):
            return self.cursor

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr(admin_export_repository_module, "connect_db", lambda: FakeConnection())

    repository = PostgresAdminExportJobRepository()
    listed = repository.list_export_job_alert_events(
        AdminExportJobAlertEventListFilter(
            job_id="job-1",
            export_type="ORDER_DETAIL",
            file_format="CSV",
            error_code="ADMIN_EXPORT_JOB_WORKER_FAILED",
            acknowledged=False,
            closed=False,
            date_from=date(2026, 7, 1),
            date_to=date(2026, 7, 1),
            page=2,
            page_size=10,
        )
    )

    count_sql, count_params = calls[0]
    list_sql, list_params = calls[1]
    assert listed.total == 1
    assert listed.items[0].job_id == "job-1"
    assert listed.items[0].error_code == "ADMIN_EXPORT_JOB_WORKER_FAILED"
    assert "FROM admin_export_job_alert_event" in count_sql
    assert "job_id = %s" in count_sql
    assert "export_type = %s" in count_sql
    assert "file_format = %s" in count_sql
    assert "error_code = %s" in count_sql
    assert "acknowledged_at IS NULL" in count_sql
    assert "closed_at IS NULL" in count_sql
    assert "created_at >= %s" in count_sql
    assert "created_at < %s" in count_sql
    assert "job-1" not in count_sql
    assert "ORDER_DETAIL" not in count_sql
    assert "CSV" not in count_sql
    assert "ADMIN_EXPORT_JOB_WORKER_FAILED" not in count_sql
    assert "2026-07-01" not in count_sql
    assert count_params == (
        "job-1",
        "ORDER_DETAIL",
        "CSV",
        "ADMIN_EXPORT_JOB_WORKER_FAILED",
        date(2026, 7, 1),
        date(2026, 7, 2),
    )
    assert "ORDER BY created_at DESC, id DESC" in list_sql
    assert "LIMIT %s OFFSET %s" in list_sql
    assert "filters" not in list_sql
    assert "storage_key" not in list_sql
    assert list_params == (
        "job-1",
        "ORDER_DETAIL",
        "CSV",
        "ADMIN_EXPORT_JOB_WORKER_FAILED",
        date(2026, 7, 1),
        date(2026, 7, 2),
        10,
        10,
    )


def test_postgres_export_job_alert_event_summary_uses_parameterized_values(monkeypatch):
    calls: list[tuple[str, tuple[object, ...]]] = []

    class FakeCursor:
        def execute(self, sql: str, params: tuple[object, ...]):
            calls.append((sql, params))
            return self

        def fetchone(self):
            return {"total": 2, "acknowledged": 1, "unacknowledged": 1, "closed": 0, "open_count": 2}

        def fetchall(self):
            return [
                {
                    "error_code": "ADMIN_EXPORT_JOB_WORKER_FAILED",
                    "total": 2,
                    "acknowledged": 1,
                    "unacknowledged": 1,
                    "closed": 0,
                    "open_count": 2,
                }
            ]

    class FakeConnection:
        def __init__(self):
            self.cursor = FakeCursor()

        def __enter__(self):
            return self.cursor

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr(admin_export_repository_module, "connect_db", lambda: FakeConnection())

    repository = PostgresAdminExportJobRepository()
    summary = repository.summarize_export_job_alert_events(
        AdminExportJobAlertEventSummaryFilter(
            export_type="ORDER_DETAIL",
            file_format="CSV",
            closed=False,
            date_from=date(2026, 7, 1),
            date_to=date(2026, 7, 1),
        )
    )

    summary_sql, summary_params = calls[0]
    by_code_sql, by_code_params = calls[1]
    assert summary.total == 2
    assert summary.acknowledged == 1
    assert summary.unacknowledged == 1
    assert summary.closed == 0
    assert summary.open_count == 2
    assert summary.by_error_code[0].error_code == "ADMIN_EXPORT_JOB_WORKER_FAILED"
    assert summary.by_error_code[0].total == 2
    assert "COUNT(*) FILTER (WHERE acknowledged_at IS NOT NULL)" in summary_sql
    assert "COUNT(*) FILTER (WHERE closed_at IS NOT NULL)" in summary_sql
    assert "COUNT(*) FILTER (WHERE closed_at IS NULL)" in summary_sql
    assert "FROM admin_export_job_alert_event" in summary_sql
    assert "export_type = %s" in summary_sql
    assert "file_format = %s" in summary_sql
    assert "closed_at IS NULL" in summary_sql
    assert "created_at >= %s" in summary_sql
    assert "created_at < %s" in summary_sql
    assert "2026-07-01" not in summary_sql
    assert "ORDER_DETAIL" not in summary_sql
    assert "CSV" not in summary_sql
    assert "filters" not in summary_sql
    assert "storage_key" not in summary_sql
    assert summary_params == ("ORDER_DETAIL", "CSV", date(2026, 7, 1), date(2026, 7, 2))
    assert "GROUP BY error_code" in by_code_sql
    assert "ORDER BY total DESC, error_code ASC" in by_code_sql
    assert "filters" not in by_code_sql
    assert "storage_key" not in by_code_sql
    assert by_code_params == ("ORDER_DETAIL", "CSV", date(2026, 7, 1), date(2026, 7, 2))


def test_postgres_export_job_alert_event_acknowledge_uses_parameterized_values(monkeypatch):
    calls: list[tuple[str, tuple[object, ...]]] = []

    class FakeCursor:
        def execute(self, sql: str, params: tuple[object, ...]):
            calls.append((sql, params))
            return self

        def fetchone(self):
            return {
                "id": 9,
                "job_id": "job-1",
                "export_type": "ORDER_DETAIL",
                "file_format": "CSV",
                "error_code": "ADMIN_EXPORT_JOB_WORKER_FAILED",
                "error_message": "导出任务处理失败",
                "alert_source": "WORKER_FINAL_FAILURE",
                "created_at": REQUESTED_AT,
                "acknowledged_at": FINISHED_AT,
                "acknowledged_by_admin_user_id": 1,
                "acknowledged_by_username": "admin",
                "acknowledged_by_display_name": "演示管理员",
                "acknowledge_note": "已人工重跑成功",
            }

    class FakeConnection:
        def __init__(self):
            self.cursor = FakeCursor()

        def __enter__(self):
            return self.cursor

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr(admin_export_repository_module, "connect_db", lambda: FakeConnection())

    repository = PostgresAdminExportJobRepository()
    acknowledged = repository.acknowledge_export_job_alert_event(
        AdminExportJobAlertEventAcknowledgeRecord(
            event_id=9,
            acknowledged_by_admin_user_id=1,
            acknowledged_by_username="admin",
            acknowledged_by_display_name="演示管理员",
            acknowledge_note="已人工重跑成功",
        )
    )

    sql, params = calls[0]
    assert acknowledged is not None
    assert acknowledged.event_id == 9
    assert acknowledged.acknowledge_note == "已人工重跑成功"
    assert "UPDATE admin_export_job_alert_event" in sql
    assert "WHERE id = %s" in sql
    assert "CASE" in sql
    assert "已人工重跑成功" not in sql
    assert "'admin'" not in sql
    assert "演示管理员" not in sql
    assert "filters" not in sql
    assert "storage_key" not in sql
    assert params == (1, "admin", "演示管理员", "已人工重跑成功", 9)


def test_postgres_export_job_alert_event_close_and_reopen_use_parameterized_values(monkeypatch):
    calls: list[tuple[str, tuple[object, ...]]] = []

    class FakeCursor:
        def execute(self, sql: str, params: tuple[object, ...]):
            calls.append((sql, params))
            return self

        def fetchone(self):
            if len(calls) == 1:
                return {
                    "id": 9,
                    "job_id": "job-1",
                    "export_type": "ORDER_DETAIL",
                    "file_format": "CSV",
                    "error_code": "ADMIN_EXPORT_JOB_WORKER_FAILED",
                    "error_message": "导出任务处理失败",
                    "alert_source": "WORKER_FINAL_FAILURE",
                    "created_at": REQUESTED_AT,
                    "acknowledged_at": None,
                    "acknowledged_by_admin_user_id": None,
                    "acknowledged_by_username": None,
                    "acknowledged_by_display_name": None,
                    "acknowledge_note": None,
                    "closed_at": FINISHED_AT,
                    "closed_by_admin_user_id": 1,
                    "closed_by_username": "admin",
                    "closed_by_display_name": "演示管理员",
                    "close_note": "无需展示",
                }
            return {
                "id": 9,
                "job_id": "job-1",
                "export_type": "ORDER_DETAIL",
                "file_format": "CSV",
                "error_code": "ADMIN_EXPORT_JOB_WORKER_FAILED",
                "error_message": "导出任务处理失败",
                "alert_source": "WORKER_FINAL_FAILURE",
                "created_at": REQUESTED_AT,
                "acknowledged_at": None,
                "acknowledged_by_admin_user_id": None,
                "acknowledged_by_username": None,
                "acknowledged_by_display_name": None,
                "acknowledge_note": None,
                "closed_at": None,
                "closed_by_admin_user_id": None,
                "closed_by_username": None,
                "closed_by_display_name": None,
                "close_note": None,
            }

    class FakeConnection:
        def __init__(self):
            self.cursor = FakeCursor()

        def __enter__(self):
            return self.cursor

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr(admin_export_repository_module, "connect_db", lambda: FakeConnection())

    repository = PostgresAdminExportJobRepository()
    closed = repository.close_export_job_alert_event(
        AdminExportJobAlertEventCloseRecord(
            event_id=9,
            closed_by_admin_user_id=1,
            closed_by_username="admin",
            closed_by_display_name="演示管理员",
            close_note="无需展示",
        )
    )
    reopened = repository.reopen_export_job_alert_event(9)

    close_sql, close_params = calls[0]
    reopen_sql, reopen_params = calls[1]
    assert closed is not None
    assert closed.close_note == "无需展示"
    assert reopened is not None
    assert reopened.closed_at is None
    assert "UPDATE admin_export_job_alert_event" in close_sql
    assert "closed_at = CASE" in close_sql
    assert "WHERE id = %s" in close_sql
    assert "无需展示" not in close_sql
    assert "'admin'" not in close_sql
    assert "演示管理员" not in close_sql
    assert "filters" not in close_sql
    assert "storage_key" not in close_sql
    assert close_params == (1, "admin", "演示管理员", "无需展示", 9)
    assert "UPDATE admin_export_job_alert_event" in reopen_sql
    assert "closed_at = NULL" in reopen_sql
    assert "closed_by_admin_user_id = NULL" in reopen_sql
    assert "existing_open AS" in reopen_sql
    assert "event.closed_at IS NULL" in reopen_sql
    assert "AND event.id <> target.id" in reopen_sql
    assert "AND NOT EXISTS (SELECT 1 FROM existing_open)" in reopen_sql
    assert "UNION ALL" in reopen_sql
    assert "WHERE id = %s" in reopen_sql
    assert "filters" not in reopen_sql
    assert "storage_key" not in reopen_sql
    assert reopen_params == (9, 9)


def test_postgres_export_job_alert_event_delete_closed_uses_parameterized_values(monkeypatch):
    calls: list[tuple[str, tuple[object, ...]]] = []

    class FakeCursor:
        def execute(self, sql: str, params: tuple[object, ...]):
            calls.append((sql, params))
            return self

        def fetchone(self):
            return {"found": True, "closed": True, "deleted": True}

    class FakeConnection:
        def __init__(self):
            self.cursor = FakeCursor()

        def __enter__(self):
            return self.cursor

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr(admin_export_repository_module, "connect_db", lambda: FakeConnection())

    repository = PostgresAdminExportJobRepository()
    result = repository.delete_closed_export_job_alert_event(9)

    sql, params = calls[0]
    assert result == AdminExportJobAlertEventDeleteResult(found=True, closed=True, deleted=True)
    assert "DELETE FROM admin_export_job_alert_event" in sql
    assert "closed_at IS NOT NULL" in sql
    assert "WHERE id = %s" in sql
    assert "filters" not in sql
    assert "storage_key" not in sql
    assert params == (9, 9)


def test_postgres_export_job_cleanup_uses_parameterized_values(monkeypatch):
    calls: list[tuple[str, tuple[object, ...]]] = []

    class FakeCursor:
        def __init__(self):
            self.last_sql = ""

        def execute(self, sql: str, params: tuple[object, ...]):
            self.last_sql = sql
            calls.append((sql, params))
            return self

        def fetchall(self):
            return [{"job_id": "job-1", "storage_key": "private/export.csv"}]

        def fetchone(self):
            return {"job_id": "job-1"}

    class FakeConnection:
        def __init__(self):
            self.cursor = FakeCursor()

        def __enter__(self):
            return self.cursor

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr(admin_export_repository_module, "connect_db", lambda: FakeConnection())

    repository = PostgresAdminExportJobRepository()
    cutoff = datetime(2026, 7, 2, tzinfo=UTC)
    records = repository.list_succeeded_export_job_files_finished_before(cutoff, limit=50)
    cleared = repository.clear_export_job_file_metadata("job-1", storage_key="private/export.csv")

    list_sql, list_params = calls[0]
    clear_sql, clear_params = calls[1]

    assert records == [AdminExportJobCleanupFileRecord(job_id="job-1", storage_key="private/export.csv")]
    assert cleared is True
    assert "private/export.csv" not in list_sql
    assert "finished_at < %s" in list_sql
    assert "LIMIT %s" in list_sql
    assert list_params == (cutoff, 50)
    assert "job-1" not in clear_sql
    assert "private/export.csv" not in clear_sql
    assert "job_id = %s" in clear_sql
    assert "AND status = 'SUCCEEDED'" in clear_sql
    assert "AND storage_key = %s" in clear_sql
    assert clear_params == ("job-1", "private/export.csv")
