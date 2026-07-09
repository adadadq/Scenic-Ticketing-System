from fastapi import APIRouter, Depends, Header, Query, Request

from app.core.errors import AppError
from app.core.responses import success_response
from app.core.security import require_double_submit_csrf
from app.schemas.common import ApiSuccessDTO
from app.schemas.orders import OrderCreateRequest, OrderMeDTO
from app.services.orders import OrderService, get_order_service

router = APIRouter(tags=["orders"])


@router.post(
    "/api/orders",
    response_model=ApiSuccessDTO[OrderMeDTO],
    response_model_exclude_none=True,
)
def create_order(
    payload: OrderCreateRequest,
    request: Request,
    order_service: OrderService = Depends(get_order_service),
) -> dict:
    require_double_submit_csrf(request)
    order = order_service.create_order(payload, request)
    return success_response(request, order.model_dump(by_alias=True, exclude_none=True, mode="json"))


@router.get(
    "/api/me/orders",
    response_model=ApiSuccessDTO[list[OrderMeDTO]],
    response_model_exclude_none=True,
)
def list_my_orders(
    request: Request,
    status: str | None = Query(default=None),
    order_service: OrderService = Depends(get_order_service),
) -> dict:
    orders = order_service.list_my_orders(request, order_status=status)
    return success_response(
        request,
        [order.model_dump(by_alias=True, exclude_none=True, mode="json") for order in orders],
    )


@router.get(
    "/api/me/orders/{order_no}",
    response_model=ApiSuccessDTO[OrderMeDTO],
    response_model_exclude_none=True,
)
def get_my_order(
    order_no: str,
    request: Request,
    order_service: OrderService = Depends(get_order_service),
) -> dict:
    order = order_service.get_my_order(order_no, request)
    return success_response(request, order.model_dump(by_alias=True, exclude_none=True, mode="json"))


@router.post(
    "/api/orders/{order_no}/pay",
    response_model=ApiSuccessDTO[OrderMeDTO],
    response_model_exclude_none=True,
)
def pay_order(
    order_no: str,
    request: Request,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    order_service: OrderService = Depends(get_order_service),
) -> dict:
    require_double_submit_csrf(request)
    clean_idempotency_key = idempotency_key.strip() if idempotency_key else ""
    if not clean_idempotency_key:
        raise AppError(400, "IDEMPOTENCY_KEY_REQUIRED", "缺少幂等键")
    if len(clean_idempotency_key) > 128:
        raise AppError(422, "IDEMPOTENCY_KEY_INVALID", "幂等键不合法")
    order = order_service.pay_order(order_no, clean_idempotency_key, request)
    return success_response(request, order.model_dump(by_alias=True, exclude_none=True, mode="json"))


@router.post(
    "/api/orders/{order_no}/cancel",
    response_model=ApiSuccessDTO[OrderMeDTO],
    response_model_exclude_none=True,
)
def cancel_order(
    order_no: str,
    request: Request,
    order_service: OrderService = Depends(get_order_service),
) -> dict:
    require_double_submit_csrf(request)
    order = order_service.cancel_order(order_no, request)
    return success_response(request, order.model_dump(by_alias=True, exclude_none=True, mode="json"))
