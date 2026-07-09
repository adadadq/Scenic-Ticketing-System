from datetime import date

from fastapi import APIRouter, Depends, Path, Query, Request, Response

from app.core.responses import success_response
from app.core.security import require_double_submit_csrf
from app.schemas.common import ApiSuccessDTO
from app.schemas.orders import (
    AdminBatchCheckInDTO,
    AdminBatchCheckInRequest,
    AdminBatchUndoCheckInDTO,
    AdminBatchUndoCheckInRequest,
    AdminCheckInFailureAuditLogListDTO,
    AdminCheckInAuditLogDTO,
    AdminCheckInAuditLogListDTO,
    AdminCheckInDTO,
    AdminCheckInRequest,
    AdminUndoCheckInDTO,
    AdminUndoCheckInRequest,
)
from app.services.orders import AdminCheckInService, get_admin_check_in_service

router = APIRouter(prefix="/api/admin/check-ins", tags=["admin-check-ins"])
check_in_logs_router = APIRouter(prefix="/api/admin/check-in-logs", tags=["admin-check-ins"])
check_in_failure_logs_router = APIRouter(prefix="/api/admin/check-in-failure-logs", tags=["admin-check-ins"])


@router.post(
    "",
    response_model=ApiSuccessDTO[AdminCheckInDTO],
    response_model_exclude_none=True,
)
def check_in_ticket(
    payload: AdminCheckInRequest,
    request: Request,
    admin_check_in_service: AdminCheckInService = Depends(get_admin_check_in_service),
) -> dict:
    require_double_submit_csrf(request)
    result = admin_check_in_service.check_in_ticket(payload, request)
    return success_response(request, result.model_dump(by_alias=True, exclude_none=True, mode="json"))


@router.post(
    "/batch",
    response_model=ApiSuccessDTO[AdminBatchCheckInDTO],
    response_model_exclude_none=True,
)
def check_in_tickets_batch(
    payload: AdminBatchCheckInRequest,
    request: Request,
    admin_check_in_service: AdminCheckInService = Depends(get_admin_check_in_service),
) -> dict:
    require_double_submit_csrf(request)
    result = admin_check_in_service.check_in_tickets_batch(payload, request)
    return success_response(request, result.model_dump(by_alias=True, exclude_none=True, mode="json"))


@router.post(
    "/batch/undo",
    response_model=ApiSuccessDTO[AdminBatchUndoCheckInDTO],
    response_model_exclude_none=True,
)
def undo_check_in_tickets_batch(
    payload: AdminBatchUndoCheckInRequest,
    request: Request,
    admin_check_in_service: AdminCheckInService = Depends(get_admin_check_in_service),
) -> dict:
    require_double_submit_csrf(request)
    result = admin_check_in_service.undo_check_in_tickets_batch(payload, request)
    return success_response(request, result.model_dump(by_alias=True, mode="json"))


@router.post(
    "/{ticket_code}/undo",
    response_model=ApiSuccessDTO[AdminUndoCheckInDTO],
    response_model_exclude_none=True,
)
def undo_check_in_ticket(
    request: Request,
    ticket_code: str = Path(min_length=1, max_length=64),
    payload: AdminUndoCheckInRequest | None = None,
    admin_check_in_service: AdminCheckInService = Depends(get_admin_check_in_service),
) -> dict:
    require_double_submit_csrf(request)
    result = admin_check_in_service.undo_check_in_ticket(ticket_code, payload, request)
    return success_response(request, result.model_dump(by_alias=True, mode="json"))


@router.get(
    "/{ticket_code}/logs",
    response_model=ApiSuccessDTO[list[AdminCheckInAuditLogDTO]],
    response_model_exclude_none=True,
)
def list_check_in_audit_logs(
    request: Request,
    ticket_code: str = Path(min_length=1, max_length=64),
    admin_check_in_service: AdminCheckInService = Depends(get_admin_check_in_service),
) -> dict:
    logs = admin_check_in_service.list_check_in_audit_logs(ticket_code, request)
    return success_response(request, [log.model_dump(by_alias=True, mode="json") for log in logs])


@check_in_logs_router.get(
    "",
    response_model=ApiSuccessDTO[AdminCheckInAuditLogListDTO],
    response_model_exclude_none=True,
)
def list_check_in_audit_log_entries(
    request: Request,
    ticket_code: str | None = Query(default=None, alias="ticketCode", max_length=64),
    order_no: str | None = Query(default=None, alias="orderNo", max_length=64),
    operator_username: str | None = Query(default=None, alias="operatorUsername", max_length=64),
    reason: str | None = Query(default=None, max_length=100),
    date_from: date | None = Query(default=None, alias="dateFrom"),
    date_to: date | None = Query(default=None, alias="dateTo"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100, alias="pageSize"),
    admin_check_in_service: AdminCheckInService = Depends(get_admin_check_in_service),
) -> dict:
    logs = admin_check_in_service.list_check_in_audit_log_entries(
        request=request,
        ticket_code=ticket_code,
        order_no=order_no,
        operator_username=operator_username,
        reason=reason,
        date_from=date_from,
        date_to=date_to,
        page=page,
        page_size=page_size,
    )
    return success_response(request, logs.model_dump(by_alias=True, mode="json"))


@check_in_failure_logs_router.get(
    "",
    response_model=ApiSuccessDTO[AdminCheckInFailureAuditLogListDTO],
    response_model_exclude_none=True,
)
def list_check_in_failure_audit_log_entries(
    request: Request,
    ticket_code: str | None = Query(default=None, alias="ticketCode", max_length=64),
    failure_code: str | None = Query(default=None, alias="failureCode", max_length=40),
    operator_username: str | None = Query(default=None, alias="operatorUsername", max_length=64),
    date_from: date | None = Query(default=None, alias="dateFrom"),
    date_to: date | None = Query(default=None, alias="dateTo"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100, alias="pageSize"),
    admin_check_in_service: AdminCheckInService = Depends(get_admin_check_in_service),
) -> dict:
    logs = admin_check_in_service.list_check_in_failure_audit_log_entries(
        request=request,
        ticket_code=ticket_code,
        failure_code=failure_code,
        operator_username=operator_username,
        date_from=date_from,
        date_to=date_to,
        page=page,
        page_size=page_size,
    )
    return success_response(request, logs.model_dump(by_alias=True, mode="json"))


@check_in_failure_logs_router.get(
    ".csv",
    response_class=Response,
    responses={
        200: {
            "description": "Admin check-in failure audit log CSV export",
            "content": {
                "text/csv": {
                    "schema": {
                        "type": "string",
                        "format": "binary",
                    }
                }
            },
        }
    },
)
def export_check_in_failure_audit_logs_csv(
    request: Request,
    ticket_code: str | None = Query(default=None, alias="ticketCode", max_length=64),
    failure_code: str | None = Query(default=None, alias="failureCode", max_length=40),
    operator_username: str | None = Query(default=None, alias="operatorUsername", max_length=64),
    date_from: date | None = Query(default=None, alias="dateFrom"),
    date_to: date | None = Query(default=None, alias="dateTo"),
    admin_check_in_service: AdminCheckInService = Depends(get_admin_check_in_service),
) -> Response:
    csv_text = admin_check_in_service.export_check_in_failure_audit_logs_csv(
        request=request,
        ticket_code=ticket_code,
        failure_code=failure_code,
        operator_username=operator_username,
        date_from=date_from,
        date_to=date_to,
    )
    filename = admin_check_in_service.check_in_failure_audit_log_export_filename(
        date_from=date_from,
        date_to=date_to,
    )
    return Response(
        content=csv_text.encode("utf-8"),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@check_in_failure_logs_router.get(
    ".xlsx",
    response_class=Response,
    responses={
        200: {
            "description": "Admin check-in failure audit log XLSX export",
            "headers": {
                "Content-Disposition": {
                    "description": "Attachment filename for the XLSX export",
                    "schema": {"type": "string"},
                }
            },
            "content": {
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {
                    "schema": {
                        "type": "string",
                        "format": "binary",
                    }
                }
            },
        }
    },
)
def export_check_in_failure_audit_logs_xlsx(
    request: Request,
    ticket_code: str | None = Query(default=None, alias="ticketCode", max_length=64),
    failure_code: str | None = Query(default=None, alias="failureCode", max_length=40),
    operator_username: str | None = Query(default=None, alias="operatorUsername", max_length=64),
    date_from: date | None = Query(default=None, alias="dateFrom"),
    date_to: date | None = Query(default=None, alias="dateTo"),
    admin_check_in_service: AdminCheckInService = Depends(get_admin_check_in_service),
) -> Response:
    xlsx_bytes = admin_check_in_service.export_check_in_failure_audit_logs_xlsx(
        request=request,
        ticket_code=ticket_code,
        failure_code=failure_code,
        operator_username=operator_username,
        date_from=date_from,
        date_to=date_to,
    )
    filename = admin_check_in_service.check_in_failure_audit_log_export_xlsx_filename(
        date_from=date_from,
        date_to=date_to,
    )
    return Response(
        content=xlsx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@check_in_logs_router.get(
    ".csv",
    response_class=Response,
    responses={
        200: {
            "description": "Admin check-in audit log CSV export",
            "content": {
                "text/csv": {
                    "schema": {
                        "type": "string",
                        "format": "binary",
                    }
                }
            },
        }
    },
)
def export_check_in_audit_logs_csv(
    request: Request,
    ticket_code: str | None = Query(default=None, alias="ticketCode", max_length=64),
    order_no: str | None = Query(default=None, alias="orderNo", max_length=64),
    operator_username: str | None = Query(default=None, alias="operatorUsername", max_length=64),
    reason: str | None = Query(default=None, max_length=100),
    date_from: date | None = Query(default=None, alias="dateFrom"),
    date_to: date | None = Query(default=None, alias="dateTo"),
    admin_check_in_service: AdminCheckInService = Depends(get_admin_check_in_service),
) -> Response:
    csv_text = admin_check_in_service.export_check_in_audit_logs_csv(
        request=request,
        ticket_code=ticket_code,
        order_no=order_no,
        operator_username=operator_username,
        reason=reason,
        date_from=date_from,
        date_to=date_to,
    )
    filename = admin_check_in_service.check_in_audit_log_export_filename(date_from=date_from, date_to=date_to)
    return Response(
        content=csv_text.encode("utf-8"),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@check_in_logs_router.get(
    ".xlsx",
    response_class=Response,
    responses={
        200: {
            "description": "Admin check-in audit log XLSX export",
            "headers": {
                "Content-Disposition": {
                    "description": "Attachment filename for the XLSX export",
                    "schema": {"type": "string"},
                }
            },
            "content": {
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {
                    "schema": {
                        "type": "string",
                        "format": "binary",
                    }
                }
            },
        }
    },
)
def export_check_in_audit_logs_xlsx(
    request: Request,
    ticket_code: str | None = Query(default=None, alias="ticketCode", max_length=64),
    order_no: str | None = Query(default=None, alias="orderNo", max_length=64),
    operator_username: str | None = Query(default=None, alias="operatorUsername", max_length=64),
    reason: str | None = Query(default=None, max_length=100),
    date_from: date | None = Query(default=None, alias="dateFrom"),
    date_to: date | None = Query(default=None, alias="dateTo"),
    admin_check_in_service: AdminCheckInService = Depends(get_admin_check_in_service),
) -> Response:
    xlsx_bytes = admin_check_in_service.export_check_in_audit_logs_xlsx(
        request=request,
        ticket_code=ticket_code,
        order_no=order_no,
        operator_username=operator_username,
        reason=reason,
        date_from=date_from,
        date_to=date_to,
    )
    filename = admin_check_in_service.check_in_audit_log_export_xlsx_filename(
        date_from=date_from,
        date_to=date_to,
    )
    return Response(
        content=xlsx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
