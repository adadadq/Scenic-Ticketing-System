from datetime import date

from fastapi import APIRouter, Depends, Path, Query, Request, Response

from app.core.responses import success_response
from app.core.security import require_double_submit_csrf
from app.schemas.common import ApiSuccessDTO
from app.schemas.orders import (
    AdminPartialRefundDTO,
    AdminPartialRefundRequest,
    AdminRefundAuditLogDTO,
    AdminRefundAuditLogListDTO,
    AdminRefundDTO,
    AdminRefundRequest,
)
from app.services.orders import AdminRefundService, get_admin_refund_service

router = APIRouter(prefix="/api/admin/orders", tags=["admin-refunds"])
refund_logs_router = APIRouter(prefix="/api/admin/refund-logs", tags=["admin-refunds"])
refund_logs_export_router = APIRouter(prefix="/api/admin", tags=["admin-refunds"])


@router.post(
    "/{order_no}/refund",
    response_model=ApiSuccessDTO[AdminRefundDTO],
    response_model_exclude_none=True,
)
def refund_order(
    payload: AdminRefundRequest,
    request: Request,
    order_no: str = Path(min_length=1, max_length=64),
    admin_refund_service: AdminRefundService = Depends(get_admin_refund_service),
) -> dict:
    require_double_submit_csrf(request)
    result = admin_refund_service.refund_order(order_no, payload, request)
    return success_response(request, result.model_dump(by_alias=True, mode="json"))


@router.post(
    "/{order_no}/refund/items",
    response_model=ApiSuccessDTO[AdminPartialRefundDTO],
    response_model_exclude_none=True,
)
def refund_order_items(
    payload: AdminPartialRefundRequest,
    request: Request,
    order_no: str = Path(min_length=1, max_length=64),
    admin_refund_service: AdminRefundService = Depends(get_admin_refund_service),
) -> dict:
    require_double_submit_csrf(request)
    result = admin_refund_service.refund_order_items(order_no, payload, request)
    return success_response(request, result.model_dump(by_alias=True, mode="json"))


@router.get(
    "/{order_no}/refund-logs",
    response_model=ApiSuccessDTO[list[AdminRefundAuditLogDTO]],
)
def list_refund_audit_logs(
    request: Request,
    order_no: str = Path(min_length=1, max_length=64),
    admin_refund_service: AdminRefundService = Depends(get_admin_refund_service),
) -> dict:
    logs = admin_refund_service.list_refund_audit_logs(order_no, request)
    return success_response(request, [log.model_dump(by_alias=True, mode="json") for log in logs])


@refund_logs_router.get(
    "",
    response_model=ApiSuccessDTO[AdminRefundAuditLogListDTO],
)
def list_refund_audit_log_entries(
    request: Request,
    refund_type: str | None = Query(default=None, alias="refundType"),
    order_no: str | None = Query(default=None, alias="orderNo", max_length=64),
    operator_username: str | None = Query(default=None, alias="operatorUsername", max_length=64),
    date_from: date | None = Query(default=None, alias="dateFrom"),
    date_to: date | None = Query(default=None, alias="dateTo"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100, alias="pageSize"),
    admin_refund_service: AdminRefundService = Depends(get_admin_refund_service),
) -> dict:
    logs = admin_refund_service.list_refund_audit_log_entries(
        request=request,
        refund_type=refund_type,
        order_no=order_no,
        operator_username=operator_username,
        date_from=date_from,
        date_to=date_to,
        page=page,
        page_size=page_size,
    )
    return success_response(request, logs.model_dump(by_alias=True, mode="json"))


@refund_logs_export_router.get(
    "/refund-logs.csv",
    response_class=Response,
    responses={
        200: {
            "description": "Admin refund audit log CSV export",
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
def export_refund_audit_logs_csv(
    request: Request,
    refund_type: str | None = Query(default=None, alias="refundType"),
    order_no: str | None = Query(default=None, alias="orderNo", max_length=64),
    operator_username: str | None = Query(default=None, alias="operatorUsername", max_length=64),
    date_from: date | None = Query(default=None, alias="dateFrom"),
    date_to: date | None = Query(default=None, alias="dateTo"),
    admin_refund_service: AdminRefundService = Depends(get_admin_refund_service),
) -> Response:
    csv_text = admin_refund_service.export_refund_audit_logs_csv(
        request=request,
        refund_type=refund_type,
        order_no=order_no,
        operator_username=operator_username,
        date_from=date_from,
        date_to=date_to,
    )
    filename = admin_refund_service.refund_audit_log_export_filename(date_from=date_from, date_to=date_to)
    return Response(
        content=csv_text.encode("utf-8"),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@refund_logs_export_router.get(
    "/refund-logs.xlsx",
    response_class=Response,
    responses={
        200: {
            "description": "Admin refund audit log XLSX export",
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
def export_refund_audit_logs_xlsx(
    request: Request,
    refund_type: str | None = Query(default=None, alias="refundType"),
    order_no: str | None = Query(default=None, alias="orderNo", max_length=64),
    operator_username: str | None = Query(default=None, alias="operatorUsername", max_length=64),
    date_from: date | None = Query(default=None, alias="dateFrom"),
    date_to: date | None = Query(default=None, alias="dateTo"),
    admin_refund_service: AdminRefundService = Depends(get_admin_refund_service),
) -> Response:
    xlsx_bytes = admin_refund_service.export_refund_audit_logs_xlsx(
        request=request,
        refund_type=refund_type,
        order_no=order_no,
        operator_username=operator_username,
        date_from=date_from,
        date_to=date_to,
    )
    filename = admin_refund_service.refund_audit_log_export_xlsx_filename(
        date_from=date_from,
        date_to=date_to,
    )
    return Response(
        content=xlsx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
