from fastapi import APIRouter, Depends, Header, Request

from app.core.responses import success_response
from app.schemas.common import ApiSuccessDTO
from app.schemas.orders import MockPaymentCallbackDTO
from app.services.orders import MockPaymentCallbackService, get_mock_payment_callback_service

router = APIRouter(prefix="/api/payments/mock", tags=["payment-callbacks"])


@router.post(
    "/callback",
    response_model=ApiSuccessDTO[MockPaymentCallbackDTO],
    response_model_exclude_none=True,
)
async def handle_mock_payment_callback(
    request: Request,
    mockpay_timestamp: str | None = Header(default=None, alias="X-Mockpay-Timestamp"),
    mockpay_signature: str | None = Header(default=None, alias="X-Mockpay-Signature"),
    callback_service: MockPaymentCallbackService = Depends(get_mock_payment_callback_service),
) -> dict:
    raw_body = await request.body()
    result = callback_service.handle_callback(
        raw_body=raw_body,
        timestamp_header=mockpay_timestamp,
        signature_header=mockpay_signature,
    )
    return success_response(request, result.model_dump(by_alias=True, mode="json"))
