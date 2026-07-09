from fastapi import APIRouter, Depends, Path, Query, Request

from app.core.responses import success_response
from app.schemas.common import ApiSuccessDTO
from app.schemas.orders import AdminOrderDetailDTO, AdminOrderListDTO
from app.services.orders import AdminOrderService, get_admin_order_service

router = APIRouter(prefix="/api/admin/orders", tags=["admin-orders"])


@router.get(
    "",
    response_model=ApiSuccessDTO[AdminOrderListDTO],
    response_model_exclude_none=True,
)
def list_admin_orders(
    request: Request,
    status: str | None = Query(default=None),
    payment_status: str | None = Query(default=None, alias="paymentStatus"),
    order_no: str | None = Query(default=None, alias="orderNo", min_length=1, max_length=64),
    buyer_phone: str | None = Query(default=None, alias="buyerPhone", min_length=4, max_length=11),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, alias="pageSize", ge=1, le=100),
    admin_order_service: AdminOrderService = Depends(get_admin_order_service),
) -> dict:
    orders = admin_order_service.list_admin_orders(
        request=request,
        status=status,
        payment_status=payment_status,
        order_no=order_no,
        buyer_phone=buyer_phone,
        page=page,
        page_size=page_size,
    )
    return success_response(request, orders.model_dump(by_alias=True, mode="json"))


@router.get(
    "/{order_no}",
    response_model=ApiSuccessDTO[AdminOrderDetailDTO],
    response_model_exclude_none=True,
)
def get_admin_order(
    request: Request,
    order_no: str = Path(min_length=1, max_length=64),
    admin_order_service: AdminOrderService = Depends(get_admin_order_service),
) -> dict:
    order = admin_order_service.get_admin_order(order_no, request)
    return success_response(request, order.model_dump(by_alias=True, exclude_none=True, mode="json"))
