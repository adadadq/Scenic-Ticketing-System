from datetime import date, datetime, time
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.auth import normalize_phone


class OrderPassengerRequest(BaseModel):
    passenger_name: str = Field(alias="passengerName", min_length=2, max_length=50)
    id_type: str = Field(alias="idType", min_length=1, max_length=20)
    id_number: str = Field(alias="idNumber", min_length=6, max_length=50)
    phone: str = Field(min_length=11, max_length=11)
    template_id: int | None = Field(default=None, alias="templateId", gt=0)

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    @field_validator("passenger_name", "id_type", "id_number")
    @classmethod
    def validate_text(cls, value: str) -> str:
        text = value.strip()
        if not text:
            raise ValueError("invalid passenger text")
        return text

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        return normalize_phone(value)


class OrderCreateItemRequest(BaseModel):
    product_id: int = Field(alias="productId", gt=0)
    time_slot_id: int = Field(alias="timeSlotId", gt=0)
    visit_date: date = Field(alias="visitDate")
    quantity: int = Field(gt=0, le=10)
    passengers: list[OrderPassengerRequest] = Field(min_length=1, max_length=10)

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class OrderCreateRequest(BaseModel):
    buyer_name: str = Field(alias="buyerName", min_length=2, max_length=50)
    buyer_phone: str = Field(alias="buyerPhone", min_length=11, max_length=11)
    items: list[OrderCreateItemRequest] = Field(min_length=1, max_length=10)

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    @field_validator("buyer_name")
    @classmethod
    def validate_buyer_name(cls, value: str) -> str:
        buyer_name = value.strip()
        if not buyer_name:
            raise ValueError("invalid buyer name")
        return buyer_name

    @field_validator("buyer_phone")
    @classmethod
    def validate_buyer_phone(cls, value: str) -> str:
        return normalize_phone(value)


class OrderItemMeDTO(BaseModel):
    item_no: str = Field(alias="itemNo")
    product_id: int = Field(alias="productId")
    ticket_type_id: int = Field(alias="ticketTypeId")
    product_name: str = Field(alias="productName")
    ticket_name: str = Field(alias="ticketName")
    time_slot_id: int = Field(alias="timeSlotId")
    visit_date: date = Field(alias="visitDate")
    slot_start_time: time = Field(alias="slotStartTime")
    slot_end_time: time = Field(alias="slotEndTime")
    original_price: Decimal = Field(alias="originalPrice")
    final_price: Decimal = Field(alias="finalPrice")
    item_status: str = Field(alias="itemStatus")
    ticket_code: str | None = Field(default=None, alias="ticketCode")
    passenger_name: str = Field(alias="passengerName")
    passenger_id_type: str = Field(alias="passengerIdType")
    passenger_id_number_masked: str = Field(alias="passengerIdNumberMasked")
    passenger_phone_masked: str = Field(alias="passengerPhoneMasked")
    raft_no: int | None = Field(default=None, alias="raftNo")
    raft_seat_no: int | None = Field(default=None, alias="raftSeatNo")
    raft_assigned_at: datetime | None = Field(default=None, alias="raftAssignedAt")

    model_config = ConfigDict(populate_by_name=True)


class OrderMeDTO(BaseModel):
    order_no: str = Field(alias="orderNo")
    buyer_name: str = Field(alias="buyerName")
    buyer_phone: str = Field(alias="buyerPhone")
    order_status: str = Field(alias="orderStatus")
    payment_status: str = Field(alias="paymentStatus")
    total_amount: Decimal = Field(alias="totalAmount")
    payable_amount: Decimal = Field(alias="payableAmount")
    order_time: datetime = Field(alias="orderTime")
    can_self_refund: bool = Field(default=False, alias="canSelfRefund")
    refund_deadline: datetime | None = Field(default=None, alias="refundDeadline")
    items: list[OrderItemMeDTO] = Field(default_factory=list)

    model_config = ConfigDict(populate_by_name=True)


class AdminOrderItemDTO(BaseModel):
    item_no: str = Field(alias="itemNo")
    product_id: int = Field(alias="productId")
    ticket_type_id: int = Field(alias="ticketTypeId")
    product_name: str = Field(alias="productName")
    ticket_name: str = Field(alias="ticketName")
    time_slot_id: int = Field(alias="timeSlotId")
    visit_date: date = Field(alias="visitDate")
    slot_start_time: time = Field(alias="slotStartTime")
    slot_end_time: time = Field(alias="slotEndTime")
    original_price: Decimal = Field(alias="originalPrice")
    final_price: Decimal = Field(alias="finalPrice")
    item_status: str = Field(alias="itemStatus")
    ticket_code: str | None = Field(default=None, alias="ticketCode")
    passenger_name: str = Field(alias="passengerName")
    passenger_id_type: str = Field(alias="passengerIdType")
    passenger_id_number_masked: str = Field(alias="passengerIdNumberMasked")
    passenger_phone_masked: str = Field(alias="passengerPhoneMasked")
    raft_no: int | None = Field(default=None, alias="raftNo")
    raft_seat_no: int | None = Field(default=None, alias="raftSeatNo")
    raft_assigned_at: datetime | None = Field(default=None, alias="raftAssignedAt")

    model_config = ConfigDict(populate_by_name=True)


class AdminOrderSummaryDTO(BaseModel):
    order_no: str = Field(alias="orderNo")
    visitor_id: int = Field(alias="visitorId")
    buyer_name: str = Field(alias="buyerName")
    buyer_phone_masked: str = Field(alias="buyerPhoneMasked")
    order_status: str = Field(alias="orderStatus")
    payment_status: str = Field(alias="paymentStatus")
    total_amount: Decimal = Field(alias="totalAmount")
    payable_amount: Decimal = Field(alias="payableAmount")
    order_time: datetime = Field(alias="orderTime")
    item_count: int = Field(alias="itemCount")

    model_config = ConfigDict(populate_by_name=True)


class AdminOrderListDTO(BaseModel):
    items: list[AdminOrderSummaryDTO]
    total: int
    page: int
    page_size: int = Field(alias="pageSize")

    model_config = ConfigDict(populate_by_name=True)


class AdminOrderDetailDTO(BaseModel):
    order_no: str = Field(alias="orderNo")
    visitor_id: int = Field(alias="visitorId")
    buyer_name: str = Field(alias="buyerName")
    buyer_phone_masked: str = Field(alias="buyerPhoneMasked")
    order_status: str = Field(alias="orderStatus")
    payment_status: str = Field(alias="paymentStatus")
    total_amount: Decimal = Field(alias="totalAmount")
    payable_amount: Decimal = Field(alias="payableAmount")
    order_time: datetime = Field(alias="orderTime")
    items: list[AdminOrderItemDTO]

    model_config = ConfigDict(populate_by_name=True)


class AdminCheckInRequest(BaseModel):
    ticket_code: str = Field(alias="ticketCode", min_length=1, max_length=64)

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    @field_validator("ticket_code")
    @classmethod
    def validate_ticket_code(cls, value: str) -> str:
        ticket_code = value.strip()
        if not ticket_code:
            raise ValueError("invalid ticket code")
        return ticket_code


class AdminBatchCheckInRequest(BaseModel):
    ticket_codes: list[str] = Field(alias="ticketCodes", min_length=1, max_length=50)

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    @field_validator("ticket_codes")
    @classmethod
    def validate_ticket_codes(cls, value: list[str]) -> list[str]:
        ticket_codes = [ticket_code.strip() for ticket_code in value]
        if any(not ticket_code for ticket_code in ticket_codes):
            raise ValueError("invalid ticket code")
        if len(set(ticket_codes)) != len(ticket_codes):
            raise ValueError("duplicate ticket code")
        if any(len(ticket_code) > 64 for ticket_code in ticket_codes):
            raise ValueError("invalid ticket code")
        return ticket_codes


class AdminCheckInDTO(BaseModel):
    order_no: str = Field(alias="orderNo")
    item_no: str = Field(alias="itemNo")
    ticket_code: str = Field(alias="ticketCode")
    order_status: str = Field(alias="orderStatus")
    item_status: str = Field(alias="itemStatus")
    checked_in_at: datetime = Field(alias="checkedInAt")
    raft_no: int | None = Field(default=None, alias="raftNo")
    raft_seat_no: int | None = Field(default=None, alias="raftSeatNo")

    model_config = ConfigDict(populate_by_name=True)


class AdminUndoCheckInDTO(BaseModel):
    order_no: str = Field(alias="orderNo")
    item_no: str = Field(alias="itemNo")
    ticket_code: str = Field(alias="ticketCode")
    order_status: str = Field(alias="orderStatus")
    item_status: str = Field(alias="itemStatus")
    undone_at: datetime = Field(alias="undoneAt")

    model_config = ConfigDict(populate_by_name=True)


class AdminUndoCheckInRequest(BaseModel):
    reason: str | None = Field(default=None, min_length=1, max_length=100)

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    @field_validator("reason", mode="before")
    @classmethod
    def validate_reason(cls, value: object) -> object:
        if value is None:
            return None
        if isinstance(value, str):
            return value.strip()
        return value


class AdminBatchUndoCheckInRequest(BaseModel):
    ticket_codes: list[str] = Field(alias="ticketCodes", min_length=1, max_length=50)
    reason: str | None = Field(default=None, min_length=1, max_length=100)

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    @field_validator("ticket_codes")
    @classmethod
    def validate_ticket_codes(cls, value: list[str]) -> list[str]:
        ticket_codes = [ticket_code.strip() for ticket_code in value]
        if any(not ticket_code for ticket_code in ticket_codes):
            raise ValueError("invalid ticket code")
        if len(set(ticket_codes)) != len(ticket_codes):
            raise ValueError("duplicate ticket code")
        if any(len(ticket_code) > 64 for ticket_code in ticket_codes):
            raise ValueError("invalid ticket code")
        return ticket_codes

    @field_validator("reason", mode="before")
    @classmethod
    def validate_reason(cls, value: object) -> object:
        if value is None:
            return None
        if isinstance(value, str):
            return value.strip()
        return value


class AdminBatchCheckInResultDTO(BaseModel):
    ticket_code: str = Field(alias="ticketCode")
    success: bool
    check_in: AdminCheckInDTO | None = Field(default=None, alias="checkIn")
    code: str | None = None
    message: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class AdminBatchCheckInDTO(BaseModel):
    total_count: int = Field(alias="totalCount")
    success_count: int = Field(alias="successCount")
    failure_count: int = Field(alias="failureCount")
    results: list[AdminBatchCheckInResultDTO]

    model_config = ConfigDict(populate_by_name=True)


class AdminBatchUndoCheckInResultDTO(BaseModel):
    ticket_code: str = Field(alias="ticketCode")
    success: bool
    undo_check_in: AdminUndoCheckInDTO | None = Field(default=None, alias="undoCheckIn")
    code: str | None = None
    message: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class AdminBatchUndoCheckInDTO(BaseModel):
    total_count: int = Field(alias="totalCount")
    success_count: int = Field(alias="successCount")
    failure_count: int = Field(alias="failureCount")
    results: list[AdminBatchUndoCheckInResultDTO]

    model_config = ConfigDict(populate_by_name=True)


class AdminCheckInAuditLogDTO(BaseModel):
    order_no: str = Field(alias="orderNo")
    item_no: str = Field(alias="itemNo")
    ticket_code: str = Field(alias="ticketCode")
    action: str
    reason: str | None = None
    operator_username: str = Field(alias="operatorUsername")
    operator_display_name: str = Field(alias="operatorDisplayName")
    request_id: str | None = Field(default=None, alias="requestId")
    created_at: datetime = Field(alias="createdAt")

    model_config = ConfigDict(populate_by_name=True)


class AdminCheckInAuditLogListDTO(BaseModel):
    items: list[AdminCheckInAuditLogDTO]
    total: int
    page: int
    page_size: int = Field(alias="pageSize")

    model_config = ConfigDict(populate_by_name=True)


class AdminCheckInFailureAuditLogDTO(BaseModel):
    ticket_code: str = Field(alias="ticketCode")
    action: str
    failure_code: str = Field(alias="failureCode")
    failure_message: str = Field(alias="failureMessage")
    operator_username: str = Field(alias="operatorUsername")
    operator_display_name: str = Field(alias="operatorDisplayName")
    request_id: str | None = Field(default=None, alias="requestId")
    created_at: datetime = Field(alias="createdAt")

    model_config = ConfigDict(populate_by_name=True)


class AdminCheckInFailureAuditLogListDTO(BaseModel):
    items: list[AdminCheckInFailureAuditLogDTO]
    total: int
    page: int
    page_size: int = Field(alias="pageSize")

    model_config = ConfigDict(populate_by_name=True)


class AdminRefundRequest(BaseModel):
    reason: str | None = Field(default=None, min_length=1, max_length=100)

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    @field_validator("reason")
    @classmethod
    def validate_reason(cls, value: str | None) -> str | None:
        if value is None:
            return None
        reason = value.strip()
        if not reason:
            raise ValueError("invalid refund reason")
        return reason


class VisitorRefundRequest(AdminRefundRequest):
    pass


class AdminRefundDTO(BaseModel):
    order_no: str = Field(alias="orderNo")
    order_status: str = Field(alias="orderStatus")
    payment_status: str = Field(alias="paymentStatus")
    refunded_amount: Decimal = Field(alias="refundedAmount")
    refunded_item_count: int = Field(alias="refundedItemCount")
    refunded_at: datetime = Field(alias="refundedAt")

    model_config = ConfigDict(populate_by_name=True)


class AdminPartialRefundRequest(BaseModel):
    item_nos: list[str] = Field(alias="itemNos", min_length=1, max_length=20)
    reason: str | None = Field(default=None, min_length=1, max_length=100)

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    @field_validator("item_nos")
    @classmethod
    def validate_item_nos(cls, value: list[str]) -> list[str]:
        item_nos = [item_no.strip() for item_no in value]
        if any(not item_no for item_no in item_nos):
            raise ValueError("invalid refund item no")
        if len(set(item_nos)) != len(item_nos):
            raise ValueError("duplicate refund item no")
        return item_nos

    @field_validator("reason")
    @classmethod
    def validate_reason(cls, value: str | None) -> str | None:
        if value is None:
            return None
        reason = value.strip()
        if not reason:
            raise ValueError("invalid refund reason")
        return reason


class AdminPartialRefundDTO(BaseModel):
    order_no: str = Field(alias="orderNo")
    order_status: str = Field(alias="orderStatus")
    payment_status: str = Field(alias="paymentStatus")
    refunded_amount: Decimal = Field(alias="refundedAmount")
    refunded_item_count: int = Field(alias="refundedItemCount")
    refunded_item_nos: list[str] = Field(alias="refundedItemNos")
    refunded_at: datetime = Field(alias="refundedAt")

    model_config = ConfigDict(populate_by_name=True)


class AdminRefundAuditLogDTO(BaseModel):
    order_no: str = Field(alias="orderNo")
    refund_type: str = Field(alias="refundType")
    refunded_amount: Decimal = Field(alias="refundedAmount")
    refunded_item_count: int = Field(alias="refundedItemCount")
    refunded_item_nos: list[str] = Field(alias="refundedItemNos")
    reason: str | None = None
    operator_username: str = Field(alias="operatorUsername")
    operator_display_name: str = Field(alias="operatorDisplayName")
    request_id: str | None = Field(default=None, alias="requestId")
    created_at: datetime = Field(alias="createdAt")

    model_config = ConfigDict(populate_by_name=True)


class AdminRefundAuditLogListDTO(BaseModel):
    items: list[AdminRefundAuditLogDTO]
    total: int
    page: int
    page_size: int = Field(alias="pageSize")

    model_config = ConfigDict(populate_by_name=True)


class AdminReportSummaryDTO(BaseModel):
    date_from: date | None = Field(default=None, alias="dateFrom")
    date_to: date | None = Field(default=None, alias="dateTo")
    order_count: int = Field(alias="orderCount")
    paid_order_count: int = Field(alias="paidOrderCount")
    completed_order_count: int = Field(alias="completedOrderCount")
    refunded_order_count: int = Field(alias="refundedOrderCount")
    cancelled_order_count: int = Field(alias="cancelledOrderCount")
    net_paid_amount: Decimal = Field(alias="netPaidAmount")
    ticket_count: int = Field(alias="ticketCount")
    sold_ticket_count: int = Field(alias="soldTicketCount")
    checked_in_ticket_count: int = Field(alias="checkedInTicketCount")
    refunded_ticket_count: int = Field(alias="refundedTicketCount")

    model_config = ConfigDict(populate_by_name=True)


class AdminPaymentReconciliationDTO(BaseModel):
    date_from: date | None = Field(default=None, alias="dateFrom")
    date_to: date | None = Field(default=None, alias="dateTo")
    order_net_paid_amount: Decimal = Field(alias="orderNetPaidAmount")
    captured_payment_amount: Decimal = Field(alias="capturedPaymentAmount")
    refund_audit_amount: Decimal = Field(alias="refundAuditAmount")
    expected_net_amount: Decimal = Field(alias="expectedNetAmount")
    unreconciled_amount: Decimal = Field(alias="unreconciledAmount")
    captured_payment_count: int = Field(alias="capturedPaymentCount")
    refund_audit_log_count: int = Field(alias="refundAuditLogCount")
    reconciled: bool

    model_config = ConfigDict(populate_by_name=True)


class AdminProductBreakdownDTO(BaseModel):
    product_id: int = Field(alias="productId")
    ticket_type_id: int = Field(alias="ticketTypeId")
    product_name: str = Field(alias="productName")
    ticket_name: str = Field(alias="ticketName")
    order_count: int = Field(alias="orderCount")
    ticket_count: int = Field(alias="ticketCount")
    sold_ticket_count: int = Field(alias="soldTicketCount")
    checked_in_ticket_count: int = Field(alias="checkedInTicketCount")
    refunded_ticket_count: int = Field(alias="refundedTicketCount")
    net_paid_amount: Decimal = Field(alias="netPaidAmount")

    model_config = ConfigDict(populate_by_name=True)


class AdminDailyTrendDTO(BaseModel):
    report_date: date = Field(alias="reportDate")
    order_count: int = Field(alias="orderCount")
    paid_order_count: int = Field(alias="paidOrderCount")
    completed_order_count: int = Field(alias="completedOrderCount")
    refunded_order_count: int = Field(alias="refundedOrderCount")
    cancelled_order_count: int = Field(alias="cancelledOrderCount")
    net_paid_amount: Decimal = Field(alias="netPaidAmount")
    ticket_count: int = Field(alias="ticketCount")
    sold_ticket_count: int = Field(alias="soldTicketCount")
    checked_in_ticket_count: int = Field(alias="checkedInTicketCount")
    refunded_ticket_count: int = Field(alias="refundedTicketCount")

    model_config = ConfigDict(populate_by_name=True)


class AdminHourlyTrendDTO(BaseModel):
    report_hour: str = Field(alias="reportHour", pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:00:00$")
    order_count: int = Field(alias="orderCount")
    paid_order_count: int = Field(alias="paidOrderCount")
    completed_order_count: int = Field(alias="completedOrderCount")
    refunded_order_count: int = Field(alias="refundedOrderCount")
    cancelled_order_count: int = Field(alias="cancelledOrderCount")
    net_paid_amount: Decimal = Field(alias="netPaidAmount")
    ticket_count: int = Field(alias="ticketCount")
    sold_ticket_count: int = Field(alias="soldTicketCount")
    checked_in_ticket_count: int = Field(alias="checkedInTicketCount")
    refunded_ticket_count: int = Field(alias="refundedTicketCount")

    model_config = ConfigDict(populate_by_name=True)


class AdminMonthlyTrendDTO(BaseModel):
    report_month: str = Field(alias="reportMonth", pattern=r"^\d{4}-\d{2}$")
    order_count: int = Field(alias="orderCount")
    paid_order_count: int = Field(alias="paidOrderCount")
    completed_order_count: int = Field(alias="completedOrderCount")
    refunded_order_count: int = Field(alias="refundedOrderCount")
    cancelled_order_count: int = Field(alias="cancelledOrderCount")
    net_paid_amount: Decimal = Field(alias="netPaidAmount")
    ticket_count: int = Field(alias="ticketCount")
    sold_ticket_count: int = Field(alias="soldTicketCount")
    checked_in_ticket_count: int = Field(alias="checkedInTicketCount")
    refunded_ticket_count: int = Field(alias="refundedTicketCount")

    model_config = ConfigDict(populate_by_name=True)


class MockPaymentCallbackRequest(BaseModel):
    event_id: str = Field(alias="eventId", min_length=1, max_length=64)
    order_no: str = Field(alias="orderNo", min_length=1, max_length=64)
    payment_no: str = Field(alias="paymentNo", min_length=1, max_length=32)
    transaction_no: str = Field(alias="transactionNo", min_length=1, max_length=64)
    paid_amount: Decimal = Field(alias="paidAmount", gt=0)
    payment_status: str = Field(alias="paymentStatus", min_length=1, max_length=20)

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    @field_validator("event_id", "order_no", "payment_no", "transaction_no")
    @classmethod
    def validate_callback_text(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("invalid callback text")
        return stripped

    @field_validator("payment_status")
    @classmethod
    def validate_callback_payment_status(cls, value: str) -> str:
        stripped = value.strip().upper()
        if not stripped:
            raise ValueError("invalid callback payment status")
        return stripped


class MockPaymentCallbackDTO(BaseModel):
    event_id: str = Field(alias="eventId")
    order_no: str = Field(alias="orderNo")
    order_status: str = Field(alias="orderStatus")
    payment_status: str = Field(alias="paymentStatus")
    idempotent: bool
    processed_at: datetime = Field(alias="processedAt")

    model_config = ConfigDict(populate_by_name=True)
