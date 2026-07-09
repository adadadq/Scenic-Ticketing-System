import csv
import io
import zipfile
from datetime import UTC, date, datetime
from decimal import Decimal
from xml.etree import ElementTree

import pytest
from fastapi.testclient import TestClient

import app.repositories.orders as order_repository_module
import app.services.orders as order_service_module
from app.main import create_app
from app.repositories.auth import get_auth_repository
from app.repositories.orders import (
    AdminDailyTrendRecord,
    AdminHourlyTrendRecord,
    AdminMonthlyTrendRecord,
    AdminOrderExportRecord,
    AdminPaymentReconciliationRecord,
    AdminProductBreakdownRecord,
    AdminReportFilter,
    PostgresOrderRepository,
    get_order_repository,
)
from app.schemas.orders import AdminHourlyTrendDTO, AdminPaymentReconciliationDTO, AdminProductBreakdownDTO
from app.services.orders import AdminReportService, SYNC_EXPORT_ROW_LIMIT

from test_admin_auth_api import FakeAuthRepository, admin_login_payload, seed_enabled_admin
from test_auth_api import csrf_headers


EXPORT_FETCH_LIMIT = SYNC_EXPORT_ROW_LIMIT + 1


class FakeReportExportRepository:
    def __init__(self):
        self.last_export_filters: AdminReportFilter | None = None
        self.last_daily_trend_filters: AdminReportFilter | None = None
        self.last_hourly_trend_filters: AdminReportFilter | None = None
        self.last_monthly_trend_filters: AdminReportFilter | None = None
        self.last_payment_reconciliation_filters: AdminReportFilter | None = None
        self.last_product_breakdown_filters: AdminReportFilter | None = None

    def list_admin_order_export_rows(self, filters: AdminReportFilter) -> list[AdminOrderExportRecord]:
        self.last_export_filters = filters
        return [
            AdminOrderExportRecord(
                order_no="O-CSV-2",
                buyer_name="+SUM(1,1)",
                buyer_phone="13911112222",
                order_status="PAID",
                payment_status="PAID",
                total_amount=Decimal("256.00"),
                payable_amount=Decimal("256.00"),
                order_time=datetime(2026, 7, 2, 9, 30, tzinfo=UTC),
                item_count=2,
            ),
            AdminOrderExportRecord(
                order_no="O-CSV-1",
                buyer_name="=cmd|' /C calc'!A0",
                buyer_phone="13800009999",
                order_status="CREATED",
                payment_status="UNPAID",
                total_amount=Decimal("128.00"),
                payable_amount=Decimal("128.00"),
                order_time=datetime(2026, 7, 1, 9, 0, tzinfo=UTC),
                item_count=1,
            ),
        ]

    def get_admin_payment_reconciliation(self, filters: AdminReportFilter) -> AdminPaymentReconciliationRecord:
        self.last_payment_reconciliation_filters = filters
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
        self.last_product_breakdown_filters = filters
        return [
            AdminProductBreakdownRecord(
                product_id=1,
                ticket_type_id=10,
                product_name="+SUM(1,1)",
                ticket_name="=cmd|' /C calc'!A0",
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
                report_date=date(2026, 7, 3),
                order_count=1,
                paid_order_count=1,
                completed_order_count=0,
                refunded_order_count=0,
                cancelled_order_count=0,
                net_paid_amount=Decimal("128.00"),
                ticket_count=1,
                sold_ticket_count=1,
                checked_in_ticket_count=0,
                refunded_ticket_count=0,
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
            )
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
                report_month="2026-09",
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


def build_client(auth_repo: FakeAuthRepository, report_repo: FakeReportExportRepository) -> TestClient:
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


def csv_rows(response_text: str) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(response_text.lstrip("\ufeff"))))


def xlsx_rows(response_content: bytes) -> list[list[str]]:
    with zipfile.ZipFile(io.BytesIO(response_content)) as workbook:
        assert "[Content_Types].xml" in workbook.namelist()
        assert "xl/workbook.xml" in workbook.namelist()
        assert "xl/worksheets/sheet1.xml" in workbook.namelist()
        worksheet_xml = workbook.read("xl/worksheets/sheet1.xml")

    root = ElementTree.fromstring(worksheet_xml)
    namespace = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    assert root.findall(".//x:f", namespace) == []
    rows = []
    for row in root.findall(".//x:row", namespace):
        rows.append([cell.findtext("x:is/x:t", default="", namespaces=namespace) for cell in row.findall("x:c", namespace)])
    return rows


def xlsx_worksheet_text(response_content: bytes) -> str:
    with zipfile.ZipFile(io.BytesIO(response_content)) as workbook:
        return workbook.read("xl/worksheets/sheet1.xml").decode("utf-8")


@pytest.mark.parametrize(
    ("raw_value", "expected_value"),
    [
        ("=cmd", "'=cmd"),
        ("+SUM(1,1)", "'+SUM(1,1)"),
        ("-1+2", "'-1+2"),
        ("@SUM(1,1)", "'@SUM(1,1)"),
        ("\t=cmd", "'\t=cmd"),
        ("\r=cmd", "'\r=cmd"),
        ("\n=cmd", "'\n=cmd"),
        (" =cmd", "' =cmd"),
    ],
)
def test_order_csv_cells_escape_formula_like_prefixes(raw_value: str, expected_value: str):
    assert AdminReportService.safe_csv_cell(raw_value) == expected_value


def test_payment_reconciliation_csv_reuses_spreadsheet_escape_for_all_values(monkeypatch):
    escaped_values = []

    def fake_safe_cell(value: object) -> str:
        escaped_values.append(str(value))
        return f"safe:{value}"

    monkeypatch.setattr(AdminReportService, "safe_spreadsheet_cell", staticmethod(fake_safe_cell))

    csv_text = AdminReportService.to_payment_reconciliation_csv(
        AdminPaymentReconciliationDTO(
            date_from=date(2026, 7, 1),
            date_to=date(2026, 7, 31),
            order_net_paid_amount=Decimal("384.00"),
            captured_payment_amount=Decimal("512.00"),
            refund_audit_amount=Decimal("128.00"),
            expected_net_amount=Decimal("384.00"),
            unreconciled_amount=Decimal("0.00"),
            captured_payment_count=3,
            refund_audit_log_count=1,
            reconciled=True,
        )
    )

    assert escaped_values == [
        "2026-07-01",
        "2026-07-31",
        "384.00",
        "512.00",
        "128.00",
        "384.00",
        "0.00",
        "3",
        "1",
        "true",
    ]
    rows = csv_rows(csv_text)
    assert rows == [
        {
            "dateFrom": "safe:2026-07-01",
            "dateTo": "safe:2026-07-31",
            "orderNetPaidAmount": "safe:384.00",
            "capturedPaymentAmount": "safe:512.00",
            "refundAuditAmount": "safe:128.00",
            "expectedNetAmount": "safe:384.00",
            "unreconciledAmount": "safe:0.00",
            "capturedPaymentCount": "safe:3",
            "refundAuditLogCount": "safe:1",
            "reconciled": "safe:true",
        }
    ]


def test_product_breakdown_csv_reuses_spreadsheet_escape_for_all_values(monkeypatch):
    escaped_values = []

    def fake_safe_cell(value: object) -> str:
        escaped_values.append(str(value))
        return f"safe:{value}"

    monkeypatch.setattr(AdminReportService, "safe_spreadsheet_cell", staticmethod(fake_safe_cell))

    csv_text = AdminReportService.to_product_breakdown_csv(
        [
            AdminProductBreakdownDTO(
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
            )
        ]
    )

    assert escaped_values == [
        "1",
        "10",
        "金龙桥至旧县成人票",
        "遇龙河成人票",
        "3",
        "6",
        "4",
        "2",
        "1",
        "512.00",
    ]
    assert csv_rows(csv_text) == [
        {
            "productId": "safe:1",
            "ticketTypeId": "safe:10",
            "productName": "safe:金龙桥至旧县成人票",
            "ticketName": "safe:遇龙河成人票",
            "orderCount": "safe:3",
            "ticketCount": "safe:6",
            "soldTicketCount": "safe:4",
            "checkedInTicketCount": "safe:2",
            "refundedTicketCount": "safe:1",
            "netPaidAmount": "safe:512.00",
        }
    ]


def test_payment_reconciliation_xlsx_uses_inline_strings_without_formula_nodes():
    workbook = AdminReportService.to_payment_reconciliation_xlsx(
        AdminPaymentReconciliationDTO(
            date_from=date(2026, 7, 1),
            date_to=date(2026, 7, 31),
            order_net_paid_amount=Decimal("384.00"),
            captured_payment_amount=Decimal("512.00"),
            refund_audit_amount=Decimal("128.00"),
            expected_net_amount=Decimal("384.00"),
            unreconciled_amount=Decimal("0.00"),
            captured_payment_count=3,
            refund_audit_log_count=1,
            reconciled=True,
        )
    )

    assert xlsx_rows(workbook) == [
        [
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
        ],
        [
            "2026-07-01",
            "2026-07-31",
            "384.00",
            "512.00",
            "128.00",
            "384.00",
            "0.00",
            "3",
            "1",
            "true",
        ],
    ]
    worksheet_text = xlsx_worksheet_text(workbook)
    assert "<f>" not in worksheet_text
    assert 't="inlineStr"' in worksheet_text


def test_product_breakdown_xlsx_uses_inline_strings_without_formula_nodes_and_cleans_xml_text():
    workbook = AdminReportService.to_product_breakdown_xlsx(
        [
            AdminProductBreakdownDTO(
                product_id=1,
                ticket_type_id=10,
                product_name="\x01=cmd|' /C calc'!A0",
                ticket_name="+SUM(1,1)",
                order_count=3,
                ticket_count=6,
                sold_ticket_count=4,
                checked_in_ticket_count=2,
                refunded_ticket_count=1,
                net_paid_amount=Decimal("512.00"),
            )
        ]
    )

    assert xlsx_rows(workbook) == [
        [
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
        ],
        [
            "1",
            "10",
            "'=cmd|' /C calc'!A0",
            "'+SUM(1,1)",
            "3",
            "6",
            "4",
            "2",
            "1",
            "512.00",
        ],
    ]
    worksheet_text = xlsx_worksheet_text(workbook)
    assert "\x01" not in worksheet_text
    assert "<f>" not in worksheet_text
    assert 't="inlineStr"' in worksheet_text


def test_admin_can_export_order_csv_with_date_filters_without_csrf_header():
    auth_repo = FakeAuthRepository()
    report_repo = FakeReportExportRepository()
    client = build_client(auth_repo, report_repo)
    login_admin(client, auth_repo)

    response = client.get(
        "/api/admin/reports/orders.csv",
        params={"dateFrom": "2026-07-01", "dateTo": "2026-07-31"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv; charset=utf-8")
    assert response.headers["content-disposition"] == 'attachment; filename="admin-orders-20260701-20260731.csv"'
    assert response.content.startswith(b"\xef\xbb\xbf")
    assert report_repo.last_export_filters == AdminReportFilter(
        date_from=date(2026, 7, 1),
        date_to=date(2026, 7, 31),
        row_limit=EXPORT_FETCH_LIMIT,
    )

    rows = csv_rows(response.text)
    assert rows == [
        {
            "orderNo": "O-CSV-2",
            "buyerName": "'+SUM(1,1)",
            "buyerPhoneMasked": "139****2222",
            "orderStatus": "PAID",
            "paymentStatus": "PAID",
            "totalAmount": "256.00",
            "payableAmount": "256.00",
            "orderTime": "2026-07-02T09:30:00Z",
            "itemCount": "2",
        },
        {
            "orderNo": "O-CSV-1",
            "buyerName": "'=cmd|' /C calc'!A0",
            "buyerPhoneMasked": "138****9999",
            "orderStatus": "CREATED",
            "paymentStatus": "UNPAID",
            "totalAmount": "128.00",
            "payableAmount": "128.00",
            "orderTime": "2026-07-01T09:00:00Z",
            "itemCount": "1",
        },
    ]
    assert "13911112222" not in response.text
    assert "13800009999" not in response.text
    assert "idNumber" not in response.text
    assert "session" not in response.text.lower()
    assert "csrf" not in response.text.lower()
    assert "password" not in response.text.lower()
    assert "hash" not in response.text.lower()
    assert "visitorId" not in response.text


def test_admin_can_export_payment_reconciliation_csv_with_date_filters_without_csrf_header():
    auth_repo = FakeAuthRepository()
    report_repo = FakeReportExportRepository()
    client = build_client(auth_repo, report_repo)
    login_admin(client, auth_repo)

    response = client.get(
        "/api/admin/reports/payment-reconciliation.csv",
        params={"dateFrom": "2026-07-01", "dateTo": "2026-07-31"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv; charset=utf-8")
    assert (
        response.headers["content-disposition"]
        == 'attachment; filename="admin-payment-reconciliation-20260701-20260731.csv"'
    )
    assert response.content.startswith(b"\xef\xbb\xbf")
    assert report_repo.last_payment_reconciliation_filters == AdminReportFilter(
        date_from=date(2026, 7, 1),
        date_to=date(2026, 7, 31),
    )
    assert csv_rows(response.text) == [
        {
            "dateFrom": "2026-07-01",
            "dateTo": "2026-07-31",
            "orderNetPaidAmount": "384.00",
            "capturedPaymentAmount": "512.00",
            "refundAuditAmount": "128.00",
            "expectedNetAmount": "384.00",
            "unreconciledAmount": "0.00",
            "capturedPaymentCount": "3",
            "refundAuditLogCount": "1",
            "reconciled": "true",
        }
    ]
    assert "buyerPhone" not in response.text
    assert "idNumber" not in response.text
    assert "paymentNo" not in response.text
    assert "transactionNo" not in response.text
    assert "session" not in response.text.lower()
    assert "csrf" not in response.text.lower()
    assert "password" not in response.text.lower()
    assert "hash" not in response.text.lower()
    assert "adminUserId" not in response.text
    assert "visitorId" not in response.text
    assert "internal" not in response.text.lower()


def test_admin_can_export_product_breakdown_csv_with_date_filters_without_csrf_header():
    auth_repo = FakeAuthRepository()
    report_repo = FakeReportExportRepository()
    client = build_client(auth_repo, report_repo)
    login_admin(client, auth_repo)

    response = client.get(
        "/api/admin/reports/product-breakdown.csv",
        params={"dateFrom": "2026-07-01", "dateTo": "2026-07-31"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv; charset=utf-8")
    assert (
        response.headers["content-disposition"]
        == 'attachment; filename="admin-product-breakdown-20260701-20260731.csv"'
    )
    assert response.content.startswith(b"\xef\xbb\xbf")
    assert report_repo.last_product_breakdown_filters == AdminReportFilter(
        date_from=date(2026, 7, 1),
        date_to=date(2026, 7, 31),
        row_limit=EXPORT_FETCH_LIMIT,
    )
    assert csv_rows(response.text) == [
        {
            "productId": "1",
            "ticketTypeId": "10",
            "productName": "'+SUM(1,1)",
            "ticketName": "'=cmd|' /C calc'!A0",
            "orderCount": "3",
            "ticketCount": "6",
            "soldTicketCount": "4",
            "checkedInTicketCount": "2",
            "refundedTicketCount": "1",
            "netPaidAmount": "512.00",
        },
        {
            "productId": "2",
            "ticketTypeId": "11",
            "productName": "水厄底至万景亲子票",
            "ticketName": "遇龙河亲子票",
            "orderCount": "1",
            "ticketCount": "2",
            "soldTicketCount": "2",
            "checkedInTicketCount": "0",
            "refundedTicketCount": "0",
            "netPaidAmount": "256.00",
        },
    ]
    assert "buyerPhone" not in response.text
    assert "idNumber" not in response.text
    assert "paymentNo" not in response.text
    assert "transactionNo" not in response.text
    assert "session" not in response.text.lower()
    assert "csrf" not in response.text.lower()
    assert "password" not in response.text.lower()
    assert "hash" not in response.text.lower()
    assert "adminUserId" not in response.text
    assert "visitorId" not in response.text
    assert "internal" not in response.text.lower()


def test_admin_can_export_product_breakdown_xlsx_with_date_filters_without_csrf_header():
    auth_repo = FakeAuthRepository()
    report_repo = FakeReportExportRepository()
    client = build_client(auth_repo, report_repo)
    login_admin(client, auth_repo)

    response = client.get(
        "/api/admin/reports/product-breakdown.xlsx",
        params={"dateFrom": "2026-07-01", "dateTo": "2026-07-31"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    assert (
        response.headers["content-disposition"]
        == 'attachment; filename="admin-product-breakdown-20260701-20260731.xlsx"'
    )
    assert report_repo.last_product_breakdown_filters == AdminReportFilter(
        date_from=date(2026, 7, 1),
        date_to=date(2026, 7, 31),
        row_limit=EXPORT_FETCH_LIMIT,
    )
    assert xlsx_rows(response.content) == [
        [
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
        ],
        [
            "1",
            "10",
            "'+SUM(1,1)",
            "'=cmd|' /C calc'!A0",
            "3",
            "6",
            "4",
            "2",
            "1",
            "512.00",
        ],
        [
            "2",
            "11",
            "水厄底至万景亲子票",
            "遇龙河亲子票",
            "1",
            "2",
            "2",
            "0",
            "0",
            "256.00",
        ],
    ]
    worksheet_text = xlsx_worksheet_text(response.content)
    assert "<f>" not in worksheet_text
    assert "buyerPhone" not in worksheet_text
    assert "idNumber" not in worksheet_text
    assert "paymentNo" not in worksheet_text
    assert "transactionNo" not in worksheet_text
    assert "session" not in worksheet_text.lower()
    assert "csrf" not in worksheet_text.lower()
    assert "password" not in worksheet_text.lower()
    assert "hash" not in worksheet_text.lower()
    assert "adminUserId" not in worksheet_text
    assert "visitorId" not in worksheet_text
    assert "internal" not in worksheet_text.lower()


def test_admin_report_export_rejects_rows_over_sync_export_limit(monkeypatch):
    monkeypatch.setattr(order_service_module, "SYNC_EXPORT_ROW_LIMIT", 1)
    auth_repo = FakeAuthRepository()
    report_repo = FakeReportExportRepository()
    client = build_client(auth_repo, report_repo)
    login_admin(client, auth_repo)

    response = client.get(
        "/api/admin/reports/product-breakdown.csv",
        params={"dateFrom": "2026-07-01", "dateTo": "2026-07-31"},
    )

    assert response.status_code == 413
    assert response.json()["code"] == "ADMIN_EXPORT_TOO_LARGE"
    assert report_repo.last_product_breakdown_filters == AdminReportFilter(
        date_from=date(2026, 7, 1),
        date_to=date(2026, 7, 31),
        row_limit=2,
    )


def test_admin_can_export_payment_reconciliation_xlsx_with_date_filters_without_csrf_header():
    auth_repo = FakeAuthRepository()
    report_repo = FakeReportExportRepository()
    client = build_client(auth_repo, report_repo)
    login_admin(client, auth_repo)

    response = client.get(
        "/api/admin/reports/payment-reconciliation.xlsx",
        params={"dateFrom": "2026-07-01", "dateTo": "2026-07-31"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    assert (
        response.headers["content-disposition"]
        == 'attachment; filename="admin-payment-reconciliation-20260701-20260731.xlsx"'
    )
    assert report_repo.last_payment_reconciliation_filters == AdminReportFilter(
        date_from=date(2026, 7, 1),
        date_to=date(2026, 7, 31),
    )
    assert xlsx_rows(response.content) == [
        [
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
        ],
        [
            "2026-07-01",
            "2026-07-31",
            "384.00",
            "512.00",
            "128.00",
            "384.00",
            "0.00",
            "3",
            "1",
            "true",
        ],
    ]
    worksheet_text = xlsx_worksheet_text(response.content)
    assert "<f>" not in worksheet_text
    assert "buyerPhone" not in worksheet_text
    assert "idNumber" not in worksheet_text
    assert "paymentNo" not in worksheet_text
    assert "transactionNo" not in worksheet_text
    assert "session" not in worksheet_text.lower()
    assert "csrf" not in worksheet_text.lower()
    assert "password" not in worksheet_text.lower()
    assert "hash" not in worksheet_text.lower()
    assert "adminUserId" not in worksheet_text
    assert "visitorId" not in worksheet_text
    assert "internal" not in worksheet_text.lower()


def test_admin_can_export_daily_trend_csv_with_zero_fill_without_csrf_header():
    auth_repo = FakeAuthRepository()
    report_repo = FakeReportExportRepository()
    client = build_client(auth_repo, report_repo)
    login_admin(client, auth_repo)

    response = client.get(
        "/api/admin/reports/daily-trend.csv",
        params={"dateFrom": "2026-07-01", "dateTo": "2026-07-03", "includeEmpty": "true"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv; charset=utf-8")
    assert response.headers["content-disposition"] == 'attachment; filename="admin-daily-trend-20260701-20260703.csv"'
    assert response.content.startswith(b"\xef\xbb\xbf")
    assert report_repo.last_daily_trend_filters == AdminReportFilter(
        date_from=date(2026, 7, 1),
        date_to=date(2026, 7, 3),
        row_limit=EXPORT_FETCH_LIMIT,
    )
    assert csv_rows(response.text) == [
        {
            "reportDate": "2026-07-01",
            "orderCount": "3",
            "paidOrderCount": "2",
            "completedOrderCount": "1",
            "refundedOrderCount": "0",
            "cancelledOrderCount": "1",
            "netPaidAmount": "384.00",
            "ticketCount": "5",
            "soldTicketCount": "3",
            "checkedInTicketCount": "1",
            "refundedTicketCount": "0",
        },
        {
            "reportDate": "2026-07-02",
            "orderCount": "0",
            "paidOrderCount": "0",
            "completedOrderCount": "0",
            "refundedOrderCount": "0",
            "cancelledOrderCount": "0",
            "netPaidAmount": "0.00",
            "ticketCount": "0",
            "soldTicketCount": "0",
            "checkedInTicketCount": "0",
            "refundedTicketCount": "0",
        },
        {
            "reportDate": "2026-07-03",
            "orderCount": "1",
            "paidOrderCount": "1",
            "completedOrderCount": "0",
            "refundedOrderCount": "0",
            "cancelledOrderCount": "0",
            "netPaidAmount": "128.00",
            "ticketCount": "1",
            "soldTicketCount": "1",
            "checkedInTicketCount": "0",
            "refundedTicketCount": "0",
        },
    ]
    assert "buyerPhone" not in response.text
    assert "idNumber" not in response.text
    assert "session" not in response.text.lower()
    assert "csrf" not in response.text.lower()
    assert "password" not in response.text.lower()
    assert "adminUserId" not in response.text


def test_admin_can_export_hourly_trend_csv_with_zero_fill_without_csrf_header():
    auth_repo = FakeAuthRepository()
    report_repo = FakeReportExportRepository()
    client = build_client(auth_repo, report_repo)
    login_admin(client, auth_repo)

    response = client.get(
        "/api/admin/reports/hourly-trend.csv",
        params={"dateFrom": "2026-07-01", "dateTo": "2026-07-01", "includeEmpty": "true"},
    )

    assert response.status_code == 200
    assert response.headers["content-disposition"] == 'attachment; filename="admin-hourly-trend-20260701-20260701.csv"'
    rows = csv_rows(response.text)
    assert len(rows) == 24
    assert rows[0]["reportHour"] == "2026-07-01T00:00:00"
    assert rows[0]["orderCount"] == "0"
    assert rows[9]["reportHour"] == "2026-07-01T09:00:00"
    assert rows[9]["netPaidAmount"] == "128.00"
    assert rows[-1]["reportHour"] == "2026-07-01T23:00:00"
    assert rows[-1]["ticketCount"] == "0"
    assert report_repo.last_hourly_trend_filters == AdminReportFilter(
        date_from=date(2026, 7, 1),
        date_to=date(2026, 7, 1),
        row_limit=EXPORT_FETCH_LIMIT,
    )


def test_admin_can_export_monthly_trend_csv_with_zero_fill_without_csrf_header():
    auth_repo = FakeAuthRepository()
    report_repo = FakeReportExportRepository()
    client = build_client(auth_repo, report_repo)
    login_admin(client, auth_repo)

    response = client.get(
        "/api/admin/reports/monthly-trend.csv",
        params={"dateFrom": "2026-07-01", "dateTo": "2026-09-30", "includeEmpty": "true"},
    )

    assert response.status_code == 200
    assert response.headers["content-disposition"] == 'attachment; filename="admin-monthly-trend-20260701-20260930.csv"'
    rows = csv_rows(response.text)
    assert [row["reportMonth"] for row in rows] == ["2026-07", "2026-08", "2026-09"]
    assert rows[1]["orderCount"] == "0"
    assert rows[1]["netPaidAmount"] == "0.00"
    assert rows[2]["orderCount"] == "4"
    assert report_repo.last_monthly_trend_filters == AdminReportFilter(
        date_from=date(2026, 7, 1),
        date_to=date(2026, 9, 30),
        row_limit=EXPORT_FETCH_LIMIT,
    )


def test_admin_can_export_daily_trend_xlsx_with_zero_fill_without_csrf_header():
    auth_repo = FakeAuthRepository()
    report_repo = FakeReportExportRepository()
    client = build_client(auth_repo, report_repo)
    login_admin(client, auth_repo)

    response = client.get(
        "/api/admin/reports/daily-trend.xlsx",
        params={"dateFrom": "2026-07-01", "dateTo": "2026-07-03", "includeEmpty": "true"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    assert response.headers["content-disposition"] == 'attachment; filename="admin-daily-trend-20260701-20260703.xlsx"'
    assert response.content.startswith(b"PK")
    assert report_repo.last_daily_trend_filters == AdminReportFilter(
        date_from=date(2026, 7, 1),
        date_to=date(2026, 7, 3),
        row_limit=EXPORT_FETCH_LIMIT,
    )
    assert xlsx_rows(response.content) == [
        [
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
        ],
        ["2026-07-01", "3", "2", "1", "0", "1", "384.00", "5", "3", "1", "0"],
        ["2026-07-02", "0", "0", "0", "0", "0", "0.00", "0", "0", "0", "0"],
        ["2026-07-03", "1", "1", "0", "0", "0", "128.00", "1", "1", "0", "0"],
    ]
    worksheet_text = xlsx_worksheet_text(response.content)
    assert "buyerPhone" not in worksheet_text
    assert "idNumber" not in worksheet_text
    assert "session" not in worksheet_text.lower()
    assert "csrf" not in worksheet_text.lower()
    assert "password" not in worksheet_text.lower()
    assert "adminUserId" not in worksheet_text


def test_admin_can_export_hourly_trend_xlsx_with_zero_fill_without_csrf_header():
    auth_repo = FakeAuthRepository()
    report_repo = FakeReportExportRepository()
    client = build_client(auth_repo, report_repo)
    login_admin(client, auth_repo)

    response = client.get(
        "/api/admin/reports/hourly-trend.xlsx",
        params={"dateFrom": "2026-07-01", "dateTo": "2026-07-01", "includeEmpty": "true"},
    )

    assert response.status_code == 200
    assert response.headers["content-disposition"] == 'attachment; filename="admin-hourly-trend-20260701-20260701.xlsx"'
    rows = xlsx_rows(response.content)
    assert len(rows) == 25
    assert rows[1][0] == "2026-07-01T00:00:00"
    assert rows[1][1] == "0"
    assert rows[10][0] == "2026-07-01T09:00:00"
    assert rows[10][6] == "128.00"
    assert rows[-1][0] == "2026-07-01T23:00:00"
    assert rows[-1][7] == "0"
    assert report_repo.last_hourly_trend_filters == AdminReportFilter(
        date_from=date(2026, 7, 1),
        date_to=date(2026, 7, 1),
        row_limit=EXPORT_FETCH_LIMIT,
    )


def test_admin_can_export_monthly_trend_xlsx_with_zero_fill_without_csrf_header():
    auth_repo = FakeAuthRepository()
    report_repo = FakeReportExportRepository()
    client = build_client(auth_repo, report_repo)
    login_admin(client, auth_repo)

    response = client.get(
        "/api/admin/reports/monthly-trend.xlsx",
        params={"dateFrom": "2026-07-01", "dateTo": "2026-09-30", "includeEmpty": "true"},
    )

    assert response.status_code == 200
    assert response.headers["content-disposition"] == 'attachment; filename="admin-monthly-trend-20260701-20260930.xlsx"'
    rows = xlsx_rows(response.content)
    assert [row[0] for row in rows[1:]] == ["2026-07", "2026-08", "2026-09"]
    assert rows[2][1] == "0"
    assert rows[2][6] == "0.00"
    assert rows[3][1] == "4"
    assert report_repo.last_monthly_trend_filters == AdminReportFilter(
        date_from=date(2026, 7, 1),
        date_to=date(2026, 9, 30),
        row_limit=EXPORT_FETCH_LIMIT,
    )


def test_trend_csv_exports_reuse_trend_range_validation():
    auth_repo = FakeAuthRepository()
    report_repo = FakeReportExportRepository()
    client = build_client(auth_repo, report_repo)
    login_admin(client, auth_repo)

    invalid_range = client.get(
        "/api/admin/reports/daily-trend.csv",
        params={"dateFrom": "2026-08-01", "dateTo": "2026-07-01"},
    )
    missing_bounds = client.get(
        "/api/admin/reports/hourly-trend.csv",
        params={"includeEmpty": "true"},
    )
    too_large = client.get(
        "/api/admin/reports/monthly-trend.csv",
        params={"dateFrom": "2021-01-01", "dateTo": "2026-01-01", "includeEmpty": "true"},
    )

    assert invalid_range.status_code == 422
    assert invalid_range.json()["code"] == "ADMIN_REPORT_DATE_RANGE_INVALID"
    assert missing_bounds.status_code == 422
    assert missing_bounds.json()["code"] == "ADMIN_REPORT_INCLUDE_EMPTY_RANGE_REQUIRED"
    assert too_large.status_code == 422
    assert too_large.json()["code"] == "ADMIN_REPORT_INCLUDE_EMPTY_RANGE_TOO_LARGE"


def test_trend_xlsx_exports_reuse_trend_range_validation():
    auth_repo = FakeAuthRepository()
    report_repo = FakeReportExportRepository()
    client = build_client(auth_repo, report_repo)
    login_admin(client, auth_repo)

    invalid_range = client.get(
        "/api/admin/reports/daily-trend.xlsx",
        params={"dateFrom": "2026-08-01", "dateTo": "2026-07-01"},
    )
    missing_bounds = client.get(
        "/api/admin/reports/hourly-trend.xlsx",
        params={"includeEmpty": "true"},
    )
    too_large = client.get(
        "/api/admin/reports/monthly-trend.xlsx",
        params={"dateFrom": "2021-01-01", "dateTo": "2026-01-01", "includeEmpty": "true"},
    )

    assert invalid_range.status_code == 422
    assert invalid_range.json()["code"] == "ADMIN_REPORT_DATE_RANGE_INVALID"
    assert missing_bounds.status_code == 422
    assert missing_bounds.json()["code"] == "ADMIN_REPORT_INCLUDE_EMPTY_RANGE_REQUIRED"
    assert too_large.status_code == 422
    assert too_large.json()["code"] == "ADMIN_REPORT_INCLUDE_EMPTY_RANGE_TOO_LARGE"


def test_daily_trend_csv_requires_admin_session_and_rejects_visitor_session():
    auth_repo = FakeAuthRepository()
    report_repo = FakeReportExportRepository()
    client = build_client(auth_repo, report_repo)

    anonymous = client.get("/api/admin/reports/daily-trend.csv")
    assert anonymous.status_code == 401
    assert anonymous.json()["code"] == "ADMIN_AUTH_REQUIRED"

    login_visitor(client)
    visitor = client.get("/api/admin/reports/daily-trend.csv")
    assert visitor.status_code == 403
    assert visitor.json()["code"] == "ADMIN_FORBIDDEN"
    assert report_repo.last_daily_trend_filters is None


def test_daily_trend_xlsx_requires_admin_session_and_rejects_visitor_session():
    auth_repo = FakeAuthRepository()
    report_repo = FakeReportExportRepository()
    client = build_client(auth_repo, report_repo)

    anonymous = client.get("/api/admin/reports/daily-trend.xlsx")
    assert anonymous.status_code == 401
    assert anonymous.json()["code"] == "ADMIN_AUTH_REQUIRED"

    login_visitor(client)
    visitor = client.get("/api/admin/reports/daily-trend.xlsx")
    assert visitor.status_code == 403
    assert visitor.json()["code"] == "ADMIN_FORBIDDEN"
    assert report_repo.last_daily_trend_filters is None


def test_trend_csv_cells_reuse_spreadsheet_escape_for_all_values(monkeypatch):
    escaped_values = []

    def fake_safe_cell(value: object) -> str:
        escaped_values.append(str(value))
        return f"safe:{value}"

    monkeypatch.setattr(AdminReportService, "safe_spreadsheet_cell", staticmethod(fake_safe_cell))

    hourly_csv = AdminReportService.to_hourly_trend_csv(
        [
            AdminHourlyTrendDTO(
                report_hour="2026-07-01T09:00:00",
                order_count=1,
                paid_order_count=1,
                completed_order_count=0,
                refunded_order_count=0,
                cancelled_order_count=0,
                net_paid_amount=Decimal("1.00"),
                ticket_count=1,
                sold_ticket_count=1,
                checked_in_ticket_count=0,
                refunded_ticket_count=0,
            )
        ]
    )

    row = csv_rows(hourly_csv)[0]
    assert row["reportHour"] == "safe:2026-07-01T09:00:00"
    assert row["netPaidAmount"] == "safe:1.00"
    assert "2026-07-01T09:00:00" in escaped_values
    assert "1.00" in escaped_values


def test_admin_can_export_order_xlsx_with_date_filters_without_csrf_header():
    auth_repo = FakeAuthRepository()
    report_repo = FakeReportExportRepository()
    client = build_client(auth_repo, report_repo)
    login_admin(client, auth_repo)

    response = client.get(
        "/api/admin/reports/orders.xlsx",
        params={"dateFrom": "2026-07-01", "dateTo": "2026-07-31"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    assert response.headers["content-disposition"] == 'attachment; filename="admin-orders-20260701-20260731.xlsx"'
    assert response.content.startswith(b"PK")
    assert report_repo.last_export_filters == AdminReportFilter(
        date_from=date(2026, 7, 1),
        date_to=date(2026, 7, 31),
        row_limit=EXPORT_FETCH_LIMIT,
    )
    assert xlsx_rows(response.content) == [
        [
            "orderNo",
            "buyerName",
            "buyerPhoneMasked",
            "orderStatus",
            "paymentStatus",
            "totalAmount",
            "payableAmount",
            "orderTime",
            "itemCount",
        ],
        [
            "O-CSV-2",
            "'+SUM(1,1)",
            "139****2222",
            "PAID",
            "PAID",
            "256.00",
            "256.00",
            "2026-07-02T09:30:00Z",
            "2",
        ],
        [
            "O-CSV-1",
            "'=cmd|' /C calc'!A0",
            "138****9999",
            "CREATED",
            "UNPAID",
            "128.00",
            "128.00",
            "2026-07-01T09:00:00Z",
            "1",
        ],
    ]
    worksheet_text = xlsx_worksheet_text(response.content)
    assert "13911112222" not in worksheet_text
    assert "13800009999" not in worksheet_text
    assert "idNumber" not in worksheet_text
    assert "session" not in worksheet_text.lower()
    assert "csrf" not in worksheet_text.lower()
    assert "password" not in worksheet_text.lower()
    assert "hash" not in worksheet_text.lower()
    assert "visitorId" not in worksheet_text


def test_admin_order_xlsx_removes_xml_1_control_characters_from_text_cells():
    workbook = AdminReportService.to_orders_xlsx(
        [
            AdminOrderExportRecord(
                order_no="O-XLSX-1",
                buyer_name="bad\x00\x0bname & <safe>",
                buyer_phone="13911112222",
                order_status="PAID",
                payment_status="PAID",
                total_amount=Decimal("256.00"),
                payable_amount=Decimal("256.00"),
                order_time=datetime(2026, 7, 2, 9, 30, tzinfo=UTC),
                item_count=2,
            )
        ]
    )

    assert xlsx_rows(workbook)[1][1] == "badname & <safe>"
    worksheet_text = xlsx_worksheet_text(workbook)
    assert "\x00" not in worksheet_text
    assert "\x0b" not in worksheet_text
    assert "badname &amp; &lt;safe&gt;" in worksheet_text


def test_admin_order_csv_requires_admin_session_and_rejects_visitor_session():
    auth_repo = FakeAuthRepository()
    report_repo = FakeReportExportRepository()
    client = build_client(auth_repo, report_repo)

    anonymous = client.get("/api/admin/reports/orders.csv")
    assert anonymous.status_code == 401
    assert anonymous.json()["code"] == "ADMIN_AUTH_REQUIRED"

    login_visitor(client)
    visitor = client.get("/api/admin/reports/orders.csv")
    assert visitor.status_code == 403
    assert visitor.json()["code"] == "ADMIN_FORBIDDEN"
    assert report_repo.last_export_filters is None


def test_admin_order_xlsx_requires_admin_session_and_rejects_visitor_session():
    auth_repo = FakeAuthRepository()
    report_repo = FakeReportExportRepository()
    client = build_client(auth_repo, report_repo)

    anonymous = client.get("/api/admin/reports/orders.xlsx")
    assert anonymous.status_code == 401
    assert anonymous.json()["code"] == "ADMIN_AUTH_REQUIRED"

    login_visitor(client)
    visitor = client.get("/api/admin/reports/orders.xlsx")
    assert visitor.status_code == 403
    assert visitor.json()["code"] == "ADMIN_FORBIDDEN"
    assert report_repo.last_export_filters is None


def test_payment_reconciliation_csv_requires_admin_session_and_rejects_visitor_session():
    auth_repo = FakeAuthRepository()
    report_repo = FakeReportExportRepository()
    client = build_client(auth_repo, report_repo)

    anonymous = client.get("/api/admin/reports/payment-reconciliation.csv")
    assert anonymous.status_code == 401
    assert anonymous.json()["code"] == "ADMIN_AUTH_REQUIRED"

    login_visitor(client)
    visitor = client.get("/api/admin/reports/payment-reconciliation.csv")
    assert visitor.status_code == 403
    assert visitor.json()["code"] == "ADMIN_FORBIDDEN"
    assert report_repo.last_payment_reconciliation_filters is None


def test_payment_reconciliation_xlsx_requires_admin_session_and_rejects_visitor_session():
    auth_repo = FakeAuthRepository()
    report_repo = FakeReportExportRepository()
    client = build_client(auth_repo, report_repo)

    anonymous = client.get("/api/admin/reports/payment-reconciliation.xlsx")
    assert anonymous.status_code == 401
    assert anonymous.json()["code"] == "ADMIN_AUTH_REQUIRED"

    login_visitor(client)
    visitor = client.get("/api/admin/reports/payment-reconciliation.xlsx")
    assert visitor.status_code == 403
    assert visitor.json()["code"] == "ADMIN_FORBIDDEN"
    assert report_repo.last_payment_reconciliation_filters is None


def test_product_breakdown_csv_requires_admin_session_and_rejects_visitor_session():
    auth_repo = FakeAuthRepository()
    report_repo = FakeReportExportRepository()
    client = build_client(auth_repo, report_repo)

    anonymous = client.get("/api/admin/reports/product-breakdown.csv")
    assert anonymous.status_code == 401
    assert anonymous.json()["code"] == "ADMIN_AUTH_REQUIRED"

    login_visitor(client)
    visitor = client.get("/api/admin/reports/product-breakdown.csv")
    assert visitor.status_code == 403
    assert visitor.json()["code"] == "ADMIN_FORBIDDEN"
    assert report_repo.last_product_breakdown_filters is None


def test_product_breakdown_xlsx_requires_admin_session_and_rejects_visitor_session():
    auth_repo = FakeAuthRepository()
    report_repo = FakeReportExportRepository()
    client = build_client(auth_repo, report_repo)

    anonymous = client.get("/api/admin/reports/product-breakdown.xlsx")
    assert anonymous.status_code == 401
    assert anonymous.json()["code"] == "ADMIN_AUTH_REQUIRED"

    login_visitor(client)
    visitor = client.get("/api/admin/reports/product-breakdown.xlsx")
    assert visitor.status_code == 403
    assert visitor.json()["code"] == "ADMIN_FORBIDDEN"
    assert report_repo.last_product_breakdown_filters is None


def test_admin_order_csv_rejects_invalid_date_range():
    auth_repo = FakeAuthRepository()
    report_repo = FakeReportExportRepository()
    client = build_client(auth_repo, report_repo)
    login_admin(client, auth_repo)

    response = client.get(
        "/api/admin/reports/orders.csv",
        params={"dateFrom": "2026-08-01", "dateTo": "2026-07-01"},
    )

    assert response.status_code == 422
    assert response.json()["code"] == "ADMIN_REPORT_DATE_RANGE_INVALID"
    assert report_repo.last_export_filters is None


def test_payment_reconciliation_csv_rejects_invalid_date_range():
    auth_repo = FakeAuthRepository()
    report_repo = FakeReportExportRepository()
    client = build_client(auth_repo, report_repo)
    login_admin(client, auth_repo)

    response = client.get(
        "/api/admin/reports/payment-reconciliation.csv",
        params={"dateFrom": "2026-08-01", "dateTo": "2026-07-01"},
    )

    assert response.status_code == 422
    assert response.json()["code"] == "ADMIN_REPORT_DATE_RANGE_INVALID"
    assert report_repo.last_payment_reconciliation_filters is None


def test_payment_reconciliation_xlsx_rejects_invalid_date_range():
    auth_repo = FakeAuthRepository()
    report_repo = FakeReportExportRepository()
    client = build_client(auth_repo, report_repo)
    login_admin(client, auth_repo)

    response = client.get(
        "/api/admin/reports/payment-reconciliation.xlsx",
        params={"dateFrom": "2026-08-01", "dateTo": "2026-07-01"},
    )

    assert response.status_code == 422
    assert response.json()["code"] == "ADMIN_REPORT_DATE_RANGE_INVALID"
    assert report_repo.last_payment_reconciliation_filters is None


def test_product_breakdown_csv_rejects_invalid_date_range():
    auth_repo = FakeAuthRepository()
    report_repo = FakeReportExportRepository()
    client = build_client(auth_repo, report_repo)
    login_admin(client, auth_repo)

    response = client.get(
        "/api/admin/reports/product-breakdown.csv",
        params={"dateFrom": "2026-08-01", "dateTo": "2026-07-01"},
    )

    assert response.status_code == 422
    assert response.json()["code"] == "ADMIN_REPORT_DATE_RANGE_INVALID"
    assert report_repo.last_product_breakdown_filters is None


def test_product_breakdown_xlsx_rejects_invalid_date_range():
    auth_repo = FakeAuthRepository()
    report_repo = FakeReportExportRepository()
    client = build_client(auth_repo, report_repo)
    login_admin(client, auth_repo)

    response = client.get(
        "/api/admin/reports/product-breakdown.xlsx",
        params={"dateFrom": "2026-08-01", "dateTo": "2026-07-01"},
    )

    assert response.status_code == 422
    assert response.json()["code"] == "ADMIN_REPORT_DATE_RANGE_INVALID"
    assert report_repo.last_product_breakdown_filters is None


def test_admin_order_xlsx_rejects_invalid_date_range():
    auth_repo = FakeAuthRepository()
    report_repo = FakeReportExportRepository()
    client = build_client(auth_repo, report_repo)
    login_admin(client, auth_repo)

    response = client.get(
        "/api/admin/reports/orders.xlsx",
        params={"dateFrom": "2026-08-01", "dateTo": "2026-07-01"},
    )

    assert response.status_code == 422
    assert response.json()["code"] == "ADMIN_REPORT_DATE_RANGE_INVALID"
    assert report_repo.last_export_filters is None


def test_postgres_admin_order_csv_export_uses_parameterized_date_filters(monkeypatch):
    calls: list[tuple[str, tuple[object, ...]]] = []

    class FakeCursor:
        def execute(self, sql: str, params: tuple[object, ...]):
            calls.append((sql, params))
            return self

        def fetchall(self):
            return [
                {
                    "order_no": "O-CSV",
                    "buyer_name": "张三",
                    "buyer_phone": "13911112222",
                    "order_status": "PAID",
                    "payment_status": "PAID",
                    "total_amount": Decimal("128.00"),
                    "payable_amount": Decimal("128.00"),
                    "order_time": datetime(2026, 7, 1, 9, 0, tzinfo=UTC),
                    "item_count": 1,
                }
            ]

    class FakeConnection:
        def __enter__(self):
            return FakeCursor()

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr(order_repository_module, "connect_db", lambda: FakeConnection())

    filters = AdminReportFilter(date_from=date(2026, 7, 1), date_to=date(2026, 7, 31))
    result = PostgresOrderRepository().list_admin_order_export_rows(filters)

    assert result[0].order_no == "O-CSV"
    assert result[0].buyer_phone == "13911112222"
    assert len(calls) == 1
    assert "ticket_order_item" in calls[0][0]
    assert "ORDER BY o.order_time DESC, o.id DESC" in calls[0][0]
    assert "2026-07-01" not in calls[0][0]
    assert "2026-07-31" not in calls[0][0]
    assert calls[0][1] == (date(2026, 7, 1), date(2026, 7, 1), date(2026, 7, 31), date(2026, 7, 31))


def test_postgres_admin_order_export_applies_optional_row_limit(monkeypatch):
    calls: list[tuple[str, tuple[object, ...]]] = []

    class FakeCursor:
        def execute(self, sql: str, params: tuple[object, ...]):
            calls.append((sql, params))
            return self

        def fetchall(self):
            return []

    class FakeConnection:
        def __enter__(self):
            return FakeCursor()

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr(order_repository_module, "connect_db", lambda: FakeConnection())

    PostgresOrderRepository().list_admin_order_export_rows(
        AdminReportFilter(
            date_from=date(2026, 7, 1),
            date_to=date(2026, 7, 31),
            row_limit=77,
        )
    )

    sql, params = calls[0]
    assert "LIMIT %s" in sql
    assert "77" not in sql
    assert params == (date(2026, 7, 1), date(2026, 7, 1), date(2026, 7, 31), date(2026, 7, 31), 77)


@pytest.mark.parametrize(
    "method_name",
    [
        "list_admin_product_breakdown",
        "list_admin_daily_trend",
        "list_admin_hourly_trend",
        "list_admin_monthly_trend",
    ],
)
def test_postgres_admin_report_exports_apply_optional_row_limit(method_name, monkeypatch):
    calls: list[tuple[str, tuple[object, ...]]] = []

    class FakeCursor:
        def execute(self, sql: str, params: tuple[object, ...]):
            calls.append((sql, params))
            return self

        def fetchall(self):
            return []

    class FakeConnection:
        def __enter__(self):
            return FakeCursor()

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr(order_repository_module, "connect_db", lambda: FakeConnection())

    getattr(PostgresOrderRepository(), method_name)(
        AdminReportFilter(
            date_from=date(2026, 7, 1),
            date_to=date(2026, 7, 31),
            row_limit=77,
        )
    )

    sql, params = calls[0]
    assert "LIMIT %s" in sql
    assert "77" not in sql
    assert params == (date(2026, 7, 1), date(2026, 7, 1), date(2026, 7, 31), date(2026, 7, 31), 77)
