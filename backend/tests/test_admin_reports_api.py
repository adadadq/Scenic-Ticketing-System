from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient

import app.repositories.orders as order_repository_module
from app.main import create_app
from app.repositories.auth import get_auth_repository
from app.repositories.orders import (
    AdminDailyTrendRecord,
    AdminHourlyTrendRecord,
    AdminMonthlyTrendRecord,
    AdminPaymentReconciliationRecord,
    AdminProductBreakdownRecord,
    AdminReportFilter,
    AdminReportSummaryRecord,
    PostgresOrderRepository,
    get_order_repository,
)

from test_admin_auth_api import FakeAuthRepository, admin_login_payload, seed_enabled_admin
from test_auth_api import csrf_headers


class FakeReportRepository:
    def __init__(self):
        self.last_filters: AdminReportFilter | None = None
        self.last_reconciliation_filters: AdminReportFilter | None = None
        self.last_product_filters: AdminReportFilter | None = None
        self.last_daily_trend_filters: AdminReportFilter | None = None
        self.last_hourly_trend_filters: AdminReportFilter | None = None
        self.last_monthly_trend_filters: AdminReportFilter | None = None

    def get_admin_report_summary(self, filters: AdminReportFilter) -> AdminReportSummaryRecord:
        self.last_filters = filters
        return AdminReportSummaryRecord(
            date_from=filters.date_from,
            date_to=filters.date_to,
            order_count=5,
            paid_order_count=2,
            completed_order_count=1,
            refunded_order_count=1,
            cancelled_order_count=1,
            net_paid_amount=Decimal("384.00"),
            ticket_count=7,
            sold_ticket_count=3,
            checked_in_ticket_count=1,
            refunded_ticket_count=2,
        )

    def get_admin_payment_reconciliation(self, filters: AdminReportFilter) -> AdminPaymentReconciliationRecord:
        self.last_reconciliation_filters = filters
        return AdminPaymentReconciliationRecord(
            date_from=filters.date_from,
            date_to=filters.date_to,
            order_net_paid_amount=Decimal("384.00"),
            captured_payment_amount=Decimal("512.00"),
            refund_audit_amount=Decimal("128.00"),
            expected_net_amount=Decimal("384.00"),
            unreconciled_amount=Decimal("0.00"),
            captured_payment_count=3,
            refund_audit_log_count=1,
            reconciled=True,
        )

    def list_admin_product_breakdown(self, filters: AdminReportFilter) -> list[AdminProductBreakdownRecord]:
        self.last_product_filters = filters
        return [
            AdminProductBreakdownRecord(
                product_id=1,
                ticket_type_id=10,
                product_name="金龙桥至旧县成人票",
                ticket_name="遇龙河成人票",
                order_count=3,
                ticket_count=6,
                sold_ticket_count=4,
                checked_in_ticket_count=2,
                refunded_ticket_count=1,
                net_paid_amount=Decimal("512.00"),
            ),
            AdminProductBreakdownRecord(
                product_id=2,
                ticket_type_id=11,
                product_name="水厄底至万景亲子票",
                ticket_name="遇龙河亲子票",
                order_count=1,
                ticket_count=2,
                sold_ticket_count=2,
                checked_in_ticket_count=0,
                refunded_ticket_count=0,
                net_paid_amount=Decimal("256.00"),
            ),
        ]

    def list_admin_daily_trend(self, filters: AdminReportFilter) -> list[AdminDailyTrendRecord]:
        self.last_daily_trend_filters = filters
        return [
            AdminDailyTrendRecord(
                report_date=date(2026, 7, 1),
                order_count=3,
                paid_order_count=2,
                completed_order_count=1,
                refunded_order_count=0,
                cancelled_order_count=1,
                net_paid_amount=Decimal("384.00"),
                ticket_count=5,
                sold_ticket_count=3,
                checked_in_ticket_count=1,
                refunded_ticket_count=0,
            ),
            AdminDailyTrendRecord(
                report_date=date(2026, 7, 2),
                order_count=2,
                paid_order_count=1,
                completed_order_count=0,
                refunded_order_count=1,
                cancelled_order_count=0,
                net_paid_amount=Decimal("128.00"),
                ticket_count=3,
                sold_ticket_count=1,
                checked_in_ticket_count=0,
                refunded_ticket_count=2,
            ),
        ]

    def list_admin_hourly_trend(self, filters: AdminReportFilter) -> list[AdminHourlyTrendRecord]:
        self.last_hourly_trend_filters = filters
        return [
            AdminHourlyTrendRecord(
                report_hour="2026-07-01T09:00:00",
                order_count=2,
                paid_order_count=1,
                completed_order_count=1,
                refunded_order_count=0,
                cancelled_order_count=1,
                net_paid_amount=Decimal("128.00"),
                ticket_count=3,
                sold_ticket_count=2,
                checked_in_ticket_count=1,
                refunded_ticket_count=0,
            ),
            AdminHourlyTrendRecord(
                report_hour="2026-07-01T10:00:00",
                order_count=1,
                paid_order_count=1,
                completed_order_count=0,
                refunded_order_count=0,
                cancelled_order_count=0,
                net_paid_amount=Decimal("256.00"),
                ticket_count=2,
                sold_ticket_count=2,
                checked_in_ticket_count=0,
                refunded_ticket_count=0,
            ),
        ]

    def list_admin_monthly_trend(self, filters: AdminReportFilter) -> list[AdminMonthlyTrendRecord]:
        self.last_monthly_trend_filters = filters
        return [
            AdminMonthlyTrendRecord(
                report_month="2026-07",
                order_count=12,
                paid_order_count=9,
                completed_order_count=6,
                refunded_order_count=1,
                cancelled_order_count=2,
                net_paid_amount=Decimal("1536.00"),
                ticket_count=18,
                sold_ticket_count=14,
                checked_in_ticket_count=6,
                refunded_ticket_count=2,
            ),
            AdminMonthlyTrendRecord(
                report_month="2026-08",
                order_count=4,
                paid_order_count=3,
                completed_order_count=1,
                refunded_order_count=1,
                cancelled_order_count=0,
                net_paid_amount=Decimal("512.00"),
                ticket_count=6,
                sold_ticket_count=4,
                checked_in_ticket_count=1,
                refunded_ticket_count=1,
            ),
        ]


def build_client(auth_repo: FakeAuthRepository, report_repo: FakeReportRepository) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_auth_repository] = lambda: auth_repo
    app.dependency_overrides[get_order_repository] = lambda: report_repo
    return TestClient(app)


def login_admin(client: TestClient, auth_repo: FakeAuthRepository) -> None:
    seed_enabled_admin(auth_repo)
    response = client.post(
        "/api/admin/auth/login",
        json=admin_login_payload(),
        headers=csrf_headers(client),
    )
    assert response.status_code == 200


def login_visitor(client: TestClient) -> None:
    response = client.post(
        "/api/auth/visitor/register",
        json={"username": "demo_visitor", "password": "Visitor123", "phone": "13911112222"},
        headers=csrf_headers(client),
    )
    assert response.status_code == 200


def test_admin_can_get_report_summary_with_date_filters_without_csrf_header():
    auth_repo = FakeAuthRepository()
    report_repo = FakeReportRepository()
    client = build_client(auth_repo, report_repo)
    login_admin(client, auth_repo)

    response = client.get(
        "/api/admin/reports/summary",
        params={"dateFrom": "2026-07-01", "dateTo": "2026-07-31"},
    )

    assert response.status_code == 200
    assert response.json()["data"] == {
        "dateFrom": "2026-07-01",
        "dateTo": "2026-07-31",
        "orderCount": 5,
        "paidOrderCount": 2,
        "completedOrderCount": 1,
        "refundedOrderCount": 1,
        "cancelledOrderCount": 1,
        "netPaidAmount": "384.00",
        "ticketCount": 7,
        "soldTicketCount": 3,
        "checkedInTicketCount": 1,
        "refundedTicketCount": 2,
    }
    assert report_repo.last_filters == AdminReportFilter(date_from=date(2026, 7, 1), date_to=date(2026, 7, 31))
    assert "buyerPhone" not in response.text
    assert "idNumber" not in response.text
    assert "session" not in response.text.lower()
    assert "csrf" not in response.text.lower()
    assert "password" not in response.text.lower()
    assert "hash" not in response.text.lower()
    assert "adminUserId" not in response.text
    assert "visitorId" not in response.text
    assert "internal" not in response.text.lower()


def test_admin_report_summary_requires_admin_session_and_rejects_visitor_session():
    auth_repo = FakeAuthRepository()
    report_repo = FakeReportRepository()
    client = build_client(auth_repo, report_repo)

    anonymous = client.get("/api/admin/reports/summary")
    assert anonymous.status_code == 401
    assert anonymous.json()["code"] == "ADMIN_AUTH_REQUIRED"

    login_visitor(client)
    visitor = client.get("/api/admin/reports/summary")
    assert visitor.status_code == 403
    assert visitor.json()["code"] == "ADMIN_FORBIDDEN"
    assert report_repo.last_filters is None


def test_admin_report_summary_rejects_invalid_date_range():
    auth_repo = FakeAuthRepository()
    report_repo = FakeReportRepository()
    client = build_client(auth_repo, report_repo)
    login_admin(client, auth_repo)

    response = client.get(
        "/api/admin/reports/summary",
        params={"dateFrom": "2026-08-01", "dateTo": "2026-07-01"},
    )

    assert response.status_code == 422
    assert response.json()["code"] == "ADMIN_REPORT_DATE_RANGE_INVALID"
    assert report_repo.last_filters is None


def test_admin_can_get_payment_reconciliation_with_date_filters_without_csrf_header():
    auth_repo = FakeAuthRepository()
    report_repo = FakeReportRepository()
    client = build_client(auth_repo, report_repo)
    login_admin(client, auth_repo)

    response = client.get(
        "/api/admin/reports/payment-reconciliation",
        params={"dateFrom": "2026-07-01", "dateTo": "2026-07-31"},
    )

    assert response.status_code == 200
    assert response.json()["data"] == {
        "dateFrom": "2026-07-01",
        "dateTo": "2026-07-31",
        "orderNetPaidAmount": "384.00",
        "capturedPaymentAmount": "512.00",
        "refundAuditAmount": "128.00",
        "expectedNetAmount": "384.00",
        "unreconciledAmount": "0.00",
        "capturedPaymentCount": 3,
        "refundAuditLogCount": 1,
        "reconciled": True,
    }
    assert report_repo.last_reconciliation_filters == AdminReportFilter(
        date_from=date(2026, 7, 1),
        date_to=date(2026, 7, 31),
    )
    assert "buyerPhone" not in response.text
    assert "idNumber" not in response.text
    assert "session" not in response.text.lower()
    assert "csrf" not in response.text.lower()
    assert "password" not in response.text.lower()
    assert "hash" not in response.text.lower()
    assert "paymentNo" not in response.text
    assert "transactionNo" not in response.text
    assert "adminUserId" not in response.text
    assert "visitorId" not in response.text
    assert "internal" not in response.text.lower()


def test_admin_payment_reconciliation_requires_admin_session_and_rejects_visitor_session():
    auth_repo = FakeAuthRepository()
    report_repo = FakeReportRepository()
    client = build_client(auth_repo, report_repo)

    anonymous = client.get("/api/admin/reports/payment-reconciliation")
    assert anonymous.status_code == 401
    assert anonymous.json()["code"] == "ADMIN_AUTH_REQUIRED"

    login_visitor(client)
    visitor = client.get("/api/admin/reports/payment-reconciliation")
    assert visitor.status_code == 403
    assert visitor.json()["code"] == "ADMIN_FORBIDDEN"
    assert report_repo.last_reconciliation_filters is None


def test_admin_payment_reconciliation_rejects_invalid_date_range():
    auth_repo = FakeAuthRepository()
    report_repo = FakeReportRepository()
    client = build_client(auth_repo, report_repo)
    login_admin(client, auth_repo)

    response = client.get(
        "/api/admin/reports/payment-reconciliation",
        params={"dateFrom": "2026-08-01", "dateTo": "2026-07-01"},
    )

    assert response.status_code == 422
    assert response.json()["code"] == "ADMIN_REPORT_DATE_RANGE_INVALID"
    assert report_repo.last_reconciliation_filters is None


def test_admin_can_get_product_breakdown_with_date_filters_without_csrf_header():
    auth_repo = FakeAuthRepository()
    report_repo = FakeReportRepository()
    client = build_client(auth_repo, report_repo)
    login_admin(client, auth_repo)

    response = client.get(
        "/api/admin/reports/product-breakdown",
        params={"dateFrom": "2026-07-01", "dateTo": "2026-07-31"},
    )

    assert response.status_code == 200
    assert response.json()["data"] == [
        {
            "productId": 1,
            "ticketTypeId": 10,
            "productName": "金龙桥至旧县成人票",
            "ticketName": "遇龙河成人票",
            "orderCount": 3,
            "ticketCount": 6,
            "soldTicketCount": 4,
            "checkedInTicketCount": 2,
            "refundedTicketCount": 1,
            "netPaidAmount": "512.00",
        },
        {
            "productId": 2,
            "ticketTypeId": 11,
            "productName": "水厄底至万景亲子票",
            "ticketName": "遇龙河亲子票",
            "orderCount": 1,
            "ticketCount": 2,
            "soldTicketCount": 2,
            "checkedInTicketCount": 0,
            "refundedTicketCount": 0,
            "netPaidAmount": "256.00",
        },
    ]
    assert report_repo.last_product_filters == AdminReportFilter(
        date_from=date(2026, 7, 1),
        date_to=date(2026, 7, 31),
    )
    assert "buyerPhone" not in response.text
    assert "idNumber" not in response.text
    assert "session" not in response.text.lower()
    assert "csrf" not in response.text.lower()
    assert "password" not in response.text.lower()
    assert "hash" not in response.text.lower()
    assert "adminUserId" not in response.text
    assert "visitorId" not in response.text
    assert "internal" not in response.text.lower()


def test_admin_product_breakdown_requires_admin_session_and_rejects_visitor_session():
    auth_repo = FakeAuthRepository()
    report_repo = FakeReportRepository()
    client = build_client(auth_repo, report_repo)

    anonymous = client.get("/api/admin/reports/product-breakdown")
    assert anonymous.status_code == 401
    assert anonymous.json()["code"] == "ADMIN_AUTH_REQUIRED"

    login_visitor(client)
    visitor = client.get("/api/admin/reports/product-breakdown")
    assert visitor.status_code == 403
    assert visitor.json()["code"] == "ADMIN_FORBIDDEN"
    assert report_repo.last_product_filters is None


def test_admin_product_breakdown_rejects_invalid_date_range():
    auth_repo = FakeAuthRepository()
    report_repo = FakeReportRepository()
    client = build_client(auth_repo, report_repo)
    login_admin(client, auth_repo)

    response = client.get(
        "/api/admin/reports/product-breakdown",
        params={"dateFrom": "2026-08-01", "dateTo": "2026-07-01"},
    )

    assert response.status_code == 422
    assert response.json()["code"] == "ADMIN_REPORT_DATE_RANGE_INVALID"
    assert report_repo.last_product_filters is None


def test_admin_can_get_daily_trend_with_date_filters_without_csrf_header():
    auth_repo = FakeAuthRepository()
    report_repo = FakeReportRepository()
    client = build_client(auth_repo, report_repo)
    login_admin(client, auth_repo)

    response = client.get(
        "/api/admin/reports/daily-trend",
        params={"dateFrom": "2026-07-01", "dateTo": "2026-07-31"},
    )

    assert response.status_code == 200
    assert response.json()["data"] == [
        {
            "reportDate": "2026-07-01",
            "orderCount": 3,
            "paidOrderCount": 2,
            "completedOrderCount": 1,
            "refundedOrderCount": 0,
            "cancelledOrderCount": 1,
            "netPaidAmount": "384.00",
            "ticketCount": 5,
            "soldTicketCount": 3,
            "checkedInTicketCount": 1,
            "refundedTicketCount": 0,
        },
        {
            "reportDate": "2026-07-02",
            "orderCount": 2,
            "paidOrderCount": 1,
            "completedOrderCount": 0,
            "refundedOrderCount": 1,
            "cancelledOrderCount": 0,
            "netPaidAmount": "128.00",
            "ticketCount": 3,
            "soldTicketCount": 1,
            "checkedInTicketCount": 0,
            "refundedTicketCount": 2,
        },
    ]
    assert report_repo.last_daily_trend_filters == AdminReportFilter(
        date_from=date(2026, 7, 1),
        date_to=date(2026, 7, 31),
    )
    assert "buyerPhone" not in response.text
    assert "idNumber" not in response.text
    assert "session" not in response.text.lower()
    assert "csrf" not in response.text.lower()
    assert "password" not in response.text.lower()
    assert "hash" not in response.text.lower()
    assert "adminUserId" not in response.text
    assert "visitorId" not in response.text
    assert "internal" not in response.text.lower()


def test_admin_daily_trend_requires_admin_session_and_rejects_visitor_session():
    auth_repo = FakeAuthRepository()
    report_repo = FakeReportRepository()
    client = build_client(auth_repo, report_repo)

    anonymous = client.get("/api/admin/reports/daily-trend")
    assert anonymous.status_code == 401
    assert anonymous.json()["code"] == "ADMIN_AUTH_REQUIRED"

    login_visitor(client)
    visitor = client.get("/api/admin/reports/daily-trend")
    assert visitor.status_code == 403
    assert visitor.json()["code"] == "ADMIN_FORBIDDEN"
    assert report_repo.last_daily_trend_filters is None


def test_admin_daily_trend_rejects_invalid_date_range():
    auth_repo = FakeAuthRepository()
    report_repo = FakeReportRepository()
    client = build_client(auth_repo, report_repo)
    login_admin(client, auth_repo)

    response = client.get(
        "/api/admin/reports/daily-trend",
        params={"dateFrom": "2026-08-01", "dateTo": "2026-07-01"},
    )

    assert response.status_code == 422
    assert response.json()["code"] == "ADMIN_REPORT_DATE_RANGE_INVALID"
    assert report_repo.last_daily_trend_filters is None


def test_admin_daily_trend_can_include_empty_days_when_date_bounds_are_present():
    auth_repo = FakeAuthRepository()
    report_repo = FakeReportRepository()
    client = build_client(auth_repo, report_repo)
    login_admin(client, auth_repo)

    response = client.get(
        "/api/admin/reports/daily-trend",
        params={"dateFrom": "2026-07-01", "dateTo": "2026-07-03", "includeEmpty": "true"},
    )

    assert response.status_code == 200
    rows = response.json()["data"]
    assert [row["reportDate"] for row in rows] == ["2026-07-01", "2026-07-02", "2026-07-03"]
    assert rows[0]["orderCount"] == 3
    assert rows[1]["orderCount"] == 2
    assert rows[2] == {
        "reportDate": "2026-07-03",
        "orderCount": 0,
        "paidOrderCount": 0,
        "completedOrderCount": 0,
        "refundedOrderCount": 0,
        "cancelledOrderCount": 0,
        "netPaidAmount": "0.00",
        "ticketCount": 0,
        "soldTicketCount": 0,
        "checkedInTicketCount": 0,
        "refundedTicketCount": 0,
    }
    assert report_repo.last_daily_trend_filters == AdminReportFilter(
        date_from=date(2026, 7, 1),
        date_to=date(2026, 7, 3),
    )


def test_admin_daily_trend_include_empty_requires_bounded_date_range():
    auth_repo = FakeAuthRepository()
    report_repo = FakeReportRepository()
    client = build_client(auth_repo, report_repo)
    login_admin(client, auth_repo)

    response = client.get(
        "/api/admin/reports/daily-trend",
        params={"dateFrom": "2026-07-01", "includeEmpty": "true"},
    )

    assert response.status_code == 422
    assert response.json()["code"] == "ADMIN_REPORT_INCLUDE_EMPTY_RANGE_REQUIRED"
    assert report_repo.last_daily_trend_filters is None


def test_admin_daily_trend_include_empty_rejects_too_large_date_range():
    auth_repo = FakeAuthRepository()
    report_repo = FakeReportRepository()
    client = build_client(auth_repo, report_repo)
    login_admin(client, auth_repo)

    response = client.get(
        "/api/admin/reports/daily-trend",
        params={"dateFrom": "2026-01-01", "dateTo": "2027-01-02", "includeEmpty": "true"},
    )

    assert response.status_code == 422
    assert response.json()["code"] == "ADMIN_REPORT_INCLUDE_EMPTY_RANGE_TOO_LARGE"
    assert report_repo.last_daily_trend_filters is None


def test_admin_can_get_hourly_trend_with_date_filters_without_csrf_header():
    auth_repo = FakeAuthRepository()
    report_repo = FakeReportRepository()
    client = build_client(auth_repo, report_repo)
    login_admin(client, auth_repo)

    response = client.get(
        "/api/admin/reports/hourly-trend",
        params={"dateFrom": "2026-07-01", "dateTo": "2026-07-01"},
    )

    assert response.status_code == 200
    assert response.json()["data"] == [
        {
            "reportHour": "2026-07-01T09:00:00",
            "orderCount": 2,
            "paidOrderCount": 1,
            "completedOrderCount": 1,
            "refundedOrderCount": 0,
            "cancelledOrderCount": 1,
            "netPaidAmount": "128.00",
            "ticketCount": 3,
            "soldTicketCount": 2,
            "checkedInTicketCount": 1,
            "refundedTicketCount": 0,
        },
        {
            "reportHour": "2026-07-01T10:00:00",
            "orderCount": 1,
            "paidOrderCount": 1,
            "completedOrderCount": 0,
            "refundedOrderCount": 0,
            "cancelledOrderCount": 0,
            "netPaidAmount": "256.00",
            "ticketCount": 2,
            "soldTicketCount": 2,
            "checkedInTicketCount": 0,
            "refundedTicketCount": 0,
        },
    ]
    assert report_repo.last_hourly_trend_filters == AdminReportFilter(
        date_from=date(2026, 7, 1),
        date_to=date(2026, 7, 1),
    )
    assert "buyerPhone" not in response.text
    assert "idNumber" not in response.text
    assert "session" not in response.text.lower()
    assert "csrf" not in response.text.lower()
    assert "password" not in response.text.lower()
    assert "hash" not in response.text.lower()
    assert "adminUserId" not in response.text
    assert "visitorId" not in response.text
    assert "internal" not in response.text.lower()


def test_admin_hourly_trend_requires_admin_session_and_rejects_visitor_session():
    auth_repo = FakeAuthRepository()
    report_repo = FakeReportRepository()
    client = build_client(auth_repo, report_repo)

    anonymous = client.get("/api/admin/reports/hourly-trend")
    assert anonymous.status_code == 401
    assert anonymous.json()["code"] == "ADMIN_AUTH_REQUIRED"

    login_visitor(client)
    visitor = client.get("/api/admin/reports/hourly-trend")
    assert visitor.status_code == 403
    assert visitor.json()["code"] == "ADMIN_FORBIDDEN"
    assert report_repo.last_hourly_trend_filters is None


def test_admin_hourly_trend_rejects_invalid_date_range():
    auth_repo = FakeAuthRepository()
    report_repo = FakeReportRepository()
    client = build_client(auth_repo, report_repo)
    login_admin(client, auth_repo)

    response = client.get(
        "/api/admin/reports/hourly-trend",
        params={"dateFrom": "2026-08-01", "dateTo": "2026-07-01"},
    )

    assert response.status_code == 422
    assert response.json()["code"] == "ADMIN_REPORT_DATE_RANGE_INVALID"
    assert report_repo.last_hourly_trend_filters is None


def test_admin_hourly_trend_can_include_empty_hours_when_date_bounds_are_present():
    auth_repo = FakeAuthRepository()
    report_repo = FakeReportRepository()
    client = build_client(auth_repo, report_repo)
    login_admin(client, auth_repo)

    response = client.get(
        "/api/admin/reports/hourly-trend",
        params={"dateFrom": "2026-07-01", "dateTo": "2026-07-01", "includeEmpty": "true"},
    )

    assert response.status_code == 200
    rows = response.json()["data"]
    assert len(rows) == 24
    assert rows[0] == {
        "reportHour": "2026-07-01T00:00:00",
        "orderCount": 0,
        "paidOrderCount": 0,
        "completedOrderCount": 0,
        "refundedOrderCount": 0,
        "cancelledOrderCount": 0,
        "netPaidAmount": "0.00",
        "ticketCount": 0,
        "soldTicketCount": 0,
        "checkedInTicketCount": 0,
        "refundedTicketCount": 0,
    }
    assert rows[9]["reportHour"] == "2026-07-01T09:00:00"
    assert rows[9]["orderCount"] == 2
    assert rows[10]["reportHour"] == "2026-07-01T10:00:00"
    assert rows[10]["orderCount"] == 1
    assert rows[-1]["reportHour"] == "2026-07-01T23:00:00"
    assert rows[-1]["orderCount"] == 0
    assert report_repo.last_hourly_trend_filters == AdminReportFilter(
        date_from=date(2026, 7, 1),
        date_to=date(2026, 7, 1),
    )


def test_admin_hourly_trend_include_empty_rejects_too_large_date_range():
    auth_repo = FakeAuthRepository()
    report_repo = FakeReportRepository()
    client = build_client(auth_repo, report_repo)
    login_admin(client, auth_repo)

    response = client.get(
        "/api/admin/reports/hourly-trend",
        params={"dateFrom": "2026-01-01", "dateTo": "2026-02-01", "includeEmpty": "true"},
    )

    assert response.status_code == 422
    assert response.json()["code"] == "ADMIN_REPORT_INCLUDE_EMPTY_RANGE_TOO_LARGE"
    assert report_repo.last_hourly_trend_filters is None


def test_admin_hourly_trend_include_empty_requires_bounded_date_range():
    auth_repo = FakeAuthRepository()
    report_repo = FakeReportRepository()
    client = build_client(auth_repo, report_repo)
    login_admin(client, auth_repo)

    response = client.get(
        "/api/admin/reports/hourly-trend",
        params={"dateTo": "2026-07-01", "includeEmpty": "true"},
    )

    assert response.status_code == 422
    assert response.json()["code"] == "ADMIN_REPORT_INCLUDE_EMPTY_RANGE_REQUIRED"
    assert report_repo.last_hourly_trend_filters is None


def test_admin_can_get_monthly_trend_with_date_filters_without_csrf_header():
    auth_repo = FakeAuthRepository()
    report_repo = FakeReportRepository()
    client = build_client(auth_repo, report_repo)
    login_admin(client, auth_repo)

    response = client.get(
        "/api/admin/reports/monthly-trend",
        params={"dateFrom": "2026-01-01", "dateTo": "2026-12-31"},
    )

    assert response.status_code == 200
    assert response.json()["data"] == [
        {
            "reportMonth": "2026-07",
            "orderCount": 12,
            "paidOrderCount": 9,
            "completedOrderCount": 6,
            "refundedOrderCount": 1,
            "cancelledOrderCount": 2,
            "netPaidAmount": "1536.00",
            "ticketCount": 18,
            "soldTicketCount": 14,
            "checkedInTicketCount": 6,
            "refundedTicketCount": 2,
        },
        {
            "reportMonth": "2026-08",
            "orderCount": 4,
            "paidOrderCount": 3,
            "completedOrderCount": 1,
            "refundedOrderCount": 1,
            "cancelledOrderCount": 0,
            "netPaidAmount": "512.00",
            "ticketCount": 6,
            "soldTicketCount": 4,
            "checkedInTicketCount": 1,
            "refundedTicketCount": 1,
        },
    ]
    assert report_repo.last_monthly_trend_filters == AdminReportFilter(
        date_from=date(2026, 1, 1),
        date_to=date(2026, 12, 31),
    )
    assert "buyerPhone" not in response.text
    assert "idNumber" not in response.text
    assert "session" not in response.text.lower()
    assert "csrf" not in response.text.lower()
    assert "password" not in response.text.lower()
    assert "hash" not in response.text.lower()
    assert "adminUserId" not in response.text
    assert "visitorId" not in response.text
    assert "internal" not in response.text.lower()


def test_admin_monthly_trend_requires_admin_session_and_rejects_visitor_session():
    auth_repo = FakeAuthRepository()
    report_repo = FakeReportRepository()
    client = build_client(auth_repo, report_repo)

    anonymous = client.get("/api/admin/reports/monthly-trend")
    assert anonymous.status_code == 401
    assert anonymous.json()["code"] == "ADMIN_AUTH_REQUIRED"

    login_visitor(client)
    visitor = client.get("/api/admin/reports/monthly-trend")
    assert visitor.status_code == 403
    assert visitor.json()["code"] == "ADMIN_FORBIDDEN"
    assert report_repo.last_monthly_trend_filters is None


def test_admin_monthly_trend_rejects_invalid_date_range():
    auth_repo = FakeAuthRepository()
    report_repo = FakeReportRepository()
    client = build_client(auth_repo, report_repo)
    login_admin(client, auth_repo)

    response = client.get(
        "/api/admin/reports/monthly-trend",
        params={"dateFrom": "2026-08-01", "dateTo": "2026-07-01"},
    )

    assert response.status_code == 422
    assert response.json()["code"] == "ADMIN_REPORT_DATE_RANGE_INVALID"
    assert report_repo.last_monthly_trend_filters is None


def test_admin_monthly_trend_can_include_empty_months_when_date_bounds_are_present():
    auth_repo = FakeAuthRepository()
    report_repo = FakeReportRepository()
    client = build_client(auth_repo, report_repo)
    login_admin(client, auth_repo)

    response = client.get(
        "/api/admin/reports/monthly-trend",
        params={"dateFrom": "2026-07-01", "dateTo": "2026-09-30", "includeEmpty": "true"},
    )

    assert response.status_code == 200
    rows = response.json()["data"]
    assert [row["reportMonth"] for row in rows] == ["2026-07", "2026-08", "2026-09"]
    assert rows[0]["orderCount"] == 12
    assert rows[1]["orderCount"] == 4
    assert rows[2] == {
        "reportMonth": "2026-09",
        "orderCount": 0,
        "paidOrderCount": 0,
        "completedOrderCount": 0,
        "refundedOrderCount": 0,
        "cancelledOrderCount": 0,
        "netPaidAmount": "0.00",
        "ticketCount": 0,
        "soldTicketCount": 0,
        "checkedInTicketCount": 0,
        "refundedTicketCount": 0,
    }
    assert report_repo.last_monthly_trend_filters == AdminReportFilter(
        date_from=date(2026, 7, 1),
        date_to=date(2026, 9, 30),
    )


def test_admin_monthly_trend_include_empty_rejects_too_large_month_range():
    auth_repo = FakeAuthRepository()
    report_repo = FakeReportRepository()
    client = build_client(auth_repo, report_repo)
    login_admin(client, auth_repo)

    response = client.get(
        "/api/admin/reports/monthly-trend",
        params={"dateFrom": "2026-01-01", "dateTo": "2031-01-31", "includeEmpty": "true"},
    )

    assert response.status_code == 422
    assert response.json()["code"] == "ADMIN_REPORT_INCLUDE_EMPTY_RANGE_TOO_LARGE"
    assert report_repo.last_monthly_trend_filters is None


def test_admin_monthly_trend_include_empty_requires_bounded_date_range():
    auth_repo = FakeAuthRepository()
    report_repo = FakeReportRepository()
    client = build_client(auth_repo, report_repo)
    login_admin(client, auth_repo)

    response = client.get(
        "/api/admin/reports/monthly-trend",
        params={"dateFrom": "2026-07-01", "includeEmpty": "true"},
    )

    assert response.status_code == 422
    assert response.json()["code"] == "ADMIN_REPORT_INCLUDE_EMPTY_RANGE_REQUIRED"
    assert report_repo.last_monthly_trend_filters is None


def test_postgres_admin_report_summary_uses_parameterized_date_filters(monkeypatch):
    calls: list[tuple[str, tuple[object, ...]]] = []

    class FakeCursor:
        def execute(self, sql: str, params: tuple[object, ...]):
            calls.append((sql, params))
            return self

        def fetchone(self):
            return {
                "order_count": 5,
                "paid_order_count": 2,
                "completed_order_count": 1,
                "refunded_order_count": 1,
                "cancelled_order_count": 1,
                "net_paid_amount": Decimal("384.00"),
                "ticket_count": 7,
                "sold_ticket_count": 3,
                "checked_in_ticket_count": 1,
                "refunded_ticket_count": 2,
            }

    class FakeConnection:
        def __enter__(self):
            return FakeCursor()

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr(order_repository_module, "connect_db", lambda: FakeConnection())

    filters = AdminReportFilter(date_from=date(2026, 7, 1), date_to=date(2026, 7, 31))
    result = PostgresOrderRepository().get_admin_report_summary(filters)

    assert result.order_count == 5
    assert result.net_paid_amount == Decimal("384.00")
    assert result.checked_in_ticket_count == 1
    assert len(calls) == 1
    assert "WITH filtered_orders" in calls[0][0]
    assert "order_stats AS" in calls[0][0]
    assert "item_stats AS" in calls[0][0]
    assert "CROSS JOIN item_stats" in calls[0][0]
    assert "ticket_order_item" in calls[0][0]
    assert "2026-07-01" not in calls[0][0]
    assert calls[0][1] == (date(2026, 7, 1), date(2026, 7, 1), date(2026, 7, 31), date(2026, 7, 31))


def test_postgres_admin_payment_reconciliation_uses_parameterized_filters_and_refunded_payments(monkeypatch):
    calls: list[tuple[str, tuple[object, ...]]] = []

    class FakeCursor:
        def execute(self, sql: str, params: tuple[object, ...]):
            calls.append((sql, params))
            return self

        def fetchone(self):
            return {
                "order_net_paid_amount": Decimal("384.00"),
                "captured_payment_amount": Decimal("512.00"),
                "refund_audit_amount": Decimal("128.00"),
                "expected_net_amount": Decimal("384.00"),
                "unreconciled_amount": Decimal("0.00"),
                "captured_payment_count": 3,
                "refund_audit_log_count": 1,
            }

    class FakeConnection:
        def __enter__(self):
            return FakeCursor()

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr(order_repository_module, "connect_db", lambda: FakeConnection())

    filters = AdminReportFilter(date_from=date(2026, 7, 1), date_to=date(2026, 7, 31))
    result = PostgresOrderRepository().get_admin_payment_reconciliation(filters)

    assert result.order_net_paid_amount == Decimal("384.00")
    assert result.captured_payment_amount == Decimal("512.00")
    assert result.refund_audit_amount == Decimal("128.00")
    assert result.expected_net_amount == Decimal("384.00")
    assert result.unreconciled_amount == Decimal("0.00")
    assert result.captured_payment_count == 3
    assert result.refund_audit_log_count == 1
    assert result.reconciled is True
    assert len(calls) == 1
    sql, params = calls[0]
    assert "WITH filtered_orders" in sql
    assert "payment_record pr" in sql
    assert "refund_audit_log ral" in sql
    assert "SUM(ral.refunded_amount)" in sql
    assert "ral.refund_amount" not in sql
    assert "pr.payment_status IN ('SUCCESS', 'REFUNDED')" in sql
    assert "payment_no" not in sql
    assert "transaction_no" not in sql
    assert "2026-07-01" not in sql
    assert "2026-07-31" not in sql
    assert params == (date(2026, 7, 1), date(2026, 7, 1), date(2026, 7, 31), date(2026, 7, 31))


def test_postgres_admin_product_breakdown_uses_parameterized_date_filters_and_item_amounts(monkeypatch):
    calls: list[tuple[str, tuple[object, ...]]] = []

    class FakeCursor:
        def execute(self, sql: str, params: tuple[object, ...]):
            calls.append((sql, params))
            return self

        def fetchall(self):
            return [
                {
                    "product_id": 1,
                    "ticket_type_id": 10,
                    "product_name": "金龙桥至旧县成人票",
                    "ticket_name": "遇龙河成人票",
                    "order_count": 3,
                    "ticket_count": 6,
                    "sold_ticket_count": 4,
                    "checked_in_ticket_count": 2,
                    "refunded_ticket_count": 1,
                    "net_paid_amount": Decimal("512.00"),
                }
            ]

    class FakeConnection:
        def __enter__(self):
            return FakeCursor()

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr(order_repository_module, "connect_db", lambda: FakeConnection())

    filters = AdminReportFilter(date_from=date(2026, 7, 1), date_to=date(2026, 7, 31))
    result = PostgresOrderRepository().list_admin_product_breakdown(filters)

    assert result[0].product_id == 1
    assert result[0].order_count == 3
    assert result[0].net_paid_amount == Decimal("512.00")
    assert len(calls) == 1
    sql, params = calls[0]
    assert "COUNT(DISTINCT o.id)" in sql
    assert "SUM(CASE WHEN toi.item_status IN ('UNUSED', 'USED') THEN toi.final_price ELSE 0 END)" in sql
    assert "o.paid_amount" not in sql
    assert "ticket_order_item" in sql
    assert "route_product" in sql
    assert "ticket_type" in sql
    assert "ORDER BY net_paid_amount DESC, ticket_count DESC, product_id ASC" in sql
    assert "2026-07-01" not in sql
    assert "2026-07-31" not in sql
    assert params == (date(2026, 7, 1), date(2026, 7, 1), date(2026, 7, 31), date(2026, 7, 31))


def test_postgres_admin_daily_trend_uses_parameterized_date_filters_and_separate_aggregates(monkeypatch):
    calls: list[tuple[str, tuple[object, ...]]] = []

    class FakeCursor:
        def execute(self, sql: str, params: tuple[object, ...]):
            calls.append((sql, params))
            return self

        def fetchall(self):
            return [
                {
                    "report_date": date(2026, 7, 1),
                    "order_count": 3,
                    "paid_order_count": 2,
                    "completed_order_count": 1,
                    "refunded_order_count": 0,
                    "cancelled_order_count": 1,
                    "net_paid_amount": Decimal("384.00"),
                    "ticket_count": 5,
                    "sold_ticket_count": 3,
                    "checked_in_ticket_count": 1,
                    "refunded_ticket_count": 0,
                }
            ]

    class FakeConnection:
        def __enter__(self):
            return FakeCursor()

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr(order_repository_module, "connect_db", lambda: FakeConnection())

    filters = AdminReportFilter(date_from=date(2026, 7, 1), date_to=date(2026, 7, 31))
    result = PostgresOrderRepository().list_admin_daily_trend(filters)

    assert result[0].report_date == date(2026, 7, 1)
    assert result[0].order_count == 3
    assert result[0].net_paid_amount == Decimal("384.00")
    assert len(calls) == 1
    sql, params = calls[0]
    assert "WITH filtered_orders" in sql
    assert "order_stats AS" in sql
    assert "item_stats AS" in sql
    assert "SUM(paid_amount)" in sql
    assert "LEFT JOIN item_stats" in sql
    assert "ticket_order_item" in sql
    assert "ORDER BY os.report_date ASC" in sql
    assert "2026-07-01" not in sql
    assert "2026-07-31" not in sql
    assert params == (date(2026, 7, 1), date(2026, 7, 1), date(2026, 7, 31), date(2026, 7, 31))


def test_postgres_admin_hourly_trend_uses_parameterized_date_filters_and_separate_aggregates(monkeypatch):
    calls: list[tuple[str, tuple[object, ...]]] = []

    class FakeCursor:
        def execute(self, sql: str, params: tuple[object, ...]):
            calls.append((sql, params))
            return self

        def fetchall(self):
            return [
                {
                    "report_hour": "2026-07-01T09:00:00",
                    "order_count": 2,
                    "paid_order_count": 1,
                    "completed_order_count": 1,
                    "refunded_order_count": 0,
                    "cancelled_order_count": 1,
                    "net_paid_amount": Decimal("128.00"),
                    "ticket_count": 3,
                    "sold_ticket_count": 2,
                    "checked_in_ticket_count": 1,
                    "refunded_ticket_count": 0,
                }
            ]

    class FakeConnection:
        def __enter__(self):
            return FakeCursor()

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr(order_repository_module, "connect_db", lambda: FakeConnection())

    filters = AdminReportFilter(date_from=date(2026, 7, 1), date_to=date(2026, 7, 31))
    result = PostgresOrderRepository().list_admin_hourly_trend(filters)

    assert result[0].report_hour == "2026-07-01T09:00:00"
    assert result[0].order_count == 2
    assert result[0].net_paid_amount == Decimal("128.00")
    assert len(calls) == 1
    sql, params = calls[0]
    assert "WITH filtered_orders" in sql
    assert "date_trunc('hour', order_time)" in sql
    assert "to_char" in sql
    assert "order_stats AS" in sql
    assert "item_stats AS" in sql
    assert "SUM(paid_amount)" in sql
    assert "LEFT JOIN item_stats" in sql
    assert "ticket_order_item" in sql
    assert "ORDER BY os.report_hour ASC" in sql
    assert "2026-07-01" not in sql
    assert "2026-07-31" not in sql
    assert params == (date(2026, 7, 1), date(2026, 7, 1), date(2026, 7, 31), date(2026, 7, 31))


def test_postgres_admin_monthly_trend_uses_parameterized_date_filters_and_separate_aggregates(monkeypatch):
    calls: list[tuple[str, tuple[object, ...]]] = []

    class FakeCursor:
        def execute(self, sql: str, params: tuple[object, ...]):
            calls.append((sql, params))
            return self

        def fetchall(self):
            return [
                {
                    "report_month": "2026-07",
                    "order_count": 12,
                    "paid_order_count": 9,
                    "completed_order_count": 6,
                    "refunded_order_count": 1,
                    "cancelled_order_count": 2,
                    "net_paid_amount": Decimal("1536.00"),
                    "ticket_count": 18,
                    "sold_ticket_count": 14,
                    "checked_in_ticket_count": 6,
                    "refunded_ticket_count": 2,
                }
            ]

    class FakeConnection:
        def __enter__(self):
            return FakeCursor()

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr(order_repository_module, "connect_db", lambda: FakeConnection())

    filters = AdminReportFilter(date_from=date(2026, 1, 1), date_to=date(2026, 12, 31))
    result = PostgresOrderRepository().list_admin_monthly_trend(filters)

    assert result[0].report_month == "2026-07"
    assert result[0].order_count == 12
    assert result[0].net_paid_amount == Decimal("1536.00")
    assert len(calls) == 1
    sql, params = calls[0]
    assert "WITH filtered_orders" in sql
    assert "date_trunc('month', order_time)" in sql
    assert "to_char" in sql
    assert "order_stats AS" in sql
    assert "item_stats AS" in sql
    assert "SUM(paid_amount)" in sql
    assert "LEFT JOIN item_stats" in sql
    assert "ticket_order_item" in sql
    assert "ORDER BY os.report_month ASC" in sql
    assert "2026-01-01" not in sql
    assert "2026-12-31" not in sql
    assert params == (date(2026, 1, 1), date(2026, 1, 1), date(2026, 12, 31), date(2026, 12, 31))
