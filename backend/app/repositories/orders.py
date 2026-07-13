from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from collections.abc import Callable
from typing import Protocol
from zoneinfo import ZoneInfo

from psycopg import errors

from app.core.db import connect_db

PAYMENT_HOLD_MINUTES = 15


@dataclass(frozen=True)
class OrderQuoteRecord:
    scenic_spot_id: int
    product_id: int
    ticket_type_id: int
    product_name: str
    ticket_name: str
    time_slot_id: int
    visit_date: date
    slot_start_time: time
    slot_end_time: time
    original_price: Decimal
    sale_price: Decimal
    quota_remaining: int


@dataclass(frozen=True)
class OrderCreateItemRecord:
    item_no: str
    product_id: int
    ticket_type_id: int
    product_name: str
    ticket_name: str
    time_slot_id: int
    visit_date: date
    slot_start_time: time
    slot_end_time: time
    original_price: Decimal
    final_price: Decimal
    item_status: str
    ticket_code: str | None = None
    passenger_name: str = ""
    passenger_id_type: str = ""
    passenger_id_number: str = ""
    passenger_phone: str = ""
    raft_no: int | None = None
    raft_seat_no: int | None = None
    raft_assigned_at: datetime | None = None


@dataclass(frozen=True)
class OrderRecord:
    order_id: int
    order_no: str
    visitor_id: int
    buyer_name: str
    buyer_phone: str
    order_status: str
    payment_status: str
    total_amount: Decimal
    payable_amount: Decimal
    order_time: datetime
    items: list[OrderCreateItemRecord]


@dataclass(frozen=True)
class AdminOrderSummaryRecord:
    order_id: int
    order_no: str
    visitor_id: int
    buyer_name: str
    buyer_phone: str
    order_status: str
    payment_status: str
    total_amount: Decimal
    payable_amount: Decimal
    order_time: datetime
    item_count: int


@dataclass(frozen=True)
class AdminOrderListFilter:
    status: str | None
    payment_status: str | None
    order_no: str | None
    buyer_phone: str | None
    page: int
    page_size: int


@dataclass(frozen=True)
class AdminOrderListRecord:
    items: list[AdminOrderSummaryRecord]
    total: int
    page: int
    page_size: int


@dataclass(frozen=True)
class AdminCheckInRecord:
    order_no: str
    item_no: str
    ticket_code: str
    order_status: str
    item_status: str
    checked_in_at: datetime
    raft_no: int | None = None
    raft_seat_no: int | None = None


@dataclass(frozen=True)
class AdminUndoCheckInRecord:
    order_no: str
    item_no: str
    ticket_code: str
    order_status: str
    item_status: str
    undone_at: datetime


@dataclass(frozen=True)
class AdminCheckInAuditInput:
    operator_admin_user_id: int
    operator_username: str
    operator_display_name: str
    request_id: str | None
    reason: str | None = None
    source_ip: str | None = None
    device_id: str | None = None
    admin_session_id: int | None = None
    user_agent: str | None = None


@dataclass(frozen=True)
class AdminCheckInAuditLogRecord:
    order_no: str
    item_no: str
    ticket_code: str
    action: str
    operator_username: str
    operator_display_name: str
    request_id: str | None
    created_at: datetime
    reason: str | None = None


@dataclass(frozen=True)
class AdminCheckInAuditLogListFilter:
    ticket_code: str | None
    order_no: str | None
    operator_username: str | None
    reason: str | None
    date_from: date | None
    date_to: date | None
    page: int
    page_size: int


@dataclass(frozen=True)
class AdminCheckInAuditLogExportFilter:
    ticket_code: str | None
    order_no: str | None
    operator_username: str | None
    reason: str | None
    date_from: date | None
    date_to: date | None
    row_limit: int | None = None


@dataclass(frozen=True)
class AdminCheckInAuditLogListRecord:
    items: list[AdminCheckInAuditLogRecord]
    total: int
    page: int
    page_size: int


@dataclass(frozen=True)
class AdminCheckInFailureAuditLogRecord:
    ticket_code: str
    action: str
    failure_code: str
    failure_message: str
    operator_username: str
    operator_display_name: str
    request_id: str | None
    created_at: datetime


@dataclass(frozen=True)
class AdminCheckInFailureAuditLogListFilter:
    ticket_code: str | None
    failure_code: str | None
    operator_username: str | None
    date_from: date | None
    date_to: date | None
    page: int
    page_size: int


@dataclass(frozen=True)
class AdminCheckInFailureAuditLogExportFilter:
    ticket_code: str | None
    failure_code: str | None
    operator_username: str | None
    date_from: date | None
    date_to: date | None
    row_limit: int | None = None


@dataclass(frozen=True)
class AdminCheckInFailureAuditLogListRecord:
    items: list[AdminCheckInFailureAuditLogRecord]
    total: int
    page: int
    page_size: int


@dataclass(frozen=True)
class AdminRefundRecord:
    order_no: str
    order_status: str
    payment_status: str
    refunded_amount: Decimal
    refunded_item_count: int
    refunded_at: datetime


@dataclass(frozen=True)
class AdminPartialRefundRecord:
    order_no: str
    order_status: str
    payment_status: str
    refunded_amount: Decimal
    refunded_item_count: int
    refunded_item_nos: list[str]
    refunded_at: datetime


@dataclass(frozen=True)
class AdminRefundAuditInput:
    operator_admin_user_id: int | None
    operator_username: str
    operator_display_name: str
    reason: str | None
    request_id: str | None
    source_ip: str | None = None
    device_id: str | None = None
    admin_session_id: int | None = None
    user_agent: str | None = None
    operator_type: str = "ADMIN"
    operator_visitor_id: int | None = None


@dataclass(frozen=True)
class AdminRefundAuditLogRecord:
    order_no: str
    refund_type: str
    refunded_amount: Decimal
    refunded_item_count: int
    refunded_item_nos: list[str]
    reason: str | None
    operator_username: str
    operator_display_name: str
    request_id: str | None
    created_at: datetime


@dataclass(frozen=True)
class AdminRefundAuditLogListFilter:
    refund_type: str | None
    order_no: str | None
    operator_username: str | None
    date_from: date | None
    date_to: date | None
    page: int
    page_size: int


@dataclass(frozen=True)
class AdminRefundAuditLogExportFilter:
    refund_type: str | None
    order_no: str | None
    operator_username: str | None
    date_from: date | None
    date_to: date | None
    row_limit: int | None = None


@dataclass(frozen=True)
class AdminRefundAuditLogListRecord:
    items: list[AdminRefundAuditLogRecord]
    total: int
    page: int
    page_size: int


@dataclass(frozen=True)
class AdminReportFilter:
    date_from: date | None
    date_to: date | None
    row_limit: int | None = None


@dataclass(frozen=True)
class AdminReportSummaryRecord:
    date_from: date | None
    date_to: date | None
    order_count: int
    paid_order_count: int
    completed_order_count: int
    refunded_order_count: int
    cancelled_order_count: int
    net_paid_amount: Decimal
    ticket_count: int
    sold_ticket_count: int
    checked_in_ticket_count: int
    refunded_ticket_count: int


@dataclass(frozen=True)
class AdminPaymentReconciliationRecord:
    date_from: date | None
    date_to: date | None
    order_net_paid_amount: Decimal
    captured_payment_amount: Decimal
    refund_audit_amount: Decimal
    expected_net_amount: Decimal
    unreconciled_amount: Decimal
    captured_payment_count: int
    refund_audit_log_count: int
    reconciled: bool


@dataclass(frozen=True)
class AdminProductBreakdownRecord:
    product_id: int
    ticket_type_id: int
    product_name: str
    ticket_name: str
    order_count: int
    ticket_count: int
    sold_ticket_count: int
    checked_in_ticket_count: int
    refunded_ticket_count: int
    net_paid_amount: Decimal


@dataclass(frozen=True)
class AdminDailyTrendRecord:
    report_date: date
    order_count: int
    paid_order_count: int
    completed_order_count: int
    refunded_order_count: int
    cancelled_order_count: int
    net_paid_amount: Decimal
    ticket_count: int
    sold_ticket_count: int
    checked_in_ticket_count: int
    refunded_ticket_count: int


@dataclass(frozen=True)
class AdminHourlyTrendRecord:
    report_hour: str
    order_count: int
    paid_order_count: int
    completed_order_count: int
    refunded_order_count: int
    cancelled_order_count: int
    net_paid_amount: Decimal
    ticket_count: int
    sold_ticket_count: int
    checked_in_ticket_count: int
    refunded_ticket_count: int


@dataclass(frozen=True)
class AdminMonthlyTrendRecord:
    report_month: str
    order_count: int
    paid_order_count: int
    completed_order_count: int
    refunded_order_count: int
    cancelled_order_count: int
    net_paid_amount: Decimal
    ticket_count: int
    sold_ticket_count: int
    checked_in_ticket_count: int
    refunded_ticket_count: int


@dataclass(frozen=True)
class AdminOrderExportRecord:
    order_no: str
    buyer_name: str
    buyer_phone: str
    order_status: str
    payment_status: str
    total_amount: Decimal
    payable_amount: Decimal
    order_time: datetime
    item_count: int


@dataclass(frozen=True)
class MockPaymentCallbackRecord:
    event_id: str
    order_no: str
    order_status: str
    payment_status: str
    idempotent: bool
    processed_at: datetime


@dataclass(frozen=True)
class PendingOrderItemInput:
    item_no: str
    product_id: int
    ticket_type_id: int
    product_name: str
    ticket_name: str
    time_slot_id: int
    visit_date: date
    slot_start_time: time
    slot_end_time: time
    original_price: Decimal
    final_price: Decimal
    passenger_name: str
    passenger_id_type: str
    passenger_id_number: str
    passenger_phone: str
    passenger_template_id: int | None = None


class OrderRepository(Protocol):
    def get_order_quote(self, product_id: int, time_slot_id: int, visit_date: date) -> OrderQuoteRecord | None:
        ...

    def expire_unpaid_orders(self, visitor_id: int, expired_before: datetime) -> int:
        ...

    def create_pending_order(
        self,
        order_no: str,
        visitor_id: int,
        scenic_spot_id: int,
        buyer_name: str,
        buyer_phone: str,
        items: list[PendingOrderItemInput],
    ) -> OrderRecord:
        ...

    def list_orders_for_visitor(self, visitor_id: int, order_status: str | None = None) -> list[OrderRecord]:
        ...

    def get_order_for_visitor(self, visitor_id: int, order_no: str) -> OrderRecord | None:
        ...

    def pay_order(
        self,
        order_no: str,
        visitor_id: int,
        idempotency_key: str,
        payment_no: str,
        transaction_no: str,
        ticket_code_factory: Callable[[], str],
    ) -> OrderRecord | None:
        ...

    def process_mock_payment_callback(
        self,
        event_id: str,
        order_no: str,
        payment_no: str,
        transaction_no: str,
        paid_amount: Decimal,
        ticket_code_factory: Callable[[], str],
    ) -> MockPaymentCallbackRecord | None:
        ...

    def cancel_order(self, order_no: str, visitor_id: int) -> OrderRecord | None:
        ...

    def list_orders_for_admin(self, filters: AdminOrderListFilter) -> AdminOrderListRecord:
        ...

    def get_order_for_admin(self, order_no: str) -> OrderRecord | None:
        ...

    def check_in_ticket(self, ticket_code: str, audit: AdminCheckInAuditInput) -> AdminCheckInRecord | None:
        ...

    def undo_check_in_ticket(self, ticket_code: str, audit: AdminCheckInAuditInput) -> AdminUndoCheckInRecord | None:
        ...

    def list_check_in_audit_logs(self, ticket_code: str) -> list[AdminCheckInAuditLogRecord] | None:
        ...

    def list_check_in_audit_log_entries(
        self,
        filters: AdminCheckInAuditLogListFilter,
    ) -> AdminCheckInAuditLogListRecord:
        ...

    def list_check_in_audit_log_export_rows(
        self,
        filters: AdminCheckInAuditLogExportFilter,
    ) -> list[AdminCheckInAuditLogRecord]:
        ...

    def record_check_in_failure_audit_log(
        self,
        ticket_code: str,
        action: str,
        failure_code: str,
        failure_message: str,
        audit: AdminCheckInAuditInput,
    ) -> None:
        ...

    def list_check_in_failure_audit_log_entries(
        self,
        filters: AdminCheckInFailureAuditLogListFilter,
    ) -> AdminCheckInFailureAuditLogListRecord:
        ...

    def list_check_in_failure_audit_log_export_rows(
        self,
        filters: AdminCheckInFailureAuditLogExportFilter,
    ) -> list[AdminCheckInFailureAuditLogRecord]:
        ...

    def refund_order(
        self,
        order_no: str,
        audit: AdminRefundAuditInput,
        visitor_id: int | None = None,
        refund_now: datetime | None = None,
    ) -> AdminRefundRecord | None:
        ...

    def refund_order_items(
        self,
        order_no: str,
        item_nos: list[str],
        audit: AdminRefundAuditInput,
    ) -> AdminPartialRefundRecord | None:
        ...

    def list_refund_audit_logs(self, order_no: str) -> list[AdminRefundAuditLogRecord] | None:
        ...

    def list_refund_audit_log_entries(
        self,
        filters: AdminRefundAuditLogListFilter,
    ) -> AdminRefundAuditLogListRecord:
        ...

    def list_refund_audit_log_export_rows(
        self,
        filters: AdminRefundAuditLogExportFilter,
    ) -> list[AdminRefundAuditLogRecord]:
        ...

    def get_admin_report_summary(self, filters: AdminReportFilter) -> AdminReportSummaryRecord:
        ...

    def get_admin_payment_reconciliation(self, filters: AdminReportFilter) -> AdminPaymentReconciliationRecord:
        ...

    def list_admin_product_breakdown(self, filters: AdminReportFilter) -> list[AdminProductBreakdownRecord]:
        ...

    def list_admin_daily_trend(self, filters: AdminReportFilter) -> list[AdminDailyTrendRecord]:
        ...

    def list_admin_hourly_trend(self, filters: AdminReportFilter) -> list[AdminHourlyTrendRecord]:
        ...

    def list_admin_monthly_trend(self, filters: AdminReportFilter) -> list[AdminMonthlyTrendRecord]:
        ...

    def list_admin_order_export_rows(self, filters: AdminReportFilter) -> list[AdminOrderExportRecord]:
        ...


def quote_from_row(row: dict) -> OrderQuoteRecord:
    return OrderQuoteRecord(
        scenic_spot_id=row["scenic_spot_id"],
        product_id=row["product_id"],
        ticket_type_id=row["ticket_type_id"],
        product_name=row["product_name"],
        ticket_name=row["ticket_name"],
        time_slot_id=row["time_slot_id"],
        visit_date=row["visit_date"],
        slot_start_time=row["slot_start_time"],
        slot_end_time=row["slot_end_time"],
        original_price=row["original_price"],
        sale_price=row["sale_price"],
        quota_remaining=max(row["quota_remaining"], 0),
    )


def item_from_row(row: dict) -> OrderCreateItemRecord:
    return OrderCreateItemRecord(
        item_no=row["item_no"],
        product_id=row["product_id"],
        ticket_type_id=row["ticket_type_id"],
        product_name=row["product_name"],
        ticket_name=row["ticket_name"],
        time_slot_id=row["time_slot_id"],
        visit_date=row["visit_date"],
        slot_start_time=row["slot_start_time"],
        slot_end_time=row["slot_end_time"],
        original_price=row["original_price"],
        final_price=row["final_price"],
        item_status=row["item_status"],
        ticket_code=row.get("ticket_code"),
        passenger_name=row.get("passenger_name", ""),
        passenger_id_type=row.get("passenger_id_type", ""),
        passenger_id_number=row.get("passenger_id_number", ""),
        passenger_phone=row.get("passenger_phone", ""),
        raft_no=row.get("raft_no"),
        raft_seat_no=row.get("raft_seat_no"),
        raft_assigned_at=row.get("raft_assigned_at"),
    )


def order_from_row(row: dict, items: list[OrderCreateItemRecord]) -> OrderRecord:
    return OrderRecord(
        order_id=row["order_id"],
        order_no=row["order_no"],
        visitor_id=row["visitor_id"],
        buyer_name=row["buyer_name"],
        buyer_phone=row["buyer_phone"],
        order_status=row["order_status"],
        payment_status=row["payment_status"],
        total_amount=row["total_amount"],
        payable_amount=row["payable_amount"],
        order_time=row["order_time"],
        items=items,
    )


def admin_summary_from_row(row: dict) -> AdminOrderSummaryRecord:
    return AdminOrderSummaryRecord(
        order_id=row["order_id"],
        order_no=row["order_no"],
        visitor_id=row["visitor_id"],
        buyer_name=row["buyer_name"],
        buyer_phone=row["buyer_phone"],
        order_status=row["order_status"],
        payment_status=row["payment_status"],
        total_amount=row["total_amount"],
        payable_amount=row["payable_amount"],
        order_time=row["order_time"],
        item_count=row["item_count"],
    )


def admin_order_export_from_row(row: dict) -> AdminOrderExportRecord:
    return AdminOrderExportRecord(
        order_no=row["order_no"],
        buyer_name=row["buyer_name"],
        buyer_phone=row["buyer_phone"],
        order_status=row["order_status"],
        payment_status=row["payment_status"],
        total_amount=row["total_amount"],
        payable_amount=row["payable_amount"],
        order_time=row["order_time"],
        item_count=row["item_count"],
    )


def admin_product_breakdown_from_row(row: dict) -> AdminProductBreakdownRecord:
    return AdminProductBreakdownRecord(
        product_id=row["product_id"],
        ticket_type_id=row["ticket_type_id"],
        product_name=row["product_name"],
        ticket_name=row["ticket_name"],
        order_count=row["order_count"],
        ticket_count=row["ticket_count"],
        sold_ticket_count=row["sold_ticket_count"],
        checked_in_ticket_count=row["checked_in_ticket_count"],
        refunded_ticket_count=row["refunded_ticket_count"],
        net_paid_amount=row["net_paid_amount"],
    )


def admin_daily_trend_from_row(row: dict) -> AdminDailyTrendRecord:
    return AdminDailyTrendRecord(
        report_date=row["report_date"],
        order_count=row["order_count"],
        paid_order_count=row["paid_order_count"],
        completed_order_count=row["completed_order_count"],
        refunded_order_count=row["refunded_order_count"],
        cancelled_order_count=row["cancelled_order_count"],
        net_paid_amount=row["net_paid_amount"],
        ticket_count=row["ticket_count"],
        sold_ticket_count=row["sold_ticket_count"],
        checked_in_ticket_count=row["checked_in_ticket_count"],
        refunded_ticket_count=row["refunded_ticket_count"],
    )


def admin_hourly_trend_from_row(row: dict) -> AdminHourlyTrendRecord:
    return AdminHourlyTrendRecord(
        report_hour=row["report_hour"],
        order_count=row["order_count"],
        paid_order_count=row["paid_order_count"],
        completed_order_count=row["completed_order_count"],
        refunded_order_count=row["refunded_order_count"],
        cancelled_order_count=row["cancelled_order_count"],
        net_paid_amount=row["net_paid_amount"],
        ticket_count=row["ticket_count"],
        sold_ticket_count=row["sold_ticket_count"],
        checked_in_ticket_count=row["checked_in_ticket_count"],
        refunded_ticket_count=row["refunded_ticket_count"],
    )


def admin_monthly_trend_from_row(row: dict) -> AdminMonthlyTrendRecord:
    return AdminMonthlyTrendRecord(
        report_month=row["report_month"],
        order_count=row["order_count"],
        paid_order_count=row["paid_order_count"],
        completed_order_count=row["completed_order_count"],
        refunded_order_count=row["refunded_order_count"],
        cancelled_order_count=row["cancelled_order_count"],
        net_paid_amount=row["net_paid_amount"],
        ticket_count=row["ticket_count"],
        sold_ticket_count=row["sold_ticket_count"],
        checked_in_ticket_count=row["checked_in_ticket_count"],
        refunded_ticket_count=row["refunded_ticket_count"],
    )


class PostgresOrderRepository:
    def get_order_quote(self, product_id: int, time_slot_id: int, visit_date: date) -> OrderQuoteRecord | None:
        with connect_db() as connection:
            row = connection.execute(
                """
                SELECT
                    ss.id AS scenic_spot_id,
                    rp.id AS product_id,
                    tt.id AS ticket_type_id,
                    rp.product_name,
                    tt.ticket_name,
                    tsq.id AS time_slot_id,
                    tsq.visit_date,
                    tsq.slot_start_time,
                    tsq.slot_end_time,
                    tt.original_price,
                    rp.sale_price,
                    (tsq.quota_total - tsq.quota_sold) AS quota_remaining
                FROM route_product rp
                JOIN ticket_type tt ON tt.id = rp.ticket_type_id
                JOIN scenic_spot ss ON ss.id = rp.scenic_spot_id
                JOIN time_slot_quota tsq ON tsq.ticket_type_id = tt.id
                JOIN pier start_pier ON start_pier.id = rp.start_pier_id
                JOIN pier end_pier ON end_pier.id = rp.end_pier_id
                WHERE rp.id = %s
                  AND tsq.id = %s
                  AND tsq.visit_date = %s
                  AND rp.status = 'ENABLED'
                  AND tt.status = 'ENABLED'
                  AND ss.status = 'ENABLED'
                  AND tsq.status = 'ENABLED'
                  AND start_pier.status = 'ENABLED'
                  AND end_pier.status = 'ENABLED'
                """,
                (product_id, time_slot_id, visit_date),
            ).fetchone()
        return quote_from_row(row) if row else None

    def create_pending_order(
        self,
        order_no: str,
        visitor_id: int,
        scenic_spot_id: int,
        buyer_name: str,
        buyer_phone: str,
        items: list[PendingOrderItemInput],
    ) -> OrderRecord:
        total_amount = sum((item.final_price for item in items), Decimal("0.00"))
        try:
            with connect_db() as connection:
                order_row = connection.execute(
                    """
                    INSERT INTO ticket_order (
                        order_no,
                        visitor_id,
                        scenic_spot_id,
                        buyer_name,
                        buyer_phone,
                        order_status,
                        payment_status,
                        total_amount,
                        discount_amount,
                        payable_amount,
                        paid_amount
                    )
                    VALUES (%s, %s, %s, %s, %s, 'CREATED', 'UNPAID', %s, 0, %s, 0)
                    RETURNING
                        id AS order_id,
                        order_no,
                        visitor_id,
                        buyer_name,
                        buyer_phone,
                        order_status,
                        payment_status,
                        total_amount,
                        payable_amount,
                        order_time
                    """,
                    (order_no, visitor_id, scenic_spot_id, buyer_name, buyer_phone, total_amount, total_amount),
                ).fetchone()

                item_records: list[OrderCreateItemRecord] = []
                for item in items:
                    passenger_template_id = item.passenger_template_id
                    if passenger_template_id is None:
                        template_row = connection.execute(
                            """
                            UPDATE visitor_passenger_template
                            SET passenger_name = %s,
                                phone = %s,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE owner_visitor_id = %s
                              AND id_type = %s
                              AND id_number = %s
                            RETURNING id
                            """,
                            (
                                item.passenger_name,
                                item.passenger_phone,
                                visitor_id,
                                item.passenger_id_type,
                                item.passenger_id_number,
                            ),
                        ).fetchone()
                        if not template_row:
                            template_row = connection.execute(
                                """
                                INSERT INTO visitor_passenger_template (
                                    owner_visitor_id,
                                    passenger_name,
                                    id_type,
                                    id_number,
                                    phone
                                )
                                VALUES (%s, %s, %s, %s, %s)
                                RETURNING id
                                """,
                                (
                                    visitor_id,
                                    item.passenger_name,
                                    item.passenger_id_type,
                                    item.passenger_id_number,
                                    item.passenger_phone,
                                ),
                            ).fetchone()
                        passenger_template_id = template_row["id"]
                    else:
                        template_row = connection.execute(
                            """
                            SELECT id
                            FROM visitor_passenger_template
                            WHERE id = %s
                              AND owner_visitor_id = %s
                              AND passenger_name = %s
                              AND id_type = %s
                              AND id_number = %s
                              AND phone = %s
                            """,
                            (
                                passenger_template_id,
                                visitor_id,
                                item.passenger_name,
                                item.passenger_id_type,
                                item.passenger_id_number,
                                item.passenger_phone,
                            ),
                        ).fetchone()
                        if not template_row:
                            raise PassengerTemplateMismatchError

                    item_row = connection.execute(
                        """
                        INSERT INTO ticket_order_item (
                            order_id,
                            ticket_type_id,
                            product_id,
                            visitor_id,
                            time_slot_id,
                            passenger_template_id,
                            passenger_name,
                            passenger_id_type,
                            passenger_id_number,
                            passenger_phone,
                            item_no,
                            visit_date,
                            original_price,
                            discount_amount,
                            final_price,
                            item_status
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'PENDING_PAYMENT')
                        RETURNING
                            item_no,
                            product_id,
                            ticket_type_id,
                            %s::VARCHAR AS product_name,
                            %s::VARCHAR AS ticket_name,
                            time_slot_id,
                            visit_date,
                            %s::TIME AS slot_start_time,
                            %s::TIME AS slot_end_time,
                            original_price,
                            final_price,
                            item_status,
                            passenger_name,
                            passenger_id_type,
                            passenger_id_number,
                            passenger_phone
                        """,
                        (
                            order_row["order_id"],
                            item.ticket_type_id,
                            item.product_id,
                            visitor_id,
                            item.time_slot_id,
                            passenger_template_id,
                            item.passenger_name,
                            item.passenger_id_type,
                            item.passenger_id_number,
                            item.passenger_phone,
                            item.item_no,
                            item.visit_date,
                            item.original_price,
                            item.original_price - item.final_price,
                            item.final_price,
                            item.product_name,
                            item.ticket_name,
                            item.slot_start_time,
                            item.slot_end_time,
                        ),
                    ).fetchone()
                    item_records.append(item_from_row(item_row))
        except errors.UniqueViolation as exc:
            if getattr(exc.diag, "constraint_name", "") == "uq_ticket_order_item_passenger_slot":
                raise PassengerTimeSlotDuplicateError from exc
            raise
        return order_from_row(order_row, item_records)

    def expire_unpaid_orders(self, visitor_id: int, expired_before: datetime) -> int:
        with connect_db() as connection:
            order_rows = connection.execute(
                """
                SELECT id
                FROM ticket_order
                WHERE visitor_id = %s
                  AND order_status = 'CREATED'
                  AND payment_status = 'UNPAID'
                  AND order_time <= %s
                FOR UPDATE
                """,
                (visitor_id, expired_before),
            ).fetchall()
            if not order_rows:
                return 0

            order_ids = [row["id"] for row in order_rows]
            placeholders = ", ".join(["%s"] * len(order_ids))
            expired_at = datetime.now(UTC)
            connection.execute(
                f"""
                UPDATE ticket_order_item
                SET item_status = 'CANCELLED',
                    updated_at = %s
                WHERE order_id IN ({placeholders})
                  AND item_status = 'PENDING_PAYMENT'
                """,
                (expired_at, *order_ids),
            )
            connection.execute(
                f"""
                UPDATE ticket_order
                SET order_status = 'CANCELLED',
                    cancel_time = %s,
                    updated_at = %s
                WHERE id IN ({placeholders})
                  AND order_status = 'CREATED'
                  AND payment_status = 'UNPAID'
                """,
                (expired_at, expired_at, *order_ids),
            )
            return len(order_ids)

    def list_orders_for_visitor(self, visitor_id: int, order_status: str | None = None) -> list[OrderRecord]:
        if order_status is None:
            where_clause = "WHERE visitor_id = %s"
            params: tuple[object, ...] = (visitor_id,)
        else:
            where_clause = "WHERE visitor_id = %s AND order_status = %s"
            params = (visitor_id, order_status)

        with connect_db() as connection:
            order_rows = connection.execute(
                f"""
                SELECT
                    id AS order_id,
                    order_no,
                    visitor_id,
                    buyer_name,
                    buyer_phone,
                    order_status,
                    payment_status,
                    total_amount,
                    payable_amount,
                    order_time
                FROM ticket_order
                {where_clause}
                ORDER BY order_time DESC, id DESC
                """,
                params,
            ).fetchall()
            orders = [
                order_from_row(
                    row,
                    self._load_items_for_order_in_connection(connection, row["order_id"]),
                )
                for row in order_rows
            ]
        return orders

    def get_order_for_visitor(self, visitor_id: int, order_no: str) -> OrderRecord | None:
        with connect_db() as connection:
            order_row = connection.execute(
                """
                SELECT
                    id AS order_id,
                    order_no,
                    visitor_id,
                    buyer_name,
                    buyer_phone,
                    order_status,
                    payment_status,
                    total_amount,
                    payable_amount,
                    order_time
                FROM ticket_order
                WHERE visitor_id = %s AND order_no = %s
                """,
                (visitor_id, order_no),
            ).fetchone()
            if not order_row:
                return None
            items = self._load_items_for_order_in_connection(connection, order_row["order_id"])
        return order_from_row(order_row, items)

    def pay_order(
        self,
        order_no: str,
        visitor_id: int,
        idempotency_key: str,
        payment_no: str,
        transaction_no: str,
        ticket_code_factory: Callable[[], str],
    ) -> OrderRecord | None:
        with connect_db() as connection:
            order_row = connection.execute(
                """
                SELECT
                    id AS order_id,
                    order_no,
                    visitor_id,
                    buyer_name,
                    buyer_phone,
                    order_status,
                    payment_status,
                    total_amount,
                    payable_amount,
                    order_time
                FROM ticket_order
                WHERE order_no = %s AND visitor_id = %s
                FOR UPDATE
                """,
                (order_no, visitor_id),
            ).fetchone()
            if not order_row:
                return None

            existing_payment = connection.execute(
                """
                SELECT id
                FROM payment_record
                WHERE order_id = %s AND idempotency_key = %s
                """,
                (order_row["order_id"], idempotency_key),
            ).fetchone()
            if existing_payment or order_row["order_status"] == "PAID":
                return self._load_order_for_visitor_in_connection(connection, visitor_id, order_no)

            if order_row["order_status"] != "CREATED" or order_row["payment_status"] != "UNPAID":
                raise OrderPaymentStateError

            item_rows = connection.execute(
                """
                SELECT
                    toi.id AS order_item_id,
                    toi.item_no,
                    rp.id AS product_id,
                    toi.ticket_type_id,
                    rp.product_name,
                    tt.ticket_name,
                    toi.time_slot_id,
                    toi.visit_date,
                    tsq.slot_start_time,
                    tsq.slot_end_time,
                    toi.original_price,
                    toi.final_price,
                    toi.item_status,
                    toi.ticket_code,
                    toi.passenger_name,
                    toi.passenger_id_type,
                    toi.passenger_id_number,
                    toi.passenger_phone
                FROM ticket_order_item toi
                JOIN ticket_type tt ON tt.id = toi.ticket_type_id
                JOIN route_product rp ON rp.id = toi.product_id
                JOIN time_slot_quota tsq ON tsq.id = toi.time_slot_id
                WHERE toi.order_id = %s
                ORDER BY toi.id
                FOR UPDATE
                """,
                (order_row["order_id"],),
            ).fetchall()

            grouped_slot_counts: dict[int, int] = {}
            for row in item_rows:
                grouped_slot_counts[row["time_slot_id"]] = grouped_slot_counts.get(row["time_slot_id"], 0) + 1

            for time_slot_id, quantity in grouped_slot_counts.items():
                updated_slot = connection.execute(
                    """
                    UPDATE time_slot_quota
                    SET quota_sold = quota_sold + %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                      AND quota_sold + %s <= quota_total
                    RETURNING id
                    """,
                    (quantity, time_slot_id, quantity),
                ).fetchone()
                if not updated_slot:
                    raise OrderQuotaNotEnoughError

            connection.execute(
                """
                INSERT INTO payment_record (
                    order_id,
                    payment_no,
                    idempotency_key,
                    payment_method,
                    payment_amount,
                    payment_status,
                    transaction_no,
                    paid_at
                )
                VALUES (%s, %s, %s, 'MOCK', %s, 'SUCCESS', %s, CURRENT_TIMESTAMP)
                """,
                (order_row["order_id"], payment_no, idempotency_key, order_row["payable_amount"], transaction_no),
            )

            for row in item_rows:
                connection.execute(
                    """
                    UPDATE ticket_order_item
                    SET item_status = 'UNUSED',
                        ticket_code = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                    """,
                    (ticket_code_factory(), row["order_item_id"]),
                )

            connection.execute(
                """
                UPDATE ticket_order
                SET order_status = 'PAID',
                    payment_status = 'PAID',
                    paid_amount = payable_amount,
                    paid_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (order_row["order_id"],),
            )

            return self._load_order_for_visitor_in_connection(connection, visitor_id, order_no)

    def process_mock_payment_callback(
        self,
        event_id: str,
        order_no: str,
        payment_no: str,
        transaction_no: str,
        paid_amount: Decimal,
        ticket_code_factory: Callable[[], str],
    ) -> MockPaymentCallbackRecord | None:
        idempotency_key = f"mockpay:{event_id}"
        processed_at = datetime.now(UTC)

        with connect_db() as connection:
            existing_event = connection.execute(
                """
                SELECT
                    o.order_no,
                    o.order_status,
                    o.payment_status
                FROM payment_record pr
                JOIN ticket_order o ON o.id = pr.order_id
                WHERE pr.idempotency_key = %s
                FOR UPDATE OF pr, o
                """,
                (idempotency_key,),
            ).fetchone()
            if existing_event:
                return MockPaymentCallbackRecord(
                    event_id=event_id,
                    order_no=existing_event["order_no"],
                    order_status=existing_event["order_status"],
                    payment_status=existing_event["payment_status"],
                    idempotent=True,
                    processed_at=processed_at,
                )

            order_row = connection.execute(
                """
                SELECT
                    id AS order_id,
                    visitor_id,
                    order_no,
                    order_status,
                    payment_status,
                    order_time,
                    payable_amount
                FROM ticket_order
                WHERE order_no = %s
                FOR UPDATE
                """,
                (order_no,),
            ).fetchone()
            if not order_row:
                return None

            existing_payment_no = connection.execute(
                """
                SELECT id
                FROM payment_record
                WHERE payment_no = %s
                FOR UPDATE
                """,
                (payment_no,),
            ).fetchone()
            if existing_payment_no:
                raise OrderPaymentStateError

            if paid_amount != order_row["payable_amount"]:
                raise OrderPaymentAmountMismatchError
            if (
                order_row["order_status"] == "CREATED"
                and order_row["payment_status"] == "UNPAID"
                and order_row["order_time"] <= processed_at - timedelta(minutes=PAYMENT_HOLD_MINUTES)
            ):
                self.expire_unpaid_orders(order_row["visitor_id"], processed_at - timedelta(minutes=PAYMENT_HOLD_MINUTES))
                raise OrderPaymentStateError
            if order_row["order_status"] != "CREATED" or order_row["payment_status"] != "UNPAID":
                raise OrderPaymentStateError

            item_rows = connection.execute(
                """
                SELECT
                    id AS order_item_id,
                    item_status,
                    time_slot_id
                FROM ticket_order_item
                WHERE order_id = %s
                ORDER BY id
                FOR UPDATE
                """,
                (order_row["order_id"],),
            ).fetchall()
            if not item_rows or any(row["item_status"] != "PENDING_PAYMENT" for row in item_rows):
                raise OrderPaymentStateError

            grouped_slot_counts: dict[int, int] = {}
            for row in item_rows:
                grouped_slot_counts[row["time_slot_id"]] = grouped_slot_counts.get(row["time_slot_id"], 0) + 1

            for time_slot_id, quantity in grouped_slot_counts.items():
                updated_slot = connection.execute(
                    """
                    UPDATE time_slot_quota
                    SET quota_sold = quota_sold + %s,
                        updated_at = %s
                    WHERE id = %s
                      AND quota_sold + %s <= quota_total
                    RETURNING id
                    """,
                    (quantity, processed_at, time_slot_id, quantity),
                ).fetchone()
                if not updated_slot:
                    raise OrderQuotaNotEnoughError

            connection.execute(
                """
                INSERT INTO payment_record (
                    order_id,
                    payment_no,
                    idempotency_key,
                    payment_method,
                    payment_amount,
                    payment_status,
                    transaction_no,
                    paid_at
                )
                VALUES (%s, %s, %s, 'MOCK', %s, 'SUCCESS', %s, %s)
                """,
                (order_row["order_id"], payment_no, idempotency_key, paid_amount, transaction_no, processed_at),
            )

            for row in item_rows:
                updated_item = connection.execute(
                    """
                    UPDATE ticket_order_item
                    SET item_status = 'UNUSED',
                        ticket_code = %s,
                        updated_at = %s
                    WHERE id = %s
                      AND item_status = 'PENDING_PAYMENT'
                    RETURNING id
                    """,
                    (ticket_code_factory(), processed_at, row["order_item_id"]),
                ).fetchone()
                if not updated_item:
                    raise OrderPaymentStateError

            connection.execute(
                """
                UPDATE ticket_order
                SET order_status = 'PAID',
                    payment_status = 'PAID',
                    paid_amount = payable_amount,
                    paid_at = %s,
                    updated_at = %s
                WHERE id = %s
                  AND order_status = 'CREATED'
                  AND payment_status = 'UNPAID'
                """,
                (processed_at, processed_at, order_row["order_id"]),
            )

        return MockPaymentCallbackRecord(
            event_id=event_id,
            order_no=order_row["order_no"],
            order_status="PAID",
            payment_status="PAID",
            idempotent=False,
            processed_at=processed_at,
        )

    def cancel_order(self, order_no: str, visitor_id: int) -> OrderRecord | None:
        with connect_db() as connection:
            order_row = connection.execute(
                """
                SELECT
                    id AS order_id,
                    order_no,
                    visitor_id,
                    buyer_name,
                    buyer_phone,
                    order_status,
                    payment_status,
                    total_amount,
                    payable_amount,
                    order_time
                FROM ticket_order
                WHERE order_no = %s AND visitor_id = %s
                FOR UPDATE
                """,
                (order_no, visitor_id),
            ).fetchone()
            if not order_row:
                return None

            if order_row["order_status"] != "CREATED" or order_row["payment_status"] != "UNPAID":
                raise OrderCancelStateError

            connection.execute(
                """
                UPDATE ticket_order_item
                SET item_status = 'CANCELLED',
                    updated_at = CURRENT_TIMESTAMP
                WHERE order_id = %s
                  AND item_status = 'PENDING_PAYMENT'
                """,
                (order_row["order_id"],),
            )
            connection.execute(
                """
                UPDATE ticket_order
                SET order_status = 'CANCELLED',
                    cancel_time = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (order_row["order_id"],),
            )
            return self._load_order_for_visitor_in_connection(connection, visitor_id, order_no)

    def list_orders_for_admin(self, filters: AdminOrderListFilter) -> AdminOrderListRecord:
        where_clause, params = self._admin_order_where_clause(filters)
        limit = filters.page_size
        offset = (filters.page - 1) * filters.page_size

        with connect_db() as connection:
            count_row = connection.execute(
                f"""
                SELECT COUNT(*) AS total
                FROM ticket_order o
                {where_clause}
                """,
                params,
            ).fetchone()
            order_rows = connection.execute(
                f"""
                SELECT
                    o.id AS order_id,
                    o.order_no,
                    o.visitor_id,
                    o.buyer_name,
                    o.buyer_phone,
                    o.order_status,
                    o.payment_status,
                    o.total_amount,
                    o.payable_amount,
                    o.order_time,
                    COUNT(toi.id)::INTEGER AS item_count
                FROM ticket_order o
                LEFT JOIN ticket_order_item toi ON toi.order_id = o.id
                {where_clause}
                GROUP BY
                    o.id,
                    o.order_no,
                    o.visitor_id,
                    o.buyer_name,
                    o.buyer_phone,
                    o.order_status,
                    o.payment_status,
                    o.total_amount,
                    o.payable_amount,
                    o.order_time
                ORDER BY o.order_time DESC, o.id DESC
                LIMIT %s OFFSET %s
                """,
                params + (limit, offset),
            ).fetchall()
        return AdminOrderListRecord(
            items=[admin_summary_from_row(row) for row in order_rows],
            total=count_row["total"] if count_row else 0,
            page=filters.page,
            page_size=filters.page_size,
        )

    def list_check_in_audit_log_export_rows(
        self,
        filters: AdminCheckInAuditLogExportFilter,
    ) -> list[AdminCheckInAuditLogRecord]:
        where_clause, params = self._check_in_audit_log_search_where_clause(filters)
        limit_clause = "LIMIT %s" if filters.row_limit is not None else ""
        query_params = params + ((filters.row_limit,) if filters.row_limit is not None else ())

        with connect_db() as connection:
            rows = connection.execute(
                f"""
                SELECT
                    order_no,
                    item_no,
                    ticket_code,
                    action,
                    reason,
                    operator_username,
                    operator_display_name,
                    request_id,
                    created_at
                FROM check_in_audit_log cial
                {where_clause}
                ORDER BY created_at DESC, id DESC
                {limit_clause}
                """,
                query_params,
            ).fetchall()
        return [self._check_in_audit_log_from_row(row) for row in rows]

    def get_order_for_admin(self, order_no: str) -> OrderRecord | None:
        with connect_db() as connection:
            order_row = connection.execute(
                """
                SELECT
                    id AS order_id,
                    order_no,
                    visitor_id,
                    buyer_name,
                    buyer_phone,
                    order_status,
                    payment_status,
                    total_amount,
                    payable_amount,
                    order_time
                FROM ticket_order
                WHERE order_no = %s
                """,
                (order_no,),
            ).fetchone()
            if not order_row:
                return None
            items = self._load_items_for_order_in_connection(connection, order_row["order_id"])
        return order_from_row(order_row, items)

    def check_in_ticket(self, ticket_code: str, audit: AdminCheckInAuditInput) -> AdminCheckInRecord | None:
        with connect_db() as connection:
            item_row = connection.execute(
                """
                SELECT
                    toi.id AS order_item_id,
                    toi.item_no,
                    toi.ticket_code,
                    toi.item_status,
                    toi.product_id,
                    toi.ticket_type_id,
                    toi.time_slot_id,
                    toi.visit_date,
                    rp.raft_capacity,
                    o.id AS order_id,
                    o.order_no,
                    o.order_status,
                    o.payment_status
                FROM ticket_order_item toi
                JOIN ticket_order o ON o.id = toi.order_id
                JOIN route_product rp ON rp.id = toi.product_id
                WHERE toi.ticket_code = %s
                FOR UPDATE OF toi, o
                """,
                (ticket_code,),
            ).fetchone()
            if not item_row:
                return None
            if item_row["item_status"] == "USED":
                raise TicketAlreadyCheckedInError
            if (
                item_row["item_status"] != "UNUSED"
                or item_row["order_status"] != "PAID"
                or item_row["payment_status"] not in ("PAID", "PARTIAL_REFUND")
            ):
                raise TicketNotCheckableError

            checked_in_at = datetime.now(UTC)
            checked_quota_row = connection.execute(
                """
                UPDATE time_slot_quota
                SET quota_checked_in = quota_checked_in + 1,
                    updated_at = %s
                WHERE id = %s
                  AND quota_checked_in + 1 <= quota_sold
                RETURNING id
                """,
                (checked_in_at, item_row["time_slot_id"]),
            ).fetchone()
            if not checked_quota_row:
                raise TicketNotCheckableError
            assigned_row = connection.execute(
                """
                SELECT COUNT(*) AS assigned_count
                FROM ticket_order_item
                WHERE product_id = %s
                  AND time_slot_id = %s
                  AND visit_date = %s
                  AND item_status = 'USED'
                  AND raft_no IS NOT NULL
                """,
                (item_row.get("product_id"), item_row["time_slot_id"], item_row.get("visit_date")),
            ).fetchone()
            assigned_count = assigned_row["assigned_count"] if assigned_row else 0
            raft_capacity = item_row.get("raft_capacity") or 2
            raft_no = assigned_count // raft_capacity + 1
            raft_seat_no = assigned_count % raft_capacity + 1
            connection.execute(
                """
                UPDATE ticket_order_item
                SET item_status = 'USED',
                    raft_no = %s,
                    raft_seat_no = %s,
                    raft_assigned_at = %s,
                    updated_at = %s
                WHERE id = %s
                  AND item_status = 'UNUSED'
                """,
                (raft_no, raft_seat_no, checked_in_at, checked_in_at, item_row["order_item_id"]),
            )
            remaining_row = connection.execute(
                """
                SELECT COUNT(*) AS remaining
                FROM ticket_order_item
                WHERE order_id = %s
                  AND item_status NOT IN ('USED', 'REFUNDED')
                """,
                (item_row["order_id"],),
            ).fetchone()
            order_status = item_row["order_status"]
            if remaining_row and remaining_row["remaining"] == 0:
                order_status = "COMPLETED"
                connection.execute(
                    """
                    UPDATE ticket_order
                    SET order_status = 'COMPLETED',
                        updated_at = %s
                    WHERE id = %s
                      AND order_status = 'PAID'
                    """,
                    (checked_in_at, item_row["order_id"]),
                )

            self._insert_check_in_audit_log(
                connection=connection,
                order_id=item_row["order_id"],
                order_item_id=item_row["order_item_id"],
                order_no=item_row["order_no"],
                item_no=item_row["item_no"],
                ticket_code=item_row["ticket_code"],
                action="CHECK_IN",
                audit=audit,
                created_at=checked_in_at,
            )

        return AdminCheckInRecord(
            order_no=item_row["order_no"],
            item_no=item_row["item_no"],
            ticket_code=item_row["ticket_code"],
            order_status=order_status,
            item_status="USED",
            checked_in_at=checked_in_at,
            raft_no=raft_no,
            raft_seat_no=raft_seat_no,
        )

    def undo_check_in_ticket(self, ticket_code: str, audit: AdminCheckInAuditInput) -> AdminUndoCheckInRecord | None:
        with connect_db() as connection:
            item_row = connection.execute(
                """
                SELECT
                    toi.id AS order_item_id,
                    toi.item_no,
                    toi.ticket_code,
                    toi.item_status,
                    toi.time_slot_id,
                    o.id AS order_id,
                    o.order_no,
                    o.order_status,
                    o.payment_status
                FROM ticket_order_item toi
                JOIN ticket_order o ON o.id = toi.order_id
                WHERE toi.ticket_code = %s
                FOR UPDATE OF toi, o
                """,
                (ticket_code,),
            ).fetchone()
            if not item_row:
                return None
            if item_row["item_status"] != "USED":
                raise TicketNotCheckedInError
            if item_row["order_status"] not in ("PAID", "COMPLETED") or item_row["payment_status"] not in (
                "PAID",
                "PARTIAL_REFUND",
            ):
                raise TicketUndoNotAllowedError

            undone_at = datetime.now(UTC)
            updated_item_row = connection.execute(
                """
                UPDATE ticket_order_item
                SET item_status = 'UNUSED',
                    raft_no = NULL,
                    raft_seat_no = NULL,
                    raft_assigned_at = NULL,
                    updated_at = %s
                WHERE id = %s
                  AND item_status = 'USED'
                RETURNING id
                """,
                (undone_at, item_row["order_item_id"]),
            ).fetchone()
            if not updated_item_row:
                raise TicketNotCheckedInError

            updated_quota_row = connection.execute(
                """
                UPDATE time_slot_quota
                SET quota_checked_in = quota_checked_in - 1,
                    updated_at = %s
                WHERE id = %s
                  AND quota_checked_in - 1 >= 0
                RETURNING id
                """,
                (undone_at, item_row["time_slot_id"]),
            ).fetchone()
            if not updated_quota_row:
                raise TicketUndoNotAllowedError

            order_status = item_row["order_status"]
            if item_row["order_status"] == "COMPLETED":
                order_status = "PAID"
                updated_order_row = connection.execute(
                    """
                    UPDATE ticket_order
                    SET order_status = 'PAID',
                        updated_at = %s
                    WHERE id = %s
                      AND order_status = 'COMPLETED'
                    RETURNING id
                    """,
                    (undone_at, item_row["order_id"]),
                ).fetchone()
                if not updated_order_row:
                    raise TicketUndoNotAllowedError

            self._insert_check_in_audit_log(
                connection=connection,
                order_id=item_row["order_id"],
                order_item_id=item_row["order_item_id"],
                order_no=item_row["order_no"],
                item_no=item_row["item_no"],
                ticket_code=item_row["ticket_code"],
                action="UNDO_CHECK_IN",
                audit=audit,
                created_at=undone_at,
            )

        return AdminUndoCheckInRecord(
            order_no=item_row["order_no"],
            item_no=item_row["item_no"],
            ticket_code=item_row["ticket_code"],
            order_status=order_status,
            item_status="UNUSED",
            undone_at=undone_at,
        )

    def list_check_in_audit_logs(self, ticket_code: str) -> list[AdminCheckInAuditLogRecord] | None:
        with connect_db() as connection:
            item_row = connection.execute(
                """
                SELECT id
                FROM ticket_order_item
                WHERE ticket_code = %s
                """,
                (ticket_code,),
            ).fetchone()
            if not item_row:
                return None
            rows = connection.execute(
                """
                SELECT
                    order_no,
                    item_no,
                    ticket_code,
                    action,
                    reason,
                    operator_username,
                    operator_display_name,
                    request_id,
                    created_at
                FROM check_in_audit_log
                WHERE ticket_code = %s
                ORDER BY created_at DESC, id DESC
                """,
                (ticket_code,),
            ).fetchall()
        return [self._check_in_audit_log_from_row(row) for row in rows]

    def list_check_in_audit_log_entries(
        self,
        filters: AdminCheckInAuditLogListFilter,
    ) -> AdminCheckInAuditLogListRecord:
        where_clause, params = self._check_in_audit_log_search_where_clause(filters)
        limit = filters.page_size
        offset = (filters.page - 1) * filters.page_size

        with connect_db() as connection:
            count_row = connection.execute(
                f"""
                SELECT COUNT(*) AS total
                FROM check_in_audit_log cial
                {where_clause}
                """,
                params,
            ).fetchone()
            rows = connection.execute(
                f"""
                SELECT
                    order_no,
                    item_no,
                    ticket_code,
                    action,
                    reason,
                    operator_username,
                    operator_display_name,
                    request_id,
                    created_at
                FROM check_in_audit_log cial
                {where_clause}
                ORDER BY created_at DESC, id DESC
                LIMIT %s OFFSET %s
                """,
                params + (limit, offset),
            ).fetchall()
        return AdminCheckInAuditLogListRecord(
            items=[self._check_in_audit_log_from_row(row) for row in rows],
            total=count_row["total"] if count_row else 0,
            page=filters.page,
            page_size=filters.page_size,
        )

    @staticmethod
    def _insert_check_in_audit_log(
        *,
        connection,
        order_id: int,
        order_item_id: int,
        order_no: str,
        item_no: str,
        ticket_code: str,
        action: str,
        audit: AdminCheckInAuditInput,
        created_at: datetime,
    ) -> None:
        connection.execute(
            """
            INSERT INTO check_in_audit_log (
                order_id,
                order_item_id,
                order_no,
                item_no,
                ticket_code,
                action,
                operator_admin_user_id,
                operator_username,
                operator_display_name,
                request_id,
                reason,
                source_ip,
                device_id,
                admin_session_id,
                user_agent,
                created_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                order_id,
                order_item_id,
                order_no,
                item_no,
                ticket_code,
                action,
                audit.operator_admin_user_id,
                audit.operator_username,
                audit.operator_display_name,
                audit.request_id,
                audit.reason,
                audit.source_ip,
                audit.device_id,
                audit.admin_session_id,
                audit.user_agent,
                created_at,
            ),
        )

    @staticmethod
    def _check_in_audit_log_from_row(row: dict) -> AdminCheckInAuditLogRecord:
        return AdminCheckInAuditLogRecord(
            order_no=row["order_no"],
            item_no=row["item_no"],
            ticket_code=row["ticket_code"],
            action=row["action"],
            operator_username=row["operator_username"],
            operator_display_name=row["operator_display_name"],
            request_id=row["request_id"],
            created_at=row["created_at"],
            reason=row["reason"],
        )

    @staticmethod
    def _check_in_audit_log_search_where_clause(
        filters: AdminCheckInAuditLogListFilter | AdminCheckInAuditLogExportFilter,
    ) -> tuple[str, tuple[object, ...]]:
        clauses: list[str] = []
        params: list[object] = []

        if filters.ticket_code:
            clauses.append("UPPER(cial.ticket_code) LIKE UPPER(%s)")
            params.append(f"%{filters.ticket_code}%")
        if filters.order_no:
            clauses.append("UPPER(cial.order_no) LIKE UPPER(%s)")
            params.append(f"%{filters.order_no}%")
        if filters.operator_username:
            clauses.append("UPPER(cial.operator_username) LIKE UPPER(%s)")
            params.append(f"%{filters.operator_username}%")
        if filters.reason:
            clauses.append("UPPER(cial.reason) LIKE UPPER(%s)")
            params.append(f"%{filters.reason}%")
        if filters.date_from:
            clauses.append("cial.created_at::date >= %s")
            params.append(filters.date_from)
        if filters.date_to:
            clauses.append("cial.created_at::date <= %s")
            params.append(filters.date_to)

        if not clauses:
            return "", ()
        return "WHERE " + " AND ".join(clauses), tuple(params)

    def record_check_in_failure_audit_log(
        self,
        ticket_code: str,
        action: str,
        failure_code: str,
        failure_message: str,
        audit: AdminCheckInAuditInput,
    ) -> None:
        with connect_db() as connection:
            self._insert_check_in_failure_audit_log(
                connection=connection,
                ticket_code=ticket_code,
                action=action,
                failure_code=failure_code,
                failure_message=failure_message,
                audit=audit,
                created_at=datetime.now(UTC),
            )

    def list_check_in_failure_audit_log_entries(
        self,
        filters: AdminCheckInFailureAuditLogListFilter,
    ) -> AdminCheckInFailureAuditLogListRecord:
        where_clause, params = self._check_in_failure_audit_log_search_where_clause(filters)
        limit = filters.page_size
        offset = (filters.page - 1) * filters.page_size

        with connect_db() as connection:
            count_row = connection.execute(
                f"""
                SELECT COUNT(*) AS total
                FROM check_in_failure_audit_log cifal
                {where_clause}
                """,
                params,
            ).fetchone()
            rows = connection.execute(
                f"""
                SELECT
                    ticket_code,
                    action,
                    failure_code,
                    failure_message,
                    operator_username,
                    operator_display_name,
                    request_id,
                    created_at
                FROM check_in_failure_audit_log cifal
                {where_clause}
                ORDER BY created_at DESC, id DESC
                LIMIT %s OFFSET %s
                """,
                params + (limit, offset),
            ).fetchall()

        return AdminCheckInFailureAuditLogListRecord(
            items=[self._check_in_failure_audit_log_from_row(row) for row in rows],
            total=count_row["total"] if count_row else 0,
            page=filters.page,
            page_size=filters.page_size,
        )

    def list_check_in_failure_audit_log_export_rows(
        self,
        filters: AdminCheckInFailureAuditLogExportFilter,
    ) -> list[AdminCheckInFailureAuditLogRecord]:
        where_clause, params = self._check_in_failure_audit_log_search_where_clause(filters)
        limit_clause = "LIMIT %s" if filters.row_limit is not None else ""
        query_params = params + ((filters.row_limit,) if filters.row_limit is not None else ())

        with connect_db() as connection:
            rows = connection.execute(
                f"""
                SELECT
                    ticket_code,
                    action,
                    failure_code,
                    failure_message,
                    operator_username,
                    operator_display_name,
                    request_id,
                    created_at
                FROM check_in_failure_audit_log cifal
                {where_clause}
                ORDER BY created_at DESC, id DESC
                {limit_clause}
                """,
                query_params,
            ).fetchall()

        return [self._check_in_failure_audit_log_from_row(row) for row in rows]

    @staticmethod
    def _insert_check_in_failure_audit_log(
        *,
        connection,
        ticket_code: str,
        action: str,
        failure_code: str,
        failure_message: str,
        audit: AdminCheckInAuditInput,
        created_at: datetime,
    ) -> None:
        connection.execute(
            """
            INSERT INTO check_in_failure_audit_log (
                ticket_code,
                action,
                failure_code,
                failure_message,
                operator_admin_user_id,
                operator_username,
                operator_display_name,
                request_id,
                source_ip,
                device_id,
                admin_session_id,
                user_agent,
                created_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                ticket_code,
                action,
                failure_code,
                failure_message,
                audit.operator_admin_user_id,
                audit.operator_username,
                audit.operator_display_name,
                audit.request_id,
                audit.source_ip,
                audit.device_id,
                audit.admin_session_id,
                audit.user_agent,
                created_at,
            ),
        )

    @staticmethod
    def _check_in_failure_audit_log_from_row(row: dict) -> AdminCheckInFailureAuditLogRecord:
        return AdminCheckInFailureAuditLogRecord(
            ticket_code=row["ticket_code"],
            action=row["action"],
            failure_code=row["failure_code"],
            failure_message=row["failure_message"],
            operator_username=row["operator_username"],
            operator_display_name=row["operator_display_name"],
            request_id=row["request_id"],
            created_at=row["created_at"],
        )

    @staticmethod
    def _check_in_failure_audit_log_search_where_clause(
        filters: AdminCheckInFailureAuditLogListFilter | AdminCheckInFailureAuditLogExportFilter,
    ) -> tuple[str, tuple[object, ...]]:
        clauses: list[str] = []
        params: list[object] = []

        if filters.ticket_code:
            clauses.append("UPPER(cifal.ticket_code) LIKE UPPER(%s)")
            params.append(f"%{filters.ticket_code}%")
        if filters.failure_code:
            clauses.append("cifal.failure_code = %s")
            params.append(filters.failure_code)
        if filters.operator_username:
            clauses.append("UPPER(cifal.operator_username) LIKE UPPER(%s)")
            params.append(f"%{filters.operator_username}%")
        if filters.date_from:
            clauses.append("cifal.created_at::date >= %s")
            params.append(filters.date_from)
        if filters.date_to:
            clauses.append("cifal.created_at::date <= %s")
            params.append(filters.date_to)

        if not clauses:
            return "", ()
        return "WHERE " + " AND ".join(clauses), tuple(params)

    def refund_order(
        self,
        order_no: str,
        audit: AdminRefundAuditInput,
        visitor_id: int | None = None,
        refund_now: datetime | None = None,
    ) -> AdminRefundRecord | None:
        with connect_db() as connection:
            ownership_clause = "" if visitor_id is None else " AND visitor_id = %s"
            order_params = (order_no,) if visitor_id is None else (order_no, visitor_id)
            order_row = connection.execute(
                f"""
                SELECT
                    id AS order_id,
                    order_no,
                    order_status,
                    payment_status,
                    paid_amount
                FROM ticket_order
                WHERE order_no = %s
                {ownership_clause}
                FOR UPDATE
                """,
                order_params,
            ).fetchone()
            if not order_row:
                return None
            if order_row["order_status"] == "REFUNDED" or order_row["payment_status"] == "REFUNDED":
                raise OrderAlreadyRefundedError
            if order_row["order_status"] != "PAID" or order_row["payment_status"] != "PAID":
                raise OrderNotRefundableError

            item_rows = connection.execute(
                """
                SELECT
                    id AS order_item_id,
                    item_no,
                    item_status,
                    time_slot_id,
                    visit_date,
                    final_price
                FROM ticket_order_item
                WHERE order_id = %s
                ORDER BY id
                FOR UPDATE
                """,
                (order_row["order_id"],),
            ).fetchall()
            if not item_rows or any(row["item_status"] != "UNUSED" for row in item_rows):
                raise OrderNotRefundableError
            if refund_now is not None:
                refund_deadline = datetime.combine(
                    min(row["visit_date"] for row in item_rows) - timedelta(days=1),
                    time(18, 0),
                    tzinfo=ZoneInfo("Asia/Shanghai"),
                )
                if refund_now.astimezone(ZoneInfo("Asia/Shanghai")) > refund_deadline:
                    raise OrderRefundDeadlinePassedError

            payment_row = connection.execute(
                """
                SELECT id AS payment_record_id
                FROM payment_record
                WHERE order_id = %s
                  AND payment_status = 'SUCCESS'
                ORDER BY id DESC
                LIMIT 1
                FOR UPDATE
                """,
                (order_row["order_id"],),
            ).fetchone()
            if not payment_row:
                raise OrderNotRefundableError

            refunded_at = datetime.now(UTC)
            grouped_slot_counts: dict[int, int] = {}
            for row in item_rows:
                grouped_slot_counts[row["time_slot_id"]] = grouped_slot_counts.get(row["time_slot_id"], 0) + 1

            for time_slot_id, quantity in grouped_slot_counts.items():
                slot_row = connection.execute(
                    """
                    UPDATE time_slot_quota
                    SET quota_sold = quota_sold - %s,
                        updated_at = %s
                    WHERE id = %s
                      AND quota_sold - %s >= quota_checked_in
                    RETURNING id
                    """,
                    (quantity, refunded_at, time_slot_id, quantity),
                ).fetchone()
                if not slot_row:
                    raise OrderNotRefundableError

            connection.execute(
                """
                UPDATE ticket_order_item
                SET item_status = 'REFUNDED',
                    updated_at = %s
                WHERE order_id = %s
                  AND item_status = 'UNUSED'
                """,
                (refunded_at, order_row["order_id"]),
            )
            updated_payment_row = connection.execute(
                """
                UPDATE payment_record
                SET payment_status = 'REFUNDED',
                    updated_at = %s
                WHERE id = %s
                  AND payment_status = 'SUCCESS'
                RETURNING id
                """,
                (refunded_at, payment_row["payment_record_id"]),
            ).fetchone()
            if not updated_payment_row:
                raise OrderNotRefundableError

            connection.execute(
                """
                UPDATE ticket_order
                SET order_status = 'REFUNDED',
                    payment_status = 'REFUNDED',
                    paid_amount = 0,
                    updated_at = %s
                WHERE id = %s
                  AND order_status = 'PAID'
                  AND payment_status = 'PAID'
                """,
                (refunded_at, order_row["order_id"]),
            )
            refunded_item_nos = [row["item_no"] for row in item_rows]
            self._insert_refund_audit_log(
                connection=connection,
                order_id=order_row["order_id"],
                order_no=order_row["order_no"],
                refund_type="FULL",
                refunded_amount=order_row["paid_amount"],
                refunded_item_count=len(item_rows),
                refunded_item_nos=refunded_item_nos,
                audit=audit,
                created_at=refunded_at,
            )

        return AdminRefundRecord(
            order_no=order_row["order_no"],
            order_status="REFUNDED",
            payment_status="REFUNDED",
            refunded_amount=order_row["paid_amount"],
            refunded_item_count=len(item_rows),
            refunded_at=refunded_at,
        )

    def refund_order_items(
        self,
        order_no: str,
        item_nos: list[str],
        audit: AdminRefundAuditInput,
    ) -> AdminPartialRefundRecord | None:
        with connect_db() as connection:
            order_row = connection.execute(
                """
                SELECT
                    id AS order_id,
                    order_no,
                    order_status,
                    payment_status,
                    paid_amount
                FROM ticket_order
                WHERE order_no = %s
                FOR UPDATE
                """,
                (order_no,),
            ).fetchone()
            if not order_row:
                return None
            if order_row["order_status"] == "REFUNDED" or order_row["payment_status"] == "REFUNDED":
                raise OrderAlreadyRefundedError
            if order_row["order_status"] != "PAID" or order_row["payment_status"] not in ("PAID", "PARTIAL_REFUND"):
                raise OrderNotRefundableError

            item_rows = connection.execute(
                """
                SELECT
                    id AS order_item_id,
                    item_no,
                    item_status,
                    time_slot_id,
                    final_price
                FROM ticket_order_item
                WHERE order_id = %s
                ORDER BY id
                FOR UPDATE
                """,
                (order_row["order_id"],),
            ).fetchall()
            if not item_rows or any(row["item_status"] not in ("UNUSED", "REFUNDED") for row in item_rows):
                raise OrderNotRefundableError

            item_by_no = {row["item_no"]: row for row in item_rows}
            if any(item_no not in item_by_no for item_no in item_nos):
                raise OrderRefundItemsInvalidError

            selected_rows = [item_by_no[item_no] for item_no in item_nos]
            if any(row["item_status"] != "UNUSED" for row in selected_rows):
                raise OrderNotRefundableError

            payment_row = connection.execute(
                """
                SELECT id AS payment_record_id
                FROM payment_record
                WHERE order_id = %s
                  AND payment_status = 'SUCCESS'
                ORDER BY id DESC
                LIMIT 1
                FOR UPDATE
                """,
                (order_row["order_id"],),
            ).fetchone()
            if not payment_row:
                raise OrderNotRefundableError

            refunded_amount = sum((row["final_price"] for row in selected_rows), Decimal("0"))
            if refunded_amount <= 0 or refunded_amount > order_row["paid_amount"]:
                raise OrderNotRefundableError

            refunded_at = datetime.now(UTC)
            grouped_slot_counts: dict[int, int] = {}
            for row in selected_rows:
                grouped_slot_counts[row["time_slot_id"]] = grouped_slot_counts.get(row["time_slot_id"], 0) + 1

            for time_slot_id, quantity in grouped_slot_counts.items():
                slot_row = connection.execute(
                    """
                    UPDATE time_slot_quota
                    SET quota_sold = quota_sold - %s,
                        updated_at = %s
                    WHERE id = %s
                      AND quota_sold - %s >= quota_checked_in
                    RETURNING id
                    """,
                    (quantity, refunded_at, time_slot_id, quantity),
                ).fetchone()
                if not slot_row:
                    raise OrderNotRefundableError

            placeholders = ", ".join(["%s"] * len(item_nos))
            updated_item_rows = connection.execute(
                f"""
                UPDATE ticket_order_item
                SET item_status = 'REFUNDED',
                    updated_at = %s
                WHERE order_id = %s
                  AND item_no IN ({placeholders})
                  AND item_status = 'UNUSED'
                RETURNING item_no
                """,
                (refunded_at, order_row["order_id"], *item_nos),
            ).fetchall()
            refunded_item_nos = [row["item_no"] for row in updated_item_rows]
            if set(refunded_item_nos) != set(item_nos):
                raise OrderNotRefundableError

            remaining_active_item_count = sum(
                1 for row in item_rows if row["item_status"] != "REFUNDED" and row["item_no"] not in set(item_nos)
            )
            order_status = "PAID" if remaining_active_item_count else "REFUNDED"
            payment_status = "PARTIAL_REFUND" if remaining_active_item_count else "REFUNDED"

            updated_order_row = connection.execute(
                """
                UPDATE ticket_order
                SET order_status = %s,
                    payment_status = %s,
                    paid_amount = paid_amount - %s,
                    updated_at = %s
                WHERE id = %s
                  AND order_status = 'PAID'
                  AND payment_status IN ('PAID', 'PARTIAL_REFUND')
                  AND paid_amount - %s >= 0
                RETURNING id
                """,
                (
                    order_status,
                    payment_status,
                    refunded_amount,
                    refunded_at,
                    order_row["order_id"],
                    refunded_amount,
                ),
            ).fetchone()
            if not updated_order_row:
                raise OrderNotRefundableError

            if payment_status == "REFUNDED":
                updated_payment_row = connection.execute(
                    """
                    UPDATE payment_record
                    SET payment_status = 'REFUNDED',
                        updated_at = %s
                    WHERE id = %s
                      AND payment_status = 'SUCCESS'
                    RETURNING id
                    """,
                    (refunded_at, payment_row["payment_record_id"]),
                ).fetchone()
                if not updated_payment_row:
                    raise OrderNotRefundableError
            self._insert_refund_audit_log(
                connection=connection,
                order_id=order_row["order_id"],
                order_no=order_row["order_no"],
                refund_type="PARTIAL",
                refunded_amount=refunded_amount,
                refunded_item_count=len(refunded_item_nos),
                refunded_item_nos=refunded_item_nos,
                audit=audit,
                created_at=refunded_at,
            )

        return AdminPartialRefundRecord(
            order_no=order_row["order_no"],
            order_status=order_status,
            payment_status=payment_status,
            refunded_amount=refunded_amount,
            refunded_item_count=len(refunded_item_nos),
            refunded_item_nos=refunded_item_nos,
            refunded_at=refunded_at,
        )

    def list_refund_audit_logs(self, order_no: str) -> list[AdminRefundAuditLogRecord] | None:
        with connect_db() as connection:
            order_row = connection.execute(
                """
                SELECT id AS order_id
                FROM ticket_order
                WHERE order_no = %s
                """,
                (order_no,),
            ).fetchone()
            if not order_row:
                return None
            rows = connection.execute(
                """
                SELECT
                    order_no,
                    refund_type,
                    refunded_amount,
                    refunded_item_count,
                    refunded_item_nos,
                    reason,
                    operator_username,
                    operator_display_name,
                    request_id,
                    created_at
                FROM refund_audit_log
                WHERE order_id = %s
                ORDER BY created_at DESC, id DESC
                """,
                (order_row["order_id"],),
            ).fetchall()
        return [self._refund_audit_log_from_row(row) for row in rows]

    def list_refund_audit_log_entries(
        self,
        filters: AdminRefundAuditLogListFilter,
    ) -> AdminRefundAuditLogListRecord:
        where_clause, params = self._refund_audit_log_search_where_clause(filters)
        limit = filters.page_size
        offset = (filters.page - 1) * filters.page_size

        with connect_db() as connection:
            count_row = connection.execute(
                f"""
                SELECT COUNT(*) AS total
                FROM refund_audit_log ral
                {where_clause}
                """,
                params,
            ).fetchone()
            rows = connection.execute(
                f"""
                SELECT
                    order_no,
                    refund_type,
                    refunded_amount,
                    refunded_item_count,
                    refunded_item_nos,
                    reason,
                    operator_username,
                    operator_display_name,
                    request_id,
                    created_at
                FROM refund_audit_log ral
                {where_clause}
                ORDER BY created_at DESC, id DESC
                LIMIT %s OFFSET %s
                """,
                params + (limit, offset),
            ).fetchall()
        return AdminRefundAuditLogListRecord(
            items=[self._refund_audit_log_from_row(row) for row in rows],
            total=count_row["total"] if count_row else 0,
            page=filters.page,
            page_size=filters.page_size,
        )

    def list_refund_audit_log_export_rows(
        self,
        filters: AdminRefundAuditLogExportFilter,
    ) -> list[AdminRefundAuditLogRecord]:
        where_clause, params = self._refund_audit_log_search_where_clause(filters)
        limit_clause = "LIMIT %s" if filters.row_limit is not None else ""
        query_params = params + ((filters.row_limit,) if filters.row_limit is not None else ())

        with connect_db() as connection:
            rows = connection.execute(
                f"""
                SELECT
                    order_no,
                    refund_type,
                    refunded_amount,
                    refunded_item_count,
                    refunded_item_nos,
                    reason,
                    operator_username,
                    operator_display_name,
                    request_id,
                    created_at
                FROM refund_audit_log ral
                {where_clause}
                ORDER BY created_at DESC, id DESC
                {limit_clause}
                """,
                query_params,
            ).fetchall()
        return [self._refund_audit_log_from_row(row) for row in rows]

    @staticmethod
    def _insert_refund_audit_log(
        *,
        connection,
        order_id: int,
        order_no: str,
        refund_type: str,
        refunded_amount: Decimal,
        refunded_item_count: int,
        refunded_item_nos: list[str],
        audit: AdminRefundAuditInput,
        created_at: datetime,
    ) -> None:
        connection.execute(
            """
            INSERT INTO refund_audit_log (
                order_id,
                order_no,
                refund_type,
                refunded_amount,
                refunded_item_count,
                refunded_item_nos,
                reason,
                operator_type,
                operator_admin_user_id,
                operator_visitor_id,
                operator_username,
                operator_display_name,
                request_id,
                source_ip,
                device_id,
                admin_session_id,
                user_agent,
                created_at
            )
            VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                order_id,
                order_no,
                refund_type,
                refunded_amount,
                refunded_item_count,
                json.dumps(refunded_item_nos, ensure_ascii=False),
                audit.reason,
                audit.operator_type,
                audit.operator_admin_user_id,
                audit.operator_visitor_id,
                audit.operator_username,
                audit.operator_display_name,
                audit.request_id,
                audit.source_ip,
                audit.device_id,
                audit.admin_session_id,
                audit.user_agent,
                created_at,
            ),
        )

    @staticmethod
    def _refund_audit_log_from_row(row: dict) -> AdminRefundAuditLogRecord:
        item_nos = row["refunded_item_nos"]
        if isinstance(item_nos, str):
            item_nos = json.loads(item_nos)
        return AdminRefundAuditLogRecord(
            order_no=row["order_no"],
            refund_type=row["refund_type"],
            refunded_amount=row["refunded_amount"],
            refunded_item_count=row["refunded_item_count"],
            refunded_item_nos=list(item_nos),
            reason=row["reason"],
            operator_username=row["operator_username"],
            operator_display_name=row["operator_display_name"],
            request_id=row["request_id"],
            created_at=row["created_at"],
        )

    @staticmethod
    def _refund_audit_log_search_where_clause(
        filters: AdminRefundAuditLogListFilter | AdminRefundAuditLogExportFilter,
    ) -> tuple[str, tuple[object, ...]]:
        clauses: list[str] = []
        params: list[object] = []

        if filters.refund_type:
            clauses.append("ral.refund_type = %s")
            params.append(filters.refund_type)
        if filters.order_no:
            clauses.append("UPPER(ral.order_no) LIKE UPPER(%s)")
            params.append(f"%{filters.order_no}%")
        if filters.operator_username:
            clauses.append("UPPER(ral.operator_username) LIKE UPPER(%s)")
            params.append(f"%{filters.operator_username}%")
        if filters.date_from:
            clauses.append("ral.created_at::date >= %s")
            params.append(filters.date_from)
        if filters.date_to:
            clauses.append("ral.created_at::date <= %s")
            params.append(filters.date_to)

        if not clauses:
            return "", ()
        return "WHERE " + " AND ".join(clauses), tuple(params)

    def get_admin_report_summary(self, filters: AdminReportFilter) -> AdminReportSummaryRecord:
        with connect_db() as connection:
            row = connection.execute(
                """
                WITH filtered_orders AS (
                    SELECT
                        id,
                        order_status,
                        payment_status,
                        paid_amount
                    FROM ticket_order
                    WHERE (%s IS NULL OR order_time::date >= %s)
                      AND (%s IS NULL OR order_time::date <= %s)
                ),
                order_stats AS (
                    SELECT
                        COUNT(*)::INTEGER AS order_count,
                        COALESCE(SUM(CASE WHEN payment_status = 'PAID' THEN 1 ELSE 0 END), 0)::INTEGER
                            AS paid_order_count,
                        COALESCE(SUM(CASE WHEN order_status = 'COMPLETED' THEN 1 ELSE 0 END), 0)::INTEGER
                            AS completed_order_count,
                        COALESCE(SUM(CASE WHEN order_status = 'REFUNDED' THEN 1 ELSE 0 END), 0)::INTEGER
                            AS refunded_order_count,
                        COALESCE(SUM(CASE WHEN order_status = 'CANCELLED' THEN 1 ELSE 0 END), 0)::INTEGER
                            AS cancelled_order_count,
                        COALESCE(SUM(paid_amount), 0) AS net_paid_amount
                    FROM filtered_orders
                ),
                item_stats AS (
                    SELECT
                        COUNT(toi.id)::INTEGER AS ticket_count,
                        COALESCE(SUM(CASE WHEN toi.item_status IN ('UNUSED', 'USED') THEN 1 ELSE 0 END), 0)::INTEGER
                            AS sold_ticket_count,
                        COALESCE(SUM(CASE WHEN toi.item_status = 'USED' THEN 1 ELSE 0 END), 0)::INTEGER
                            AS checked_in_ticket_count,
                        COALESCE(SUM(CASE WHEN toi.item_status = 'REFUNDED' THEN 1 ELSE 0 END), 0)::INTEGER
                            AS refunded_ticket_count
                    FROM filtered_orders fo
                    LEFT JOIN ticket_order_item toi ON toi.order_id = fo.id
                )
                SELECT
                    os.order_count,
                    os.paid_order_count,
                    os.completed_order_count,
                    os.refunded_order_count,
                    os.cancelled_order_count,
                    os.net_paid_amount,
                    its.ticket_count,
                    its.sold_ticket_count,
                    its.checked_in_ticket_count,
                    its.refunded_ticket_count
                FROM order_stats os
                CROSS JOIN item_stats its
                """,
                (filters.date_from, filters.date_from, filters.date_to, filters.date_to),
            ).fetchone()

        return AdminReportSummaryRecord(
            date_from=filters.date_from,
            date_to=filters.date_to,
            order_count=row["order_count"] if row else 0,
            paid_order_count=row["paid_order_count"] if row else 0,
            completed_order_count=row["completed_order_count"] if row else 0,
            refunded_order_count=row["refunded_order_count"] if row else 0,
            cancelled_order_count=row["cancelled_order_count"] if row else 0,
            net_paid_amount=row["net_paid_amount"] if row else Decimal("0"),
            ticket_count=row["ticket_count"] if row else 0,
            sold_ticket_count=row["sold_ticket_count"] if row else 0,
            checked_in_ticket_count=row["checked_in_ticket_count"] if row else 0,
            refunded_ticket_count=row["refunded_ticket_count"] if row else 0,
        )

    def get_admin_payment_reconciliation(self, filters: AdminReportFilter) -> AdminPaymentReconciliationRecord:
        with connect_db() as connection:
            row = connection.execute(
                """
                WITH filtered_orders AS (
                    SELECT
                        id,
                        paid_amount
                    FROM ticket_order
                    WHERE (%s IS NULL OR order_time::date >= %s)
                      AND (%s IS NULL OR order_time::date <= %s)
                ),
                order_totals AS (
                    SELECT
                        COALESCE(SUM(paid_amount), 0) AS order_net_paid_amount
                    FROM filtered_orders
                ),
                payment_totals AS (
                    SELECT
                        COALESCE(SUM(pr.payment_amount), 0) AS captured_payment_amount,
                        COUNT(pr.id)::INTEGER AS captured_payment_count
                    FROM filtered_orders fo
                    LEFT JOIN payment_record pr
                      ON pr.order_id = fo.id
                     AND pr.payment_status IN ('SUCCESS', 'REFUNDED')
                ),
                refund_totals AS (
                    SELECT
                        COALESCE(SUM(ral.refunded_amount), 0) AS refund_audit_amount,
                        COUNT(ral.id)::INTEGER AS refund_audit_log_count
                    FROM filtered_orders fo
                    LEFT JOIN refund_audit_log ral ON ral.order_id = fo.id
                )
                SELECT
                    ot.order_net_paid_amount,
                    pt.captured_payment_amount,
                    rt.refund_audit_amount,
                    pt.captured_payment_amount - rt.refund_audit_amount AS expected_net_amount,
                    ot.order_net_paid_amount - (pt.captured_payment_amount - rt.refund_audit_amount)
                        AS unreconciled_amount,
                    pt.captured_payment_count,
                    rt.refund_audit_log_count
                FROM order_totals ot
                CROSS JOIN payment_totals pt
                CROSS JOIN refund_totals rt
                """,
                (filters.date_from, filters.date_from, filters.date_to, filters.date_to),
            ).fetchone()

        order_net_paid_amount = row["order_net_paid_amount"] if row else Decimal("0")
        captured_payment_amount = row["captured_payment_amount"] if row else Decimal("0")
        refund_audit_amount = row["refund_audit_amount"] if row else Decimal("0")
        expected_net_amount = row["expected_net_amount"] if row else Decimal("0")
        unreconciled_amount = row["unreconciled_amount"] if row else Decimal("0")
        return AdminPaymentReconciliationRecord(
            date_from=filters.date_from,
            date_to=filters.date_to,
            order_net_paid_amount=order_net_paid_amount,
            captured_payment_amount=captured_payment_amount,
            refund_audit_amount=refund_audit_amount,
            expected_net_amount=expected_net_amount,
            unreconciled_amount=unreconciled_amount,
            captured_payment_count=row["captured_payment_count"] if row else 0,
            refund_audit_log_count=row["refund_audit_log_count"] if row else 0,
            reconciled=unreconciled_amount == Decimal("0"),
        )

    def list_admin_order_export_rows(self, filters: AdminReportFilter) -> list[AdminOrderExportRecord]:
        limit_clause = "LIMIT %s" if filters.row_limit is not None else ""
        query_params = (
            filters.date_from,
            filters.date_from,
            filters.date_to,
            filters.date_to,
        ) + ((filters.row_limit,) if filters.row_limit is not None else ())
        with connect_db() as connection:
            rows = connection.execute(
                f"""
                SELECT
                    o.order_no,
                    o.buyer_name,
                    o.buyer_phone,
                    o.order_status,
                    o.payment_status,
                    o.total_amount,
                    o.payable_amount,
                    o.order_time,
                    COUNT(toi.id)::INTEGER AS item_count
                FROM ticket_order o
                LEFT JOIN ticket_order_item toi ON toi.order_id = o.id
                WHERE (%s IS NULL OR o.order_time::date >= %s)
                  AND (%s IS NULL OR o.order_time::date <= %s)
                GROUP BY
                    o.id,
                    o.order_no,
                    o.buyer_name,
                    o.buyer_phone,
                    o.order_status,
                    o.payment_status,
                    o.total_amount,
                    o.payable_amount,
                    o.order_time
                ORDER BY o.order_time DESC, o.id DESC
                {limit_clause}
                """,
                query_params,
            ).fetchall()

        return [admin_order_export_from_row(row) for row in rows]

    def list_admin_product_breakdown(self, filters: AdminReportFilter) -> list[AdminProductBreakdownRecord]:
        limit_clause = "LIMIT %s" if filters.row_limit is not None else ""
        query_params = (
            filters.date_from,
            filters.date_from,
            filters.date_to,
            filters.date_to,
        ) + ((filters.row_limit,) if filters.row_limit is not None else ())
        with connect_db() as connection:
            rows = connection.execute(
                f"""
                SELECT
                    toi.product_id,
                    toi.ticket_type_id,
                    rp.product_name,
                    tt.ticket_name,
                    COUNT(DISTINCT o.id)::INTEGER AS order_count,
                    COUNT(toi.id)::INTEGER AS ticket_count,
                    COALESCE(SUM(CASE WHEN toi.item_status IN ('UNUSED', 'USED') THEN 1 ELSE 0 END), 0)::INTEGER
                        AS sold_ticket_count,
                    COALESCE(SUM(CASE WHEN toi.item_status = 'USED' THEN 1 ELSE 0 END), 0)::INTEGER
                        AS checked_in_ticket_count,
                    COALESCE(SUM(CASE WHEN toi.item_status = 'REFUNDED' THEN 1 ELSE 0 END), 0)::INTEGER
                        AS refunded_ticket_count,
                    COALESCE(
                        SUM(CASE WHEN toi.item_status IN ('UNUSED', 'USED') THEN toi.final_price ELSE 0 END),
                        0
                    ) AS net_paid_amount
                FROM ticket_order o
                JOIN ticket_order_item toi ON toi.order_id = o.id
                JOIN route_product rp ON rp.id = toi.product_id
                JOIN ticket_type tt ON tt.id = toi.ticket_type_id
                WHERE (%s IS NULL OR o.order_time::date >= %s)
                  AND (%s IS NULL OR o.order_time::date <= %s)
                GROUP BY
                    toi.product_id,
                    toi.ticket_type_id,
                    rp.product_name,
                    tt.ticket_name
                ORDER BY net_paid_amount DESC, ticket_count DESC, product_id ASC
                {limit_clause}
                """,
                query_params,
            ).fetchall()

        return [admin_product_breakdown_from_row(row) for row in rows]

    def list_admin_daily_trend(self, filters: AdminReportFilter) -> list[AdminDailyTrendRecord]:
        limit_clause = "LIMIT %s" if filters.row_limit is not None else ""
        query_params = (
            filters.date_from,
            filters.date_from,
            filters.date_to,
            filters.date_to,
        ) + ((filters.row_limit,) if filters.row_limit is not None else ())
        with connect_db() as connection:
            rows = connection.execute(
                f"""
                WITH filtered_orders AS (
                    SELECT
                        id,
                        order_time::date AS report_date,
                        order_status,
                        payment_status,
                        paid_amount
                    FROM ticket_order
                    WHERE (%s IS NULL OR order_time::date >= %s)
                      AND (%s IS NULL OR order_time::date <= %s)
                ),
                order_stats AS (
                    SELECT
                        report_date,
                        COUNT(*)::INTEGER AS order_count,
                        COALESCE(SUM(CASE WHEN payment_status = 'PAID' THEN 1 ELSE 0 END), 0)::INTEGER
                            AS paid_order_count,
                        COALESCE(SUM(CASE WHEN order_status = 'COMPLETED' THEN 1 ELSE 0 END), 0)::INTEGER
                            AS completed_order_count,
                        COALESCE(SUM(CASE WHEN order_status = 'REFUNDED' THEN 1 ELSE 0 END), 0)::INTEGER
                            AS refunded_order_count,
                        COALESCE(SUM(CASE WHEN order_status = 'CANCELLED' THEN 1 ELSE 0 END), 0)::INTEGER
                            AS cancelled_order_count,
                        COALESCE(SUM(paid_amount), 0) AS net_paid_amount
                    FROM filtered_orders
                    GROUP BY report_date
                ),
                item_stats AS (
                    SELECT
                        fo.report_date,
                        COUNT(toi.id)::INTEGER AS ticket_count,
                        COALESCE(SUM(CASE WHEN toi.item_status IN ('UNUSED', 'USED') THEN 1 ELSE 0 END), 0)::INTEGER
                            AS sold_ticket_count,
                        COALESCE(SUM(CASE WHEN toi.item_status = 'USED' THEN 1 ELSE 0 END), 0)::INTEGER
                            AS checked_in_ticket_count,
                        COALESCE(SUM(CASE WHEN toi.item_status = 'REFUNDED' THEN 1 ELSE 0 END), 0)::INTEGER
                            AS refunded_ticket_count
                    FROM filtered_orders fo
                    LEFT JOIN ticket_order_item toi ON toi.order_id = fo.id
                    GROUP BY fo.report_date
                )
                SELECT
                    os.report_date,
                    os.order_count,
                    os.paid_order_count,
                    os.completed_order_count,
                    os.refunded_order_count,
                    os.cancelled_order_count,
                    os.net_paid_amount,
                    COALESCE(its.ticket_count, 0)::INTEGER AS ticket_count,
                    COALESCE(its.sold_ticket_count, 0)::INTEGER AS sold_ticket_count,
                    COALESCE(its.checked_in_ticket_count, 0)::INTEGER AS checked_in_ticket_count,
                    COALESCE(its.refunded_ticket_count, 0)::INTEGER AS refunded_ticket_count
                FROM order_stats os
                LEFT JOIN item_stats its ON its.report_date = os.report_date
                ORDER BY os.report_date ASC
                {limit_clause}
                """,
                query_params,
            ).fetchall()

        return [admin_daily_trend_from_row(row) for row in rows]

    def list_admin_hourly_trend(self, filters: AdminReportFilter) -> list[AdminHourlyTrendRecord]:
        limit_clause = "LIMIT %s" if filters.row_limit is not None else ""
        query_params = (
            filters.date_from,
            filters.date_from,
            filters.date_to,
            filters.date_to,
        ) + ((filters.row_limit,) if filters.row_limit is not None else ())
        with connect_db() as connection:
            rows = connection.execute(
                f"""
                WITH filtered_orders AS (
                    SELECT
                        id,
                        to_char(date_trunc('hour', order_time), 'YYYY-MM-DD"T"HH24:00:00') AS report_hour,
                        order_status,
                        payment_status,
                        paid_amount
                    FROM ticket_order
                    WHERE (%s IS NULL OR order_time::date >= %s)
                      AND (%s IS NULL OR order_time::date <= %s)
                ),
                order_stats AS (
                    SELECT
                        report_hour,
                        COUNT(*)::INTEGER AS order_count,
                        COALESCE(SUM(CASE WHEN payment_status = 'PAID' THEN 1 ELSE 0 END), 0)::INTEGER
                            AS paid_order_count,
                        COALESCE(SUM(CASE WHEN order_status = 'COMPLETED' THEN 1 ELSE 0 END), 0)::INTEGER
                            AS completed_order_count,
                        COALESCE(SUM(CASE WHEN order_status = 'REFUNDED' THEN 1 ELSE 0 END), 0)::INTEGER
                            AS refunded_order_count,
                        COALESCE(SUM(CASE WHEN order_status = 'CANCELLED' THEN 1 ELSE 0 END), 0)::INTEGER
                            AS cancelled_order_count,
                        COALESCE(SUM(paid_amount), 0) AS net_paid_amount
                    FROM filtered_orders
                    GROUP BY report_hour
                ),
                item_stats AS (
                    SELECT
                        fo.report_hour,
                        COUNT(toi.id)::INTEGER AS ticket_count,
                        COALESCE(SUM(CASE WHEN toi.item_status IN ('UNUSED', 'USED') THEN 1 ELSE 0 END), 0)::INTEGER
                            AS sold_ticket_count,
                        COALESCE(SUM(CASE WHEN toi.item_status = 'USED' THEN 1 ELSE 0 END), 0)::INTEGER
                            AS checked_in_ticket_count,
                        COALESCE(SUM(CASE WHEN toi.item_status = 'REFUNDED' THEN 1 ELSE 0 END), 0)::INTEGER
                            AS refunded_ticket_count
                    FROM filtered_orders fo
                    LEFT JOIN ticket_order_item toi ON toi.order_id = fo.id
                    GROUP BY fo.report_hour
                )
                SELECT
                    os.report_hour,
                    os.order_count,
                    os.paid_order_count,
                    os.completed_order_count,
                    os.refunded_order_count,
                    os.cancelled_order_count,
                    os.net_paid_amount,
                    COALESCE(its.ticket_count, 0)::INTEGER AS ticket_count,
                    COALESCE(its.sold_ticket_count, 0)::INTEGER AS sold_ticket_count,
                    COALESCE(its.checked_in_ticket_count, 0)::INTEGER AS checked_in_ticket_count,
                    COALESCE(its.refunded_ticket_count, 0)::INTEGER AS refunded_ticket_count
                FROM order_stats os
                LEFT JOIN item_stats its ON its.report_hour = os.report_hour
                ORDER BY os.report_hour ASC
                {limit_clause}
                """,
                query_params,
            ).fetchall()

        return [admin_hourly_trend_from_row(row) for row in rows]

    def list_admin_monthly_trend(self, filters: AdminReportFilter) -> list[AdminMonthlyTrendRecord]:
        limit_clause = "LIMIT %s" if filters.row_limit is not None else ""
        query_params = (
            filters.date_from,
            filters.date_from,
            filters.date_to,
            filters.date_to,
        ) + ((filters.row_limit,) if filters.row_limit is not None else ())
        with connect_db() as connection:
            rows = connection.execute(
                f"""
                WITH filtered_orders AS (
                    SELECT
                        id,
                        to_char(date_trunc('month', order_time), 'YYYY-MM') AS report_month,
                        order_status,
                        payment_status,
                        paid_amount
                    FROM ticket_order
                    WHERE (%s IS NULL OR order_time::date >= %s)
                      AND (%s IS NULL OR order_time::date <= %s)
                ),
                order_stats AS (
                    SELECT
                        report_month,
                        COUNT(*)::INTEGER AS order_count,
                        COALESCE(SUM(CASE WHEN payment_status = 'PAID' THEN 1 ELSE 0 END), 0)::INTEGER
                            AS paid_order_count,
                        COALESCE(SUM(CASE WHEN order_status = 'COMPLETED' THEN 1 ELSE 0 END), 0)::INTEGER
                            AS completed_order_count,
                        COALESCE(SUM(CASE WHEN order_status = 'REFUNDED' THEN 1 ELSE 0 END), 0)::INTEGER
                            AS refunded_order_count,
                        COALESCE(SUM(CASE WHEN order_status = 'CANCELLED' THEN 1 ELSE 0 END), 0)::INTEGER
                            AS cancelled_order_count,
                        COALESCE(SUM(paid_amount), 0) AS net_paid_amount
                    FROM filtered_orders
                    GROUP BY report_month
                ),
                item_stats AS (
                    SELECT
                        fo.report_month,
                        COUNT(toi.id)::INTEGER AS ticket_count,
                        COALESCE(SUM(CASE WHEN toi.item_status IN ('UNUSED', 'USED') THEN 1 ELSE 0 END), 0)::INTEGER
                            AS sold_ticket_count,
                        COALESCE(SUM(CASE WHEN toi.item_status = 'USED' THEN 1 ELSE 0 END), 0)::INTEGER
                            AS checked_in_ticket_count,
                        COALESCE(SUM(CASE WHEN toi.item_status = 'REFUNDED' THEN 1 ELSE 0 END), 0)::INTEGER
                            AS refunded_ticket_count
                    FROM filtered_orders fo
                    LEFT JOIN ticket_order_item toi ON toi.order_id = fo.id
                    GROUP BY fo.report_month
                )
                SELECT
                    os.report_month,
                    os.order_count,
                    os.paid_order_count,
                    os.completed_order_count,
                    os.refunded_order_count,
                    os.cancelled_order_count,
                    os.net_paid_amount,
                    COALESCE(its.ticket_count, 0)::INTEGER AS ticket_count,
                    COALESCE(its.sold_ticket_count, 0)::INTEGER AS sold_ticket_count,
                    COALESCE(its.checked_in_ticket_count, 0)::INTEGER AS checked_in_ticket_count,
                    COALESCE(its.refunded_ticket_count, 0)::INTEGER AS refunded_ticket_count
                FROM order_stats os
                LEFT JOIN item_stats its ON its.report_month = os.report_month
                ORDER BY os.report_month ASC
                {limit_clause}
                """,
                query_params,
            ).fetchall()

        return [admin_monthly_trend_from_row(row) for row in rows]

    @staticmethod
    def _admin_order_where_clause(filters: AdminOrderListFilter) -> tuple[str, tuple[object, ...]]:
        clauses: list[str] = []
        params: list[object] = []

        if filters.status:
            clauses.append("o.order_status = %s")
            params.append(filters.status)
        if filters.payment_status:
            clauses.append("o.payment_status = %s")
            params.append(filters.payment_status)
        if filters.order_no:
            clauses.append("UPPER(o.order_no) LIKE UPPER(%s)")
            params.append(f"%{filters.order_no}%")
        if filters.buyer_phone:
            if filters.buyer_phone.isdigit() and len(filters.buyer_phone) == 4:
                clauses.append("o.buyer_phone LIKE %s")
                params.append(f"%{filters.buyer_phone}")
            else:
                clauses.append("o.buyer_phone = %s")
                params.append(filters.buyer_phone)

        if not clauses:
            return "", ()
        return "WHERE " + " AND ".join(clauses), tuple(params)

    def _load_order_for_visitor_in_connection(self, connection, visitor_id: int, order_no: str) -> OrderRecord | None:
        order_row = connection.execute(
            """
            SELECT
                id AS order_id,
                order_no,
                visitor_id,
                buyer_name,
                buyer_phone,
                order_status,
                payment_status,
                total_amount,
                payable_amount,
                order_time
            FROM ticket_order
            WHERE visitor_id = %s AND order_no = %s
            """,
            (visitor_id, order_no),
        ).fetchone()
        if not order_row:
            return None
        return order_from_row(order_row, self._load_items_for_order_in_connection(connection, order_row["order_id"]))

    def _load_items_for_order_in_connection(self, connection, order_id: int) -> list[OrderCreateItemRecord]:
        item_rows = connection.execute(
            """
            SELECT
                toi.item_no,
                rp.id AS product_id,
                toi.ticket_type_id,
                rp.product_name,
                tt.ticket_name,
                toi.time_slot_id,
                toi.visit_date,
                tsq.slot_start_time,
                tsq.slot_end_time,
                toi.original_price,
                toi.final_price,
                toi.item_status,
                toi.ticket_code,
                toi.passenger_name,
                toi.passenger_id_type,
                toi.passenger_id_number,
                toi.passenger_phone,
                toi.raft_no,
                toi.raft_seat_no,
                toi.raft_assigned_at
            FROM ticket_order_item toi
            JOIN ticket_type tt ON tt.id = toi.ticket_type_id
            JOIN route_product rp ON rp.id = toi.product_id
            JOIN time_slot_quota tsq ON tsq.id = toi.time_slot_id
            WHERE toi.order_id = %s
            ORDER BY toi.id
            """,
            (order_id,),
        ).fetchall()
        return [item_from_row(row) for row in item_rows]


def get_order_repository() -> OrderRepository:
    return PostgresOrderRepository()


class OrderPaymentStateError(Exception):
    pass


class OrderPaymentAmountMismatchError(Exception):
    pass


class OrderQuotaNotEnoughError(Exception):
    pass


class PassengerTemplateMismatchError(Exception):
    pass


class PassengerTimeSlotDuplicateError(Exception):
    pass


class OrderCancelStateError(Exception):
    pass


class TicketAlreadyCheckedInError(Exception):
    pass


class TicketNotCheckableError(Exception):
    pass


class TicketNotCheckedInError(Exception):
    pass


class TicketUndoNotAllowedError(Exception):
    pass


class OrderAlreadyRefundedError(Exception):
    pass


class OrderNotRefundableError(Exception):
    pass


class OrderRefundDeadlinePassedError(Exception):
    pass


class OrderRefundItemsInvalidError(Exception):
    pass
