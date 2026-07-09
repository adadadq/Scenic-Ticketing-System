from fastapi import APIRouter, Depends, Path, Query, Request, Response

from app.core.responses import success_response
from app.core.security import require_double_submit_csrf
from app.schemas.admin_exports import (
    AdminExportJobAlertEventAcknowledgeRequest,
    AdminExportJobAlertEventBatchAcknowledgeDTO,
    AdminExportJobAlertEventBatchAcknowledgeRequest,
    AdminExportJobAlertEventBatchCloseDTO,
    AdminExportJobAlertEventBatchCloseRequest,
    AdminExportJobAlertEventBatchDeleteDTO,
    AdminExportJobAlertEventBatchDeleteRequest,
    AdminExportJobAlertEventCloseRequest,
    AdminExportJobAlertEventDeleteDTO,
    AdminExportJobAlertEventDTO,
    AdminExportJobAlertEventListDTO,
    AdminExportJobAlertEventSummaryDTO,
    AdminExportJobCreateRequest,
    AdminExportJobDTO,
    AdminExportJobListDTO,
)
from app.schemas.common import ApiSuccessDTO
from app.services.admin_exports import (
    AdminExportFileStorage,
    AdminExportJobService,
    get_admin_export_file_storage,
    get_admin_export_job_service,
)

router = APIRouter(prefix="/api/admin/export-jobs", tags=["admin-export-jobs"])
alert_events_router = APIRouter(
    prefix="/api/admin/export-job-alert-events",
    tags=["admin-export-job-alert-events"],
)


@router.post(
    "",
    response_model=ApiSuccessDTO[AdminExportJobDTO],
    response_model_exclude_none=True,
)
def create_admin_export_job(
    payload: AdminExportJobCreateRequest,
    request: Request,
    admin_export_job_service: AdminExportJobService = Depends(get_admin_export_job_service),
) -> dict:
    require_double_submit_csrf(request)
    job = admin_export_job_service.create_export_job(payload, request)
    job = admin_export_job_service.to_public_export_job_dto(job)
    return success_response(request, job.model_dump(by_alias=True, exclude_none=True, mode="json"))


@router.post(
    "/{job_id}/retry",
    response_model=ApiSuccessDTO[AdminExportJobDTO],
    response_model_exclude_none=True,
)
def retry_admin_export_job(
    request: Request,
    job_id: str = Path(alias="job_id", min_length=1, max_length=64),
    admin_export_job_service: AdminExportJobService = Depends(get_admin_export_job_service),
) -> dict:
    require_double_submit_csrf(request)
    job = admin_export_job_service.retry_failed_export_job(job_id, request)
    job = admin_export_job_service.to_public_export_job_dto(job)
    return success_response(request, job.model_dump(by_alias=True, exclude_none=True, mode="json"))


@router.get(
    "",
    response_model=ApiSuccessDTO[AdminExportJobListDTO],
    response_model_exclude_none=True,
)
def list_admin_export_jobs(
    request: Request,
    export_type: str | None = Query(default=None, alias="exportType"),
    file_format: str | None = Query(default=None, alias="fileFormat"),
    status: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, alias="pageSize", ge=1, le=100),
    admin_export_job_service: AdminExportJobService = Depends(get_admin_export_job_service),
) -> dict:
    jobs = admin_export_job_service.list_export_jobs(
        request=request,
        export_type=export_type,
        file_format=file_format,
        status=status,
        page=page,
        page_size=page_size,
    )
    jobs = admin_export_job_service.to_public_export_job_list_dto(jobs)
    return success_response(request, jobs.model_dump(by_alias=True, exclude_none=True, mode="json"))


@router.get(
    "/{job_id}/download",
    response_class=Response,
    responses={
        200: {
            "description": "Export file download",
            "content": {
                "text/csv; charset=utf-8": {"schema": {"type": "string", "format": "binary"}},
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {
                    "schema": {"type": "string", "format": "binary"},
                },
            },
            "headers": {
                "Content-Disposition": {
                    "schema": {"type": "string"},
                },
            },
        }
    },
)
def download_admin_export_job(
    request: Request,
    job_id: str = Path(alias="job_id", min_length=1, max_length=64),
    admin_export_job_service: AdminExportJobService = Depends(get_admin_export_job_service),
    admin_export_file_storage: AdminExportFileStorage = Depends(get_admin_export_file_storage),
) -> Response:
    download = admin_export_job_service.download_export_job_file(job_id, request, admin_export_file_storage)
    return Response(
        content=download.content,
        media_type=download.media_type,
        headers={"Content-Disposition": download.content_disposition},
    )


@router.get(
    "/{job_id}",
    response_model=ApiSuccessDTO[AdminExportJobDTO],
    response_model_exclude_none=True,
)
def get_admin_export_job(
    request: Request,
    job_id: str = Path(alias="job_id", min_length=1, max_length=64),
    admin_export_job_service: AdminExportJobService = Depends(get_admin_export_job_service),
) -> dict:
    job = admin_export_job_service.get_export_job(job_id, request)
    job = admin_export_job_service.to_public_export_job_dto(job)
    return success_response(request, job.model_dump(by_alias=True, exclude_none=True, mode="json"))


@alert_events_router.get(
    "",
    response_model=ApiSuccessDTO[AdminExportJobAlertEventListDTO],
    response_model_exclude_none=True,
)
def list_admin_export_job_alert_events(
    request: Request,
    job_id: str | None = Query(default=None, alias="jobId", max_length=64),
    export_type: str | None = Query(default=None, alias="exportType"),
    file_format: str | None = Query(default=None, alias="fileFormat"),
    error_code: str | None = Query(default=None, alias="errorCode", max_length=80),
    acknowledged: str | None = Query(default=None),
    closed: str | None = Query(default=None),
    date_from: str | None = Query(default=None, alias="dateFrom"),
    date_to: str | None = Query(default=None, alias="dateTo"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, alias="pageSize", ge=1, le=100),
    admin_export_job_service: AdminExportJobService = Depends(get_admin_export_job_service),
) -> dict:
    events = admin_export_job_service.list_export_job_alert_events(
        request=request,
        job_id=job_id,
        export_type=export_type,
        file_format=file_format,
        error_code=error_code,
        acknowledged=acknowledged,
        closed=closed,
        date_from=date_from,
        date_to=date_to,
        page=page,
        page_size=page_size,
    )
    return success_response(request, events.model_dump(by_alias=True, exclude_none=True, mode="json"))


@alert_events_router.get(
    "/summary",
    response_model=ApiSuccessDTO[AdminExportJobAlertEventSummaryDTO],
    response_model_exclude_none=True,
)
def summarize_admin_export_job_alert_events(
    request: Request,
    export_type: str | None = Query(default=None, alias="exportType"),
    file_format: str | None = Query(default=None, alias="fileFormat"),
    closed: str | None = Query(default=None),
    date_from: str | None = Query(default=None, alias="dateFrom"),
    date_to: str | None = Query(default=None, alias="dateTo"),
    admin_export_job_service: AdminExportJobService = Depends(get_admin_export_job_service),
) -> dict:
    summary = admin_export_job_service.summarize_export_job_alert_events(
        request=request,
        export_type=export_type,
        file_format=file_format,
        closed=closed,
        date_from=date_from,
        date_to=date_to,
    )
    return success_response(request, summary.model_dump(by_alias=True, mode="json"))


@alert_events_router.post(
    "/{event_id}/close",
    response_model=ApiSuccessDTO[AdminExportJobAlertEventDTO],
    response_model_exclude_none=True,
)
def close_admin_export_job_alert_event(
    payload: AdminExportJobAlertEventCloseRequest,
    request: Request,
    event_id: int = Path(alias="event_id", ge=1),
    admin_export_job_service: AdminExportJobService = Depends(get_admin_export_job_service),
) -> dict:
    require_double_submit_csrf(request)
    event = admin_export_job_service.close_export_job_alert_event(
        event_id=event_id,
        payload=payload,
        request=request,
    )
    return success_response(request, event.model_dump(by_alias=True, exclude_none=True, mode="json"))


@alert_events_router.post(
    "/batch-close",
    response_model=ApiSuccessDTO[AdminExportJobAlertEventBatchCloseDTO],
    response_model_exclude_none=True,
)
def batch_close_admin_export_job_alert_events(
    payload: AdminExportJobAlertEventBatchCloseRequest,
    request: Request,
    admin_export_job_service: AdminExportJobService = Depends(get_admin_export_job_service),
) -> dict:
    require_double_submit_csrf(request)
    result = admin_export_job_service.batch_close_export_job_alert_events(payload=payload, request=request)
    return success_response(request, result.model_dump(by_alias=True, exclude_none=True, mode="json"))


@alert_events_router.post(
    "/{event_id}/reopen",
    response_model=ApiSuccessDTO[AdminExportJobAlertEventDTO],
    response_model_exclude_none=True,
)
def reopen_admin_export_job_alert_event(
    request: Request,
    event_id: int = Path(alias="event_id", ge=1),
    admin_export_job_service: AdminExportJobService = Depends(get_admin_export_job_service),
) -> dict:
    require_double_submit_csrf(request)
    event = admin_export_job_service.reopen_export_job_alert_event(event_id=event_id, request=request)
    return success_response(request, event.model_dump(by_alias=True, exclude_none=True, mode="json"))


@alert_events_router.post(
    "/{event_id}/acknowledge",
    response_model=ApiSuccessDTO[AdminExportJobAlertEventDTO],
    response_model_exclude_none=True,
)
def acknowledge_admin_export_job_alert_event(
    payload: AdminExportJobAlertEventAcknowledgeRequest,
    request: Request,
    event_id: int = Path(alias="event_id", ge=1),
    admin_export_job_service: AdminExportJobService = Depends(get_admin_export_job_service),
) -> dict:
    require_double_submit_csrf(request)
    event = admin_export_job_service.acknowledge_export_job_alert_event(
        event_id=event_id,
        payload=payload,
        request=request,
    )
    return success_response(request, event.model_dump(by_alias=True, exclude_none=True, mode="json"))


@alert_events_router.post(
    "/batch-acknowledge",
    response_model=ApiSuccessDTO[AdminExportJobAlertEventBatchAcknowledgeDTO],
    response_model_exclude_none=True,
)
def batch_acknowledge_admin_export_job_alert_events(
    payload: AdminExportJobAlertEventBatchAcknowledgeRequest,
    request: Request,
    admin_export_job_service: AdminExportJobService = Depends(get_admin_export_job_service),
) -> dict:
    require_double_submit_csrf(request)
    result = admin_export_job_service.batch_acknowledge_export_job_alert_events(payload=payload, request=request)
    return success_response(request, result.model_dump(by_alias=True, exclude_none=True, mode="json"))


@alert_events_router.post(
    "/batch-delete",
    response_model=ApiSuccessDTO[AdminExportJobAlertEventBatchDeleteDTO],
    response_model_exclude_none=True,
)
def batch_delete_admin_export_job_alert_events(
    payload: AdminExportJobAlertEventBatchDeleteRequest,
    request: Request,
    admin_export_job_service: AdminExportJobService = Depends(get_admin_export_job_service),
) -> dict:
    require_double_submit_csrf(request)
    result = admin_export_job_service.batch_delete_export_job_alert_events(payload=payload, request=request)
    return success_response(request, result.model_dump(by_alias=True, exclude_none=True, mode="json"))


@alert_events_router.delete(
    "/{event_id}",
    response_model=ApiSuccessDTO[AdminExportJobAlertEventDeleteDTO],
    response_model_exclude_none=True,
)
def delete_admin_export_job_alert_event(
    request: Request,
    event_id: int = Path(alias="event_id", ge=1),
    admin_export_job_service: AdminExportJobService = Depends(get_admin_export_job_service),
) -> dict:
    require_double_submit_csrf(request)
    result = admin_export_job_service.delete_export_job_alert_event(event_id=event_id, request=request)
    return success_response(request, result.model_dump(by_alias=True, mode="json"))
