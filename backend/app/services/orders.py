import csv
import hashlib
import hmac
import io
import re
import secrets
import time
import zipfile
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from xml.sax.saxutils import escape, quoteattr

from fastapi import Depends, Request
from pydantic import ValidationError

from app.core.config import AppSettings, get_settings
from app.core.admin_audit import get_admin_audit_context
from app.core.errors import AppError
from app.repositories.auth import VisitorRecord
from app.repositories.orders import (
    AdminOrderListFilter,
    AdminOrderListRecord,
    AdminOrderExportRecord,
    AdminOrderSummaryRecord,
    AdminCheckInAuditInput,
    AdminCheckInFailureAuditLogExportFilter,
    AdminCheckInFailureAuditLogListFilter,
    AdminCheckInFailureAuditLogListRecord,
    AdminCheckInFailureAuditLogRecord,
    AdminCheckInAuditLogExportFilter,
    AdminCheckInAuditLogRecord,
    AdminCheckInAuditLogListFilter,
    AdminCheckInAuditLogListRecord,
    AdminCheckInRecord,
    AdminDailyTrendRecord,
    AdminHourlyTrendRecord,
    AdminMonthlyTrendRecord,
    AdminUndoCheckInRecord,
    AdminRefundAuditInput,
    AdminRefundAuditLogExportFilter,
    AdminRefundAuditLogRecord,
    AdminRefundAuditLogListFilter,
    AdminRefundAuditLogListRecord,
    AdminPartialRefundRecord,
    AdminPaymentReconciliationRecord,
    AdminProductBreakdownRecord,
    AdminReportFilter,
    AdminReportSummaryRecord,
    AdminRefundRecord,
    MockPaymentCallbackRecord,
    OrderCancelStateError,
    OrderAlreadyRefundedError,
    OrderCreateItemRecord,
    OrderPaymentAmountMismatchError,
    OrderNotRefundableError,
    OrderPaymentStateError,
    PAYMENT_HOLD_MINUTES,
    OrderQuotaNotEnoughError,
    OrderRecord,
    OrderRefundItemsInvalidError,
    OrderRepository,
    PassengerTemplateMismatchError,
    PassengerTimeSlotDuplicateError,
    PendingOrderItemInput,
    TicketAlreadyCheckedInError,
    TicketNotCheckableError,
    TicketNotCheckedInError,
    TicketUndoNotAllowedError,
    get_order_repository,
)
from app.schemas.orders import (
    AdminBatchCheckInDTO,
    AdminBatchCheckInResultDTO,
    AdminBatchCheckInRequest,
    AdminBatchUndoCheckInDTO,
    AdminBatchUndoCheckInRequest,
    AdminBatchUndoCheckInResultDTO,
    AdminCheckInDTO,
    AdminCheckInFailureAuditLogDTO,
    AdminCheckInFailureAuditLogListDTO,
    AdminCheckInAuditLogDTO,
    AdminCheckInAuditLogListDTO,
    AdminCheckInRequest,
    AdminDailyTrendDTO,
    AdminHourlyTrendDTO,
    AdminMonthlyTrendDTO,
    AdminOrderDetailDTO,
    AdminOrderItemDTO,
    AdminOrderListDTO,
    AdminOrderSummaryDTO,
    AdminPartialRefundDTO,
    AdminPartialRefundRequest,
    AdminPaymentReconciliationDTO,
    AdminRefundAuditLogDTO,
    AdminRefundAuditLogListDTO,
    AdminProductBreakdownDTO,
    AdminReportSummaryDTO,
    AdminRefundDTO,
    AdminRefundRequest,
    AdminUndoCheckInDTO,
    AdminUndoCheckInRequest,
    MockPaymentCallbackDTO,
    MockPaymentCallbackRequest,
    OrderCreateRequest,
    OrderItemMeDTO,
    OrderMeDTO,
)
from app.services.auth import AdminAuthService, AuthService, get_admin_auth_service, get_auth_service

ORDER_STATUS_FILTER_OPTIONS = ("CREATED", "PAID", "CANCELLED")
ORDER_STATUS_FILTERS = set(ORDER_STATUS_FILTER_OPTIONS)
ADMIN_ORDER_STATUS_FILTER_OPTIONS = ("CREATED", "PAID", "CANCELLED", "COMPLETED", "REFUNDING", "REFUNDED")
ADMIN_ORDER_STATUS_FILTERS = set(ADMIN_ORDER_STATUS_FILTER_OPTIONS)
ADMIN_PAYMENT_STATUS_FILTER_OPTIONS = ("UNPAID", "PAID", "PARTIAL_REFUND", "REFUNDED", "FAILED")
ADMIN_PAYMENT_STATUS_FILTERS = set(ADMIN_PAYMENT_STATUS_FILTER_OPTIONS)
ADMIN_REFUND_AUDIT_LOG_TYPE_OPTIONS = ("FULL", "PARTIAL")
ADMIN_REFUND_AUDIT_LOG_TYPE_FILTERS = set(ADMIN_REFUND_AUDIT_LOG_TYPE_OPTIONS)
ORDER_NOT_FOUND_MESSAGE = "订单不存在或无权限访问"
REFUND_AUDIT_REQUEST_ID_MAX_LENGTH = 64
CHECK_IN_AUDIT_REQUEST_ID_MAX_LENGTH = 64
SYNC_EXPORT_ROW_LIMIT = 5000


def sync_export_fetch_limit() -> int:
    return SYNC_EXPORT_ROW_LIMIT + 1


def enforce_sync_export_row_limit(rows: list, *, row_label: str = "导出记录") -> None:
    if len(rows) > SYNC_EXPORT_ROW_LIMIT:
        raise AppError(413, "ADMIN_EXPORT_TOO_LARGE", f"{row_label}超过同步导出上限，请缩小筛选范围或使用异步导出")
CHECK_IN_BATCH_RESULT_ERROR_CODES = {"TICKET_NOT_FOUND", "TICKET_ALREADY_USED", "TICKET_NOT_CHECKABLE"}
CHECK_IN_FAILURE_AUDIT_LOG_CODE_OPTIONS = (
    "TICKET_NOT_FOUND",
    "TICKET_ALREADY_USED",
    "TICKET_NOT_CHECKABLE",
    "TICKET_NOT_CHECKED_IN",
    "TICKET_UNDO_NOT_ALLOWED",
)
CHECK_IN_FAILURE_AUDIT_LOG_CODES = set(CHECK_IN_FAILURE_AUDIT_LOG_CODE_OPTIONS)
UNDO_CHECK_IN_BATCH_RESULT_ERROR_CODES = {"TICKET_NOT_FOUND", "TICKET_NOT_CHECKED_IN", "TICKET_UNDO_NOT_ALLOWED"}


class OrderService:
    def __init__(self, repository: OrderRepository, auth_service: AuthService):
        self.repository = repository
        self.auth_service = auth_service

    def create_order(self, payload: OrderCreateRequest, request: Request) -> OrderMeDTO:
        visitor = self.auth_service.require_registered_visitor(request)
        self.expire_unpaid_orders(visitor.id)
        pending_items: list[PendingOrderItemInput] = []
        scenic_spot_ids: set[int] = set()
        grouped_quantities: dict[tuple[int, int, date], int] = {}

        for requested_item in payload.items:
            if requested_item.quantity != len(requested_item.passengers):
                raise AppError(422, "PASSENGER_COUNT_MISMATCH", "每张票都必须填写出行人")
            key = (requested_item.product_id, requested_item.time_slot_id, requested_item.visit_date)
            grouped_quantities[key] = grouped_quantities.get(key, 0) + requested_item.quantity

        for product_id, time_slot_id, visit_date in grouped_quantities:
            quote = self.repository.get_order_quote(
                product_id=product_id,
                time_slot_id=time_slot_id,
                visit_date=visit_date,
            )
            if quote is None:
                raise AppError(404, "PRODUCT_TIME_SLOT_NOT_FOUND", "票种或时段不存在")
            quantity = grouped_quantities[(product_id, time_slot_id, visit_date)]
            if quote.quota_remaining < quantity:
                raise AppError(409, "TIME_SLOT_QUOTA_NOT_ENOUGH", "当前时段余票不足")

            scenic_spot_ids.add(quote.scenic_spot_id)
            requested_passengers = [
                passenger
                for requested_item in payload.items
                if (
                    requested_item.product_id,
                    requested_item.time_slot_id,
                    requested_item.visit_date,
                ) == (product_id, time_slot_id, visit_date)
                for passenger in requested_item.passengers
            ]
            seen_passenger_keys: set[tuple[int, int, date, str, str]] = set()
            for passenger in requested_passengers:
                passenger_key = (
                    quote.ticket_type_id,
                    quote.time_slot_id,
                    quote.visit_date,
                    passenger.id_type,
                    passenger.id_number,
                )
                if passenger_key in seen_passenger_keys:
                    raise AppError(409, "PASSENGER_DUPLICATED_IN_ORDER", "同一出行人不能重复购买同一时段票")
                seen_passenger_keys.add(passenger_key)
                pending_items.append(
                    PendingOrderItemInput(
                        item_no=self.generate_item_no(),
                        product_id=quote.product_id,
                        ticket_type_id=quote.ticket_type_id,
                        product_name=quote.product_name,
                        ticket_name=quote.ticket_name,
                        time_slot_id=quote.time_slot_id,
                        visit_date=quote.visit_date,
                        slot_start_time=quote.slot_start_time,
                        slot_end_time=quote.slot_end_time,
                        original_price=quote.original_price,
                        final_price=quote.sale_price,
                        passenger_template_id=passenger.template_id,
                        passenger_name=passenger.passenger_name,
                        passenger_id_type=passenger.id_type,
                        passenger_id_number=passenger.id_number,
                        passenger_phone=passenger.phone,
                    )
                )

        if len(scenic_spot_ids) != 1:
            raise AppError(400, "ORDER_SCENIC_SPOT_MISMATCH", "一次订单只能购买同一景区票品")

        try:
            order = self.repository.create_pending_order(
                order_no=self.generate_order_no(),
                visitor_id=visitor.id,
                scenic_spot_id=next(iter(scenic_spot_ids)),
                buyer_name=payload.buyer_name,
                buyer_phone=payload.buyer_phone,
                items=pending_items,
            )
        except PassengerTemplateMismatchError as exc:
            raise AppError(403, "PASSENGER_TEMPLATE_FORBIDDEN", "出行人模板不可用") from exc
        except PassengerTimeSlotDuplicateError as exc:
            raise AppError(409, "PASSENGER_TIME_SLOT_DUPLICATED", "同一出行人已购买该时段票") from exc
        return self.to_order_dto(order)

    def list_my_orders(self, request: Request, order_status: str | None = None) -> list[OrderMeDTO]:
        visitor = self.current_visitor(request)
        normalized_status = self.normalize_order_status(order_status)
        return [
            self.to_order_dto(order)
            for order in self.repository.list_orders_for_visitor(visitor.id, order_status=normalized_status)
        ]

    def get_my_order(self, order_no: str, request: Request) -> OrderMeDTO:
        visitor = self.current_visitor(request)
        order = self.repository.get_order_for_visitor(visitor.id, order_no)
        if order is None:
            raise AppError(404, "ORDER_NOT_FOUND", ORDER_NOT_FOUND_MESSAGE)
        return self.to_order_dto(order)

    def pay_order(self, order_no: str, idempotency_key: str, request: Request) -> OrderMeDTO:
        visitor = self.current_visitor(request)
        self.expire_unpaid_orders(visitor.id)
        try:
            order = self.repository.pay_order(
                order_no=order_no,
                visitor_id=visitor.id,
                idempotency_key=idempotency_key,
                payment_no=self.generate_payment_no(),
                transaction_no=self.generate_transaction_no(),
                ticket_code_factory=self.generate_ticket_code,
            )
        except OrderQuotaNotEnoughError as exc:
            raise AppError(409, "TIME_SLOT_QUOTA_NOT_ENOUGH", "当前时段余票不足") from exc
        except OrderPaymentStateError as exc:
            raise AppError(409, "ORDER_NOT_PAYABLE", "订单状态不可支付") from exc

        if order is None:
            raise AppError(404, "ORDER_NOT_FOUND", ORDER_NOT_FOUND_MESSAGE)
        return self.to_order_dto(order)

    def expire_unpaid_orders(self, visitor_id: int) -> None:
        self.repository.expire_unpaid_orders(
            visitor_id,
            datetime.now(UTC) - timedelta(minutes=PAYMENT_HOLD_MINUTES),
        )

    def cancel_order(self, order_no: str, request: Request) -> OrderMeDTO:
        visitor = self.current_visitor(request)
        try:
            order = self.repository.cancel_order(order_no=order_no, visitor_id=visitor.id)
        except OrderCancelStateError as exc:
            raise AppError(409, "ORDER_NOT_CANCELABLE", "当前订单状态不可取消") from exc

        if order is None:
            raise AppError(404, "ORDER_NOT_FOUND", ORDER_NOT_FOUND_MESSAGE)
        return self.to_order_dto(order)

    def current_visitor(self, request: Request) -> VisitorRecord:
        return self.auth_service.current_session_visitor(request).visitor

    @staticmethod
    def normalize_order_status(order_status: str | None) -> str | None:
        if order_status is None:
            return None
        normalized_status = order_status.strip().upper()
        if not normalized_status:
            return None
        if normalized_status not in ORDER_STATUS_FILTERS:
            raise AppError(422, "ORDER_STATUS_INVALID", "订单状态筛选不合法")
        return normalized_status

    @staticmethod
    def generate_order_no() -> str:
        return f"O{datetime.now(UTC):%Y%m%d%H%M%S}{secrets.token_hex(4).upper()}"

    @staticmethod
    def generate_item_no() -> str:
        return f"I{secrets.token_hex(8).upper()}"

    @staticmethod
    def generate_payment_no() -> str:
        return f"P{datetime.now(UTC):%Y%m%d%H%M%S}{secrets.token_hex(4).upper()}"

    @staticmethod
    def generate_transaction_no() -> str:
        return f"T{secrets.token_hex(12).upper()}"

    @staticmethod
    def generate_ticket_code() -> str:
        return f"TK{secrets.token_urlsafe(12).replace('-', '').replace('_', '')[:14].upper()}"

    @staticmethod
    def mask_phone(phone: str) -> str:
        clean_phone = phone.strip()
        if len(clean_phone) == 11:
            return f"{clean_phone[:3]}****{clean_phone[-4:]}"
        if len(clean_phone) <= 4:
            return "****"
        return f"****{clean_phone[-4:]}"

    @staticmethod
    def mask_id_number(id_number: str) -> str:
        clean_id = id_number.strip()
        if len(clean_id) <= 6:
            return "***"
        return f"{clean_id[:3]}********{clean_id[-3:]}"

    @staticmethod
    def to_order_dto(order: OrderRecord) -> OrderMeDTO:
        return OrderMeDTO(
            order_no=order.order_no,
            buyer_name=order.buyer_name,
            buyer_phone=OrderService.mask_phone(order.buyer_phone),
            order_status=order.order_status,
            payment_status=order.payment_status,
            total_amount=order.total_amount,
            payable_amount=order.payable_amount,
            order_time=order.order_time,
            items=[OrderService.to_item_dto(item) for item in order.items],
        )

    @staticmethod
    def to_item_dto(item: OrderCreateItemRecord) -> OrderItemMeDTO:
        return OrderItemMeDTO(
            item_no=item.item_no,
            product_id=item.product_id,
            ticket_type_id=item.ticket_type_id,
            product_name=item.product_name,
            ticket_name=item.ticket_name,
            time_slot_id=item.time_slot_id,
            visit_date=item.visit_date,
            slot_start_time=item.slot_start_time,
            slot_end_time=item.slot_end_time,
            original_price=item.original_price,
            final_price=item.final_price,
            item_status=item.item_status,
            ticket_code=item.ticket_code,
            passenger_name=item.passenger_name,
            passenger_id_type=item.passenger_id_type,
            passenger_id_number_masked=OrderService.mask_id_number(item.passenger_id_number),
            passenger_phone_masked=OrderService.mask_phone(item.passenger_phone),
            raft_no=item.raft_no,
            raft_seat_no=item.raft_seat_no,
            raft_assigned_at=item.raft_assigned_at,
        )


def get_order_service(
    repository: OrderRepository = Depends(get_order_repository),
    auth_service: AuthService = Depends(get_auth_service),
) -> OrderService:
    return OrderService(repository, auth_service)


class AdminOrderService:
    def __init__(self, repository: OrderRepository, admin_auth_service: AdminAuthService):
        self.repository = repository
        self.admin_auth_service = admin_auth_service

    def list_admin_orders(
        self,
        request: Request,
        status: str | None,
        payment_status: str | None,
        order_no: str | None,
        buyer_phone: str | None,
        page: int,
        page_size: int,
    ) -> AdminOrderListDTO:
        self.admin_auth_service.current_session_admin(request)
        filters = AdminOrderListFilter(
            status=self.normalize_admin_order_status(status),
            payment_status=self.normalize_admin_payment_status(payment_status),
            order_no=self.normalize_optional_text(order_no),
            buyer_phone=self.normalize_optional_text(buyer_phone),
            page=page,
            page_size=page_size,
        )
        return self.to_admin_order_list_dto(self.repository.list_orders_for_admin(filters))

    def get_admin_order(self, order_no: str, request: Request) -> AdminOrderDetailDTO:
        self.admin_auth_service.current_session_admin(request)
        order = self.repository.get_order_for_admin(order_no.strip())
        if order is None:
            raise AppError(404, "ADMIN_ORDER_NOT_FOUND", "订单不存在")
        return self.to_admin_order_detail_dto(order)

    @staticmethod
    def normalize_admin_order_status(order_status: str | None) -> str | None:
        if order_status is None:
            return None
        normalized_status = order_status.strip().upper()
        if not normalized_status:
            return None
        if normalized_status not in ADMIN_ORDER_STATUS_FILTERS:
            raise AppError(422, "ADMIN_ORDER_STATUS_INVALID", "订单状态筛选不合法")
        return normalized_status

    @staticmethod
    def normalize_admin_payment_status(payment_status: str | None) -> str | None:
        if payment_status is None:
            return None
        normalized_status = payment_status.strip().upper()
        if not normalized_status:
            return None
        if normalized_status not in ADMIN_PAYMENT_STATUS_FILTERS:
            raise AppError(422, "ADMIN_PAYMENT_STATUS_INVALID", "支付状态筛选不合法")
        return normalized_status

    @staticmethod
    def normalize_optional_text(value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None

    @staticmethod
    def to_admin_order_list_dto(record: AdminOrderListRecord) -> AdminOrderListDTO:
        return AdminOrderListDTO(
            items=[AdminOrderService.to_admin_order_summary_dto(item) for item in record.items],
            total=record.total,
            page=record.page,
            page_size=record.page_size,
        )

    @staticmethod
    def to_admin_order_summary_dto(record: AdminOrderSummaryRecord) -> AdminOrderSummaryDTO:
        return AdminOrderSummaryDTO(
            order_no=record.order_no,
            visitor_id=record.visitor_id,
            buyer_name=record.buyer_name,
            buyer_phone_masked=OrderService.mask_phone(record.buyer_phone),
            order_status=record.order_status,
            payment_status=record.payment_status,
            total_amount=record.total_amount,
            payable_amount=record.payable_amount,
            order_time=record.order_time,
            item_count=record.item_count,
        )

    @staticmethod
    def to_admin_order_detail_dto(order: OrderRecord) -> AdminOrderDetailDTO:
        return AdminOrderDetailDTO(
            order_no=order.order_no,
            visitor_id=order.visitor_id,
            buyer_name=order.buyer_name,
            buyer_phone_masked=OrderService.mask_phone(order.buyer_phone),
            order_status=order.order_status,
            payment_status=order.payment_status,
            total_amount=order.total_amount,
            payable_amount=order.payable_amount,
            order_time=order.order_time,
            items=[AdminOrderService.to_admin_order_item_dto(item) for item in order.items],
        )

    @staticmethod
    def to_admin_order_item_dto(item: OrderCreateItemRecord) -> AdminOrderItemDTO:
        return AdminOrderItemDTO(
            item_no=item.item_no,
            product_id=item.product_id,
            ticket_type_id=item.ticket_type_id,
            product_name=item.product_name,
            ticket_name=item.ticket_name,
            time_slot_id=item.time_slot_id,
            visit_date=item.visit_date,
            slot_start_time=item.slot_start_time,
            slot_end_time=item.slot_end_time,
            original_price=item.original_price,
            final_price=item.final_price,
            item_status=item.item_status,
            ticket_code=item.ticket_code,
            passenger_name=item.passenger_name,
            passenger_id_type=item.passenger_id_type,
            passenger_id_number_masked=OrderService.mask_id_number(item.passenger_id_number),
            passenger_phone_masked=OrderService.mask_phone(item.passenger_phone),
            raft_no=item.raft_no,
            raft_seat_no=item.raft_seat_no,
            raft_assigned_at=item.raft_assigned_at,
        )


def get_admin_order_service(
    repository: OrderRepository = Depends(get_order_repository),
    admin_auth_service: AdminAuthService = Depends(get_admin_auth_service),
) -> AdminOrderService:
    return AdminOrderService(repository, admin_auth_service)


class AdminCheckInService:
    CHECK_IN_AUDIT_LOG_EXPORT_HEADERS = (
        "orderNo",
        "itemNo",
        "ticketCode",
        "action",
        "reason",
        "operatorUsername",
        "operatorDisplayName",
        "requestId",
        "createdAt",
    )
    CHECK_IN_FAILURE_AUDIT_LOG_EXPORT_HEADERS = (
        "ticketCode",
        "action",
        "failureCode",
        "failureMessage",
        "operatorUsername",
        "operatorDisplayName",
        "requestId",
        "createdAt",
    )

    def __init__(self, repository: OrderRepository, admin_auth_service: AdminAuthService):
        self.repository = repository
        self.admin_auth_service = admin_auth_service

    def check_in_ticket(self, payload: AdminCheckInRequest, request: Request) -> AdminCheckInDTO:
        session_record = self.admin_auth_service.current_session_admin(request)
        return self.check_in_ticket_for_admin(payload.ticket_code, session_record.admin, request)

    def check_in_tickets_batch(self, payload: AdminBatchCheckInRequest, request: Request) -> AdminBatchCheckInDTO:
        session_record = self.admin_auth_service.current_session_admin(request)
        results: list[AdminBatchCheckInResultDTO] = []
        success_count = 0

        for ticket_code in payload.ticket_codes:
            try:
                check_in = self.check_in_ticket_for_admin(ticket_code, session_record.admin, request)
            except AppError as exc:
                if exc.code not in CHECK_IN_BATCH_RESULT_ERROR_CODES:
                    raise
                results.append(
                    AdminBatchCheckInResultDTO(
                        ticket_code=ticket_code,
                        success=False,
                        code=exc.code,
                        message=exc.message,
                    )
                )
                continue

            success_count += 1
            results.append(
                AdminBatchCheckInResultDTO(
                    ticket_code=ticket_code,
                    success=True,
                    check_in=check_in,
                )
            )

        return AdminBatchCheckInDTO(
            total_count=len(payload.ticket_codes),
            success_count=success_count,
            failure_count=len(payload.ticket_codes) - success_count,
            results=results,
        )

    def undo_check_in_tickets_batch(
        self,
        payload: AdminBatchUndoCheckInRequest,
        request: Request,
    ) -> AdminBatchUndoCheckInDTO:
        session_record = self.admin_auth_service.current_session_admin(request)
        results: list[AdminBatchUndoCheckInResultDTO] = []
        success_count = 0

        for ticket_code in payload.ticket_codes:
            try:
                undo_check_in = self.undo_check_in_ticket_for_admin(
                    ticket_code,
                    session_record.admin,
                    request,
                    reason=payload.reason,
                )
            except AppError as exc:
                if exc.code not in UNDO_CHECK_IN_BATCH_RESULT_ERROR_CODES:
                    raise
                results.append(
                    AdminBatchUndoCheckInResultDTO(
                        ticket_code=ticket_code,
                        success=False,
                        code=exc.code,
                        message=exc.message,
                    )
                )
                continue

            success_count += 1
            results.append(
                AdminBatchUndoCheckInResultDTO(
                    ticket_code=ticket_code,
                    success=True,
                    undo_check_in=undo_check_in,
                )
            )

        return AdminBatchUndoCheckInDTO(
            total_count=len(payload.ticket_codes),
            success_count=success_count,
            failure_count=len(payload.ticket_codes) - success_count,
            results=results,
        )

    def check_in_ticket_for_admin(self, ticket_code: str, admin, request: Request) -> AdminCheckInDTO:
        audit = self.to_check_in_audit_input(admin, request)
        normalized_ticket_code = ticket_code.strip()
        try:
            record = self.repository.check_in_ticket(normalized_ticket_code, audit)
        except TicketAlreadyCheckedInError as exc:
            self.record_check_in_failure_audit_log(
                ticket_code=normalized_ticket_code,
                failure_code="TICKET_ALREADY_USED",
                failure_message="票码已核销",
                audit=audit,
            )
            raise AppError(409, "TICKET_ALREADY_USED", "票码已核销") from exc
        except TicketNotCheckableError as exc:
            self.record_check_in_failure_audit_log(
                ticket_code=normalized_ticket_code,
                failure_code="TICKET_NOT_CHECKABLE",
                failure_message="当前票码不可核销",
                audit=audit,
            )
            raise AppError(409, "TICKET_NOT_CHECKABLE", "当前票码不可核销") from exc
        if record is None:
            self.record_check_in_failure_audit_log(
                ticket_code=normalized_ticket_code,
                failure_code="TICKET_NOT_FOUND",
                failure_message="票码不存在",
                audit=audit,
            )
            raise AppError(404, "TICKET_NOT_FOUND", "票码不存在")
        return self.to_check_in_dto(record)

    def undo_check_in_ticket(
        self,
        ticket_code: str,
        payload: AdminUndoCheckInRequest | None,
        request: Request,
    ) -> AdminUndoCheckInDTO:
        session_record = self.admin_auth_service.current_session_admin(request)
        return self.undo_check_in_ticket_for_admin(
            ticket_code,
            session_record.admin,
            request,
            reason=payload.reason if payload else None,
        )

    def undo_check_in_ticket_for_admin(
        self,
        ticket_code: str,
        admin,
        request: Request,
        *,
        reason: str | None = None,
    ) -> AdminUndoCheckInDTO:
        audit = self.to_check_in_audit_input(admin, request, reason=reason)
        normalized_ticket_code = ticket_code.strip()
        try:
            record = self.repository.undo_check_in_ticket(normalized_ticket_code, audit)
        except TicketNotCheckedInError as exc:
            self.record_check_in_failure_audit_log(
                ticket_code=normalized_ticket_code,
                action="UNDO_CHECK_IN",
                failure_code="TICKET_NOT_CHECKED_IN",
                failure_message="票码未核销",
                audit=audit,
            )
            raise AppError(409, "TICKET_NOT_CHECKED_IN", "票码未核销") from exc
        except TicketUndoNotAllowedError as exc:
            self.record_check_in_failure_audit_log(
                ticket_code=normalized_ticket_code,
                action="UNDO_CHECK_IN",
                failure_code="TICKET_UNDO_NOT_ALLOWED",
                failure_message="当前票码不可撤销核销",
                audit=audit,
            )
            raise AppError(409, "TICKET_UNDO_NOT_ALLOWED", "当前票码不可撤销核销") from exc
        if record is None:
            self.record_check_in_failure_audit_log(
                ticket_code=normalized_ticket_code,
                action="UNDO_CHECK_IN",
                failure_code="TICKET_NOT_FOUND",
                failure_message="票码不存在",
                audit=audit,
            )
            raise AppError(404, "TICKET_NOT_FOUND", "票码不存在")
        return self.to_undo_check_in_dto(record)

    def list_check_in_audit_logs(self, ticket_code: str, request: Request) -> list[AdminCheckInAuditLogDTO]:
        self.admin_auth_service.current_session_admin(request)
        records = self.repository.list_check_in_audit_logs(ticket_code.strip())
        if records is None:
            raise AppError(404, "TICKET_NOT_FOUND", "票码不存在")
        return [self.to_check_in_audit_log_dto(record) for record in records]

    def list_check_in_audit_log_entries(
        self,
        request: Request,
        ticket_code: str | None,
        order_no: str | None,
        operator_username: str | None,
        reason: str | None,
        date_from: date | None,
        date_to: date | None,
        page: int,
        page_size: int,
    ) -> AdminCheckInAuditLogListDTO:
        self.admin_auth_service.current_session_admin(request)
        self.validate_check_in_audit_date_range(date_from, date_to)
        filters = AdminCheckInAuditLogListFilter(
            ticket_code=AdminOrderService.normalize_optional_text(ticket_code),
            order_no=AdminOrderService.normalize_optional_text(order_no),
            operator_username=AdminOrderService.normalize_optional_text(operator_username),
            reason=AdminOrderService.normalize_optional_text(reason),
            date_from=date_from,
            date_to=date_to,
            page=page,
            page_size=page_size,
        )
        return self.to_check_in_audit_log_list_dto(self.repository.list_check_in_audit_log_entries(filters))

    def list_check_in_failure_audit_log_entries(
        self,
        request: Request,
        ticket_code: str | None,
        failure_code: str | None,
        operator_username: str | None,
        date_from: date | None,
        date_to: date | None,
        page: int,
        page_size: int,
    ) -> AdminCheckInFailureAuditLogListDTO:
        self.admin_auth_service.current_session_admin(request)
        self.validate_check_in_failure_audit_date_range(date_from, date_to)
        filters = AdminCheckInFailureAuditLogListFilter(
            ticket_code=AdminOrderService.normalize_optional_text(ticket_code),
            failure_code=self.normalize_check_in_failure_audit_log_code(failure_code),
            operator_username=AdminOrderService.normalize_optional_text(operator_username),
            date_from=date_from,
            date_to=date_to,
            page=page,
            page_size=page_size,
        )
        return self.to_check_in_failure_audit_log_list_dto(
            self.repository.list_check_in_failure_audit_log_entries(filters)
        )

    def export_check_in_audit_logs_csv(
        self,
        request: Request,
        ticket_code: str | None,
        order_no: str | None,
        operator_username: str | None,
        reason: str | None,
        date_from: date | None,
        date_to: date | None,
    ) -> str:
        self.admin_auth_service.current_session_admin(request)
        self.validate_check_in_audit_date_range(date_from, date_to)
        filters = AdminCheckInAuditLogExportFilter(
            ticket_code=AdminOrderService.normalize_optional_text(ticket_code),
            order_no=AdminOrderService.normalize_optional_text(order_no),
            operator_username=AdminOrderService.normalize_optional_text(operator_username),
            reason=AdminOrderService.normalize_optional_text(reason),
            date_from=date_from,
            date_to=date_to,
            row_limit=sync_export_fetch_limit(),
        )
        records = self.repository.list_check_in_audit_log_export_rows(filters)
        enforce_sync_export_row_limit(records, row_label="核销审计日志")
        return self.to_check_in_audit_logs_csv(records)

    def export_check_in_audit_logs_csv_for_worker(
        self,
        ticket_code: str | None,
        order_no: str | None,
        operator_username: str | None,
        reason: str | None,
        date_from: date | None,
        date_to: date | None,
    ) -> str:
        self.validate_check_in_audit_date_range(date_from, date_to)
        filters = AdminCheckInAuditLogExportFilter(
            ticket_code=AdminOrderService.normalize_optional_text(ticket_code),
            order_no=AdminOrderService.normalize_optional_text(order_no),
            operator_username=AdminOrderService.normalize_optional_text(operator_username),
            reason=AdminOrderService.normalize_optional_text(reason),
            date_from=date_from,
            date_to=date_to,
        )
        records = self.repository.list_check_in_audit_log_export_rows(filters)
        return self.to_check_in_audit_logs_csv(records)

    def export_check_in_audit_logs_xlsx_for_worker(
        self,
        ticket_code: str | None,
        order_no: str | None,
        operator_username: str | None,
        reason: str | None,
        date_from: date | None,
        date_to: date | None,
    ) -> bytes:
        self.validate_check_in_audit_date_range(date_from, date_to)
        filters = AdminCheckInAuditLogExportFilter(
            ticket_code=AdminOrderService.normalize_optional_text(ticket_code),
            order_no=AdminOrderService.normalize_optional_text(order_no),
            operator_username=AdminOrderService.normalize_optional_text(operator_username),
            reason=AdminOrderService.normalize_optional_text(reason),
            date_from=date_from,
            date_to=date_to,
        )
        records = self.repository.list_check_in_audit_log_export_rows(filters)
        return self.to_check_in_audit_logs_xlsx(records)

    def export_check_in_failure_audit_logs_csv(
        self,
        request: Request,
        ticket_code: str | None,
        failure_code: str | None,
        operator_username: str | None,
        date_from: date | None,
        date_to: date | None,
    ) -> str:
        self.admin_auth_service.current_session_admin(request)
        self.validate_check_in_failure_audit_date_range(date_from, date_to)
        filters = AdminCheckInFailureAuditLogExportFilter(
            ticket_code=AdminOrderService.normalize_optional_text(ticket_code),
            failure_code=self.normalize_check_in_failure_audit_log_code(failure_code),
            operator_username=AdminOrderService.normalize_optional_text(operator_username),
            date_from=date_from,
            date_to=date_to,
            row_limit=sync_export_fetch_limit(),
        )
        records = self.repository.list_check_in_failure_audit_log_export_rows(filters)
        enforce_sync_export_row_limit(records, row_label="核销失败审计日志")
        return self.to_check_in_failure_audit_logs_csv(records)

    def export_check_in_failure_audit_logs_csv_for_worker(
        self,
        ticket_code: str | None,
        failure_code: str | None,
        operator_username: str | None,
        date_from: date | None,
        date_to: date | None,
    ) -> str:
        self.validate_check_in_failure_audit_date_range(date_from, date_to)
        filters = AdminCheckInFailureAuditLogExportFilter(
            ticket_code=AdminOrderService.normalize_optional_text(ticket_code),
            failure_code=self.normalize_check_in_failure_audit_log_code(failure_code),
            operator_username=AdminOrderService.normalize_optional_text(operator_username),
            date_from=date_from,
            date_to=date_to,
        )
        records = self.repository.list_check_in_failure_audit_log_export_rows(filters)
        return self.to_check_in_failure_audit_logs_csv(records)

    def export_check_in_failure_audit_logs_xlsx(
        self,
        request: Request,
        ticket_code: str | None,
        failure_code: str | None,
        operator_username: str | None,
        date_from: date | None,
        date_to: date | None,
    ) -> bytes:
        self.admin_auth_service.current_session_admin(request)
        self.validate_check_in_failure_audit_date_range(date_from, date_to)
        filters = AdminCheckInFailureAuditLogExportFilter(
            ticket_code=AdminOrderService.normalize_optional_text(ticket_code),
            failure_code=self.normalize_check_in_failure_audit_log_code(failure_code),
            operator_username=AdminOrderService.normalize_optional_text(operator_username),
            date_from=date_from,
            date_to=date_to,
            row_limit=sync_export_fetch_limit(),
        )
        records = self.repository.list_check_in_failure_audit_log_export_rows(filters)
        enforce_sync_export_row_limit(records, row_label="核销失败审计日志")
        return self.to_check_in_failure_audit_logs_xlsx(records)

    def export_check_in_failure_audit_logs_xlsx_for_worker(
        self,
        ticket_code: str | None,
        failure_code: str | None,
        operator_username: str | None,
        date_from: date | None,
        date_to: date | None,
    ) -> bytes:
        self.validate_check_in_failure_audit_date_range(date_from, date_to)
        filters = AdminCheckInFailureAuditLogExportFilter(
            ticket_code=AdminOrderService.normalize_optional_text(ticket_code),
            failure_code=self.normalize_check_in_failure_audit_log_code(failure_code),
            operator_username=AdminOrderService.normalize_optional_text(operator_username),
            date_from=date_from,
            date_to=date_to,
        )
        records = self.repository.list_check_in_failure_audit_log_export_rows(filters)
        return self.to_check_in_failure_audit_logs_xlsx(records)

    def export_check_in_audit_logs_xlsx(
        self,
        request: Request,
        ticket_code: str | None,
        order_no: str | None,
        operator_username: str | None,
        reason: str | None,
        date_from: date | None,
        date_to: date | None,
    ) -> bytes:
        self.admin_auth_service.current_session_admin(request)
        self.validate_check_in_audit_date_range(date_from, date_to)
        filters = AdminCheckInAuditLogExportFilter(
            ticket_code=AdminOrderService.normalize_optional_text(ticket_code),
            order_no=AdminOrderService.normalize_optional_text(order_no),
            operator_username=AdminOrderService.normalize_optional_text(operator_username),
            reason=AdminOrderService.normalize_optional_text(reason),
            date_from=date_from,
            date_to=date_to,
            row_limit=sync_export_fetch_limit(),
        )
        records = self.repository.list_check_in_audit_log_export_rows(filters)
        enforce_sync_export_row_limit(records, row_label="核销审计日志")
        return self.to_check_in_audit_logs_xlsx(records)

    @staticmethod
    def to_check_in_audit_input(admin, request: Request, reason: str | None = None) -> AdminCheckInAuditInput:
        context = get_admin_audit_context(request, admin)
        return AdminCheckInAuditInput(
            operator_admin_user_id=context.admin_user_id,
            operator_username=context.operator_username,
            operator_display_name=context.operator_display_name,
            request_id=AdminCheckInService.to_check_in_audit_request_id(context.request_id),
            reason=reason,
            source_ip=context.source_ip,
            device_id=context.device_id,
            admin_session_id=context.admin_session_id,
            user_agent=context.user_agent,
        )

    @staticmethod
    def to_check_in_audit_request_id(request_id: str | None) -> str | None:
        if not request_id:
            return None
        return request_id[:CHECK_IN_AUDIT_REQUEST_ID_MAX_LENGTH]

    @staticmethod
    def to_check_in_dto(record: AdminCheckInRecord) -> AdminCheckInDTO:
        return AdminCheckInDTO(
            order_no=record.order_no,
            item_no=record.item_no,
            ticket_code=record.ticket_code,
            order_status=record.order_status,
            item_status=record.item_status,
            checked_in_at=record.checked_in_at,
            raft_no=record.raft_no,
            raft_seat_no=record.raft_seat_no,
        )

    @staticmethod
    def to_undo_check_in_dto(record: AdminUndoCheckInRecord) -> AdminUndoCheckInDTO:
        return AdminUndoCheckInDTO(
            order_no=record.order_no,
            item_no=record.item_no,
            ticket_code=record.ticket_code,
            order_status=record.order_status,
            item_status=record.item_status,
            undone_at=record.undone_at,
        )

    @staticmethod
    def to_check_in_audit_log_dto(record: AdminCheckInAuditLogRecord) -> AdminCheckInAuditLogDTO:
        return AdminCheckInAuditLogDTO(
            order_no=record.order_no,
            item_no=record.item_no,
            ticket_code=record.ticket_code,
            action=record.action,
            reason=record.reason,
            operator_username=record.operator_username,
            operator_display_name=record.operator_display_name,
            request_id=record.request_id,
            created_at=record.created_at,
        )

    @staticmethod
    def to_check_in_failure_audit_log_dto(
        record: AdminCheckInFailureAuditLogRecord,
    ) -> AdminCheckInFailureAuditLogDTO:
        return AdminCheckInFailureAuditLogDTO(
            ticket_code=record.ticket_code,
            action=record.action,
            failure_code=record.failure_code,
            failure_message=record.failure_message,
            operator_username=record.operator_username,
            operator_display_name=record.operator_display_name,
            request_id=record.request_id,
            created_at=record.created_at,
        )

    @staticmethod
    def validate_check_in_audit_date_range(date_from: date | None, date_to: date | None) -> None:
        if date_from is not None and date_to is not None and date_from > date_to:
            raise AppError(422, "ADMIN_CHECK_IN_LOG_DATE_RANGE_INVALID", "核销审计日期范围不合法")

    @staticmethod
    def validate_check_in_failure_audit_date_range(date_from: date | None, date_to: date | None) -> None:
        if date_from is not None and date_to is not None and date_from > date_to:
            raise AppError(422, "ADMIN_CHECK_IN_FAILURE_LOG_DATE_RANGE_INVALID", "核销失败审计日期范围不合法")

    @staticmethod
    def normalize_check_in_failure_audit_log_code(failure_code: str | None) -> str | None:
        if failure_code is None:
            return None
        normalized_code = failure_code.strip().upper()
        if not normalized_code:
            return None
        if normalized_code not in CHECK_IN_FAILURE_AUDIT_LOG_CODES:
            raise AppError(422, "ADMIN_CHECK_IN_FAILURE_CODE_INVALID", "核销失败码筛选不合法")
        return normalized_code

    @staticmethod
    def to_check_in_audit_log_list_dto(record: AdminCheckInAuditLogListRecord) -> AdminCheckInAuditLogListDTO:
        return AdminCheckInAuditLogListDTO(
            items=[AdminCheckInService.to_check_in_audit_log_dto(item) for item in record.items],
            total=record.total,
            page=record.page,
            page_size=record.page_size,
        )

    @staticmethod
    def to_check_in_failure_audit_log_list_dto(
        record: AdminCheckInFailureAuditLogListRecord,
    ) -> AdminCheckInFailureAuditLogListDTO:
        return AdminCheckInFailureAuditLogListDTO(
            items=[AdminCheckInService.to_check_in_failure_audit_log_dto(item) for item in record.items],
            total=record.total,
            page=record.page,
            page_size=record.page_size,
        )

    def record_check_in_failure_audit_log(
        self,
        *,
        ticket_code: str,
        action: str = "CHECK_IN",
        failure_code: str,
        failure_message: str,
        audit: AdminCheckInAuditInput,
    ) -> None:
        self.repository.record_check_in_failure_audit_log(
            ticket_code=ticket_code,
            action=action,
            failure_code=failure_code,
            failure_message=failure_message,
            audit=audit,
        )

    @classmethod
    def to_check_in_audit_logs_csv(cls, records: list[AdminCheckInAuditLogRecord]) -> str:
        output = io.StringIO(newline="")
        writer = csv.writer(output)
        writer.writerow(cls.CHECK_IN_AUDIT_LOG_EXPORT_HEADERS)
        for row in cls.check_in_audit_log_export_rows(records):
            writer.writerow(row)
        return "\ufeff" + output.getvalue()

    @classmethod
    def to_check_in_audit_logs_xlsx(cls, records: list[AdminCheckInAuditLogRecord]) -> bytes:
        rows = [cls.CHECK_IN_AUDIT_LOG_EXPORT_HEADERS, *cls.check_in_audit_log_export_rows(records)]
        return AdminReportService.to_xlsx_workbook(rows, sheet_name="CheckInLogs")

    @classmethod
    def check_in_audit_log_export_rows(cls, records: list[AdminCheckInAuditLogRecord]) -> list[list[str]]:
        return [
            [
                cls.safe_csv_cell(record.order_no),
                cls.safe_csv_cell(record.item_no),
                cls.safe_csv_cell(record.ticket_code),
                cls.safe_csv_cell(record.action),
                cls.safe_csv_cell(record.reason or ""),
                cls.safe_csv_cell(record.operator_username),
                cls.safe_csv_cell(record.operator_display_name),
                cls.safe_csv_cell(record.request_id or ""),
                cls.safe_csv_cell(AdminReportService.format_datetime(record.created_at)),
            ]
            for record in records
        ]

    @classmethod
    def to_check_in_failure_audit_logs_csv(cls, records: list[AdminCheckInFailureAuditLogRecord]) -> str:
        output = io.StringIO(newline="")
        writer = csv.writer(output)
        writer.writerow(cls.CHECK_IN_FAILURE_AUDIT_LOG_EXPORT_HEADERS)
        for row in cls.check_in_failure_audit_log_export_rows(records):
            writer.writerow(row)
        return "\ufeff" + output.getvalue()

    @classmethod
    def to_check_in_failure_audit_logs_xlsx(cls, records: list[AdminCheckInFailureAuditLogRecord]) -> bytes:
        rows = [cls.CHECK_IN_FAILURE_AUDIT_LOG_EXPORT_HEADERS, *cls.check_in_failure_audit_log_export_rows(records)]
        return AdminReportService.to_xlsx_workbook(rows, sheet_name="CheckInFailureLogs")

    @classmethod
    def check_in_failure_audit_log_export_rows(
        cls,
        records: list[AdminCheckInFailureAuditLogRecord],
    ) -> list[list[str]]:
        return [
            [
                cls.safe_csv_cell(record.ticket_code),
                cls.safe_csv_cell(record.action),
                cls.safe_csv_cell(record.failure_code),
                cls.safe_csv_cell(record.failure_message),
                cls.safe_csv_cell(record.operator_username),
                cls.safe_csv_cell(record.operator_display_name),
                cls.safe_csv_cell(record.request_id or ""),
                cls.safe_csv_cell(AdminReportService.format_datetime(record.created_at)),
            ]
            for record in records
        ]

    @staticmethod
    def safe_csv_cell(value: object) -> str:
        return AdminReportService.safe_csv_cell(value)

    @staticmethod
    def check_in_audit_log_export_filename(date_from: date | None, date_to: date | None) -> str:
        return f"{AdminCheckInService.check_in_audit_log_export_filename_stem(date_from=date_from, date_to=date_to)}.csv"

    @staticmethod
    def check_in_failure_audit_log_export_filename(date_from: date | None, date_to: date | None) -> str:
        return (
            f"{AdminCheckInService.check_in_failure_audit_log_export_filename_stem(date_from=date_from, date_to=date_to)}.csv"
        )

    @staticmethod
    def check_in_audit_log_export_xlsx_filename(date_from: date | None, date_to: date | None) -> str:
        return f"{AdminCheckInService.check_in_audit_log_export_filename_stem(date_from=date_from, date_to=date_to)}.xlsx"

    @staticmethod
    def check_in_failure_audit_log_export_xlsx_filename(date_from: date | None, date_to: date | None) -> str:
        return (
            f"{AdminCheckInService.check_in_failure_audit_log_export_filename_stem(date_from=date_from, date_to=date_to)}.xlsx"
        )

    @staticmethod
    def check_in_audit_log_export_filename_stem(date_from: date | None, date_to: date | None) -> str:
        start = date_from.strftime("%Y%m%d") if date_from else "start"
        end = date_to.strftime("%Y%m%d") if date_to else "end"
        return f"admin-check-in-logs-{start}-{end}"

    @staticmethod
    def check_in_failure_audit_log_export_filename_stem(date_from: date | None, date_to: date | None) -> str:
        start = date_from.strftime("%Y%m%d") if date_from else "start"
        end = date_to.strftime("%Y%m%d") if date_to else "end"
        return f"admin-check-in-failure-logs-{start}-{end}"


def get_admin_check_in_service(
    repository: OrderRepository = Depends(get_order_repository),
    admin_auth_service: AdminAuthService = Depends(get_admin_auth_service),
) -> AdminCheckInService:
    return AdminCheckInService(repository, admin_auth_service)


class AdminRefundService:
    REFUND_AUDIT_LOG_EXPORT_HEADERS = (
        "orderNo",
        "refundType",
        "refundedAmount",
        "refundedItemCount",
        "refundedItemNos",
        "reason",
        "operatorUsername",
        "operatorDisplayName",
        "requestId",
        "createdAt",
    )

    def __init__(self, repository: OrderRepository, admin_auth_service: AdminAuthService):
        self.repository = repository
        self.admin_auth_service = admin_auth_service

    def refund_order(self, order_no: str, payload: AdminRefundRequest, request: Request) -> AdminRefundDTO:
        session_record = self.admin_auth_service.require_super_admin(request)
        audit = self.to_refund_audit_input(session_record.admin, payload.reason, request)
        try:
            record = self.repository.refund_order(order_no.strip(), audit)
        except OrderAlreadyRefundedError as exc:
            raise AppError(409, "ORDER_ALREADY_REFUNDED", "订单已退款") from exc
        except OrderNotRefundableError as exc:
            raise AppError(409, "ORDER_NOT_REFUNDABLE", "当前订单不可退款") from exc
        if record is None:
            raise AppError(404, "ADMIN_ORDER_NOT_FOUND", "订单不存在")
        return self.to_refund_dto(record)

    def refund_order_items(
        self,
        order_no: str,
        payload: AdminPartialRefundRequest,
        request: Request,
    ) -> AdminPartialRefundDTO:
        session_record = self.admin_auth_service.require_super_admin(request)
        audit = self.to_refund_audit_input(session_record.admin, payload.reason, request)
        try:
            record = self.repository.refund_order_items(order_no.strip(), payload.item_nos, audit)
        except OrderAlreadyRefundedError as exc:
            raise AppError(409, "ORDER_ALREADY_REFUNDED", "订单已退款") from exc
        except OrderRefundItemsInvalidError as exc:
            raise AppError(409, "ORDER_REFUND_ITEMS_INVALID", "退款票项无效") from exc
        except OrderNotRefundableError as exc:
            raise AppError(409, "ORDER_NOT_PARTIALLY_REFUNDABLE", "当前订单不可部分退款") from exc
        if record is None:
            raise AppError(404, "ADMIN_ORDER_NOT_FOUND", "订单不存在")
        return self.to_partial_refund_dto(record)

    def list_refund_audit_logs(self, order_no: str, request: Request) -> list[AdminRefundAuditLogDTO]:
        self.admin_auth_service.current_session_admin(request)
        records = self.repository.list_refund_audit_logs(order_no.strip())
        if records is None:
            raise AppError(404, "ADMIN_ORDER_NOT_FOUND", "订单不存在")
        return [self.to_refund_audit_log_dto(record) for record in records]

    def list_refund_audit_log_entries(
        self,
        request: Request,
        refund_type: str | None,
        order_no: str | None,
        operator_username: str | None,
        date_from: date | None,
        date_to: date | None,
        page: int,
        page_size: int,
    ) -> AdminRefundAuditLogListDTO:
        self.admin_auth_service.current_session_admin(request)
        self.validate_refund_audit_date_range(date_from, date_to)
        filters = AdminRefundAuditLogListFilter(
            refund_type=self.normalize_refund_audit_log_type(refund_type),
            order_no=AdminOrderService.normalize_optional_text(order_no),
            operator_username=AdminOrderService.normalize_optional_text(operator_username),
            date_from=date_from,
            date_to=date_to,
            page=page,
            page_size=page_size,
        )
        return self.to_refund_audit_log_list_dto(self.repository.list_refund_audit_log_entries(filters))

    def export_refund_audit_logs_csv(
        self,
        request: Request,
        refund_type: str | None,
        order_no: str | None,
        operator_username: str | None,
        date_from: date | None,
        date_to: date | None,
    ) -> str:
        self.admin_auth_service.current_session_admin(request)
        self.validate_refund_audit_date_range(date_from, date_to)
        filters = AdminRefundAuditLogExportFilter(
            refund_type=self.normalize_refund_audit_log_type(refund_type),
            order_no=AdminOrderService.normalize_optional_text(order_no),
            operator_username=AdminOrderService.normalize_optional_text(operator_username),
            date_from=date_from,
            date_to=date_to,
            row_limit=sync_export_fetch_limit(),
        )
        records = self.repository.list_refund_audit_log_export_rows(filters)
        enforce_sync_export_row_limit(records, row_label="退款审计日志")
        return self.to_refund_audit_logs_csv(records)

    def export_refund_audit_logs_csv_for_worker(
        self,
        refund_type: str | None,
        order_no: str | None,
        operator_username: str | None,
        date_from: date | None,
        date_to: date | None,
    ) -> str:
        self.validate_refund_audit_date_range(date_from, date_to)
        filters = AdminRefundAuditLogExportFilter(
            refund_type=self.normalize_refund_audit_log_type(refund_type),
            order_no=AdminOrderService.normalize_optional_text(order_no),
            operator_username=AdminOrderService.normalize_optional_text(operator_username),
            date_from=date_from,
            date_to=date_to,
        )
        records = self.repository.list_refund_audit_log_export_rows(filters)
        return self.to_refund_audit_logs_csv(records)

    def export_refund_audit_logs_xlsx(
        self,
        request: Request,
        refund_type: str | None,
        order_no: str | None,
        operator_username: str | None,
        date_from: date | None,
        date_to: date | None,
    ) -> bytes:
        self.admin_auth_service.current_session_admin(request)
        self.validate_refund_audit_date_range(date_from, date_to)
        filters = AdminRefundAuditLogExportFilter(
            refund_type=self.normalize_refund_audit_log_type(refund_type),
            order_no=AdminOrderService.normalize_optional_text(order_no),
            operator_username=AdminOrderService.normalize_optional_text(operator_username),
            date_from=date_from,
            date_to=date_to,
            row_limit=sync_export_fetch_limit(),
        )
        records = self.repository.list_refund_audit_log_export_rows(filters)
        enforce_sync_export_row_limit(records, row_label="退款审计日志")
        return self.to_refund_audit_logs_xlsx(records)

    def export_refund_audit_logs_xlsx_for_worker(
        self,
        refund_type: str | None,
        order_no: str | None,
        operator_username: str | None,
        date_from: date | None,
        date_to: date | None,
    ) -> bytes:
        self.validate_refund_audit_date_range(date_from, date_to)
        filters = AdminRefundAuditLogExportFilter(
            refund_type=self.normalize_refund_audit_log_type(refund_type),
            order_no=AdminOrderService.normalize_optional_text(order_no),
            operator_username=AdminOrderService.normalize_optional_text(operator_username),
            date_from=date_from,
            date_to=date_to,
        )
        records = self.repository.list_refund_audit_log_export_rows(filters)
        return self.to_refund_audit_logs_xlsx(records)

    @staticmethod
    def to_refund_audit_input(admin, reason: str | None, request: Request) -> AdminRefundAuditInput:
        context = get_admin_audit_context(request, admin)
        return AdminRefundAuditInput(
            operator_admin_user_id=context.admin_user_id,
            operator_username=context.operator_username,
            operator_display_name=context.operator_display_name,
            reason=reason,
            request_id=AdminRefundService.to_refund_audit_request_id(context.request_id),
            source_ip=context.source_ip,
            device_id=context.device_id,
            admin_session_id=context.admin_session_id,
            user_agent=context.user_agent,
        )

    @staticmethod
    def to_refund_audit_request_id(request_id: str | None) -> str | None:
        if not request_id:
            return None
        return request_id[:REFUND_AUDIT_REQUEST_ID_MAX_LENGTH]

    @staticmethod
    def to_refund_dto(record: AdminRefundRecord) -> AdminRefundDTO:
        return AdminRefundDTO(
            order_no=record.order_no,
            order_status=record.order_status,
            payment_status=record.payment_status,
            refunded_amount=record.refunded_amount,
            refunded_item_count=record.refunded_item_count,
            refunded_at=record.refunded_at,
        )

    @staticmethod
    def to_partial_refund_dto(record: AdminPartialRefundRecord) -> AdminPartialRefundDTO:
        return AdminPartialRefundDTO(
            order_no=record.order_no,
            order_status=record.order_status,
            payment_status=record.payment_status,
            refunded_amount=record.refunded_amount,
            refunded_item_count=record.refunded_item_count,
            refunded_item_nos=record.refunded_item_nos,
            refunded_at=record.refunded_at,
        )

    @staticmethod
    def to_refund_audit_log_dto(record: AdminRefundAuditLogRecord) -> AdminRefundAuditLogDTO:
        return AdminRefundAuditLogDTO(
            order_no=record.order_no,
            refund_type=record.refund_type,
            refunded_amount=record.refunded_amount,
            refunded_item_count=record.refunded_item_count,
            refunded_item_nos=record.refunded_item_nos,
            reason=record.reason,
            operator_username=record.operator_username,
            operator_display_name=record.operator_display_name,
            request_id=record.request_id,
            created_at=record.created_at,
        )

    @staticmethod
    def normalize_refund_audit_log_type(refund_type: str | None) -> str | None:
        if refund_type is None:
            return None
        normalized_type = refund_type.strip().upper()
        if not normalized_type:
            return None
        if normalized_type not in ADMIN_REFUND_AUDIT_LOG_TYPE_FILTERS:
            raise AppError(422, "ADMIN_REFUND_LOG_TYPE_INVALID", "退款审计类型筛选不合法")
        return normalized_type

    @staticmethod
    def validate_refund_audit_date_range(date_from: date | None, date_to: date | None) -> None:
        if date_from is not None and date_to is not None and date_from > date_to:
            raise AppError(422, "ADMIN_REFUND_LOG_DATE_RANGE_INVALID", "退款审计日期范围不合法")

    @staticmethod
    def to_refund_audit_log_list_dto(record: AdminRefundAuditLogListRecord) -> AdminRefundAuditLogListDTO:
        return AdminRefundAuditLogListDTO(
            items=[AdminRefundService.to_refund_audit_log_dto(item) for item in record.items],
            total=record.total,
            page=record.page,
            page_size=record.page_size,
        )

    @classmethod
    def to_refund_audit_logs_csv(cls, records: list[AdminRefundAuditLogRecord]) -> str:
        output = io.StringIO(newline="")
        writer = csv.writer(output)
        writer.writerow(cls.REFUND_AUDIT_LOG_EXPORT_HEADERS)
        for row in cls.refund_audit_log_export_rows(records):
            writer.writerow(row)
        return "\ufeff" + output.getvalue()

    @classmethod
    def to_refund_audit_logs_xlsx(cls, records: list[AdminRefundAuditLogRecord]) -> bytes:
        rows = [cls.REFUND_AUDIT_LOG_EXPORT_HEADERS, *cls.refund_audit_log_export_rows(records)]
        return AdminReportService.to_xlsx_workbook(rows, sheet_name="RefundLogs")

    @classmethod
    def refund_audit_log_export_rows(cls, records: list[AdminRefundAuditLogRecord]) -> list[list[str]]:
        return [
            [
                cls.safe_csv_cell(record.order_no),
                cls.safe_csv_cell(record.refund_type),
                cls.safe_csv_cell(record.refunded_amount),
                cls.safe_csv_cell(record.refunded_item_count),
                cls.safe_csv_cell(";".join(record.refunded_item_nos)),
                cls.safe_csv_cell(record.reason or ""),
                cls.safe_csv_cell(record.operator_username),
                cls.safe_csv_cell(record.operator_display_name),
                cls.safe_csv_cell(record.request_id or ""),
                cls.safe_csv_cell(AdminReportService.format_datetime(record.created_at)),
            ]
            for record in records
        ]

    @staticmethod
    def safe_csv_cell(value: object) -> str:
        return AdminReportService.safe_csv_cell(value)

    @staticmethod
    def refund_audit_log_export_filename(date_from: date | None, date_to: date | None) -> str:
        return f"{AdminRefundService.refund_audit_log_export_filename_stem(date_from=date_from, date_to=date_to)}.csv"

    @staticmethod
    def refund_audit_log_export_xlsx_filename(date_from: date | None, date_to: date | None) -> str:
        return f"{AdminRefundService.refund_audit_log_export_filename_stem(date_from=date_from, date_to=date_to)}.xlsx"

    @staticmethod
    def refund_audit_log_export_filename_stem(date_from: date | None, date_to: date | None) -> str:
        start = date_from.strftime("%Y%m%d") if date_from else "start"
        end = date_to.strftime("%Y%m%d") if date_to else "end"
        return f"admin-refund-logs-{start}-{end}"


def get_admin_refund_service(
    repository: OrderRepository = Depends(get_order_repository),
    admin_auth_service: AdminAuthService = Depends(get_admin_auth_service),
) -> AdminRefundService:
    return AdminRefundService(repository, admin_auth_service)


class AdminReportService:
    ORDER_EXPORT_HEADERS = (
        "orderNo",
        "buyerName",
        "buyerPhoneMasked",
        "orderStatus",
        "paymentStatus",
        "totalAmount",
        "payableAmount",
        "orderTime",
        "itemCount",
    )
    DAILY_TREND_EXPORT_HEADERS = (
        "reportDate",
        "orderCount",
        "paidOrderCount",
        "completedOrderCount",
        "refundedOrderCount",
        "cancelledOrderCount",
        "netPaidAmount",
        "ticketCount",
        "soldTicketCount",
        "checkedInTicketCount",
        "refundedTicketCount",
    )
    HOURLY_TREND_EXPORT_HEADERS = (
        "reportHour",
        "orderCount",
        "paidOrderCount",
        "completedOrderCount",
        "refundedOrderCount",
        "cancelledOrderCount",
        "netPaidAmount",
        "ticketCount",
        "soldTicketCount",
        "checkedInTicketCount",
        "refundedTicketCount",
    )
    MONTHLY_TREND_EXPORT_HEADERS = (
        "reportMonth",
        "orderCount",
        "paidOrderCount",
        "completedOrderCount",
        "refundedOrderCount",
        "cancelledOrderCount",
        "netPaidAmount",
        "ticketCount",
        "soldTicketCount",
        "checkedInTicketCount",
        "refundedTicketCount",
    )
    PAYMENT_RECONCILIATION_EXPORT_HEADERS = (
        "dateFrom",
        "dateTo",
        "orderNetPaidAmount",
        "capturedPaymentAmount",
        "refundAuditAmount",
        "expectedNetAmount",
        "unreconciledAmount",
        "capturedPaymentCount",
        "refundAuditLogCount",
        "reconciled",
    )
    PRODUCT_BREAKDOWN_EXPORT_HEADERS = (
        "productId",
        "ticketTypeId",
        "productName",
        "ticketName",
        "orderCount",
        "ticketCount",
        "soldTicketCount",
        "checkedInTicketCount",
        "refundedTicketCount",
        "netPaidAmount",
    )

    def __init__(self, repository: OrderRepository, admin_auth_service: AdminAuthService):
        self.repository = repository
        self.admin_auth_service = admin_auth_service

    def get_summary(self, request: Request, date_from: date | None, date_to: date | None) -> AdminReportSummaryDTO:
        self.admin_auth_service.current_session_admin(request)
        self.validate_date_range(date_from, date_to)
        record = self.repository.get_admin_report_summary(AdminReportFilter(date_from=date_from, date_to=date_to))
        return self.to_summary_dto(record)

    def get_payment_reconciliation(
        self,
        request: Request,
        date_from: date | None,
        date_to: date | None,
    ) -> AdminPaymentReconciliationDTO:
        self.admin_auth_service.current_session_admin(request)
        self.validate_date_range(date_from, date_to)
        record = self.repository.get_admin_payment_reconciliation(
            AdminReportFilter(date_from=date_from, date_to=date_to)
        )
        return self.to_payment_reconciliation_dto(record)

    def export_payment_reconciliation_csv(
        self,
        request: Request,
        date_from: date | None,
        date_to: date | None,
    ) -> str:
        reconciliation = self.get_payment_reconciliation(
            request=request,
            date_from=date_from,
            date_to=date_to,
        )
        return self.to_payment_reconciliation_csv(reconciliation)

    def export_payment_reconciliation_xlsx(
        self,
        request: Request,
        date_from: date | None,
        date_to: date | None,
    ) -> bytes:
        reconciliation = self.get_payment_reconciliation(
            request=request,
            date_from=date_from,
            date_to=date_to,
        )
        return self.to_payment_reconciliation_xlsx(reconciliation)

    def export_payment_reconciliation_csv_for_worker(
        self,
        date_from: date | None,
        date_to: date | None,
    ) -> str:
        self.validate_date_range(date_from, date_to)
        record = self.repository.get_admin_payment_reconciliation(
            AdminReportFilter(date_from=date_from, date_to=date_to)
        )
        return self.to_payment_reconciliation_csv(self.to_payment_reconciliation_dto(record))

    def export_payment_reconciliation_xlsx_for_worker(
        self,
        date_from: date | None,
        date_to: date | None,
    ) -> bytes:
        self.validate_date_range(date_from, date_to)
        record = self.repository.get_admin_payment_reconciliation(
            AdminReportFilter(date_from=date_from, date_to=date_to)
        )
        return self.to_payment_reconciliation_xlsx(self.to_payment_reconciliation_dto(record))

    def list_product_breakdown(
        self,
        request: Request,
        date_from: date | None,
        date_to: date | None,
        row_limit: int | None = None,
    ) -> list[AdminProductBreakdownDTO]:
        self.admin_auth_service.current_session_admin(request)
        self.validate_date_range(date_from, date_to)
        records = self.repository.list_admin_product_breakdown(
            AdminReportFilter(date_from=date_from, date_to=date_to, row_limit=row_limit)
        )
        return [self.to_product_breakdown_dto(record) for record in records]

    def export_product_breakdown_csv(
        self,
        request: Request,
        date_from: date | None,
        date_to: date | None,
    ) -> str:
        rows = self.list_product_breakdown(
            request=request,
            date_from=date_from,
            date_to=date_to,
            row_limit=sync_export_fetch_limit(),
        )
        enforce_sync_export_row_limit(rows, row_label="产品维度报表")
        return self.to_product_breakdown_csv(rows)

    def export_product_breakdown_xlsx(
        self,
        request: Request,
        date_from: date | None,
        date_to: date | None,
    ) -> bytes:
        rows = self.list_product_breakdown(
            request=request,
            date_from=date_from,
            date_to=date_to,
            row_limit=sync_export_fetch_limit(),
        )
        enforce_sync_export_row_limit(rows, row_label="产品维度报表")
        return self.to_product_breakdown_xlsx(rows)

    def export_product_breakdown_csv_for_worker(self, date_from: date | None, date_to: date | None) -> str:
        self.validate_date_range(date_from, date_to)
        records = self.repository.list_admin_product_breakdown(
            AdminReportFilter(date_from=date_from, date_to=date_to)
        )
        rows = [self.to_product_breakdown_dto(record) for record in records]
        return self.to_product_breakdown_csv(rows)

    def export_product_breakdown_xlsx_for_worker(self, date_from: date | None, date_to: date | None) -> bytes:
        self.validate_date_range(date_from, date_to)
        records = self.repository.list_admin_product_breakdown(
            AdminReportFilter(date_from=date_from, date_to=date_to)
        )
        rows = [self.to_product_breakdown_dto(record) for record in records]
        return self.to_product_breakdown_xlsx(rows)

    def list_daily_trend(
        self,
        request: Request,
        date_from: date | None,
        date_to: date | None,
        include_empty: bool = False,
        row_limit: int | None = None,
    ) -> list[AdminDailyTrendDTO]:
        self.admin_auth_service.current_session_admin(request)
        self.validate_date_range(date_from, date_to)
        self.validate_trend_zero_fill_range(
            include_empty=include_empty,
            date_from=date_from,
            date_to=date_to,
            max_days=366,
        )
        records = self.repository.list_admin_daily_trend(
            AdminReportFilter(date_from=date_from, date_to=date_to, row_limit=row_limit)
        )
        rows = [self.to_daily_trend_dto(record) for record in records]
        if include_empty:
            return self.zero_fill_daily_trend(rows, date_from=date_from, date_to=date_to)
        return rows

    def list_hourly_trend(
        self,
        request: Request,
        date_from: date | None,
        date_to: date | None,
        include_empty: bool = False,
        row_limit: int | None = None,
    ) -> list[AdminHourlyTrendDTO]:
        self.admin_auth_service.current_session_admin(request)
        self.validate_date_range(date_from, date_to)
        self.validate_trend_zero_fill_range(
            include_empty=include_empty,
            date_from=date_from,
            date_to=date_to,
            max_days=31,
        )
        records = self.repository.list_admin_hourly_trend(
            AdminReportFilter(date_from=date_from, date_to=date_to, row_limit=row_limit)
        )
        rows = [self.to_hourly_trend_dto(record) for record in records]
        if include_empty:
            return self.zero_fill_hourly_trend(rows, date_from=date_from, date_to=date_to)
        return rows

    def list_monthly_trend(
        self,
        request: Request,
        date_from: date | None,
        date_to: date | None,
        include_empty: bool = False,
        row_limit: int | None = None,
    ) -> list[AdminMonthlyTrendDTO]:
        self.admin_auth_service.current_session_admin(request)
        self.validate_date_range(date_from, date_to)
        self.validate_trend_zero_fill_range(
            include_empty=include_empty,
            date_from=date_from,
            date_to=date_to,
            max_months=60,
        )
        records = self.repository.list_admin_monthly_trend(
            AdminReportFilter(date_from=date_from, date_to=date_to, row_limit=row_limit)
        )
        rows = [self.to_monthly_trend_dto(record) for record in records]
        if include_empty:
            return self.zero_fill_monthly_trend(rows, date_from=date_from, date_to=date_to)
        return rows

    def export_orders_csv(self, request: Request, date_from: date | None, date_to: date | None) -> str:
        self.admin_auth_service.current_session_admin(request)
        self.validate_date_range(date_from, date_to)
        records = self.repository.list_admin_order_export_rows(
            AdminReportFilter(date_from=date_from, date_to=date_to, row_limit=sync_export_fetch_limit())
        )
        enforce_sync_export_row_limit(records, row_label="订单明细")
        return self.to_orders_csv(records)

    def export_order_detail_csv_for_worker(self, date_from: date | None, date_to: date | None) -> str:
        self.validate_date_range(date_from, date_to)
        records = self.repository.list_admin_order_export_rows(
            AdminReportFilter(date_from=date_from, date_to=date_to)
        )
        return self.to_orders_csv(records)

    def export_order_detail_xlsx_for_worker(self, date_from: date | None, date_to: date | None) -> bytes:
        self.validate_date_range(date_from, date_to)
        records = self.repository.list_admin_order_export_rows(
            AdminReportFilter(date_from=date_from, date_to=date_to)
        )
        return self.to_orders_xlsx(records)

    def export_orders_xlsx(self, request: Request, date_from: date | None, date_to: date | None) -> bytes:
        self.admin_auth_service.current_session_admin(request)
        self.validate_date_range(date_from, date_to)
        records = self.repository.list_admin_order_export_rows(
            AdminReportFilter(date_from=date_from, date_to=date_to, row_limit=sync_export_fetch_limit())
        )
        enforce_sync_export_row_limit(records, row_label="订单明细")
        return self.to_orders_xlsx(records)

    def export_daily_trend_csv(
        self,
        request: Request,
        date_from: date | None,
        date_to: date | None,
        include_empty: bool = False,
    ) -> str:
        rows = self.list_daily_trend(
            request=request,
            date_from=date_from,
            date_to=date_to,
            include_empty=include_empty,
            row_limit=sync_export_fetch_limit(),
        )
        enforce_sync_export_row_limit(rows, row_label="日报趋势")
        return self.to_daily_trend_csv(rows)

    def export_daily_trend_csv_for_worker(
        self,
        date_from: date | None,
        date_to: date | None,
        include_empty: bool = False,
    ) -> str:
        self.validate_date_range(date_from, date_to)
        self.validate_trend_zero_fill_range(
            include_empty=include_empty,
            date_from=date_from,
            date_to=date_to,
            max_days=366,
        )
        records = self.repository.list_admin_daily_trend(
            AdminReportFilter(date_from=date_from, date_to=date_to)
        )
        rows = [self.to_daily_trend_dto(record) for record in records]
        if include_empty:
            rows = self.zero_fill_daily_trend(rows, date_from=date_from, date_to=date_to)
        return self.to_daily_trend_csv(rows)

    def export_hourly_trend_csv(
        self,
        request: Request,
        date_from: date | None,
        date_to: date | None,
        include_empty: bool = False,
    ) -> str:
        rows = self.list_hourly_trend(
            request=request,
            date_from=date_from,
            date_to=date_to,
            include_empty=include_empty,
            row_limit=sync_export_fetch_limit(),
        )
        enforce_sync_export_row_limit(rows, row_label="小时趋势")
        return self.to_hourly_trend_csv(rows)

    def export_hourly_trend_csv_for_worker(
        self,
        date_from: date | None,
        date_to: date | None,
        include_empty: bool = False,
    ) -> str:
        self.validate_date_range(date_from, date_to)
        self.validate_trend_zero_fill_range(
            include_empty=include_empty,
            date_from=date_from,
            date_to=date_to,
            max_days=31,
        )
        records = self.repository.list_admin_hourly_trend(
            AdminReportFilter(date_from=date_from, date_to=date_to)
        )
        rows = [self.to_hourly_trend_dto(record) for record in records]
        if include_empty:
            rows = self.zero_fill_hourly_trend(rows, date_from=date_from, date_to=date_to)
        return self.to_hourly_trend_csv(rows)

    def export_monthly_trend_csv(
        self,
        request: Request,
        date_from: date | None,
        date_to: date | None,
        include_empty: bool = False,
    ) -> str:
        rows = self.list_monthly_trend(
            request=request,
            date_from=date_from,
            date_to=date_to,
            include_empty=include_empty,
            row_limit=sync_export_fetch_limit(),
        )
        enforce_sync_export_row_limit(rows, row_label="月度趋势")
        return self.to_monthly_trend_csv(rows)

    def export_monthly_trend_csv_for_worker(
        self,
        date_from: date | None,
        date_to: date | None,
        include_empty: bool = False,
    ) -> str:
        self.validate_date_range(date_from, date_to)
        self.validate_trend_zero_fill_range(
            include_empty=include_empty,
            date_from=date_from,
            date_to=date_to,
            max_months=60,
        )
        records = self.repository.list_admin_monthly_trend(
            AdminReportFilter(date_from=date_from, date_to=date_to)
        )
        rows = [self.to_monthly_trend_dto(record) for record in records]
        if include_empty:
            rows = self.zero_fill_monthly_trend(rows, date_from=date_from, date_to=date_to)
        return self.to_monthly_trend_csv(rows)

    def export_daily_trend_xlsx(
        self,
        request: Request,
        date_from: date | None,
        date_to: date | None,
        include_empty: bool = False,
    ) -> bytes:
        rows = self.list_daily_trend(
            request=request,
            date_from=date_from,
            date_to=date_to,
            include_empty=include_empty,
            row_limit=sync_export_fetch_limit(),
        )
        enforce_sync_export_row_limit(rows, row_label="日报趋势")
        return self.to_daily_trend_xlsx(rows)

    def export_daily_trend_xlsx_for_worker(
        self,
        date_from: date | None,
        date_to: date | None,
        include_empty: bool = False,
    ) -> bytes:
        self.validate_date_range(date_from, date_to)
        self.validate_trend_zero_fill_range(
            include_empty=include_empty,
            date_from=date_from,
            date_to=date_to,
            max_days=366,
        )
        records = self.repository.list_admin_daily_trend(
            AdminReportFilter(date_from=date_from, date_to=date_to)
        )
        rows = [self.to_daily_trend_dto(record) for record in records]
        if include_empty:
            rows = self.zero_fill_daily_trend(rows, date_from=date_from, date_to=date_to)
        return self.to_daily_trend_xlsx(rows)

    def export_hourly_trend_xlsx(
        self,
        request: Request,
        date_from: date | None,
        date_to: date | None,
        include_empty: bool = False,
    ) -> bytes:
        rows = self.list_hourly_trend(
            request=request,
            date_from=date_from,
            date_to=date_to,
            include_empty=include_empty,
            row_limit=sync_export_fetch_limit(),
        )
        enforce_sync_export_row_limit(rows, row_label="小时趋势")
        return self.to_hourly_trend_xlsx(rows)

    def export_hourly_trend_xlsx_for_worker(
        self,
        date_from: date | None,
        date_to: date | None,
        include_empty: bool = False,
    ) -> bytes:
        self.validate_date_range(date_from, date_to)
        self.validate_trend_zero_fill_range(
            include_empty=include_empty,
            date_from=date_from,
            date_to=date_to,
            max_days=31,
        )
        records = self.repository.list_admin_hourly_trend(
            AdminReportFilter(date_from=date_from, date_to=date_to)
        )
        rows = [self.to_hourly_trend_dto(record) for record in records]
        if include_empty:
            rows = self.zero_fill_hourly_trend(rows, date_from=date_from, date_to=date_to)
        return self.to_hourly_trend_xlsx(rows)

    def export_monthly_trend_xlsx(
        self,
        request: Request,
        date_from: date | None,
        date_to: date | None,
        include_empty: bool = False,
    ) -> bytes:
        rows = self.list_monthly_trend(
            request=request,
            date_from=date_from,
            date_to=date_to,
            include_empty=include_empty,
            row_limit=sync_export_fetch_limit(),
        )
        enforce_sync_export_row_limit(rows, row_label="月度趋势")
        return self.to_monthly_trend_xlsx(rows)

    def export_monthly_trend_xlsx_for_worker(
        self,
        date_from: date | None,
        date_to: date | None,
        include_empty: bool = False,
    ) -> bytes:
        self.validate_date_range(date_from, date_to)
        self.validate_trend_zero_fill_range(
            include_empty=include_empty,
            date_from=date_from,
            date_to=date_to,
            max_months=60,
        )
        records = self.repository.list_admin_monthly_trend(
            AdminReportFilter(date_from=date_from, date_to=date_to)
        )
        rows = [self.to_monthly_trend_dto(record) for record in records]
        if include_empty:
            rows = self.zero_fill_monthly_trend(rows, date_from=date_from, date_to=date_to)
        return self.to_monthly_trend_xlsx(rows)

    @staticmethod
    def validate_date_range(date_from: date | None, date_to: date | None) -> None:
        if date_from is not None and date_to is not None and date_from > date_to:
            raise AppError(422, "ADMIN_REPORT_DATE_RANGE_INVALID", "报表日期范围不合法")

    @classmethod
    def validate_trend_zero_fill_range(
        cls,
        *,
        include_empty: bool,
        date_from: date | None,
        date_to: date | None,
        max_days: int | None = None,
        max_months: int | None = None,
    ) -> None:
        if not include_empty:
            return
        if date_from is None or date_to is None:
            raise AppError(422, "ADMIN_REPORT_INCLUDE_EMPTY_RANGE_REQUIRED", "补零趋势必须提供开始和结束日期")
        if max_days is not None and (date_to - date_from).days + 1 > max_days:
            raise AppError(422, "ADMIN_REPORT_INCLUDE_EMPTY_RANGE_TOO_LARGE", "补零趋势日期范围过大")
        if max_months is not None and cls.month_span(date_from, date_to) > max_months:
            raise AppError(422, "ADMIN_REPORT_INCLUDE_EMPTY_RANGE_TOO_LARGE", "补零趋势月份范围过大")

    @staticmethod
    def month_span(date_from: date, date_to: date) -> int:
        return (date_to.year - date_from.year) * 12 + date_to.month - date_from.month + 1

    @classmethod
    def zero_fill_daily_trend(
        cls,
        rows: list[AdminDailyTrendDTO],
        *,
        date_from: date | None,
        date_to: date | None,
    ) -> list[AdminDailyTrendDTO]:
        assert date_from is not None and date_to is not None
        rows_by_date = {row.report_date: row for row in rows}
        day_count = (date_to - date_from).days + 1
        return [
            rows_by_date.get(current_date, cls.zero_daily_trend_dto(current_date))
            for current_date in (date_from + timedelta(days=offset) for offset in range(day_count))
        ]

    @classmethod
    def zero_fill_hourly_trend(
        cls,
        rows: list[AdminHourlyTrendDTO],
        *,
        date_from: date | None,
        date_to: date | None,
    ) -> list[AdminHourlyTrendDTO]:
        assert date_from is not None and date_to is not None
        rows_by_hour = {row.report_hour: row for row in rows}
        start = datetime.combine(date_from, datetime.min.time())
        hour_count = ((date_to - date_from).days + 1) * 24
        return [
            rows_by_hour.get(report_hour, cls.zero_hourly_trend_dto(report_hour))
            for report_hour in (
                (start + timedelta(hours=offset)).strftime("%Y-%m-%dT%H:00:00")
                for offset in range(hour_count)
            )
        ]

    @classmethod
    def zero_fill_monthly_trend(
        cls,
        rows: list[AdminMonthlyTrendDTO],
        *,
        date_from: date | None,
        date_to: date | None,
    ) -> list[AdminMonthlyTrendDTO]:
        assert date_from is not None and date_to is not None
        rows_by_month = {row.report_month: row for row in rows}
        months = cls.month_labels(date_from, date_to)
        return [rows_by_month.get(report_month, cls.zero_monthly_trend_dto(report_month)) for report_month in months]

    @staticmethod
    def month_labels(date_from: date, date_to: date) -> list[str]:
        current = date(date_from.year, date_from.month, 1)
        end = date(date_to.year, date_to.month, 1)
        labels = []
        while current <= end:
            labels.append(current.strftime("%Y-%m"))
            if current.month == 12:
                current = date(current.year + 1, 1, 1)
            else:
                current = date(current.year, current.month + 1, 1)
        return labels

    @staticmethod
    def zero_daily_trend_dto(report_date: date) -> AdminDailyTrendDTO:
        return AdminDailyTrendDTO(
            report_date=report_date,
            order_count=0,
            paid_order_count=0,
            completed_order_count=0,
            refunded_order_count=0,
            cancelled_order_count=0,
            net_paid_amount=Decimal("0.00"),
            ticket_count=0,
            sold_ticket_count=0,
            checked_in_ticket_count=0,
            refunded_ticket_count=0,
        )

    @staticmethod
    def zero_hourly_trend_dto(report_hour: str) -> AdminHourlyTrendDTO:
        return AdminHourlyTrendDTO(
            report_hour=report_hour,
            order_count=0,
            paid_order_count=0,
            completed_order_count=0,
            refunded_order_count=0,
            cancelled_order_count=0,
            net_paid_amount=Decimal("0.00"),
            ticket_count=0,
            sold_ticket_count=0,
            checked_in_ticket_count=0,
            refunded_ticket_count=0,
        )

    @staticmethod
    def zero_monthly_trend_dto(report_month: str) -> AdminMonthlyTrendDTO:
        return AdminMonthlyTrendDTO(
            report_month=report_month,
            order_count=0,
            paid_order_count=0,
            completed_order_count=0,
            refunded_order_count=0,
            cancelled_order_count=0,
            net_paid_amount=Decimal("0.00"),
            ticket_count=0,
            sold_ticket_count=0,
            checked_in_ticket_count=0,
            refunded_ticket_count=0,
        )

    @staticmethod
    def to_summary_dto(record: AdminReportSummaryRecord) -> AdminReportSummaryDTO:
        return AdminReportSummaryDTO(
            date_from=record.date_from,
            date_to=record.date_to,
            order_count=record.order_count,
            paid_order_count=record.paid_order_count,
            completed_order_count=record.completed_order_count,
            refunded_order_count=record.refunded_order_count,
            cancelled_order_count=record.cancelled_order_count,
            net_paid_amount=record.net_paid_amount,
            ticket_count=record.ticket_count,
            sold_ticket_count=record.sold_ticket_count,
            checked_in_ticket_count=record.checked_in_ticket_count,
            refunded_ticket_count=record.refunded_ticket_count,
        )

    @staticmethod
    def to_payment_reconciliation_dto(record: AdminPaymentReconciliationRecord) -> AdminPaymentReconciliationDTO:
        return AdminPaymentReconciliationDTO(
            date_from=record.date_from,
            date_to=record.date_to,
            order_net_paid_amount=record.order_net_paid_amount,
            captured_payment_amount=record.captured_payment_amount,
            refund_audit_amount=record.refund_audit_amount,
            expected_net_amount=record.expected_net_amount,
            unreconciled_amount=record.unreconciled_amount,
            captured_payment_count=record.captured_payment_count,
            refund_audit_log_count=record.refund_audit_log_count,
            reconciled=record.reconciled,
        )

    @staticmethod
    def to_product_breakdown_dto(record: AdminProductBreakdownRecord) -> AdminProductBreakdownDTO:
        return AdminProductBreakdownDTO(
            product_id=record.product_id,
            ticket_type_id=record.ticket_type_id,
            product_name=record.product_name,
            ticket_name=record.ticket_name,
            order_count=record.order_count,
            ticket_count=record.ticket_count,
            sold_ticket_count=record.sold_ticket_count,
            checked_in_ticket_count=record.checked_in_ticket_count,
            refunded_ticket_count=record.refunded_ticket_count,
            net_paid_amount=record.net_paid_amount,
        )

    @staticmethod
    def to_daily_trend_dto(record: AdminDailyTrendRecord) -> AdminDailyTrendDTO:
        return AdminDailyTrendDTO(
            report_date=record.report_date,
            order_count=record.order_count,
            paid_order_count=record.paid_order_count,
            completed_order_count=record.completed_order_count,
            refunded_order_count=record.refunded_order_count,
            cancelled_order_count=record.cancelled_order_count,
            net_paid_amount=record.net_paid_amount,
            ticket_count=record.ticket_count,
            sold_ticket_count=record.sold_ticket_count,
            checked_in_ticket_count=record.checked_in_ticket_count,
            refunded_ticket_count=record.refunded_ticket_count,
        )

    @staticmethod
    def to_hourly_trend_dto(record: AdminHourlyTrendRecord) -> AdminHourlyTrendDTO:
        return AdminHourlyTrendDTO(
            report_hour=record.report_hour,
            order_count=record.order_count,
            paid_order_count=record.paid_order_count,
            completed_order_count=record.completed_order_count,
            refunded_order_count=record.refunded_order_count,
            cancelled_order_count=record.cancelled_order_count,
            net_paid_amount=record.net_paid_amount,
            ticket_count=record.ticket_count,
            sold_ticket_count=record.sold_ticket_count,
            checked_in_ticket_count=record.checked_in_ticket_count,
            refunded_ticket_count=record.refunded_ticket_count,
        )

    @staticmethod
    def to_monthly_trend_dto(record: AdminMonthlyTrendRecord) -> AdminMonthlyTrendDTO:
        return AdminMonthlyTrendDTO(
            report_month=record.report_month,
            order_count=record.order_count,
            paid_order_count=record.paid_order_count,
            completed_order_count=record.completed_order_count,
            refunded_order_count=record.refunded_order_count,
            cancelled_order_count=record.cancelled_order_count,
            net_paid_amount=record.net_paid_amount,
            ticket_count=record.ticket_count,
            sold_ticket_count=record.sold_ticket_count,
            checked_in_ticket_count=record.checked_in_ticket_count,
            refunded_ticket_count=record.refunded_ticket_count,
        )

    @classmethod
    def to_orders_csv(cls, records: list[AdminOrderExportRecord]) -> str:
        output = io.StringIO(newline="")
        writer = csv.writer(output)
        writer.writerow(cls.ORDER_EXPORT_HEADERS)
        for row in cls.order_export_rows(records):
            writer.writerow(row)
        return "\ufeff" + output.getvalue()

    @classmethod
    def to_daily_trend_csv(cls, rows: list[AdminDailyTrendDTO]) -> str:
        return cls.to_csv(cls.DAILY_TREND_EXPORT_HEADERS, cls.daily_trend_export_rows(rows))

    @classmethod
    def to_hourly_trend_csv(cls, rows: list[AdminHourlyTrendDTO]) -> str:
        return cls.to_csv(cls.HOURLY_TREND_EXPORT_HEADERS, cls.hourly_trend_export_rows(rows))

    @classmethod
    def to_monthly_trend_csv(cls, rows: list[AdminMonthlyTrendDTO]) -> str:
        return cls.to_csv(cls.MONTHLY_TREND_EXPORT_HEADERS, cls.monthly_trend_export_rows(rows))

    @classmethod
    def to_payment_reconciliation_csv(cls, row: AdminPaymentReconciliationDTO) -> str:
        return cls.to_csv(cls.PAYMENT_RECONCILIATION_EXPORT_HEADERS, [cls.payment_reconciliation_export_row(row)])

    @classmethod
    def to_product_breakdown_csv(cls, rows: list[AdminProductBreakdownDTO]) -> str:
        return cls.to_csv(cls.PRODUCT_BREAKDOWN_EXPORT_HEADERS, cls.product_breakdown_export_rows(rows))

    @classmethod
    def to_product_breakdown_xlsx(cls, rows: list[AdminProductBreakdownDTO]) -> bytes:
        return cls.to_xlsx_workbook(
            [cls.PRODUCT_BREAKDOWN_EXPORT_HEADERS, *cls.product_breakdown_export_rows(rows)],
            sheet_name="ProductBreakdown",
        )

    @classmethod
    def to_payment_reconciliation_xlsx(cls, row: AdminPaymentReconciliationDTO) -> bytes:
        return cls.to_xlsx_workbook(
            [cls.PAYMENT_RECONCILIATION_EXPORT_HEADERS, cls.payment_reconciliation_export_row(row)],
            sheet_name="PaymentReconciliation",
        )

    @classmethod
    def to_daily_trend_xlsx(cls, rows: list[AdminDailyTrendDTO]) -> bytes:
        return cls.to_xlsx_workbook(
            [cls.DAILY_TREND_EXPORT_HEADERS, *cls.daily_trend_export_rows(rows)],
            sheet_name="DailyTrend",
        )

    @classmethod
    def to_hourly_trend_xlsx(cls, rows: list[AdminHourlyTrendDTO]) -> bytes:
        return cls.to_xlsx_workbook(
            [cls.HOURLY_TREND_EXPORT_HEADERS, *cls.hourly_trend_export_rows(rows)],
            sheet_name="HourlyTrend",
        )

    @classmethod
    def to_monthly_trend_xlsx(cls, rows: list[AdminMonthlyTrendDTO]) -> bytes:
        return cls.to_xlsx_workbook(
            [cls.MONTHLY_TREND_EXPORT_HEADERS, *cls.monthly_trend_export_rows(rows)],
            sheet_name="MonthlyTrend",
        )

    @classmethod
    def to_csv(cls, headers: tuple[str, ...], rows: list[list[str]]) -> str:
        output = io.StringIO(newline="")
        writer = csv.writer(output)
        writer.writerow(headers)
        for row in rows:
            writer.writerow(row)
        return "\ufeff" + output.getvalue()

    @classmethod
    def to_orders_xlsx(cls, records: list[AdminOrderExportRecord]) -> bytes:
        rows = [cls.ORDER_EXPORT_HEADERS, *cls.order_export_rows(records)]
        return cls.to_xlsx_workbook(rows, sheet_name="Orders")

    @classmethod
    def to_xlsx_workbook(cls, rows: list[tuple[str, ...] | list[str]], sheet_name: str) -> bytes:
        worksheet_xml = cls.build_xlsx_worksheet(rows)
        sheet_name_attribute = quoteattr(cls.clean_xml_text(sheet_name))
        workbook_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name=%s sheetId="1" r:id="rId1"/></sheets></workbook>""" % sheet_name_attribute
        workbook_rels_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>"""
        root_rels_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>"""
        content_types_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>"""

        output = io.BytesIO()
        with zipfile.ZipFile(output, mode="w", compression=zipfile.ZIP_DEFLATED) as workbook:
            workbook.writestr("[Content_Types].xml", content_types_xml)
            workbook.writestr("_rels/.rels", root_rels_xml)
            workbook.writestr("xl/workbook.xml", workbook_xml)
            workbook.writestr("xl/_rels/workbook.xml.rels", workbook_rels_xml)
            workbook.writestr("xl/worksheets/sheet1.xml", worksheet_xml)
        return output.getvalue()

    @classmethod
    def order_export_rows(cls, records: list[AdminOrderExportRecord]) -> list[list[str]]:
        return [
            [
                cls.safe_spreadsheet_cell(record.order_no),
                cls.safe_spreadsheet_cell(record.buyer_name),
                cls.safe_spreadsheet_cell(OrderService.mask_phone(record.buyer_phone)),
                cls.safe_spreadsheet_cell(record.order_status),
                cls.safe_spreadsheet_cell(record.payment_status),
                cls.safe_spreadsheet_cell(record.total_amount),
                cls.safe_spreadsheet_cell(record.payable_amount),
                cls.safe_spreadsheet_cell(cls.format_datetime(record.order_time)),
                cls.safe_spreadsheet_cell(record.item_count),
            ]
            for record in records
        ]

    @classmethod
    def daily_trend_export_rows(cls, rows: list[AdminDailyTrendDTO]) -> list[list[str]]:
        return [
            [
                cls.safe_spreadsheet_cell(row.report_date.isoformat()),
                cls.safe_spreadsheet_cell(row.order_count),
                cls.safe_spreadsheet_cell(row.paid_order_count),
                cls.safe_spreadsheet_cell(row.completed_order_count),
                cls.safe_spreadsheet_cell(row.refunded_order_count),
                cls.safe_spreadsheet_cell(row.cancelled_order_count),
                cls.safe_spreadsheet_cell(row.net_paid_amount),
                cls.safe_spreadsheet_cell(row.ticket_count),
                cls.safe_spreadsheet_cell(row.sold_ticket_count),
                cls.safe_spreadsheet_cell(row.checked_in_ticket_count),
                cls.safe_spreadsheet_cell(row.refunded_ticket_count),
            ]
            for row in rows
        ]

    @classmethod
    def hourly_trend_export_rows(cls, rows: list[AdminHourlyTrendDTO]) -> list[list[str]]:
        return [
            [
                cls.safe_spreadsheet_cell(row.report_hour),
                cls.safe_spreadsheet_cell(row.order_count),
                cls.safe_spreadsheet_cell(row.paid_order_count),
                cls.safe_spreadsheet_cell(row.completed_order_count),
                cls.safe_spreadsheet_cell(row.refunded_order_count),
                cls.safe_spreadsheet_cell(row.cancelled_order_count),
                cls.safe_spreadsheet_cell(row.net_paid_amount),
                cls.safe_spreadsheet_cell(row.ticket_count),
                cls.safe_spreadsheet_cell(row.sold_ticket_count),
                cls.safe_spreadsheet_cell(row.checked_in_ticket_count),
                cls.safe_spreadsheet_cell(row.refunded_ticket_count),
            ]
            for row in rows
        ]

    @classmethod
    def monthly_trend_export_rows(cls, rows: list[AdminMonthlyTrendDTO]) -> list[list[str]]:
        return [
            [
                cls.safe_spreadsheet_cell(row.report_month),
                cls.safe_spreadsheet_cell(row.order_count),
                cls.safe_spreadsheet_cell(row.paid_order_count),
                cls.safe_spreadsheet_cell(row.completed_order_count),
                cls.safe_spreadsheet_cell(row.refunded_order_count),
                cls.safe_spreadsheet_cell(row.cancelled_order_count),
                cls.safe_spreadsheet_cell(row.net_paid_amount),
                cls.safe_spreadsheet_cell(row.ticket_count),
                cls.safe_spreadsheet_cell(row.sold_ticket_count),
                cls.safe_spreadsheet_cell(row.checked_in_ticket_count),
                cls.safe_spreadsheet_cell(row.refunded_ticket_count),
            ]
            for row in rows
        ]

    @classmethod
    def payment_reconciliation_export_row(cls, row: AdminPaymentReconciliationDTO) -> list[str]:
        return [
            cls.safe_spreadsheet_cell(row.date_from.isoformat() if row.date_from else ""),
            cls.safe_spreadsheet_cell(row.date_to.isoformat() if row.date_to else ""),
            cls.safe_spreadsheet_cell(row.order_net_paid_amount),
            cls.safe_spreadsheet_cell(row.captured_payment_amount),
            cls.safe_spreadsheet_cell(row.refund_audit_amount),
            cls.safe_spreadsheet_cell(row.expected_net_amount),
            cls.safe_spreadsheet_cell(row.unreconciled_amount),
            cls.safe_spreadsheet_cell(row.captured_payment_count),
            cls.safe_spreadsheet_cell(row.refund_audit_log_count),
            cls.safe_spreadsheet_cell("true" if row.reconciled else "false"),
        ]

    @classmethod
    def product_breakdown_export_rows(cls, rows: list[AdminProductBreakdownDTO]) -> list[list[str]]:
        return [
            [
                cls.safe_spreadsheet_cell(row.product_id),
                cls.safe_spreadsheet_cell(row.ticket_type_id),
                cls.safe_spreadsheet_cell(row.product_name),
                cls.safe_spreadsheet_cell(row.ticket_name),
                cls.safe_spreadsheet_cell(row.order_count),
                cls.safe_spreadsheet_cell(row.ticket_count),
                cls.safe_spreadsheet_cell(row.sold_ticket_count),
                cls.safe_spreadsheet_cell(row.checked_in_ticket_count),
                cls.safe_spreadsheet_cell(row.refunded_ticket_count),
                cls.safe_spreadsheet_cell(row.net_paid_amount),
            ]
            for row in rows
        ]

    @classmethod
    def build_xlsx_worksheet(cls, rows: list[tuple[str, ...] | list[str]]) -> str:
        row_xml = []
        for row_index, row in enumerate(rows, start=1):
            cells = []
            for column_index, value in enumerate(row, start=1):
                cell_ref = f"{cls.xlsx_column_name(column_index)}{row_index}"
                text = escape(cls.safe_xlsx_text(value))
                cells.append(f'<c r="{cell_ref}" t="inlineStr"><is><t>{text}</t></is></c>')
            row_xml.append(f'<row r="{row_index}">{"".join(cells)}</row>')
        return (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            f'<sheetData>{"".join(row_xml)}</sheetData>'
            "</worksheet>"
        )

    @staticmethod
    def clean_xml_text(value: str) -> str:
        return "".join(
            character
            for character in value
            if (
                (codepoint := ord(character)) in (0x09, 0x0A, 0x0D)
                or 0x20 <= codepoint <= 0xD7FF
                or 0xE000 <= codepoint <= 0xFFFD
                or 0x10000 <= codepoint <= 0x10FFFF
            )
        )

    @staticmethod
    def xlsx_column_name(index: int) -> str:
        name = ""
        while index:
            index, remainder = divmod(index - 1, 26)
            name = chr(65 + remainder) + name
        return name

    @staticmethod
    def safe_spreadsheet_cell(value: object) -> str:
        text = str(value)
        if text.startswith(("=", "+", "-", "@", "\t", "\r", "\n")) or text.lstrip(" ").startswith(
            ("=", "+", "-", "@", "\t", "\r", "\n")
        ):
            return f"'{text}"
        return text

    @classmethod
    def safe_xlsx_text(cls, value: object) -> str:
        return cls.safe_spreadsheet_cell(cls.clean_xml_text(str(value)))

    safe_csv_cell = safe_spreadsheet_cell

    @staticmethod
    def format_datetime(value: datetime) -> str:
        if value.tzinfo is UTC:
            return value.isoformat().replace("+00:00", "Z")
        return value.isoformat()

    @staticmethod
    def order_export_filename(date_from: date | None, date_to: date | None) -> str:
        return f"{AdminReportService.order_export_filename_stem(date_from=date_from, date_to=date_to)}.csv"

    @staticmethod
    def order_export_xlsx_filename(date_from: date | None, date_to: date | None) -> str:
        return f"{AdminReportService.order_export_filename_stem(date_from=date_from, date_to=date_to)}.xlsx"

    @staticmethod
    def order_export_filename_stem(date_from: date | None, date_to: date | None) -> str:
        start = date_from.strftime("%Y%m%d") if date_from else "start"
        end = date_to.strftime("%Y%m%d") if date_to else "end"
        return f"admin-orders-{start}-{end}"

    @staticmethod
    def trend_export_filename(trend: str, date_from: date | None, date_to: date | None) -> str:
        start = date_from.strftime("%Y%m%d") if date_from else "start"
        end = date_to.strftime("%Y%m%d") if date_to else "end"
        return f"admin-{trend}-trend-{start}-{end}.csv"

    @staticmethod
    def payment_reconciliation_export_filename(date_from: date | None, date_to: date | None) -> str:
        return f"{AdminReportService.payment_reconciliation_export_filename_stem(date_from=date_from, date_to=date_to)}.csv"

    @staticmethod
    def payment_reconciliation_export_xlsx_filename(date_from: date | None, date_to: date | None) -> str:
        return f"{AdminReportService.payment_reconciliation_export_filename_stem(date_from=date_from, date_to=date_to)}.xlsx"

    @staticmethod
    def product_breakdown_export_filename(date_from: date | None, date_to: date | None) -> str:
        return f"{AdminReportService.product_breakdown_export_filename_stem(date_from=date_from, date_to=date_to)}.csv"

    @staticmethod
    def product_breakdown_export_xlsx_filename(date_from: date | None, date_to: date | None) -> str:
        return f"{AdminReportService.product_breakdown_export_filename_stem(date_from=date_from, date_to=date_to)}.xlsx"

    @staticmethod
    def product_breakdown_export_filename_stem(date_from: date | None, date_to: date | None) -> str:
        start = date_from.strftime("%Y%m%d") if date_from else "start"
        end = date_to.strftime("%Y%m%d") if date_to else "end"
        return f"admin-product-breakdown-{start}-{end}"

    @staticmethod
    def payment_reconciliation_export_filename_stem(date_from: date | None, date_to: date | None) -> str:
        start = date_from.strftime("%Y%m%d") if date_from else "start"
        end = date_to.strftime("%Y%m%d") if date_to else "end"
        return f"admin-payment-reconciliation-{start}-{end}"

    @staticmethod
    def trend_export_xlsx_filename(trend: str, date_from: date | None, date_to: date | None) -> str:
        start = date_from.strftime("%Y%m%d") if date_from else "start"
        end = date_to.strftime("%Y%m%d") if date_to else "end"
        return f"admin-{trend}-trend-{start}-{end}.xlsx"


def get_admin_report_service(
    repository: OrderRepository = Depends(get_order_repository),
    admin_auth_service: AdminAuthService = Depends(get_admin_auth_service),
) -> AdminReportService:
    return AdminReportService(repository, admin_auth_service)


class MockPaymentCallbackService:
    def __init__(self, repository: OrderRepository, settings: AppSettings):
        self.repository = repository
        self.settings = settings

    def handle_callback(
        self,
        raw_body: bytes,
        timestamp_header: str | None,
        signature_header: str | None,
    ) -> MockPaymentCallbackDTO:
        self.verify_signature(raw_body, timestamp_header, signature_header)
        try:
            payload = MockPaymentCallbackRequest.model_validate_json(raw_body)
        except ValidationError as exc:
            raise AppError(422, "VALIDATION_ERROR", "请求参数不合法") from exc
        if payload.payment_status != "SUCCESS":
            raise AppError(422, "MOCKPAY_EVENT_INVALID", "支付回调事件不合法")

        try:
            record = self.repository.process_mock_payment_callback(
                event_id=payload.event_id,
                order_no=payload.order_no,
                payment_no=payload.payment_no,
                transaction_no=payload.transaction_no,
                paid_amount=payload.paid_amount,
                ticket_code_factory=OrderService.generate_ticket_code,
            )
        except OrderQuotaNotEnoughError as exc:
            raise AppError(409, "TIME_SLOT_QUOTA_NOT_ENOUGH", "当前时段余票不足") from exc
        except OrderPaymentAmountMismatchError as exc:
            raise AppError(409, "MOCKPAY_AMOUNT_MISMATCH", "支付回调金额不匹配") from exc
        except OrderPaymentStateError as exc:
            raise AppError(409, "ORDER_NOT_PAYABLE", "订单状态不可支付") from exc

        if record is None:
            raise AppError(404, "MOCKPAY_ORDER_NOT_FOUND", "支付回调订单不存在")
        return self.to_callback_dto(record)

    def verify_signature(self, raw_body: bytes, timestamp_header: str | None, signature_header: str | None) -> None:
        timestamp_text = (timestamp_header or "").strip()
        provided_signature = (signature_header or "").strip().lower()
        if not timestamp_text or not provided_signature:
            raise AppError(401, "MOCKPAY_SIGNATURE_INVALID", "支付回调签名无效")
        if not re.fullmatch(r"[0-9a-f]{64}", provided_signature):
            raise AppError(401, "MOCKPAY_SIGNATURE_INVALID", "支付回调签名无效")
        try:
            timestamp_value = int(timestamp_text)
        except ValueError as exc:
            raise AppError(401, "MOCKPAY_TIMESTAMP_INVALID", "支付回调时间戳无效") from exc

        now = int(time.time())
        tolerance = self.settings.security.mockpay_callback_tolerance_seconds
        if abs(now - timestamp_value) > tolerance:
            raise AppError(401, "MOCKPAY_TIMESTAMP_INVALID", "支付回调时间戳无效")

        message = timestamp_text.encode("utf-8") + b"." + raw_body
        expected_signature = hmac.new(
            self.settings.security.mockpay_callback_secret.encode("utf-8"),
            message,
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(expected_signature, provided_signature):
            raise AppError(401, "MOCKPAY_SIGNATURE_INVALID", "支付回调签名无效")

    @staticmethod
    def to_callback_dto(record: MockPaymentCallbackRecord) -> MockPaymentCallbackDTO:
        return MockPaymentCallbackDTO(
            event_id=record.event_id,
            order_no=record.order_no,
            order_status=record.order_status,
            payment_status=record.payment_status,
            idempotent=record.idempotent,
            processed_at=record.processed_at,
        )


def get_mock_payment_callback_service(
    repository: OrderRepository = Depends(get_order_repository),
    settings: AppSettings = Depends(get_settings),
) -> MockPaymentCallbackService:
    return MockPaymentCallbackService(repository, settings)
