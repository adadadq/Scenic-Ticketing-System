from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote
from uuid import uuid4

from fastapi import Depends, Request

from app.core.config import get_settings
from app.core.errors import AppError
from app.repositories.admin_exports import (
    AdminExportJobAlertEventAcknowledgeRecord,
    AdminExportJobAlertEventCloseRecord,
    AdminExportJobAlertEventCreateRecord,
    AdminExportJobAlertEventListFilter,
    AdminExportJobAlertEventListRecord,
    AdminExportJobAlertEventRecord,
    AdminExportJobAlertEventSummaryFilter,
    AdminExportJobAlertEventSummaryRecord,
    AdminExportJobCreateRecord,
    AdminExportJobCleanupFileRecord,
    AdminExportJobFileRecord,
    AdminExportJobListFilter,
    AdminExportJobListRecord,
    AdminExportJobRecord,
    AdminExportJobRepository,
    get_admin_export_job_repository,
)
from app.schemas.admin_exports import (
    AdminExportJobAlertEventAcknowledgeRequest,
    AdminExportJobAlertEventBatchAcknowledgeDTO,
    AdminExportJobAlertEventBatchAcknowledgeRequest,
    AdminExportJobAlertEventBatchAcknowledgeResultDTO,
    AdminExportJobAlertEventBatchCloseDTO,
    AdminExportJobAlertEventBatchCloseRequest,
    AdminExportJobAlertEventBatchCloseResultDTO,
    AdminExportJobAlertEventBatchDeleteDTO,
    AdminExportJobAlertEventBatchDeleteRequest,
    AdminExportJobAlertEventBatchDeleteResultDTO,
    AdminExportJobAlertEventCloseRequest,
    AdminExportJobAlertEventDeleteDTO,
    AdminExportJobAlertEventDTO,
    AdminExportJobAlertEventListDTO,
    AdminExportJobAlertEventSummaryByErrorCodeDTO,
    AdminExportJobAlertEventSummaryDTO,
    AdminExportJobCreateRequest,
    AdminExportJobDTO,
    AdminExportJobListDTO,
)
from app.services.auth import AdminAuthService, get_admin_auth_service
from app.services.orders import (
    AdminCheckInService,
    AdminRefundService,
    AdminReportService,
    get_admin_check_in_service,
    get_admin_refund_service,
    get_admin_report_service,
)


ADMIN_EXPORT_JOB_TYPE_OPTIONS = (
    "ORDER_DETAIL",
    "CHECK_IN_AUDIT",
    "CHECK_IN_FAILURE_AUDIT",
    "REFUND_AUDIT",
    "PAYMENT_RECONCILIATION",
    "PRODUCT_BREAKDOWN",
    "DAILY_TREND",
    "HOURLY_TREND",
    "MONTHLY_TREND",
)
ADMIN_EXPORT_JOB_STATUS_OPTIONS = ("PENDING", "RUNNING", "SUCCEEDED", "FAILED")
ADMIN_EXPORT_JOB_FILE_FORMAT_OPTIONS = ("CSV", "XLSX")
ADMIN_EXPORT_JOB_FILTER_FIELDS = {
    "ORDER_DETAIL": {"dateFrom", "dateTo"},
    "CHECK_IN_AUDIT": {"ticketCode", "orderNo", "operatorUsername", "reason", "dateFrom", "dateTo"},
    "CHECK_IN_FAILURE_AUDIT": {"ticketCode", "failureCode", "operatorUsername", "dateFrom", "dateTo"},
    "REFUND_AUDIT": {"refundType", "orderNo", "operatorUsername", "dateFrom", "dateTo"},
    "PAYMENT_RECONCILIATION": {"dateFrom", "dateTo"},
    "PRODUCT_BREAKDOWN": {"dateFrom", "dateTo"},
    "DAILY_TREND": {"dateFrom", "dateTo", "includeEmpty"},
    "HOURLY_TREND": {"dateFrom", "dateTo", "includeEmpty"},
    "MONTHLY_TREND": {"dateFrom", "dateTo", "includeEmpty"},
}
ADMIN_EXPORT_JOB_TEXT_FILTER_MAX_LENGTHS = {
    "ticketCode": 64,
    "orderNo": 64,
    "operatorUsername": 64,
    "reason": 100,
    "failureCode": 40,
}
ADMIN_EXPORT_JOB_FAILURE_CODE_OPTIONS = {
    "TICKET_NOT_FOUND",
    "TICKET_ALREADY_USED",
    "TICKET_NOT_CHECKABLE",
    "TICKET_NOT_CHECKED_IN",
    "TICKET_UNDO_NOT_ALLOWED",
}
ADMIN_EXPORT_JOB_REFUND_TYPE_OPTIONS = {"FULL", "PARTIAL"}
ADMIN_EXPORT_JOB_FILE_NAME_MAX_LENGTH = 255
ADMIN_EXPORT_JOB_STORAGE_KEY_MAX_LENGTH = 255
ADMIN_EXPORT_JOB_ERROR_CODE_MAX_LENGTH = 80
ADMIN_EXPORT_JOB_ERROR_MESSAGE_MAX_LENGTH = 500
ADMIN_EXPORT_JOB_UNSUPPORTED_ERROR_CODE = "ADMIN_EXPORT_JOB_UNSUPPORTED"
ADMIN_EXPORT_JOB_WORKER_FAILED_ERROR_CODE = "ADMIN_EXPORT_JOB_WORKER_FAILED"
ADMIN_EXPORT_JOB_WORKER_TIMEOUT_ERROR_CODE = "ADMIN_EXPORT_JOB_WORKER_TIMEOUT"
ADMIN_EXPORT_JOB_RETRY_NOT_ALLOWED_ERROR_CODE = "ADMIN_EXPORT_JOB_RETRY_NOT_ALLOWED"
ADMIN_EXPORT_JOB_FILE_FORMAT_INVALID_ERROR_CODE = "ADMIN_EXPORT_JOB_FILE_FORMAT_INVALID"
ADMIN_EXPORT_JOB_ALERT_EVENT_FILTER_INVALID_ERROR_CODE = "ADMIN_EXPORT_JOB_ALERT_EVENT_FILTER_INVALID"
ADMIN_EXPORT_JOB_ALERT_EVENT_ACK_INVALID_ERROR_CODE = "ADMIN_EXPORT_JOB_ALERT_EVENT_ACK_INVALID"
ADMIN_EXPORT_JOB_ALERT_EVENT_CLOSE_INVALID_ERROR_CODE = "ADMIN_EXPORT_JOB_ALERT_EVENT_CLOSE_INVALID"
ADMIN_EXPORT_JOB_ALERT_EVENT_DELETE_NOT_ALLOWED_ERROR_CODE = "ADMIN_EXPORT_JOB_ALERT_EVENT_DELETE_NOT_ALLOWED"
ADMIN_EXPORT_JOB_ALERT_SOURCE_WORKER_FINAL_FAILURE = "WORKER_FINAL_FAILURE"
ADMIN_EXPORT_JOB_CLEANUP_LIMIT_MAX = 1000
ADMIN_EXPORT_JOB_RUNNING_TIMEOUT_SECONDS = 30 * 60
ADMIN_EXPORT_JOB_PUBLIC_FILTER_FIELDS = {"dateFrom", "dateTo", "failureCode", "refundType", "includeEmpty"}
ADMIN_EXPORT_JOB_REDACTED_FILTER_VALUE = "***"
ADMIN_EXPORT_JOB_ALERT_EVENT_ACK_NOTE_MAX_LENGTH = 200


@dataclass(frozen=True)
class AdminExportJobDownloadFile:
    content: bytes
    media_type: str
    content_disposition: str


@dataclass(frozen=True)
class AdminExportJobCleanupResult:
    scanned: int
    files_deleted: int
    files_missing: int
    metadata_cleared: int
    skipped: int


class AdminExportFileStorage:
    def __init__(self, root_dir: str | Path):
        self.root_dir = Path(root_dir)

    def read_file(self, storage_key: str) -> bytes:
        file_path = self.resolve_storage_key(storage_key)
        if not file_path.is_file():
            raise AppError(404, "ADMIN_EXPORT_FILE_NOT_FOUND", "导出文件不存在")
        return file_path.read_bytes()

    def write_file(self, storage_key: str, content: bytes) -> None:
        file_path = self.resolve_storage_key(storage_key)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(content)

    def delete_file(self, storage_key: str) -> bool:
        file_path = self.resolve_storage_key(storage_key)
        if not file_path.exists():
            return False
        if not file_path.is_file():
            raise AppError(404, "ADMIN_EXPORT_FILE_NOT_FOUND", "导出文件不存在")
        file_path.unlink()
        return True

    def resolve_storage_key(self, storage_key: str) -> Path:
        if not isinstance(storage_key, str) or not storage_key.strip():
            raise AppError(404, "ADMIN_EXPORT_FILE_NOT_FOUND", "导出文件不存在")
        root = self.root_dir.resolve()
        file_path = (root / storage_key.strip()).resolve()
        if file_path != root and root not in file_path.parents:
            raise AppError(404, "ADMIN_EXPORT_FILE_NOT_FOUND", "导出文件不存在")
        return file_path


class AdminExportJobService:
    def __init__(self, repository: AdminExportJobRepository, admin_auth_service: AdminAuthService):
        self.repository = repository
        self.admin_auth_service = admin_auth_service

    def create_export_job(self, payload: AdminExportJobCreateRequest, request: Request) -> AdminExportJobDTO:
        session_record = self.admin_auth_service.current_session_admin(request)
        normalized_filters = self.normalize_filters(payload.export_type, payload.filters)
        record = self.repository.create_export_job(
            AdminExportJobCreateRecord(
                job_id=str(uuid4()),
                export_type=payload.export_type,
                file_format=payload.file_format,
                filters=normalized_filters,
                request_id=self.to_export_job_request_id(getattr(request.state, "request_id", None)),
                requested_by_admin_user_id=session_record.admin.id,
                requested_by_username=session_record.admin.username,
                requested_by_display_name=session_record.admin.display_name,
            )
        )
        return self.to_export_job_dto(record)

    def claim_next_pending_job(self) -> AdminExportJobDTO | None:
        record = self.repository.claim_next_pending_job()
        return self.to_export_job_dto(record) if record else None

    def recover_stale_running_jobs(self) -> int:
        recovery = self.repository.recover_stale_running_jobs(
            timeout_seconds=ADMIN_EXPORT_JOB_RUNNING_TIMEOUT_SECONDS,
            error_code=ADMIN_EXPORT_JOB_WORKER_TIMEOUT_ERROR_CODE,
            error_message="导出任务处理超时",
        )
        for record in recovery.final_failed_jobs:
            self.record_final_failure_alert(record)
        return recovery.recovered_count

    def mark_export_job_succeeded(
        self,
        job_id: str,
        *,
        file_name: str,
        storage_key: str,
    ) -> AdminExportJobDTO | None:
        normalized_job_id = self.normalize_job_id(job_id)
        normalized_file_name = self.normalize_required_text(
            file_name,
            max_length=ADMIN_EXPORT_JOB_FILE_NAME_MAX_LENGTH,
        )
        normalized_storage_key = self.normalize_required_text(
            storage_key,
            max_length=ADMIN_EXPORT_JOB_STORAGE_KEY_MAX_LENGTH,
        )
        record = self.repository.mark_export_job_succeeded(
            normalized_job_id,
            file_name=normalized_file_name,
            storage_key=normalized_storage_key,
        )
        return self.to_export_job_dto(record) if record else None

    def mark_export_job_failed(
        self,
        job_id: str,
        *,
        error_code: str,
        error_message: str,
        retryable: bool = False,
    ) -> AdminExportJobDTO | None:
        normalized_job_id = self.normalize_job_id(job_id)
        normalized_error_code = self.normalize_required_text(
            error_code,
            max_length=ADMIN_EXPORT_JOB_ERROR_CODE_MAX_LENGTH,
        )
        normalized_error_message = self.normalize_required_text(
            error_message,
            max_length=ADMIN_EXPORT_JOB_ERROR_MESSAGE_MAX_LENGTH,
        )
        record = self.repository.mark_export_job_failed(
            normalized_job_id,
            error_code=normalized_error_code,
            error_message=normalized_error_message,
            retryable=retryable,
        )
        if record is not None and record.status == "FAILED":
            self.record_final_failure_alert(record)
        return self.to_export_job_dto(record) if record else None

    def record_final_failure_alert(self, record: AdminExportJobRecord) -> None:
        if record.error_code is None or record.error_message is None:
            return
        try:
            self.repository.create_export_job_alert_event(
                AdminExportJobAlertEventCreateRecord(
                    job_id=record.job_id,
                    export_type=record.export_type,
                    file_format=record.file_format,
                    error_code=record.error_code,
                    error_message=record.error_message,
                    alert_source=ADMIN_EXPORT_JOB_ALERT_SOURCE_WORKER_FINAL_FAILURE,
                )
            )
        except Exception:
            return

    def retry_failed_export_job(self, job_id: str, request: Request) -> AdminExportJobDTO:
        self.admin_auth_service.current_session_admin(request)
        normalized_job_id = self.normalize_job_id(job_id)
        record = self.repository.retry_failed_export_job(normalized_job_id)
        if record is not None:
            return self.to_export_job_dto(record)
        if self.repository.get_export_job(normalized_job_id) is None:
            raise AppError(404, "ADMIN_EXPORT_JOB_NOT_FOUND", "导出任务不存在")
        raise AppError(409, ADMIN_EXPORT_JOB_RETRY_NOT_ALLOWED_ERROR_CODE, "只有失败的导出任务可以重试")

    def list_export_jobs(
        self,
        *,
        request: Request,
        export_type: str | None,
        file_format: str | None,
        status: str | None,
        page: int,
        page_size: int,
    ) -> AdminExportJobListDTO:
        self.admin_auth_service.current_session_admin(request)
        filters = AdminExportJobListFilter(
            export_type=self.normalize_export_type(export_type),
            file_format=self.normalize_file_format(file_format),
            status=self.normalize_status(status),
            page=page,
            page_size=page_size,
        )
        return self.to_export_job_list_dto(self.repository.list_export_jobs(filters))

    def list_export_job_alert_events(
        self,
        *,
        request: Request,
        job_id: str | None,
        export_type: str | None,
        file_format: str | None,
        error_code: str | None,
        acknowledged: str | None,
        closed: str | None,
        date_from: str | None,
        date_to: str | None,
        page: int,
        page_size: int,
    ) -> AdminExportJobAlertEventListDTO:
        self.admin_auth_service.current_session_admin(request)
        normalized_date_from = self.normalize_optional_alert_date(date_from)
        normalized_date_to = self.normalize_optional_alert_date(date_to)
        if (
            normalized_date_from is not None
            and normalized_date_to is not None
            and normalized_date_from > normalized_date_to
        ):
            self.raise_invalid_alert_event_filters()
        filters = AdminExportJobAlertEventListFilter(
            job_id=self.normalize_optional_alert_text(job_id, max_length=64),
            export_type=self.normalize_optional_alert_export_type(export_type),
            file_format=self.normalize_optional_alert_file_format(file_format),
            error_code=self.normalize_optional_alert_text(
                error_code,
                max_length=ADMIN_EXPORT_JOB_ERROR_CODE_MAX_LENGTH,
                uppercase=True,
            ),
            acknowledged=self.normalize_optional_alert_bool(acknowledged),
            closed=self.normalize_optional_alert_bool(closed),
            date_from=normalized_date_from,
            date_to=normalized_date_to,
            page=page,
            page_size=page_size,
        )
        return self.to_export_job_alert_event_list_dto(self.repository.list_export_job_alert_events(filters))

    def summarize_export_job_alert_events(
        self,
        *,
        request: Request,
        export_type: str | None,
        file_format: str | None,
        closed: str | None,
        date_from: str | None,
        date_to: str | None,
    ) -> AdminExportJobAlertEventSummaryDTO:
        self.admin_auth_service.current_session_admin(request)
        normalized_date_from = self.normalize_optional_alert_date(date_from)
        normalized_date_to = self.normalize_optional_alert_date(date_to)
        if (
            normalized_date_from is not None
            and normalized_date_to is not None
            and normalized_date_from > normalized_date_to
        ):
            self.raise_invalid_alert_event_filters()
        record = self.repository.summarize_export_job_alert_events(
            AdminExportJobAlertEventSummaryFilter(
                export_type=self.normalize_optional_alert_export_type(export_type),
                file_format=self.normalize_optional_alert_file_format(file_format),
                closed=self.normalize_optional_alert_bool(closed),
                date_from=normalized_date_from,
                date_to=normalized_date_to,
            )
        )
        return self.to_export_job_alert_event_summary_dto(record)

    def acknowledge_export_job_alert_event(
        self,
        *,
        event_id: int,
        payload: AdminExportJobAlertEventAcknowledgeRequest,
        request: Request,
    ) -> AdminExportJobAlertEventDTO:
        session_record = self.admin_auth_service.current_session_admin(request)
        note = self.normalize_alert_acknowledge_note(payload.note)
        record = self.repository.acknowledge_export_job_alert_event(
            AdminExportJobAlertEventAcknowledgeRecord(
                event_id=event_id,
                acknowledged_by_admin_user_id=session_record.admin.id,
                acknowledged_by_username=session_record.admin.username,
                acknowledged_by_display_name=session_record.admin.display_name,
                acknowledge_note=note,
            )
        )
        if record is None:
            raise AppError(404, "ADMIN_EXPORT_JOB_ALERT_EVENT_NOT_FOUND", "导出任务告警事件不存在")
        return self.to_export_job_alert_event_dto(record)

    def batch_acknowledge_export_job_alert_events(
        self,
        *,
        payload: AdminExportJobAlertEventBatchAcknowledgeRequest,
        request: Request,
    ) -> AdminExportJobAlertEventBatchAcknowledgeDTO:
        session_record = self.admin_auth_service.current_session_admin(request)
        note = self.normalize_alert_acknowledge_note(payload.note)
        results: list[AdminExportJobAlertEventBatchAcknowledgeResultDTO] = []
        for event_id in payload.event_ids:
            record = self.repository.acknowledge_export_job_alert_event(
                AdminExportJobAlertEventAcknowledgeRecord(
                    event_id=event_id,
                    acknowledged_by_admin_user_id=session_record.admin.id,
                    acknowledged_by_username=session_record.admin.username,
                    acknowledged_by_display_name=session_record.admin.display_name,
                    acknowledge_note=note,
                )
            )
            if record is None:
                results.append(
                    AdminExportJobAlertEventBatchAcknowledgeResultDTO(
                        eventId=event_id,
                        acknowledged=False,
                        code="ADMIN_EXPORT_JOB_ALERT_EVENT_NOT_FOUND",
                        message="导出任务告警事件不存在",
                    )
                )
                continue
            results.append(AdminExportJobAlertEventBatchAcknowledgeResultDTO(eventId=event_id, acknowledged=True))
        success_count = sum(1 for result in results if result.acknowledged)
        return AdminExportJobAlertEventBatchAcknowledgeDTO(
            totalCount=len(results),
            successCount=success_count,
            failureCount=len(results) - success_count,
            results=results,
        )

    def close_export_job_alert_event(
        self,
        *,
        event_id: int,
        payload: AdminExportJobAlertEventCloseRequest,
        request: Request,
    ) -> AdminExportJobAlertEventDTO:
        session_record = self.admin_auth_service.current_session_admin(request)
        note = self.normalize_alert_close_note(payload.note)
        record = self.repository.close_export_job_alert_event(
            AdminExportJobAlertEventCloseRecord(
                event_id=event_id,
                closed_by_admin_user_id=session_record.admin.id,
                closed_by_username=session_record.admin.username,
                closed_by_display_name=session_record.admin.display_name,
                close_note=note,
            )
        )
        if record is None:
            raise AppError(404, "ADMIN_EXPORT_JOB_ALERT_EVENT_NOT_FOUND", "导出任务告警事件不存在")
        return self.to_export_job_alert_event_dto(record)

    def batch_close_export_job_alert_events(
        self,
        *,
        payload: AdminExportJobAlertEventBatchCloseRequest,
        request: Request,
    ) -> AdminExportJobAlertEventBatchCloseDTO:
        session_record = self.admin_auth_service.current_session_admin(request)
        note = self.normalize_alert_close_note(payload.note)
        results: list[AdminExportJobAlertEventBatchCloseResultDTO] = []
        for event_id in payload.event_ids:
            record = self.repository.close_export_job_alert_event(
                AdminExportJobAlertEventCloseRecord(
                    event_id=event_id,
                    closed_by_admin_user_id=session_record.admin.id,
                    closed_by_username=session_record.admin.username,
                    closed_by_display_name=session_record.admin.display_name,
                    close_note=note,
                )
            )
            if record is None:
                results.append(
                    AdminExportJobAlertEventBatchCloseResultDTO(
                        eventId=event_id,
                        closed=False,
                        code="ADMIN_EXPORT_JOB_ALERT_EVENT_NOT_FOUND",
                        message="导出任务告警事件不存在",
                    )
                )
                continue
            results.append(AdminExportJobAlertEventBatchCloseResultDTO(eventId=event_id, closed=True))
        success_count = sum(1 for result in results if result.closed)
        return AdminExportJobAlertEventBatchCloseDTO(
            totalCount=len(results),
            successCount=success_count,
            failureCount=len(results) - success_count,
            results=results,
        )

    def reopen_export_job_alert_event(self, *, event_id: int, request: Request) -> AdminExportJobAlertEventDTO:
        self.admin_auth_service.current_session_admin(request)
        record = self.repository.reopen_export_job_alert_event(event_id)
        if record is None:
            raise AppError(404, "ADMIN_EXPORT_JOB_ALERT_EVENT_NOT_FOUND", "导出任务告警事件不存在")
        return self.to_export_job_alert_event_dto(record)

    def delete_export_job_alert_event(self, *, event_id: int, request: Request) -> AdminExportJobAlertEventDeleteDTO:
        self.admin_auth_service.current_session_admin(request)
        result = self.repository.delete_closed_export_job_alert_event(event_id)
        if not result.found:
            raise AppError(404, "ADMIN_EXPORT_JOB_ALERT_EVENT_NOT_FOUND", "导出任务告警事件不存在")
        if not result.deleted:
            raise AppError(
                409,
                ADMIN_EXPORT_JOB_ALERT_EVENT_DELETE_NOT_ALLOWED_ERROR_CODE,
                "只有已关闭的导出任务告警事件可以删除",
            )
        return AdminExportJobAlertEventDeleteDTO(eventId=event_id, deleted=True)

    def batch_delete_export_job_alert_events(
        self,
        *,
        payload: AdminExportJobAlertEventBatchDeleteRequest,
        request: Request,
    ) -> AdminExportJobAlertEventBatchDeleteDTO:
        self.admin_auth_service.current_session_admin(request)
        results: list[AdminExportJobAlertEventBatchDeleteResultDTO] = []
        for event_id in payload.event_ids:
            result = self.repository.delete_closed_export_job_alert_event(event_id)
            if not result.found:
                results.append(
                    AdminExportJobAlertEventBatchDeleteResultDTO(
                        eventId=event_id,
                        deleted=False,
                        code="ADMIN_EXPORT_JOB_ALERT_EVENT_NOT_FOUND",
                        message="导出任务告警事件不存在",
                    )
                )
                continue
            if not result.deleted:
                results.append(
                    AdminExportJobAlertEventBatchDeleteResultDTO(
                        eventId=event_id,
                        deleted=False,
                        code=ADMIN_EXPORT_JOB_ALERT_EVENT_DELETE_NOT_ALLOWED_ERROR_CODE,
                        message="只有已关闭的导出任务告警事件可以删除",
                    )
                )
                continue
            results.append(AdminExportJobAlertEventBatchDeleteResultDTO(eventId=event_id, deleted=True))
        success_count = sum(1 for result in results if result.deleted)
        return AdminExportJobAlertEventBatchDeleteDTO(
            totalCount=len(results),
            successCount=success_count,
            failureCount=len(results) - success_count,
            results=results,
        )

    def get_export_job(self, job_id: str, request: Request) -> AdminExportJobDTO:
        self.admin_auth_service.current_session_admin(request)
        job = self.repository.get_export_job(job_id.strip())
        if job is None:
            raise AppError(404, "ADMIN_EXPORT_JOB_NOT_FOUND", "导出任务不存在")
        return self.to_export_job_dto(job)

    def download_export_job_file(
        self,
        job_id: str,
        request: Request,
        storage: AdminExportFileStorage,
    ) -> AdminExportJobDownloadFile:
        self.admin_auth_service.current_session_admin(request)
        file_record = self.repository.get_export_job_file(job_id.strip())
        if file_record is None:
            raise AppError(409, "ADMIN_EXPORT_JOB_FILE_NOT_READY", "导出文件尚未生成")
        return AdminExportJobDownloadFile(
            content=storage.read_file(file_record.storage_key),
            media_type=self.export_file_media_type(file_record),
            content_disposition=self.content_disposition(file_record.file_name),
        )

    def cleanup_succeeded_export_job_files(
        self,
        *,
        finished_before: Any,
        limit: int,
        storage: AdminExportFileStorage,
    ) -> AdminExportJobCleanupResult:
        if not isinstance(finished_before, datetime):
            raise AppError(422, "ADMIN_EXPORT_JOB_CLEANUP_INPUT_INVALID", "导出文件清理输入不合法")
        normalized_limit = self.normalize_cleanup_limit(limit)
        candidates = self.repository.list_succeeded_export_job_files_finished_before(
            finished_before,
            limit=normalized_limit,
        )
        return self.cleanup_export_job_file_candidates(candidates, storage)

    def cleanup_export_job_file_candidates(
        self,
        candidates: list[AdminExportJobCleanupFileRecord],
        storage: AdminExportFileStorage,
    ) -> AdminExportJobCleanupResult:
        files_deleted = 0
        files_missing = 0
        metadata_cleared = 0
        skipped = 0

        for candidate in candidates:
            try:
                deleted = storage.delete_file(candidate.storage_key)
            except AppError:
                skipped += 1
                continue
            if deleted:
                files_deleted += 1
            else:
                files_missing += 1
            if self.repository.clear_export_job_file_metadata(candidate.job_id, storage_key=candidate.storage_key):
                metadata_cleared += 1
            else:
                skipped += 1

        return AdminExportJobCleanupResult(
            scanned=len(candidates),
            files_deleted=files_deleted,
            files_missing=files_missing,
            metadata_cleared=metadata_cleared,
            skipped=skipped,
        )

    @staticmethod
    def normalize_cleanup_limit(limit: int) -> int:
        if not isinstance(limit, int) or limit < 1 or limit > ADMIN_EXPORT_JOB_CLEANUP_LIMIT_MAX:
            raise AppError(422, "ADMIN_EXPORT_JOB_CLEANUP_INPUT_INVALID", "导出文件清理输入不合法")
        return limit

    @staticmethod
    def to_export_job_request_id(request_id: str | None) -> str | None:
        if not request_id:
            return None
        return request_id[:64]

    @staticmethod
    def normalize_job_id(job_id: str) -> str:
        if not isinstance(job_id, str):
            raise AppError(422, "ADMIN_EXPORT_JOB_WORKER_INPUT_INVALID", "导出任务 worker 输入不合法")
        normalized = job_id.strip()
        if not normalized or len(normalized) > 64:
            raise AppError(422, "ADMIN_EXPORT_JOB_WORKER_INPUT_INVALID", "导出任务 worker 输入不合法")
        return normalized

    @staticmethod
    def normalize_required_text(value: str, *, max_length: int) -> str:
        if not isinstance(value, str):
            raise AppError(422, "ADMIN_EXPORT_JOB_WORKER_INPUT_INVALID", "导出任务 worker 输入不合法")
        normalized = value.strip()
        if not normalized or len(normalized) > max_length:
            raise AppError(422, "ADMIN_EXPORT_JOB_WORKER_INPUT_INVALID", "导出任务 worker 输入不合法")
        return normalized

    @staticmethod
    def normalize_export_type(export_type: str | None) -> str | None:
        if export_type is None or not export_type.strip():
            return None
        normalized = export_type.strip().upper()
        if normalized not in ADMIN_EXPORT_JOB_TYPE_OPTIONS:
            raise AppError(422, "ADMIN_EXPORT_JOB_TYPE_INVALID", "导出任务类型不合法")
        return normalized

    @staticmethod
    def normalize_status(status: str | None) -> str | None:
        if status is None or not status.strip():
            return None
        normalized = status.strip().upper()
        if normalized not in ADMIN_EXPORT_JOB_STATUS_OPTIONS:
            raise AppError(422, "ADMIN_EXPORT_JOB_STATUS_INVALID", "导出任务状态不合法")
        return normalized

    @staticmethod
    def normalize_file_format(file_format: str | None) -> str | None:
        if file_format is None or not file_format.strip():
            return None
        normalized = file_format.strip().upper()
        if normalized not in ADMIN_EXPORT_JOB_FILE_FORMAT_OPTIONS:
            raise AppError(422, ADMIN_EXPORT_JOB_FILE_FORMAT_INVALID_ERROR_CODE, "导出任务文件格式不合法")
        return normalized

    @staticmethod
    def normalize_optional_alert_text(
        value: str | None,
        *,
        max_length: int,
        uppercase: bool = False,
    ) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise AppError(
                422,
                ADMIN_EXPORT_JOB_ALERT_EVENT_FILTER_INVALID_ERROR_CODE,
                "导出任务告警事件筛选条件不合法",
            )
        normalized = value.strip()
        if not normalized:
            return None
        if len(normalized) > max_length:
            raise AppError(
                422,
                ADMIN_EXPORT_JOB_ALERT_EVENT_FILTER_INVALID_ERROR_CODE,
                "导出任务告警事件筛选条件不合法",
            )
        return normalized.upper() if uppercase else normalized

    @staticmethod
    def normalize_optional_alert_export_type(value: str | None) -> str | None:
        normalized = AdminExportJobService.normalize_optional_alert_text(value, max_length=64, uppercase=True)
        if normalized is None:
            return None
        if normalized not in ADMIN_EXPORT_JOB_TYPE_OPTIONS:
            AdminExportJobService.raise_invalid_alert_event_filters()
        return normalized

    @staticmethod
    def normalize_optional_alert_file_format(value: str | None) -> str | None:
        normalized = AdminExportJobService.normalize_optional_alert_text(value, max_length=16, uppercase=True)
        if normalized is None:
            return None
        if normalized not in ADMIN_EXPORT_JOB_FILE_FORMAT_OPTIONS:
            AdminExportJobService.raise_invalid_alert_event_filters()
        return normalized

    @staticmethod
    def normalize_optional_alert_bool(value: str | None) -> bool | None:
        if value is None:
            return None
        if not isinstance(value, str):
            AdminExportJobService.raise_invalid_alert_event_filters()
        normalized = value.strip().lower()
        if not normalized:
            return None
        if normalized == "true":
            return True
        if normalized == "false":
            return False
        AdminExportJobService.raise_invalid_alert_event_filters()

    @staticmethod
    def normalize_optional_alert_date(value: str | None) -> date | None:
        if value is None:
            return None
        if not isinstance(value, str):
            AdminExportJobService.raise_invalid_alert_event_filters()
        normalized = value.strip()
        if not normalized:
            return None
        if len(normalized) != 10 or normalized[4] != "-" or normalized[7] != "-":
            AdminExportJobService.raise_invalid_alert_event_filters()
        try:
            return date.fromisoformat(normalized)
        except ValueError as exc:
            raise AppError(
                422,
                ADMIN_EXPORT_JOB_ALERT_EVENT_FILTER_INVALID_ERROR_CODE,
                "导出任务告警事件筛选条件不合法",
            ) from exc

    @staticmethod
    def raise_invalid_alert_event_filters() -> None:
        raise AppError(
            422,
            ADMIN_EXPORT_JOB_ALERT_EVENT_FILTER_INVALID_ERROR_CODE,
            "导出任务告警事件筛选条件不合法",
        )

    @staticmethod
    def normalize_alert_acknowledge_note(value: str | None) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise AppError(
                422,
                ADMIN_EXPORT_JOB_ALERT_EVENT_ACK_INVALID_ERROR_CODE,
                "导出任务告警事件确认内容不合法",
            )
        normalized = value.strip()
        if not normalized:
            return None
        if len(normalized) > ADMIN_EXPORT_JOB_ALERT_EVENT_ACK_NOTE_MAX_LENGTH:
            raise AppError(
                422,
                ADMIN_EXPORT_JOB_ALERT_EVENT_ACK_INVALID_ERROR_CODE,
                "导出任务告警事件确认内容不合法",
            )
        return normalized

    @staticmethod
    def normalize_alert_close_note(value: str | None) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise AppError(
                422,
                ADMIN_EXPORT_JOB_ALERT_EVENT_CLOSE_INVALID_ERROR_CODE,
                "导出任务告警事件关闭内容不合法",
            )
        normalized = value.strip()
        if not normalized:
            return None
        if len(normalized) > ADMIN_EXPORT_JOB_ALERT_EVENT_ACK_NOTE_MAX_LENGTH:
            raise AppError(
                422,
                ADMIN_EXPORT_JOB_ALERT_EVENT_CLOSE_INVALID_ERROR_CODE,
                "导出任务告警事件关闭内容不合法",
            )
        return normalized

    @classmethod
    def normalize_filters(cls, export_type: str, filters: dict[str, Any]) -> dict[str, Any]:
        allowed_fields = ADMIN_EXPORT_JOB_FILTER_FIELDS[export_type]
        unknown_fields = set(filters) - allowed_fields
        if unknown_fields:
            cls.raise_invalid_filters()

        normalized: dict[str, Any] = {}
        for key in ("dateFrom", "dateTo"):
            if key in filters:
                normalized[key] = cls.normalize_filter_date(filters[key]).isoformat()

        if "dateFrom" in normalized and "dateTo" in normalized and normalized["dateFrom"] > normalized["dateTo"]:
            cls.raise_invalid_filters()

        for key in ("ticketCode", "orderNo", "operatorUsername", "reason"):
            if key in filters:
                value = cls.normalize_text_filter(filters[key], key)
                if value is not None:
                    normalized[key] = value

        if "failureCode" in filters:
            normalized["failureCode"] = cls.normalize_failure_code(filters["failureCode"])

        if "refundType" in filters:
            normalized["refundType"] = cls.normalize_refund_type(filters["refundType"])

        if "includeEmpty" in filters:
            normalized["includeEmpty"] = cls.normalize_include_empty(filters["includeEmpty"])

        return normalized

    @staticmethod
    def normalize_filter_date(value: Any) -> date:
        if not isinstance(value, str):
            AdminExportJobService.raise_invalid_filters()
        if len(value) != 10 or value[4] != "-" or value[7] != "-":
            AdminExportJobService.raise_invalid_filters()
        try:
            return date.fromisoformat(value)
        except ValueError as exc:
            raise AppError(422, "ADMIN_EXPORT_JOB_FILTERS_INVALID", "导出任务筛选条件不合法") from exc

    @staticmethod
    def normalize_text_filter(value: Any, key: str) -> str | None:
        if not isinstance(value, str):
            AdminExportJobService.raise_invalid_filters()
        normalized = value.strip()
        if not normalized:
            return None
        if len(normalized) > ADMIN_EXPORT_JOB_TEXT_FILTER_MAX_LENGTHS[key]:
            AdminExportJobService.raise_invalid_filters()
        return normalized

    @staticmethod
    def normalize_failure_code(value: Any) -> str:
        normalized = AdminExportJobService.normalize_text_filter(value, "failureCode")
        if normalized is None:
            AdminExportJobService.raise_invalid_filters()
        normalized = normalized.upper()
        if normalized not in ADMIN_EXPORT_JOB_FAILURE_CODE_OPTIONS:
            AdminExportJobService.raise_invalid_filters()
        return normalized

    @staticmethod
    def normalize_refund_type(value: Any) -> str:
        if not isinstance(value, str):
            AdminExportJobService.raise_invalid_filters()
        normalized = value.strip().upper()
        if normalized not in ADMIN_EXPORT_JOB_REFUND_TYPE_OPTIONS:
            AdminExportJobService.raise_invalid_filters()
        return normalized

    @staticmethod
    def normalize_include_empty(value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized == "true":
                return True
            if normalized == "false":
                return False
        AdminExportJobService.raise_invalid_filters()

    @staticmethod
    def raise_invalid_filters() -> None:
        raise AppError(422, "ADMIN_EXPORT_JOB_FILTERS_INVALID", "导出任务筛选条件不合法")

    @staticmethod
    def export_file_media_type(file_record: AdminExportJobFileRecord) -> str:
        if file_record.file_format == "XLSX":
            return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        return "text/csv; charset=utf-8"

    @classmethod
    def content_disposition(cls, file_name: str) -> str:
        normalized = file_name.strip() or "admin-export"
        utf8_filename = cls.header_safe_filename(normalized)
        ascii_fallback = cls.ascii_download_filename(utf8_filename)
        encoded_filename = quote(utf8_filename, safe="")
        return f'attachment; filename="{ascii_fallback}"; filename*=UTF-8\'\'{encoded_filename}'

    @staticmethod
    def header_safe_filename(file_name: str) -> str:
        return "".join(
            "_" if char in {'"', "\\", "\r", "\n"} or ord(char) < 32 or ord(char) == 127 else char
            for char in file_name
        )

    @staticmethod
    def ascii_download_filename(file_name: str) -> str:
        normalized = "".join("_" if ord(char) > 126 else char for char in file_name)
        return normalized.strip(" .") or "admin-export"

    @classmethod
    def to_export_job_list_dto(cls, record: AdminExportJobListRecord) -> AdminExportJobListDTO:
        return AdminExportJobListDTO(
            items=[cls.to_export_job_dto(item) for item in record.items],
            total=record.total,
            page=record.page,
            page_size=record.page_size,
        )

    @classmethod
    def to_public_export_job_list_dto(cls, dto: AdminExportJobListDTO) -> AdminExportJobListDTO:
        return dto.model_copy(
            update={
                "items": [cls.to_public_export_job_dto(item) for item in dto.items],
            }
        )

    @classmethod
    def to_public_export_job_dto(cls, dto: AdminExportJobDTO) -> AdminExportJobDTO:
        return dto.model_copy(update={"filters": cls.redact_public_filters(dto.filters)})

    @classmethod
    def to_export_job_alert_event_list_dto(
        cls,
        record: AdminExportJobAlertEventListRecord,
    ) -> AdminExportJobAlertEventListDTO:
        return AdminExportJobAlertEventListDTO(
            items=[cls.to_export_job_alert_event_dto(item) for item in record.items],
            total=record.total,
            page=record.page,
            page_size=record.page_size,
        )

    @staticmethod
    def to_export_job_alert_event_summary_dto(
        record: AdminExportJobAlertEventSummaryRecord,
    ) -> AdminExportJobAlertEventSummaryDTO:
        return AdminExportJobAlertEventSummaryDTO(
            total=record.total,
            acknowledged=record.acknowledged,
            unacknowledged=record.unacknowledged,
            closed=record.closed,
            open_count=record.open_count,
            by_error_code=[
                AdminExportJobAlertEventSummaryByErrorCodeDTO(
                    error_code=item.error_code,
                    total=item.total,
                    acknowledged=item.acknowledged,
                    unacknowledged=item.unacknowledged,
                    closed=item.closed,
                    open_count=item.open_count,
                )
                for item in record.by_error_code
            ],
        )

    @staticmethod
    def to_export_job_alert_event_dto(record: AdminExportJobAlertEventRecord) -> AdminExportJobAlertEventDTO:
        return AdminExportJobAlertEventDTO(
            event_id=record.event_id,
            job_id=record.job_id,
            export_type=record.export_type,
            file_format=record.file_format,
            error_code=record.error_code,
            error_message=record.error_message,
            alert_source=record.alert_source,
            created_at=record.created_at,
            occurrence_count=record.occurrence_count,
            last_seen_at=record.last_seen_at or record.created_at,
            acknowledged_at=record.acknowledged_at,
            acknowledged_by_username=record.acknowledged_by_username,
            acknowledged_by_display_name=record.acknowledged_by_display_name,
            acknowledge_note=record.acknowledge_note,
            closed_at=record.closed_at,
            closed_by_username=record.closed_by_username,
            closed_by_display_name=record.closed_by_display_name,
            close_note=record.close_note,
        )

    @staticmethod
    def redact_public_filters(filters: dict[str, Any]) -> dict[str, Any]:
        return {
            key: value if key in ADMIN_EXPORT_JOB_PUBLIC_FILTER_FIELDS else ADMIN_EXPORT_JOB_REDACTED_FILTER_VALUE
            for key, value in filters.items()
        }

    @staticmethod
    def to_export_job_dto(record: AdminExportJobRecord) -> AdminExportJobDTO:
        return AdminExportJobDTO(
            job_id=record.job_id,
            export_type=record.export_type,
            file_format=record.file_format,
            filters=record.filters,
            status=record.status,
            request_id=record.request_id,
            requested_by_username=record.requested_by_username,
            requested_by_display_name=record.requested_by_display_name,
            requested_at=record.requested_at,
            started_at=record.started_at,
            finished_at=record.finished_at,
            file_name=record.file_name,
            error_code=record.error_code,
            error_message=record.error_message,
        )


def get_admin_export_job_service(
    repository: AdminExportJobRepository = Depends(get_admin_export_job_repository),
    admin_auth_service: AdminAuthService = Depends(get_admin_auth_service),
) -> AdminExportJobService:
    return AdminExportJobService(repository, admin_auth_service)


def get_admin_export_file_storage() -> AdminExportFileStorage:
    settings = get_settings()
    if settings.admin_export_storage_provider == "local":
        return AdminExportFileStorage(settings.admin_export_storage_dir)
    raise AppError(500, "ADMIN_EXPORT_STORAGE_PROVIDER_UNSUPPORTED", "导出文件存储未配置")


class AdminExportJobWorkerService:
    def __init__(
        self,
        admin_export_job_service: AdminExportJobService,
        admin_report_service: AdminReportService,
        admin_check_in_service: AdminCheckInService,
        admin_refund_service: AdminRefundService,
        storage: AdminExportFileStorage,
    ):
        self.admin_export_job_service = admin_export_job_service
        self.admin_report_service = admin_report_service
        self.admin_check_in_service = admin_check_in_service
        self.admin_refund_service = admin_refund_service
        self.storage = storage

    def process_next_pending_job(self) -> AdminExportJobDTO | None:
        self.admin_export_job_service.recover_stale_running_jobs()
        job = self.admin_export_job_service.claim_next_pending_job()
        if job is None:
            return None

        try:
            return self.process_running_job(job)
        except KeyboardInterrupt:
            self.admin_export_job_service.mark_export_job_failed(
                job.job_id,
                error_code=ADMIN_EXPORT_JOB_WORKER_FAILED_ERROR_CODE,
                error_message="导出任务处理失败",
            )
            raise
        except AppError as exc:
            return self.admin_export_job_service.mark_export_job_failed(
                job.job_id,
                error_code=exc.code,
                error_message=exc.message,
            )
        except Exception:
            return self.admin_export_job_service.mark_export_job_failed(
                job.job_id,
                error_code=ADMIN_EXPORT_JOB_WORKER_FAILED_ERROR_CODE,
                error_message="导出任务处理失败",
                retryable=True,
            )

    def process_running_job(self, job: AdminExportJobDTO) -> AdminExportJobDTO | None:
        if job.export_type == "ORDER_DETAIL" and job.file_format == "XLSX":
            date_from = self.filter_date(job.filters, "dateFrom")
            date_to = self.filter_date(job.filters, "dateTo")
            content = self.admin_report_service.export_order_detail_xlsx_for_worker(date_from, date_to)
            file_name = self.admin_report_service.order_export_xlsx_filename(date_from=date_from, date_to=date_to)
            return self.write_file_and_mark_succeeded(job, file_name=file_name, content=content)

        if job.export_type == "ORDER_DETAIL" and job.file_format == "CSV":
            date_from = self.filter_date(job.filters, "dateFrom")
            date_to = self.filter_date(job.filters, "dateTo")
            csv_text = self.admin_report_service.export_order_detail_csv_for_worker(date_from, date_to)
            content = csv_text.encode("utf-8")
            file_name = self.admin_report_service.order_export_filename(date_from=date_from, date_to=date_to)
            return self.write_file_and_mark_succeeded(job, file_name=file_name, content=content)

        if job.export_type == "CHECK_IN_AUDIT" and job.file_format == "CSV":
            date_from = self.filter_date(job.filters, "dateFrom")
            date_to = self.filter_date(job.filters, "dateTo")
            csv_text = self.admin_check_in_service.export_check_in_audit_logs_csv_for_worker(
                ticket_code=self.filter_text(job.filters, "ticketCode"),
                order_no=self.filter_text(job.filters, "orderNo"),
                operator_username=self.filter_text(job.filters, "operatorUsername"),
                reason=self.filter_text(job.filters, "reason"),
                date_from=date_from,
                date_to=date_to,
            )
            content = csv_text.encode("utf-8")
            file_name = self.admin_check_in_service.check_in_audit_log_export_filename(
                date_from=date_from,
                date_to=date_to,
            )
            return self.write_file_and_mark_succeeded(job, file_name=file_name, content=content)

        if job.export_type == "CHECK_IN_AUDIT" and job.file_format == "XLSX":
            date_from = self.filter_date(job.filters, "dateFrom")
            date_to = self.filter_date(job.filters, "dateTo")
            content = self.admin_check_in_service.export_check_in_audit_logs_xlsx_for_worker(
                ticket_code=self.filter_text(job.filters, "ticketCode"),
                order_no=self.filter_text(job.filters, "orderNo"),
                operator_username=self.filter_text(job.filters, "operatorUsername"),
                reason=self.filter_text(job.filters, "reason"),
                date_from=date_from,
                date_to=date_to,
            )
            file_name = self.admin_check_in_service.check_in_audit_log_export_xlsx_filename(
                date_from=date_from,
                date_to=date_to,
            )
            return self.write_file_and_mark_succeeded(job, file_name=file_name, content=content)

        if job.export_type == "CHECK_IN_FAILURE_AUDIT" and job.file_format == "CSV":
            date_from = self.filter_date(job.filters, "dateFrom")
            date_to = self.filter_date(job.filters, "dateTo")
            csv_text = self.admin_check_in_service.export_check_in_failure_audit_logs_csv_for_worker(
                ticket_code=self.filter_text(job.filters, "ticketCode"),
                failure_code=self.filter_text(job.filters, "failureCode"),
                operator_username=self.filter_text(job.filters, "operatorUsername"),
                date_from=date_from,
                date_to=date_to,
            )
            content = csv_text.encode("utf-8")
            file_name = self.admin_check_in_service.check_in_failure_audit_log_export_filename(
                date_from=date_from,
                date_to=date_to,
            )
            return self.write_file_and_mark_succeeded(job, file_name=file_name, content=content)

        if job.export_type == "CHECK_IN_FAILURE_AUDIT" and job.file_format == "XLSX":
            date_from = self.filter_date(job.filters, "dateFrom")
            date_to = self.filter_date(job.filters, "dateTo")
            content = self.admin_check_in_service.export_check_in_failure_audit_logs_xlsx_for_worker(
                ticket_code=self.filter_text(job.filters, "ticketCode"),
                failure_code=self.filter_text(job.filters, "failureCode"),
                operator_username=self.filter_text(job.filters, "operatorUsername"),
                date_from=date_from,
                date_to=date_to,
            )
            file_name = self.admin_check_in_service.check_in_failure_audit_log_export_xlsx_filename(
                date_from=date_from,
                date_to=date_to,
            )
            return self.write_file_and_mark_succeeded(job, file_name=file_name, content=content)

        if job.export_type == "REFUND_AUDIT" and job.file_format == "CSV":
            date_from = self.filter_date(job.filters, "dateFrom")
            date_to = self.filter_date(job.filters, "dateTo")
            csv_text = self.admin_refund_service.export_refund_audit_logs_csv_for_worker(
                refund_type=self.filter_text(job.filters, "refundType"),
                order_no=self.filter_text(job.filters, "orderNo"),
                operator_username=self.filter_text(job.filters, "operatorUsername"),
                date_from=date_from,
                date_to=date_to,
            )
            content = csv_text.encode("utf-8")
            file_name = self.admin_refund_service.refund_audit_log_export_filename(
                date_from=date_from,
                date_to=date_to,
            )
            return self.write_file_and_mark_succeeded(job, file_name=file_name, content=content)

        if job.export_type == "REFUND_AUDIT" and job.file_format == "XLSX":
            date_from = self.filter_date(job.filters, "dateFrom")
            date_to = self.filter_date(job.filters, "dateTo")
            content = self.admin_refund_service.export_refund_audit_logs_xlsx_for_worker(
                refund_type=self.filter_text(job.filters, "refundType"),
                order_no=self.filter_text(job.filters, "orderNo"),
                operator_username=self.filter_text(job.filters, "operatorUsername"),
                date_from=date_from,
                date_to=date_to,
            )
            file_name = self.admin_refund_service.refund_audit_log_export_xlsx_filename(
                date_from=date_from,
                date_to=date_to,
            )
            return self.write_file_and_mark_succeeded(job, file_name=file_name, content=content)

        if job.export_type == "PAYMENT_RECONCILIATION" and job.file_format == "CSV":
            date_from = self.filter_date(job.filters, "dateFrom")
            date_to = self.filter_date(job.filters, "dateTo")
            csv_text = self.admin_report_service.export_payment_reconciliation_csv_for_worker(date_from, date_to)
            content = csv_text.encode("utf-8")
            file_name = self.admin_report_service.payment_reconciliation_export_filename(
                date_from=date_from,
                date_to=date_to,
            )
            return self.write_file_and_mark_succeeded(job, file_name=file_name, content=content)

        if job.export_type == "PAYMENT_RECONCILIATION" and job.file_format == "XLSX":
            date_from = self.filter_date(job.filters, "dateFrom")
            date_to = self.filter_date(job.filters, "dateTo")
            content = self.admin_report_service.export_payment_reconciliation_xlsx_for_worker(date_from, date_to)
            file_name = self.admin_report_service.payment_reconciliation_export_xlsx_filename(
                date_from=date_from,
                date_to=date_to,
            )
            return self.write_file_and_mark_succeeded(job, file_name=file_name, content=content)

        if job.export_type == "PRODUCT_BREAKDOWN" and job.file_format == "CSV":
            date_from = self.filter_date(job.filters, "dateFrom")
            date_to = self.filter_date(job.filters, "dateTo")
            csv_text = self.admin_report_service.export_product_breakdown_csv_for_worker(date_from, date_to)
            content = csv_text.encode("utf-8")
            file_name = self.admin_report_service.product_breakdown_export_filename(
                date_from=date_from,
                date_to=date_to,
            )
            return self.write_file_and_mark_succeeded(job, file_name=file_name, content=content)

        if job.export_type == "PRODUCT_BREAKDOWN" and job.file_format == "XLSX":
            date_from = self.filter_date(job.filters, "dateFrom")
            date_to = self.filter_date(job.filters, "dateTo")
            content = self.admin_report_service.export_product_breakdown_xlsx_for_worker(date_from, date_to)
            file_name = self.admin_report_service.product_breakdown_export_xlsx_filename(
                date_from=date_from,
                date_to=date_to,
            )
            return self.write_file_and_mark_succeeded(job, file_name=file_name, content=content)

        if job.export_type == "DAILY_TREND" and job.file_format == "CSV":
            date_from = self.filter_date(job.filters, "dateFrom")
            date_to = self.filter_date(job.filters, "dateTo")
            csv_text = self.admin_report_service.export_daily_trend_csv_for_worker(
                date_from,
                date_to,
                include_empty=self.filter_bool(job.filters, "includeEmpty"),
            )
            content = csv_text.encode("utf-8")
            file_name = self.admin_report_service.trend_export_filename("daily", date_from, date_to)
            return self.write_file_and_mark_succeeded(job, file_name=file_name, content=content)

        if job.export_type == "DAILY_TREND" and job.file_format == "XLSX":
            date_from = self.filter_date(job.filters, "dateFrom")
            date_to = self.filter_date(job.filters, "dateTo")
            content = self.admin_report_service.export_daily_trend_xlsx_for_worker(
                date_from,
                date_to,
                include_empty=self.filter_bool(job.filters, "includeEmpty"),
            )
            file_name = self.admin_report_service.trend_export_xlsx_filename("daily", date_from, date_to)
            return self.write_file_and_mark_succeeded(job, file_name=file_name, content=content)

        if job.export_type == "HOURLY_TREND" and job.file_format == "CSV":
            date_from = self.filter_date(job.filters, "dateFrom")
            date_to = self.filter_date(job.filters, "dateTo")
            csv_text = self.admin_report_service.export_hourly_trend_csv_for_worker(
                date_from,
                date_to,
                include_empty=self.filter_bool(job.filters, "includeEmpty"),
            )
            content = csv_text.encode("utf-8")
            file_name = self.admin_report_service.trend_export_filename("hourly", date_from, date_to)
            return self.write_file_and_mark_succeeded(job, file_name=file_name, content=content)

        if job.export_type == "HOURLY_TREND" and job.file_format == "XLSX":
            date_from = self.filter_date(job.filters, "dateFrom")
            date_to = self.filter_date(job.filters, "dateTo")
            content = self.admin_report_service.export_hourly_trend_xlsx_for_worker(
                date_from,
                date_to,
                include_empty=self.filter_bool(job.filters, "includeEmpty"),
            )
            file_name = self.admin_report_service.trend_export_xlsx_filename("hourly", date_from, date_to)
            return self.write_file_and_mark_succeeded(job, file_name=file_name, content=content)

        if job.export_type == "MONTHLY_TREND" and job.file_format == "CSV":
            date_from = self.filter_date(job.filters, "dateFrom")
            date_to = self.filter_date(job.filters, "dateTo")
            csv_text = self.admin_report_service.export_monthly_trend_csv_for_worker(
                date_from,
                date_to,
                include_empty=self.filter_bool(job.filters, "includeEmpty"),
            )
            content = csv_text.encode("utf-8")
            file_name = self.admin_report_service.trend_export_filename("monthly", date_from, date_to)
            return self.write_file_and_mark_succeeded(job, file_name=file_name, content=content)

        if job.export_type == "MONTHLY_TREND" and job.file_format == "XLSX":
            date_from = self.filter_date(job.filters, "dateFrom")
            date_to = self.filter_date(job.filters, "dateTo")
            content = self.admin_report_service.export_monthly_trend_xlsx_for_worker(
                date_from,
                date_to,
                include_empty=self.filter_bool(job.filters, "includeEmpty"),
            )
            file_name = self.admin_report_service.trend_export_xlsx_filename("monthly", date_from, date_to)
            return self.write_file_and_mark_succeeded(job, file_name=file_name, content=content)

        return self.admin_export_job_service.mark_export_job_failed(
            job.job_id,
            error_code=ADMIN_EXPORT_JOB_UNSUPPORTED_ERROR_CODE,
            error_message="暂不支持该异步导出类型或格式",
        )

    def write_file_and_mark_succeeded(
        self,
        job: AdminExportJobDTO,
        *,
        file_name: str,
        content: bytes,
    ) -> AdminExportJobDTO | None:
        storage_key = self.storage_key_for_job(job.job_id, file_name)
        self.storage.write_file(storage_key, content)
        try:
            marked = self.admin_export_job_service.mark_export_job_succeeded(
                job.job_id,
                file_name=file_name,
                storage_key=storage_key,
            )
        except Exception:
            self.delete_generated_file_safely(storage_key)
            raise
        if marked is None:
            self.delete_generated_file_safely(storage_key)
        return marked

    def delete_generated_file_safely(self, storage_key: str) -> None:
        try:
            self.storage.delete_file(storage_key)
        except Exception:
            return

    @staticmethod
    def filter_date(filters: dict[str, Any], key: str) -> date | None:
        value = filters.get(key)
        if value is None:
            return None
        if not isinstance(value, str):
            raise AppError(422, "ADMIN_EXPORT_JOB_FILTERS_INVALID", "导出任务筛选条件不合法")
        return AdminExportJobService.normalize_filter_date(value)

    @staticmethod
    def filter_text(filters: dict[str, Any], key: str) -> str | None:
        value = filters.get(key)
        if value is None:
            return None
        if not isinstance(value, str):
            raise AppError(422, "ADMIN_EXPORT_JOB_FILTERS_INVALID", "导出任务筛选条件不合法")
        return value

    @staticmethod
    def filter_bool(filters: dict[str, Any], key: str) -> bool:
        value = filters.get(key)
        if value is None:
            return False
        if not isinstance(value, bool):
            raise AppError(422, "ADMIN_EXPORT_JOB_FILTERS_INVALID", "导出任务筛选条件不合法")
        return value

    @staticmethod
    def storage_key_for_job(job_id: str, file_name: str) -> str:
        safe_job_id = "".join(char if char.isalnum() or char in {"-", "_"} else "_" for char in job_id)
        safe_file_name = "".join(
            char if char.isalnum() or char in {"-", "_", "."} else "_" for char in file_name
        )
        return f"export-jobs/{safe_job_id}/{safe_file_name}"


def get_admin_export_job_worker_service(
    admin_export_job_service: AdminExportJobService = Depends(get_admin_export_job_service),
    admin_report_service: AdminReportService = Depends(get_admin_report_service),
    admin_check_in_service: AdminCheckInService = Depends(get_admin_check_in_service),
    admin_refund_service: AdminRefundService = Depends(get_admin_refund_service),
    storage: AdminExportFileStorage = Depends(get_admin_export_file_storage),
) -> AdminExportJobWorkerService:
    return AdminExportJobWorkerService(
        admin_export_job_service,
        admin_report_service,
        admin_check_in_service,
        admin_refund_service,
        storage,
    )
